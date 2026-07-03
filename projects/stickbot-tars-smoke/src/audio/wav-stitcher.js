import { spawn } from 'node:child_process';
import { copyFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

function assertSafeAudioPath(filePath, label = 'audio path') {
  const s = String(filePath || '');
  if (!path.isAbsolute(s)) throw new Error(`${label} must be absolute`);
  if (s === '/mnt/c' || s.startsWith('/mnt/c/')) {
    const e = new Error(`${label} must use WSL-native storage, not /mnt/c.`);
    e.classification = 'BLOCKED_MNT_C_AUDIO_PATH';
    throw e;
  }
  return s;
}

function quoteConcatPath(filePath) {
  return String(filePath).replace(/'/g, "'\\''");
}

function runFfmpeg(ffmpegBin, args, { timeoutMs = 60000, maxStderrBytes = 64 * 1024 } = {}) {
  assertSafeAudioPath(ffmpegBin, 'ffmpeg binary');
  return new Promise((resolve, reject) => {
    const child = spawn(ffmpegBin, args, { shell: false, stdio: ['ignore', 'ignore', 'pipe'] });
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      const e = new Error('FFMPEG_TIMEOUT');
      e.classification = 'FFMPEG_TIMEOUT';
      reject(e);
    }, timeoutMs);
    child.stderr.on('data', (buf) => {
      stderr += buf.toString('utf8');
      if (Buffer.byteLength(stderr) > maxStderrBytes) stderr = stderr.slice(-maxStderrBytes);
    });
    child.on('error', (e) => {
      clearTimeout(timer);
      reject(e);
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code === 0) return resolve({ code, stderr });
      const e = new Error(`FFMPEG_EXIT_${code}: ${stderr}`);
      e.classification = 'FFMPEG_STITCH_FAIL';
      e.exitCode = code;
      e.stderr = stderr;
      reject(e);
    });
  });
}

export async function createSilenceWav({ ffmpegBin, outPath, durationMs, sampleRate = 24000, channels = 1, timeoutMs = 60000 } = {}) {
  const out = assertSafeAudioPath(outPath, 'silence output path');
  await mkdir(path.dirname(out), { recursive: true });
  const seconds = Math.max(0.01, Number(durationMs || 0) / 1000).toFixed(3);
  await runFfmpeg(ffmpegBin, [
    '-hide_banner',
    '-y',
    '-f', 'lavfi',
    '-i', `anullsrc=r=${sampleRate}:cl=${channels === 1 ? 'mono' : 'stereo'}`,
    '-t', seconds,
    '-acodec', 'pcm_s16le',
    '-ar', String(sampleRate),
    '-ac', String(channels),
    out
  ], { timeoutMs });
  return out;
}

export async function stitchWavSequence({
  ffmpegBin,
  sequence = [],
  outPath,
  workDir,
  sampleRate = 24000,
  channels = 1,
  timeoutMs = 60000
} = {}) {
  const out = assertSafeAudioPath(outPath, 'stitched output path');
  const root = assertSafeAudioPath(workDir || path.dirname(out), 'stitch work dir');
  await mkdir(root, { recursive: true });
  await mkdir(path.dirname(out), { recursive: true });

  const audioEntries = [];
  for (const [index, entry] of sequence.entries()) {
    const file = assertSafeAudioPath(entry.file, `sequence[${index}].file`);
    audioEntries.push(file);
    const pauseMs = Math.max(0, Number(entry.pauseAfterMs || 0));
    if (pauseMs >= 20 && index < sequence.length - 1) {
      const silencePath = path.join(root, `silence-${String(index + 1).padStart(3, '0')}-${Math.round(pauseMs)}ms.wav`);
      await createSilenceWav({ ffmpegBin, outPath: silencePath, durationMs: pauseMs, sampleRate, channels, timeoutMs });
      audioEntries.push(silencePath);
    }
  }

  if (audioEntries.length === 0) {
    const e = new Error('No audio entries supplied to stitcher.');
    e.classification = 'AUDIO_STITCH_EMPTY_SEQUENCE';
    throw e;
  }

  if (audioEntries.length === 1) {
    await copyFile(audioEntries[0], out);
    return { file: out, renderer: 'single_chunk_copy', entries: audioEntries };
  }

  const listPath = path.join(root, 'concat-list.txt');
  await writeFile(listPath, audioEntries.map((file) => `file '${quoteConcatPath(file)}'`).join('\n') + '\n', 'utf8');
  await runFfmpeg(ffmpegBin, [
    '-hide_banner',
    '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', listPath,
    '-acodec', 'pcm_s16le',
    '-ar', String(sampleRate),
    '-ac', String(channels),
    out
  ], { timeoutMs });

  return { file: out, renderer: 'ffmpeg_concat_with_silence', entries: audioEntries, concatList: listPath };
}
