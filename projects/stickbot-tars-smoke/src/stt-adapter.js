import { spawn as spawnChild } from 'node:child_process';

export class SttAdapterError extends Error {
  constructor(classification, message) {
    super(message);
    this.name = 'SttAdapterError';
    this.classification = classification;
  }
}

function asArrayFromJson(value) {
  if (!value) return [];
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch (e) {
    throw new SttAdapterError('STT_ARGS_JSON_INVALID', `STT_ARGS_JSON must be JSON: ${e.message}`);
  }
  if (!Array.isArray(parsed) || !parsed.every((v) => typeof v === 'string')) {
    throw new SttAdapterError('STT_ARGS_JSON_INVALID', 'STT_ARGS_JSON must be an array of strings');
  }
  return parsed;
}

function whitelistedEnv(env = process.env) {
  const out = {};
  for (const key of ['PATH', 'HOME', 'LANG', 'LC_ALL', 'TERM', 'NO_COLOR']) {
    if (env[key] !== undefined) out[key] = env[key];
  }
  return out;
}

function appendBounded(current, chunk, maxBytes, label, child) {
  const next = current + chunk.toString('utf8');
  if (Buffer.byteLength(next) > maxBytes) {
    child.kill('SIGKILL');
    throw new SttAdapterError('STT_STDIO_LIMIT_EXCEEDED', `${label} exceeded ${maxBytes} bytes`);
  }
  return next;
}

function pickTranscript(value) {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return null;
  for (const key of ['text', 'transcript', 'output', 'result']) {
    const picked = pickTranscript(value[key]);
    if (picked) return picked;
  }
  if (Array.isArray(value.segments)) {
    const joined = value.segments.map((s) => s?.text).filter(Boolean).join(' ').trim();
    if (joined) return joined;
  }
  return null;
}

export function parseSttOutput(stdout) {
  const trimmed = String(stdout || '').trim();
  if (!trimmed) throw new SttAdapterError('STT_EMPTY_OUTPUT', 'STT returned empty output');
  try {
    const parsed = JSON.parse(trimmed);
    const transcript = pickTranscript(parsed);
    if (!transcript || !transcript.trim()) throw new SttAdapterError('STT_TRANSCRIPT_NOT_FOUND', 'STT JSON output did not contain transcript text');
    return transcript.trim();
  } catch (e) {
    if (e instanceof SttAdapterError) throw e;
    // Plain text CLI output is accepted for local tools that do not support JSON.
    return trimmed;
  }
}

export function buildSttCommand(config, audioPath) {
  const args = asArrayFromJson(config.sttArgsJson).map((a) => (a === '{file}' ? audioPath : a));
  if (!args.includes(audioPath)) {
    throw new SttAdapterError('STT_FILE_PLACEHOLDER_MISSING', 'STT args must include a {file} placeholder');
  }
  if (args.length > 64) throw new SttAdapterError('STT_ARGS_TOO_MANY', 'STT args exceed safety limit');
  return { file: config.sttBin, args };
}

export async function transcribeAudio(audioPath, config, options = {}) {
  if (config.sttMode === 'capture') {
    throw new SttAdapterError('STT_CAPTURE_ONLY', 'Local STT not wired yet; audio was captured only');
  }
  if (config.sttMode === 'fixture') {
    return config.sttFixtureText;
  }
  if (config.sttMode !== 'cli') {
    throw new SttAdapterError('STT_MODE_UNSUPPORTED', `Unsupported STT mode: ${config.sttMode}`);
  }

  const spawnImpl = options.spawnImpl || spawnChild;
  const { file, args } = buildSttCommand(config, audioPath);
  const timeoutMs = config.sttTimeoutMs;
  const maxBytes = config.sttMaxStdoutBytes;

  return await new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    let settled = false;
    let child;
    let timer;

    function finish(err, value) {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      if (err) reject(err);
      else resolve(value);
    }

    try {
      child = spawnImpl(file, args, {
        cwd: config.workspace,
        shell: false,
        windowsHide: true,
        env: whitelistedEnv(options.env || process.env),
        stdio: ['ignore', 'pipe', 'pipe']
      });
    } catch (e) {
      return finish(new SttAdapterError('STT_SPAWN_FAILED', e.message));
    }

    timer = setTimeout(() => {
      child.kill('SIGKILL');
      finish(new SttAdapterError('STT_TIMEOUT', `STT command timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    child.stdout.on('data', (d) => {
      try { stdout = appendBounded(stdout, d, maxBytes, 'stdout', child); }
      catch (e) { finish(e); }
    });
    child.stderr.on('data', (d) => {
      try { stderr = appendBounded(stderr, d, maxBytes, 'stderr', child); }
      catch (e) { finish(e); }
    });
    child.on('error', (e) => finish(new SttAdapterError('STT_SPAWN_FAILED', e.message)));
    child.on('close', (code) => {
      if (settled) return;
      if (code !== 0) {
        return finish(new SttAdapterError('STT_EXIT_NONZERO', `STT CLI exited ${code}: ${(stderr || stdout).slice(0, 1000)}`));
      }
      try { finish(null, parseSttOutput(stdout)); }
      catch (e) { finish(e); }
    });
  });
}
