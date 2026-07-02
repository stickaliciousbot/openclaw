import { boolEnv, validateNetworkConfig } from '../safety/network-policy.js';

export class ConfigError extends Error {
  constructor(classification, message) {
    super(message);
    this.name = 'ConfigError';
    this.classification = classification;
  }
}

function asInt(value, fallback) {
  const n = Number(value ?? fallback);
  if (!Number.isInteger(n) || n <= 0) return fallback;
  return n;
}

export function loadConfig(env = process.env) {
  const config = {
    workspace: env.WORKSPACE_DIR || '/home/stickai/.openclaw/workspace',
    host: env.HOST || '127.0.0.1',
    port: asInt(env.PORT, 18788),
    allowLan: boolEnv(env.VOICE_DEMO_ALLOW_LAN),
    allowRemoteXtts: boolEnv(env.VOICE_DEMO_ALLOW_REMOTE_XTTS),
    xttsUrl: env.XTTS_URL || 'http://127.0.0.1:8020',
    xttsSpeaker: env.XTTS_SPEAKER || 'reference.wav',
    xttsLanguage: env.XTTS_LANGUAGE || 'en',
    openclawMode: env.OPENCLAW_MODE || 'echo',
    openclawBin: env.OPENCLAW_BIN || 'openclaw',
    openclawArgsJson: env.OPENCLAW_ARGS_JSON || '',
    openclawTimeoutMs: asInt(env.OPENCLAW_TIMEOUT_MS, 120000),
    openclawMaxStdoutBytes: asInt(env.OPENCLAW_MAX_STDOUT_BYTES, 256 * 1024),
    maxJsonBodyBytes: asInt(env.MAX_JSON_BODY_BYTES, 64 * 1024),
    maxTextChars: asInt(env.MAX_TEXT_CHARS, 4000),
    maxAudioUploadBytes: asInt(env.MAX_AUDIO_UPLOAD_BYTES, 8 * 1024 * 1024),
    maxAudioDurationSeconds: asInt(env.MAX_AUDIO_DURATION_SECONDS, 60)
  };

  try {
    validateNetworkConfig({
      host: config.host,
      port: config.port,
      xttsUrl: config.xttsUrl,
      allowLan: config.allowLan,
      allowRemoteXtts: config.allowRemoteXtts
    });
  } catch (e) {
    throw new ConfigError(e.classification || 'BLOCKED_UNSAFE_CONFIG', e.message);
  }

  return Object.freeze(config);
}
