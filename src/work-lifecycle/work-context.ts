// OpenClaw Stickbot Work Lifecycle Ledger — M3 work context helper
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { randomUUID } from 'node:crypto';

export function makeWorkRunId(date = new Date(), suffix = randomUUID().slice(0, 8)) {
  const stamp = date.toISOString().replace(/[-:.]/g, '').replace(/\.\d{3}Z$/, 'Z');
  return `work_${stamp}_${suffix}`;
}

export function redactSurfaceId(value, fallback = 'redacted') {
  if (value === null || value === undefined || value === '') return fallback;
  const text = String(value);
  if (text.includes('telegram')) {
    if (text.includes('turn') || text.includes('message')) return 'telegram:turn:sha256-redacted';
    return 'telegram:direct:sha256-redacted';
  }
  return `${fallback}:sha256-redacted`;
}

export function createWorkContext(request, options = {}) {
  const now = options.now ?? new Date();
  const runId = options.runId ?? makeWorkRunId(now, options.runSuffix);
  const surface = request?.surface ?? 'unknown_surface';

  return {
    schema_version: 'work_lifecycle.context.v1',
    run_id: runId,
    parent_run_id: options.parentRunId ?? request?.parent_run_id ?? null,
    user_turn_id: redactSurfaceId(request?.user_turn_id ?? request?.message_id, `${surface}:turn`),
    surface,
    chat_id: redactSurfaceId(request?.chat_id, `${surface}:chat`),
    actor: options.actor ?? 'stickbot',
    requested_by: request?.requested_by ?? 'operator',
    started_at: now.toISOString(),
    safety_boundary: options.safetyBoundary ?? request?.safety_boundary ?? defaultSafetyBoundary()
  };
}

export function defaultSafetyBoundary() {
  return {
    mode: 'repo_patch',
    allowed_mutations: ['working_tree', 'local_artifacts', 'state_sidecar_samples', 'focused_tests'],
    forbidden_mutations: [
      'production_gateway_config',
      'gateway_restart',
      'service_restart',
      'provider_auth',
      'secrets',
      'route_change',
      'fallback_change',
      'memory_promotion',
      'ge2_mutation',
      'vnext_mesh_mutation',
      'vector_graph_memory_mutation',
      'runtime_hook_import'
    ],
    requires_operator_approval: ['production_apply', 'service_restart', 'network_exposure_change'],
    rollback_required: false,
    secrets_redaction_required: true
  };
}
