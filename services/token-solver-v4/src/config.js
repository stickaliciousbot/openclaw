import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { loadIntentPreselectorV5State } from './intentPreselectorV5ControlSurface.js';

function loadDotEnv() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const candidates = [
    path.resolve(here, '../.env'),
    path.resolve(here, '../../token-solver-v3/.env'),
    path.resolve(process.cwd(), '.env')
  ];

  for (const envPath of candidates) {
    if (!fs.existsSync(envPath)) continue;
    const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
    for (const line of lines) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const i = t.indexOf('=');
      if (i <= 0) continue;
      const key = t.slice(0, i).trim();
      const value = t.slice(i + 1).trim();
      if (process.env[key] === undefined) process.env[key] = value;
    }
  }
}

loadDotEnv();

const intentPreselectorV5State = loadIntentPreselectorV5State();

export const config = {
  serviceId: 'token-solver-v4',
  port: Number(process.env.TOKEN_SOLVER_V4_PORT || 8800),
  apiKey: String(process.env.TOKEN_SOLVER_V4_API_KEY || ''),
  stateDir: String(process.env.TOKEN_SOLVER_V4_STATE_DIR || '/home/stickai/.openclaw/workspace/state/token-solver-v4'),
  upstreamV3BaseUrl: String(process.env.TOKEN_SOLVER_V4_UPSTREAM_V3_BASE_URL || 'http://127.0.0.1:8799').replace(/\/$/, ''),
  upstreamV3ApiKey: String(process.env.TOKEN_SOLVER_V4_UPSTREAM_V3_API_KEY || process.env.TOKEN_SOLVER_V3_API_KEY || ''),
  upstreamV3RecoveryScript: String(process.env.TOKEN_SOLVER_V4_UPSTREAM_V3_RECOVERY_SCRIPT || '/home/stickai/.openclaw/workspace/scripts/restart_token_solver_v3.sh'),
  upstreamV3RecoveryTimeoutMs: Number(process.env.TOKEN_SOLVER_V4_UPSTREAM_V3_RECOVERY_TIMEOUT_MS || 90000),
  upstreamV3RecoveryCooldownMs: Number(process.env.TOKEN_SOLVER_V4_UPSTREAM_V3_RECOVERY_COOLDOWN_MS || 30000),
  upstreamV3HealthTimeoutMs: Number(process.env.TOKEN_SOLVER_V4_UPSTREAM_V3_HEALTH_TIMEOUT_MS || 2500),
  // Keep v4's upstream budget below the OpenClaw gateway client's 120s default
  // so v4 can fail closed with a structured response instead of letting the
  // gateway hang/timeout first.
  requestTimeoutMs: Number(process.env.TOKEN_SOLVER_V4_REQUEST_TIMEOUT_MS || 105000),
  // Simple/nano turns still traverse token-solver-v3 and may hit a cold or
  // locally-routed nano backend. Keep this comfortably below Gateway's 120s
  // client budget, but not so low that healthy simple turns fail as v4 504s.
  simpleForwardTimeoutMs: Number(process.env.TOKEN_SOLVER_V4_SIMPLE_FORWARD_TIMEOUT_MS || 60000),
  // Explicit local Ollama lanes need enough time for a cold warmup plus the
  // local generation window. Default: 120s warmup + 420s generation + 30s
  // cushion. This is intentionally separate from requestTimeoutMs, which stays
  // Gateway-bounded for default/status/tool-required routes.
  localForwardTimeoutMs: Number(process.env.TOKEN_SOLVER_V4_LOCAL_FORWARD_TIMEOUT_MS || (
    Number(process.env.OLLAMA_WARMUP_TIMEOUT_SEC || 120) * 1000
    + Number(process.env.V3_LOCAL_GENERATE_TIMEOUT_MS || process.env.V2_LOCAL_GENERATE_TIMEOUT_MS || 420000)
    + 30000
  )),
  localAgenticMaxChars: Number(process.env.TOKEN_SOLVER_V4_LOCAL_AGENTIC_MAX_CHARS || 6000),
  localReasoningMaxChars: Number(process.env.TOKEN_SOLVER_V4_LOCAL_REASONING_MAX_CHARS || 10000),
  ollamaCloudHeavyCoderForwardTimeoutMs: Number(process.env.TOKEN_SOLVER_V4_OLLAMA_CLOUD_HEAVY_CODER_FORWARD_TIMEOUT_MS || 105000),
  complexPlanningMinScore: Number(process.env.TOKEN_SOLVER_V4_COMPLEX_PLANNING_MIN_SCORE || 4),
  compositeStrongMinScore: Number(process.env.TOKEN_SOLVER_V4_COMPOSITE_STRONG_MIN_SCORE || 6),
  largeToolEnvelopeMaxPromptChars: Number(process.env.TOKEN_SOLVER_V4_TOOL_ENVELOPE_MAX_PROMPT_CHARS || 8000),
  strongCodingLane: String(process.env.TOKEN_SOLVER_V4_STRONG_CODING_LANE || 'ollama-cloud-heavy-coder'),
  strongCodingProviderModel: String(process.env.TOKEN_SOLVER_V4_STRONG_CODING_MODEL || 'ollama/deepseek-v4-pro:cloud'),
  requiredStrongProviderModel: String(process.env.TOKEN_SOLVER_V4_REQUIRED_STRONG_MODEL || 'openai-codex/gpt-5.5'),
  nanoProviderModel: String(process.env.TOKEN_SOLVER_V4_NANO_MODEL || 'gpt-5.4-nano'),
  intentPreselectorV5ShadowEnabled: String(process.env.TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_SHADOW || 'true').toLowerCase() !== 'false',
  intentPreselectorV5TraceEnabled: String(process.env.TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_TRACE || 'false').toLowerCase() === 'true',
  intentPreselectorV5StatePath: intentPreselectorV5State.statePath,
  intentPreselectorV5Mode: intentPreselectorV5State.mode,
  intentPreselectorV5Enforced: intentPreselectorV5State.enforced,
  intentPreselectorV5ControlSurface: intentPreselectorV5State.controlSurface
};
