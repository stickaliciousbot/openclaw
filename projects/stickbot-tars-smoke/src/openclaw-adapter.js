import { spawn as spawnChild } from 'node:child_process';

export class OpenClawAdapterError extends Error {
  constructor(classification, message) {
    super(message);
    this.name = 'OpenClawAdapterError';
    this.classification = classification;
  }
}

const DEFAULT_ARGS_BY_MODE = Object.freeze({
  cli: ['agent', '--message', '{prompt}', '--json'],
  infer: ['infer', 'model', 'run', '--prompt', '{prompt}', '--json'],
  agent: ['agent', '--message', '{prompt}', '--json']
});

function asArrayFromJson(value, fallback) {
  if (!value) return fallback;
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch (e) {
    throw new OpenClawAdapterError('OPENCLAW_ARGS_JSON_INVALID', `OPENCLAW_ARGS_JSON must be JSON: ${e.message}`);
  }
  if (!Array.isArray(parsed) || !parsed.every((v) => typeof v === 'string')) {
    throw new OpenClawAdapterError('OPENCLAW_ARGS_JSON_INVALID', 'OPENCLAW_ARGS_JSON must be an array of strings');
  }
  return parsed;
}

function boundedAppend(current, chunk, maxBytes, label, child) {
  const next = current + chunk.toString('utf8');
  if (Buffer.byteLength(next) > maxBytes) {
    child.kill('SIGKILL');
    throw new OpenClawAdapterError('OPENCLAW_STDIO_LIMIT_EXCEEDED', `${label} exceeded ${maxBytes} bytes`);
  }
  return next;
}

function whitelistedEnv(env = process.env) {
  const out = {};
  for (const key of ['PATH', 'HOME', 'LANG', 'LC_ALL', 'TERM', 'NO_COLOR', 'OPENCLAW_STATE_DIR', 'OPENCLAW_CONFIG_PATH', 'OPENCLAW_GATEWAY_URL', 'OPENCLAW_PROFILE']) {
    if (env[key] !== undefined) out[key] = env[key];
  }
  return out;
}

function pickText(value) {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return null;
  for (const key of ['text', 'output', 'response', 'content', 'message', 'reply', 'result']) {
    const picked = pickText(value[key]);
    if (picked) return picked;
  }
  if (Array.isArray(value.choices)) {
    for (const choice of value.choices) {
      const picked = pickText(choice?.message?.content ?? choice?.text ?? choice?.content);
      if (picked) return picked;
    }
  }
  if (Array.isArray(value.messages)) {
    for (const message of value.messages) {
      const picked = pickText(message?.content ?? message?.text);
      if (picked) return picked;
    }
  }
  return null;
}

export function parseOpenClawJsonOutput(stdout) {
  const trimmed = String(stdout || '').trim();
  if (!trimmed) {
    throw new OpenClawAdapterError('OPENCLAW_EMPTY_OUTPUT', 'OpenClaw returned empty output');
  }
  let parsed;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    // Some CLIs print logs before a final JSON object. Try the last JSON-looking line.
    const line = trimmed.split(/\r?\n/).reverse().find((l) => l.trim().startsWith('{') || l.trim().startsWith('['));
    if (!line) throw new OpenClawAdapterError('OPENCLAW_JSON_PARSE_FAILED', 'OpenClaw JSON output could not be parsed');
    try {
      parsed = JSON.parse(line);
    } catch (e) {
      throw new OpenClawAdapterError('OPENCLAW_JSON_PARSE_FAILED', `OpenClaw JSON output could not be parsed: ${e.message}`);
    }
  }
  const text = pickText(parsed);
  if (!text || !String(text).trim()) {
    throw new OpenClawAdapterError('OPENCLAW_TEXT_NOT_FOUND', 'OpenClaw JSON output did not contain text');
  }
  return String(text).trim();
}

export function buildOpenClawCommand(config, prompt) {
  const mode = config.openclawMode;
  if (!['cli', 'infer', 'agent'].includes(mode)) {
    throw new OpenClawAdapterError('OPENCLAW_MODE_UNSUPPORTED', `Unsupported OpenClaw mode: ${mode}`);
  }
  const fallback = DEFAULT_ARGS_BY_MODE[mode];
  const args = asArrayFromJson(config.openclawArgsJson, fallback).map((a) => (a === '{prompt}' ? prompt : a));
  if (!args.includes(prompt)) {
    throw new OpenClawAdapterError('OPENCLAW_PROMPT_PLACEHOLDER_MISSING', 'OpenClaw args must include a {prompt} placeholder');
  }
  if (args.length > 64) {
    throw new OpenClawAdapterError('OPENCLAW_ARGS_TOO_MANY', 'OpenClaw args exceed safety limit');
  }
  return { file: config.openclawBin, args };
}

export async function askOpenClaw(prompt, config, options = {}) {
  if (config.openclawMode === 'echo') {
    return `Echo smoke response: ${prompt}`;
  }

  const spawnImpl = options.spawnImpl || spawnChild;
  const timeoutMs = config.openclawTimeoutMs;
  const maxBytes = config.openclawMaxStdoutBytes;
  const { file, args } = buildOpenClawCommand(config, prompt);

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
      return finish(new OpenClawAdapterError('OPENCLAW_SPAWN_FAILED', e.message));
    }

    timer = setTimeout(() => {
      child.kill('SIGKILL');
      finish(new OpenClawAdapterError('OPENCLAW_TIMEOUT', `OpenClaw command timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    child.stdout.on('data', (d) => {
      try { stdout = boundedAppend(stdout, d, maxBytes, 'stdout', child); }
      catch (e) { finish(e); }
    });
    child.stderr.on('data', (d) => {
      try { stderr = boundedAppend(stderr, d, maxBytes, 'stderr', child); }
      catch (e) { finish(e); }
    });
    child.on('error', (e) => finish(new OpenClawAdapterError('OPENCLAW_SPAWN_FAILED', e.message)));
    child.on('close', (code) => {
      if (settled) return;
      if (code !== 0) {
        return finish(new OpenClawAdapterError('OPENCLAW_EXIT_NONZERO', `OpenClaw CLI exited ${code}: ${(stderr || stdout).slice(0, 1000)}`));
      }
      try {
        const text = config.openclawMode === 'cli' ? String(stdout || '').trim() : parseOpenClawJsonOutput(stdout);
        if (!text) throw new OpenClawAdapterError('OPENCLAW_EMPTY_OUTPUT', 'OpenClaw returned empty output');
        finish(null, text);
      } catch (e) {
        finish(e);
      }
    });
  });
}
