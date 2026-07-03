import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

export const VOICE_BODY_MASTERING_SCHEMA = 'stickbot.tars.voice-body-mastering-stage.v1';
export const VOICE_BODY_MASTERING_FRAME_SCHEMA = 'stickbot.tars.voice-body-mastering-frame.v1';

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
      const e = new Error('VOICE_BODY_MASTERING_FFMPEG_TIMEOUT');
      e.classification = 'VOICE_BODY_MASTERING_FFMPEG_TIMEOUT';
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
      const e = new Error(`VOICE_BODY_MASTERING_FFMPEG_EXIT_${code}: ${stderr}`);
      e.classification = 'VOICE_BODY_MASTERING_FFMPEG_FAIL';
      e.exitCode = code;
      e.stderr = stderr;
      reject(e);
    });
  });
}

export function deriveVoiceBodyMasteringProfile({ voicePersona = 'TARS', strength = 'light' } = {}) {
  const isCase = voicePersona === 'CASE';
  const heavier = strength === 'body' || strength === 'heavier';
  return {
    schema: 'stickbot.tars.voice-body-mastering-profile.v1',
    mode: 'local_ffmpeg_voice_body_mastering',
    trimLeadingSilenceOnly: true,
    trimEndingSilence: false,
    tailGuardPadMs: 900,
    highpassHz: heavier ? 55 : 60,
    bodyEq: {
      lowBodyHz: heavier ? 150 : 170,
      lowBodyGainDb: heavier ? 4 : 3,
      lowBodyQ: heavier ? 0.9 : 1.0,
      upperBodyHz: heavier ? 240 : 320,
      upperBodyGainDb: heavier ? 2 : 1.5,
      upperBodyQ: heavier ? 1.0 : 1.2,
      presenceHz: heavier ? 2800 : 3200,
      presenceGainDb: heavier ? -2 : -1.5,
      presenceQ: heavier ? 1.4 : 1.2
    },
    compressor: {
      thresholdDb: heavier ? -22 : -20,
      ratio: heavier ? 2.8 : 2.2,
      attackMs: heavier ? 10 : 8,
      releaseMs: heavier ? 120 : 90,
      makeupDb: heavier ? 3 : 2
    },
    loudness: {
      integratedLUFS: isCase ? -18 : (heavier ? -17 : -18),
      truePeakDb: -1.5,
      lra: heavier ? 8 : 9
    },
    output: {
      codec: 'pcm_s16le',
      sampleRate: 48000,
      channels: 1,
      bitRate: 768000
    },
    boundaries: {
      localOnly: true,
      canonicalTextAuthoritative: true,
      textRewriteAllowed: false,
      voiceIdentityRewriteAllowed: false,
      stereoWideningApplied: false
    },
    notes: {
      intent: 'light body/mastering for browser playback; raw XTTS and DSP intermediates remain preserved',
      caution: 'avoid excessive 150-250 Hz boost to prevent mud'
    }
  };
}

export function buildVoiceBodyMasteringFilterGraph(profile = {}) {
  const highpassHz = clamp(profile.highpassHz, 40, 120, 60);
  const eq = profile.bodyEq || {};
  const comp = profile.compressor || {};
  const loud = profile.loudness || {};
  return [
    'silenceremove=start_periods=1:start_duration=0.03:start_threshold=-50dB',
    `highpass=f=${highpassHz}`,
    `equalizer=f=${clamp(eq.lowBodyHz, 100, 260, 170)}:t=q:w=${clamp(eq.lowBodyQ, 0.4, 3, 1).toFixed(2)}:g=${clamp(eq.lowBodyGainDb, -3, 5, 3).toFixed(1)}`,
    `equalizer=f=${clamp(eq.upperBodyHz, 180, 500, 320)}:t=q:w=${clamp(eq.upperBodyQ, 0.4, 3, 1.2).toFixed(2)}:g=${clamp(eq.upperBodyGainDb, -3, 3, 1.5).toFixed(1)}`,
    `equalizer=f=${clamp(eq.presenceHz, 1800, 4500, 3200)}:t=q:w=${clamp(eq.presenceQ, 0.4, 3, 1.2).toFixed(2)}:g=${clamp(eq.presenceGainDb, -4, 3, -1.5).toFixed(1)}`,
    `acompressor=threshold=${clamp(comp.thresholdDb, -36, -8, -20)}dB:ratio=${clamp(comp.ratio, 1, 6, 2.2).toFixed(2)}:attack=${clamp(comp.attackMs, 1, 50, 8)}:release=${clamp(comp.releaseMs, 20, 400, 90)}:makeup=${clamp(comp.makeupDb, 0, 8, 2).toFixed(1)}`,
    `loudnorm=I=${clamp(loud.integratedLUFS, -30, -12, -18)}:TP=${clamp(loud.truePeakDb, -6, -0.5, -1.5)}:LRA=${clamp(loud.lra, 3, 20, 9)}`,
    `apad=pad_dur=${(clamp(profile.tailGuardPadMs, 0, 1500, 900) / 1000).toFixed(3)}`
  ].join(',');
}

export async function masterVoiceBodyFrameWithFfmpeg({
  ffmpegBin,
  inputFile,
  outputFile,
  profile,
  timeoutMs = 60000
} = {}) {
  const input = assertSafeAudioPath(inputFile, 'voice body input file');
  const output = assertSafeAudioPath(outputFile, 'voice body output file');
  const p = profile || deriveVoiceBodyMasteringProfile();
  await mkdir(path.dirname(output), { recursive: true });
  const filter = buildVoiceBodyMasteringFilterGraph(p);
  await runFfmpeg(ffmpegBin, [
    '-hide_banner',
    '-y',
    '-i', input,
    '-af', filter,
    '-acodec', p.output?.codec || 'pcm_s16le',
    '-ar', String(p.output?.sampleRate || 48000),
    '-ac', String(p.output?.channels || 1),
    output
  ], { timeoutMs });
  return {
    schema: VOICE_BODY_MASTERING_FRAME_SCHEMA,
    classification: 'STICKBOT_TARS_M56_VOICE_BODY_FRAME_MASTERED',
    inputFile,
    outputFile,
    filter,
    profile: p,
    boundaries: p.boundaries
  };
}

export async function masterVoiceBodyArtifacts({
  chunkArtifacts = [],
  ffmpegBin,
  outputDir,
  voicePersona = 'TARS',
  strength = 'light',
  processor = masterVoiceBodyFrameWithFfmpeg,
  timeoutMs = 60000
} = {}) {
  if (!chunkArtifacts.length) {
    return {
      schema: VOICE_BODY_MASTERING_SCHEMA,
      enabled: false,
      frameSchema: VOICE_BODY_MASTERING_FRAME_SCHEMA,
      frames: [],
      artifacts: chunkArtifacts,
      classification: 'STICKBOT_TARS_M56_VOICE_BODY_EMPTY_NOOP'
    };
  }
  const root = assertSafeAudioPath(outputDir, 'voice body output dir');
  await mkdir(root, { recursive: true });
  const profile = deriveVoiceBodyMasteringProfile({ voicePersona, strength });
  const frames = [];
  const masteredArtifacts = [];
  for (const artifact of chunkArtifacts) {
    const ext = path.extname(artifact.file);
    const outputFile = path.join(root, `${path.basename(artifact.file, ext)}.master.wav`);
    const frame = await processor({
      ffmpegBin,
      inputFile: artifact.file,
      outputFile,
      profile,
      timeoutMs
    });
    frames.push({
      schema: VOICE_BODY_MASTERING_FRAME_SCHEMA,
      chunkId: artifact.chunkId,
      chunkIndex: artifact.chunkIndex,
      textSha256: artifact.textSha256,
      phraseRole: artifact.phraseRole,
      inputFileBasename: path.basename(artifact.file),
      outputFileBasename: path.basename(frame.outputFile || outputFile),
      filter: frame.filter || null,
      profile,
      classification: frame.classification || 'STICKBOT_TARS_M56_VOICE_BODY_FRAME_MASTERED'
    });
    masteredArtifacts.push({
      ...artifact,
      preMasterFile: artifact.file,
      file: frame.outputFile || outputFile,
      fileBasename: path.basename(frame.outputFile || outputFile),
      mastering: frames.at(-1)
    });
  }
  return {
    schema: VOICE_BODY_MASTERING_SCHEMA,
    enabled: true,
    frameSchema: VOICE_BODY_MASTERING_FRAME_SCHEMA,
    classification: 'STICKBOT_TARS_M56_VOICE_BODY_POSTPROCESS_PASS',
    frames,
    artifacts: masteredArtifacts,
    format: profile.output,
    boundaries: profile.boundaries
  };
}

export function publicVoiceBodyMasteringSummary(stage = {}) {
  return {
    schema: stage.schema || VOICE_BODY_MASTERING_SCHEMA,
    enabled: Boolean(stage.enabled),
    frameSchema: stage.frameSchema || VOICE_BODY_MASTERING_FRAME_SCHEMA,
    classification: stage.classification,
    format: stage.format || null,
    frames: (stage.frames || []).map((frame) => ({
      schema: frame.schema,
      chunkId: frame.chunkId,
      chunkIndex: frame.chunkIndex,
      textSha256: frame.textSha256,
      phraseRole: frame.phraseRole,
      inputFileBasename: frame.inputFileBasename,
      outputFileBasename: frame.outputFileBasename,
      filter: frame.filter,
      profile: frame.profile,
      classification: frame.classification
    })),
    boundaries: stage.boundaries
  };
}
