import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

export const DSP_FRAME_SCHEMA = 'stickbot.tars.audio-dsp-frame.v1';

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

function clamp(n, min, max, fallback = min) {
  const x = Number(n);
  if (!Number.isFinite(x)) return fallback;
  return Math.min(max, Math.max(min, x));
}

function runFfmpeg(ffmpegBin, args, { timeoutMs = 60000, maxStderrBytes = 64 * 1024 } = {}) {
  assertSafeAudioPath(ffmpegBin, 'ffmpeg binary');
  return new Promise((resolve, reject) => {
    const child = spawn(ffmpegBin, args, { shell: false, stdio: ['ignore', 'ignore', 'pipe'] });
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      const e = new Error('DSP_FFMPEG_TIMEOUT');
      e.classification = 'DSP_FFMPEG_TIMEOUT';
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
      const e = new Error(`DSP_FFMPEG_EXIT_${code}: ${stderr}`);
      e.classification = 'DSP_FFMPEG_FAIL';
      e.exitCode = code;
      e.stderr = stderr;
      reject(e);
    });
  });
}

export function deriveDspProfileFromProsody({ phraseRole = 'evidence', effectiveXtts = {}, voicePersona = 'TARS' } = {}) {
  const speed = clamp(effectiveXtts.speed, 0.88, 1.12, 1);
  const isWarning = phraseRole === 'warning' || phraseRole === 'blocker';
  const isPunchline = phraseRole === 'punchline' || phraseRole === 'aside';
  return {
    schema: 'stickbot.tars.dsp-profile.v1',
    mode: 'local_ffmpeg_light_polish',
    loudnessI: voicePersona === 'CASE' ? -18 : -17,
    loudnessTp: -1.5,
    loudnessLra: isWarning ? 7 : 9,
    compressorThresholdDb: isWarning ? -22 : -24,
    compressorRatio: isWarning ? 2.2 : 1.7,
    limiterLimit: isPunchline ? 0.9 : 0.86,
    atempo: clamp(speed, 0.92, 1.08, 1),
    notes: {
      phraseRole,
      personaBias: voicePersona,
      intent: 'subtle polish only; no voice identity rewrite'
    }
  };
}

export function buildDspFilterGraph(profile = {}) {
  const atempo = clamp(profile.atempo, 0.5, 2, 1);
  const threshold = clamp(profile.compressorThresholdDb, -60, 0, -24);
  const ratio = clamp(profile.compressorRatio, 1, 20, 1.7);
  const limit = clamp(profile.limiterLimit, 0.2, 1, 0.86);
  const i = clamp(profile.loudnessI, -70, -5, -17);
  const tp = clamp(profile.loudnessTp, -9, 0, -1.5);
  const lra = clamp(profile.loudnessLra, 1, 20, 9);
  return [
    `acompressor=threshold=${threshold}dB:ratio=${ratio}:attack=8:release=80`,
    `alimiter=limit=${limit}`,
    `loudnorm=I=${i}:TP=${tp}:LRA=${lra}`,
    `atempo=${atempo.toFixed(3)}`
  ].join(',');
}

export async function polishAudioFrameWithFfmpeg({
  ffmpegBin,
  inputFile,
  outputFile,
  profile,
  sampleRate = 24000,
  channels = 1,
  timeoutMs = 60000
} = {}) {
  const input = assertSafeAudioPath(inputFile, 'DSP input file');
  const output = assertSafeAudioPath(outputFile, 'DSP output file');
  await mkdir(path.dirname(output), { recursive: true });
  const filter = buildDspFilterGraph(profile);
  await runFfmpeg(ffmpegBin, [
    '-hide_banner',
    '-y',
    '-i', input,
    '-af', filter,
    '-acodec', 'pcm_s16le',
    '-ar', String(sampleRate),
    '-ac', String(channels),
    output
  ], { timeoutMs });
  return {
    schema: DSP_FRAME_SCHEMA,
    classification: 'STICKBOT_TARS_M7J_DSP_FRAME_POLISHED',
    inputFile,
    outputFile,
    filter,
    profile,
    boundaries: {
      localOnly: true,
      textRewriteAllowed: false,
      voiceIdentityRewriteAllowed: false
    }
  };
}

export async function polishChunkArtifacts({
  chunkArtifacts = [],
  ffmpegBin,
  outputDir,
  voicePersona = 'TARS',
  processor = polishAudioFrameWithFfmpeg,
  timeoutMs = 60000
} = {}) {
  if (!chunkArtifacts.length) {
    return {
      schema: 'stickbot.tars.dsp-stage.v1',
      enabled: false,
      frameSchema: DSP_FRAME_SCHEMA,
      frames: [],
      artifacts: chunkArtifacts,
      classification: 'STICKBOT_TARS_M7J_DSP_STAGE_EMPTY_NOOP'
    };
  }
  const root = assertSafeAudioPath(outputDir, 'DSP output dir');
  await mkdir(root, { recursive: true });
  const frames = [];
  const polishedArtifacts = [];
  for (const artifact of chunkArtifacts) {
    const profile = deriveDspProfileFromProsody({
      phraseRole: artifact.phraseRole,
      effectiveXtts: artifact.effectiveXtts,
      voicePersona
    });
    const outputFile = path.join(root, `${path.basename(artifact.file, path.extname(artifact.file))}.dsp.wav`);
    const frame = await processor({
      ffmpegBin,
      inputFile: artifact.file,
      outputFile,
      profile,
      timeoutMs
    });
    frames.push({
      schema: DSP_FRAME_SCHEMA,
      chunkId: artifact.chunkId,
      chunkIndex: artifact.chunkIndex,
      textSha256: artifact.textSha256,
      phraseRole: artifact.phraseRole,
      inputAudioSha256: artifact.audioSha256 || null,
      outputFileBasename: path.basename(frame.outputFile || outputFile),
      filter: frame.filter || null,
      profile,
      classification: frame.classification || 'STICKBOT_TARS_M7J_DSP_FRAME_POLISHED'
    });
    polishedArtifacts.push({
      ...artifact,
      preDspFile: artifact.file,
      file: frame.outputFile || outputFile,
      fileBasename: path.basename(frame.outputFile || outputFile),
      dsp: frames.at(-1)
    });
  }
  return {
    schema: 'stickbot.tars.dsp-stage.v1',
    enabled: true,
    frameSchema: DSP_FRAME_SCHEMA,
    classification: 'STICKBOT_TARS_M7J_DSP_STAGE_LOCAL_PASS',
    frames,
    artifacts: polishedArtifacts,
    boundaries: {
      localOnly: true,
      textRewriteAllowed: false,
      voiceIdentityRewriteAllowed: false
    }
  };
}

export function publicDspStageSummary(stage = {}) {
  return {
    schema: stage.schema || 'stickbot.tars.dsp-stage.v1',
    enabled: Boolean(stage.enabled),
    interfaceReserved: stage.interfaceReserved || !stage.enabled,
    frameSchema: stage.frameSchema || DSP_FRAME_SCHEMA,
    classification: stage.classification,
    frames: (stage.frames || []).map((frame) => ({
      schema: frame.schema,
      chunkId: frame.chunkId,
      chunkIndex: frame.chunkIndex,
      textSha256: frame.textSha256,
      phraseRole: frame.phraseRole,
      inputAudioSha256: frame.inputAudioSha256,
      outputFileBasename: frame.outputFileBasename,
      filter: frame.filter,
      profile: frame.profile,
      classification: frame.classification
    })),
    boundaries: stage.boundaries
  };
}
