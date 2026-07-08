import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  loadIntentPreselectorV5State,
  validateIntentPreselectorV5ProductionState,
  intentPreselectorV5RequestAllowed,
  REQUIRED_M6_EVIDENCE,
  PRODUCTION_CONTROL_SURFACE_SCHEMA,
  PRODUCTION_CONTROL_SURFACE_SUBJECT
} from '../src/intentPreselectorV5ControlSurface.js';
import { buildV5ShadowContract } from '../src/v5Contract.js';

function validProtectedState(overrides = {}) {
  return {
    schema: PRODUCTION_CONTROL_SURFACE_SCHEMA,
    subject: PRODUCTION_CONTROL_SURFACE_SUBJECT,
    enabled: true,
    mode: 'enforced_route_contract',
    authority: 'lane_selection_only',
    traffic_scope: 'owner_operator_live_turns_only',
    operator_allowlist: ['telegram:8495203551'],
    kill_switch: false,
    m6_evidence: { ...REQUIRED_M6_EVIDENCE },
    guards: {
      prompt_preserved_required: true,
      context_may_replace_prompt: false,
      remote_llm_for_scoring_allowed: false,
      direct_provider_bypass_allowed: false,
      cache_allowed: false,
      artifact_memory_promotion_allowed: false,
      default_model_change_allowed: false,
      provider_model_change_allowed: false,
      write_action_authority: 'unchanged_existing_policy_only'
    },
    ...overrides
  };
}

const missingPath = join(mkdtempSync(join(tmpdir(), 'm10a-missing-')), 'enforcement.json');
const missing = loadIntentPreselectorV5State({ env: { TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_STATE_PATH: missingPath, TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED: 'true' } });
assert.equal(missing.enforced, false, 'env enforced must be ignored without protected state');
assert.equal(missing.mode, 'shadow_contract_only');
assert.equal(missing.controlSurface.reason, 'env_enforced_ignored_without_valid_protected_state');

const advisoryOnly = validateIntentPreselectorV5ProductionState({
  context_plus_semantic_preselector: { m9_advisory_canary: { enabled: true } }
});
assert.equal(advisoryOnly.enforced, false, 'M9 advisory key must not become live-route authority');
assert.ok(advisoryOnly.reasons.includes('schema_mismatch'));
assert.ok(advisoryOnly.reasons.includes('subject_mismatch'));

const broad = validateIntentPreselectorV5ProductionState(validProtectedState({ traffic_scope: 'all_live_traffic', operator_allowlist: ['*'] }));
assert.equal(broad.enforced, false, 'broad traffic cannot validate in M10A');
assert.ok(broad.reasons.includes('traffic_scope_not_initial_owner_operator_only'));
assert.ok(broad.reasons.includes('operator_allowlist_broad_wildcard'));

const dir = mkdtempSync(join(tmpdir(), 'm10a-valid-'));
const statePath = join(dir, 'enforcement.json');
writeFileSync(statePath, JSON.stringify(validProtectedState(), null, 2));
const loaded = loadIntentPreselectorV5State({ env: { TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_STATE_PATH: statePath } });
assert.equal(loaded.enforced, true);
assert.equal(loaded.mode, 'enforced_route_contract');
assert.equal(loaded.controlSurface.active, true);

const allowed = intentPreselectorV5RequestAllowed({ controlSurface: loaded.controlSurface, sessionKey: 'agent:main:telegram:direct:8495203551' });
assert.equal(allowed.allowed, true, 'owner/operator Telegram session should be allowlisted');
const denied = intentPreselectorV5RequestAllowed({ controlSurface: loaded.controlSurface, sessionKey: 'agent:main:telegram:direct:0000000000' });
assert.equal(denied.allowed, false, 'non-allowlisted Telegram session must not get live-route enforcement');

const disabled = validateIntentPreselectorV5ProductionState(validProtectedState({ enabled: false, mode: 'shadow_contract_only', kill_switch: true, m6_evidence: undefined, guards: undefined }));
assert.equal(disabled.valid, true, 'safe disabled state should validate');
assert.equal(disabled.enforced, false);

const prompt = 'Inspect the current artifact status and summarize the validation state';
const routeScore = { recommendedLane: 'nano-fast', intent: { label: 'artifact_state_inspection' }, toolNeedProbability: 0 };
const commonConfig = { serviceId: 'token-solver-v4', intentPreselectorV5ShadowEnabled: true, intentPreselectorV5TraceEnabled: false };
const noProtectedStateV5 = await buildV5ShadowContract({ prompt, routeScore, sessionKey: 'agent:main:telegram:direct:8495203551', config: { ...commonConfig, intentPreselectorV5Enforced: false, intentPreselectorV5ControlSurface: missing.controlSurface } });
assert.equal(noProtectedStateV5.enforced, false, 'missing protected state must remain shadow-only at v5 contract boundary');

const nonAllowlistedV5 = await buildV5ShadowContract({ prompt, routeScore, sessionKey: 'agent:main:telegram:direct:0000000000', config: { ...commonConfig, intentPreselectorV5Enforced: true, intentPreselectorV5ControlSurface: loaded.controlSurface } });
assert.equal(nonAllowlistedV5.enforced, false, 'valid protected state must still reject non-allowlisted sessions');
assert.equal(nonAllowlistedV5.control_surface.request_allowed, false);

const allowlistedV5 = await buildV5ShadowContract({ prompt, routeScore, sessionKey: 'agent:main:telegram:direct:8495203551', config: { ...commonConfig, intentPreselectorV5Enforced: true, intentPreselectorV5ControlSurface: loaded.controlSurface } });
assert.equal(allowlistedV5.enforced, true, 'valid protected state plus allowlisted owner scope may mark route contract enforced');
assert.equal(allowlistedV5.control_surface.request_allowed, true);
assert.equal(allowlistedV5.context_may_replace_prompt, false);
assert.equal(allowlistedV5.prompt_preserved, true);

console.log(JSON.stringify({ ok: true, name: 'intent-preselector-v5-enforcement', assertions: 23, provider_calls: 0 }));
