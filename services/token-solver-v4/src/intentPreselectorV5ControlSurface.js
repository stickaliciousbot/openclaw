import fs from 'node:fs';

export const PRODUCTION_CONTROL_SURFACE_SCHEMA = 'stickbot.context_plus_semantic_preselector.production_control_surface.v1';
export const PRODUCTION_CONTROL_SURFACE_SUBJECT = 'CONTEXT_PLUS_SEMANTIC_PRESELECTOR';
export const DEFAULT_INTENT_PRESELECTOR_V5_STATE_PATH = '/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json';

export const REQUIRED_M6_EVIDENCE = Object.freeze({
  comparator_classification: 'PASS_FALSE_POSITIVE_BASELINE_IMPROVED',
  production_false_positives: '22/235',
  context_plus_shadow_false_positives: '0/235',
  proposal_commit: '871522c5204b6062419e48a5a47a4d9cd4cf97a6',
  preflight_commit: '551c019bdee3704e3da2a8d4eb9eb9d4c10b388e',
  runbook_hold_commit: 'c2e2decfeaa4fad82e81a54362779d461d1ebf77',
  m8_discovery_hold_commit: '1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20'
});

const REQUIRED_FALSE_GUARDS = Object.freeze([
  'context_may_replace_prompt',
  'remote_llm_for_scoring_allowed',
  'direct_provider_bypass_allowed',
  'cache_allowed',
  'artifact_memory_promotion_allowed',
  'default_model_change_allowed',
  'provider_model_change_allowed'
]);

function boolFrom(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return !['0', 'false', 'no', 'off'].includes(String(value).trim().toLowerCase());
}

function addReason(reasons, reason) {
  if (reason && !reasons.includes(reason)) reasons.push(reason);
}

function normalizeList(value) {
  return Array.isArray(value) ? value.map((item) => String(item || '').trim()).filter(Boolean) : [];
}

function hasBroadWildcard(list = []) {
  return list.some((item) => ['*', 'all', 'all_live_traffic', 'any', 'everyone'].includes(String(item || '').trim().toLowerCase()));
}

function safeReadJson(path) {
  try {
    if (!fs.existsSync(path)) return { ok: true, exists: false, value: null };
    return { ok: true, exists: true, value: JSON.parse(fs.readFileSync(path, 'utf8')) };
  } catch (err) {
    return { ok: false, exists: true, value: null, error: String(err?.message || err).slice(0, 240) };
  }
}

export function validateIntentPreselectorV5ProductionState(value = null) {
  const reasons = [];
  const state = value && typeof value === 'object' && !Array.isArray(value) ? value : null;
  if (!state) {
    return {
      valid: false,
      active: false,
      enforced: false,
      enabled: false,
      mode: 'shadow_contract_only',
      trafficScope: null,
      operatorAllowlist: [],
      reasons: ['state_not_object']
    };
  }

  if (state.schema !== PRODUCTION_CONTROL_SURFACE_SCHEMA) addReason(reasons, 'schema_mismatch');
  if (state.subject !== PRODUCTION_CONTROL_SURFACE_SUBJECT) addReason(reasons, 'subject_mismatch');

  const enabled = state.enabled === true;
  const killSwitch = state.kill_switch === true;
  const mode = String(state.mode || 'shadow_contract_only');
  if (!['shadow_contract_only', 'enforced_route_contract'].includes(mode)) addReason(reasons, 'mode_invalid');
  if (state.authority !== 'lane_selection_only') addReason(reasons, 'authority_not_lane_selection_only');

  const trafficScope = String(state.traffic_scope || 'owner_operator_live_turns_only');
  if (trafficScope !== 'owner_operator_live_turns_only') addReason(reasons, 'traffic_scope_not_initial_owner_operator_only');

  const operatorAllowlist = normalizeList(state.operator_allowlist);
  if (operatorAllowlist.length < 1) addReason(reasons, 'operator_allowlist_empty');
  if (hasBroadWildcard(operatorAllowlist)) addReason(reasons, 'operator_allowlist_broad_wildcard');
  if (!operatorAllowlist.includes('telegram:8495203551')) addReason(reasons, 'operator_allowlist_missing_owner_telegram');

  if (mode === 'enforced_route_contract') {
    if (!enabled) addReason(reasons, 'enforced_mode_requires_enabled_true');
    if (killSwitch) addReason(reasons, 'enforced_mode_requires_kill_switch_false');
    const evidence = state.m6_evidence && typeof state.m6_evidence === 'object' ? state.m6_evidence : {};
    for (const [key, expected] of Object.entries(REQUIRED_M6_EVIDENCE)) {
      if (evidence[key] !== expected) addReason(reasons, `m6_evidence_${key}_mismatch`);
    }
  }

  const guards = state.guards && typeof state.guards === 'object' ? state.guards : {};
  if (mode === 'enforced_route_contract') {
    if (guards.prompt_preserved_required !== true) addReason(reasons, 'prompt_preserved_required_not_true');
    for (const key of REQUIRED_FALSE_GUARDS) {
      if (guards[key] !== false) addReason(reasons, `guard_${key}_not_false`);
    }
    if (guards.write_action_authority !== 'unchanged_existing_policy_only') addReason(reasons, 'write_action_authority_not_unchanged');
  }

  const valid = reasons.length === 0;
  const active = valid && enabled && mode === 'enforced_route_contract' && !killSwitch;
  return {
    valid,
    active,
    enforced: active,
    enabled,
    killSwitch,
    mode: active ? 'enforced_route_contract' : 'shadow_contract_only',
    requestedMode: mode,
    trafficScope,
    operatorAllowlist,
    authority: state.authority || null,
    schema: state.schema || null,
    subject: state.subject || null,
    reasons
  };
}

export function loadIntentPreselectorV5State({ env = process.env, statePathDefault = DEFAULT_INTENT_PRESELECTOR_V5_STATE_PATH } = {}) {
  const statePath = String(env.TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_STATE_PATH || statePathDefault);
  const read = safeReadJson(statePath);
  const envRequestedEnforced = boolFrom(env.TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED, false);

  if (!read.ok) {
    return {
      statePath,
      mode: 'shadow_contract_only',
      enforced: false,
      controlSurface: {
        present: true,
        valid: false,
        active: false,
        reason: 'state_file_parse_failed',
        error: read.error,
        envRequestedEnforcedIgnored: envRequestedEnforced
      }
    };
  }

  if (!read.exists) {
    return {
      statePath,
      mode: 'shadow_contract_only',
      enforced: false,
      controlSurface: {
        present: false,
        valid: true,
        active: false,
        reason: envRequestedEnforced ? 'env_enforced_ignored_without_valid_protected_state' : 'state_file_missing_safe_default',
        envRequestedEnforcedIgnored: envRequestedEnforced
      }
    };
  }

  const validation = validateIntentPreselectorV5ProductionState(read.value);
  return {
    statePath,
    mode: validation.active ? 'enforced_route_contract' : 'shadow_contract_only',
    enforced: validation.active,
    controlSurface: {
      present: true,
      ...validation,
      reason: validation.valid ? (validation.active ? 'protected_state_active_scope_checked_per_request' : 'protected_state_valid_shadow_only') : 'protected_state_invalid_safe_shadow_only',
      envRequestedEnforcedIgnored: envRequestedEnforced && !validation.active
    }
  };
}

function requestIdentityCandidates({ rawBody = null, sessionKey = null } = {}) {
  const candidates = new Set();
  const add = (value) => {
    const text = String(value || '').trim();
    if (text) candidates.add(text);
  };
  add(sessionKey);
  add(rawBody?.sessionKey);
  add(rawBody?.session_key);
  add(rawBody?.metadata?.chat_id);
  add(rawBody?.metadata?.sender_id);
  add(rawBody?.metadata?.sender);
  add(rawBody?.openclaw?.chat_id);
  add(rawBody?.openclaw?.sender_id);
  add(rawBody?.conversation?.chat_id);
  add(rawBody?.conversation?.sender_id);

  for (const value of Array.from(candidates)) {
    const text = String(value);
    const telegramId = text.match(/telegram[^0-9]*([0-9]{5,})/i)?.[1];
    if (telegramId) candidates.add(`telegram:${telegramId}`);
    if (/^[0-9]{5,}$/.test(text)) candidates.add(`telegram:${text}`);
  }
  return Array.from(candidates);
}

export function intentPreselectorV5RequestAllowed({ controlSurface = null, rawBody = null, sessionKey = null } = {}) {
  const surface = controlSurface || {};
  if (!surface.active || !surface.enforced) {
    return { allowed: false, reason: surface.reason || 'control_surface_not_active', candidates: [] };
  }
  if (surface.trafficScope !== 'owner_operator_live_turns_only') {
    return { allowed: false, reason: 'traffic_scope_not_owner_operator_live_turns_only', candidates: [] };
  }
  const candidates = requestIdentityCandidates({ rawBody, sessionKey });
  const allowlist = normalizeList(surface.operatorAllowlist);
  const allowed = allowlist.some((allowedIdentity) => candidates.includes(allowedIdentity));
  return {
    allowed,
    reason: allowed ? 'owner_operator_allowlist_match' : 'owner_operator_allowlist_no_match',
    candidates
  };
}
