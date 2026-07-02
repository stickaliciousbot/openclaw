import { spawn as spawnChild } from 'node:child_process';
import path from 'node:path';

export class AudioNormalizerError extends Error {
  constructor(classification, message) {
    super(message);
    this.name = 'AudioNormalizerError';
    this.classification = classification;
  }
}

function appendBounded(current, chunk, maxBytes, label, child) {
  const next = current + chunk.toString('utf8');
  if (Buffer.byteLength(next) > maxBytes) {
    child.kill('SIGKILL');
    throw new AudioNormalizerError('AUDIO_NORMALIZER_STDIO_LIMIT_EXCEEDED', `${label} exceeded ${maxBytes} bytes`);
  }
  return next;
}

function assertSafePath(label, filePath) {
  const resolved = path.resolve(filePath);
  if (resolved.startsWith('/mnt/c/') || resolved === '/mnt/c') {
    throw new AudioNormalizerError('AUDIO_NORMALIZER_MNT_C_PATH_BLOCKED', `${label} must be WSL-native, not /mnt/c`);
  }
  if (resolved.includes('\0')) {
    throw new AudioNormalizerError('AUDIO_NORMALIZER_BAD_PATH', `${label} contains NUL`);
  }
  return resolved;
}

export function buildFfmpegNormalizeCommand(config, inputPath, outputPath) {
  if (!config.ffmpegBin) throw new AudioNormalizerError('FFMPEG_BIN_MISSING', 'FFMPEG_BIN is required');
  const file = assertSafePath('ffmpeg binary', config.ffmpegBin);
  const input = assertSafePath('input audio', inputPath);
  const output = assertSafePath('output audio', outputPath);
  return {
    file,
    args: [
      '-nostdin',
      '-hide_banner',
      '-loglevel',
      'error',
      '-y',
      '-i',
      input,
      '-ac',
      '1',
      '-ar',
      '16000',
      '-f',
      'wav',
      output
    ]
  };
}

export async function normalizeAudio(inputPath, outputPath, config, options = {}) {
  const spawnImpl = options.spawnImpl || spawnChild;
  const { file, args } = buildFfmpegNormalizeCommand(config, inputPath, outputPath);
  const timeoutMs = config.audioNormalizeTimeoutMs;
  const maxBytes = config.audioNormalizeMaxStderrBytes;

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
        env: {
          PATH: process.env.PATH || '/usr/bin:/bin',
          LANG: process.env.LANG || 'C.UTF-8',
          LC_ALL: process.env.LC_ALL || 'C.UTF-8'
        },
        stdio: ['ignore', 'pipe', 'pipe']
      });
    } catch (e) {
      return finish(new AudioNormalizerError('AUDIO_NORMALIZER_SPAWN_FAILED', e.message));
    }

    timer = setTimeout(() => {
      child.kill('SIGKILL');
      finish(new AudioNormalizerError('AUDIO_NORMALIZER_TIMEOUT', `ffmpeg timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    child.stdout.on('data', (d) => {
      try { stdout = appendBounded(stdout, d, maxBytes, 'stdout', child); }
      catch (e) { finish(e); }
    });
    child.stderr.on('data', (d) => {
      try { stderr = appendBounded(stderr, d, maxBytes, 'stderr', child); }
      catch (e) { finish(e); }
    });
    child.on('error', (e) => finish(new AudioNormalizerError('AUDIO_NORMALIZER_SPAWN_FAILED', e.message)));
    child.on('close', (code) => {
      if (settled) return;
      if (code !== 0) {
        return finish(new AudioNormalizerError('AUDIO_NORMALIZER_EXIT_NONZERO', `ffmpeg exited ${code}: ${(stderr || stdout).slice(0, 1000)}`));
      }
      finish(null, { inputPath, outputPath, format: 'wav', channels: 1, sampleRate: 16000 });
    });
  });
}
