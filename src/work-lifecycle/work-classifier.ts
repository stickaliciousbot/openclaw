// OpenClaw Stickbot Work Lifecycle Ledger — M3 lifecycle-managed work classifier
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

const TOOLFUL_HINTS = Object.freeze([
  'edit',
  'write',
  'patch',
  'commit',
  'push',
  'test',
  'validate',
  'run',
  'implement',
  'fix',
  'repair',
  'deploy',
  'restart',
  'investigate',
  'audit',
  'build',
  'smoke'
]);

export function classifyWorkRequest(request = {}) {
  const text = String(request.text ?? request.prompt ?? '').toLowerCase();
  const reasons = [];

  if (request.forceLifecycle === true) reasons.push('force_lifecycle');
  if (request.usesTools === true || request.toolful === true) reasons.push('tool_use_expected');
  if (request.modifiesFiles === true) reasons.push('file_mutation_expected');
  if (request.longRunning === true) reasons.push('long_running_expected');
  if (request.productionAffecting === true) reasons.push('production_affecting');
  if (request.multiStep === true) reasons.push('multi_step');

  const matchedHints = TOOLFUL_HINTS.filter((hint) => text.includes(hint));
  if (matchedHints.length > 0) reasons.push(`text_hints:${matchedHints.slice(0, 5).join(',')}`);

  const managed = reasons.length > 0 && request.noLifecycle !== true;
  return {
    schema_version: 'work_lifecycle.classification.v1',
    lifecycle_managed: managed,
    acknowledgement_required: managed && request.visibleAck !== false,
    title: request.title ?? inferTitle(text),
    scope: request.scope ?? inferScope(text, reasons),
    first_checkpoint: request.first_checkpoint ?? inferFirstCheckpoint(reasons),
    reasons
  };
}

function inferTitle(text) {
  const trimmed = text.trim();
  if (!trimmed) return 'Lifecycle-managed work';
  return trimmed.length > 80 ? `${trimmed.slice(0, 77)}...` : trimmed;
}

function inferScope(text, reasons) {
  if (text.includes('work lifecycle')) return 'Work Lifecycle Ledger sidecar implementation and validation';
  if (reasons.some((reason) => reason.includes('file') || reason.includes('tool'))) return 'Toolful local workspace work';
  return 'Lifecycle-managed request';
}

function inferFirstCheckpoint(reasons) {
  if (reasons.some((reason) => reason.includes('production'))) return 'Preflight and safety-boundary validation';
  if (reasons.some((reason) => reason.includes('test') || reason.includes('validate'))) return 'Focused validation result';
  return 'First milestone gate result';
}
