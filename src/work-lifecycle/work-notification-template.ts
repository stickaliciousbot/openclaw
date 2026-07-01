// OpenClaw Stickbot Work Lifecycle Ledger — M4 terminal notification templates
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

const RAW_SECRET_PATTERNS = Object.freeze([
  /\b\d{9,}\b/g,
  /telegram:[^\s`]+:[0-9]{6,}/gi,
  /(authorization|token|api[_-]?key|secret)\s*[:=]\s*[^\s,;]+/gi
]);

export class WorkNotificationTemplateError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkNotificationTemplateError';
    this.code = code;
    this.details = details;
  }
}

export function redactNotificationText(text) {
  let output = String(text ?? '');
  for (const pattern of RAW_SECRET_PATTERNS) {
    output = output.replace(pattern, (match) => {
      if (/^(authorization|token|api[_-]?key|secret)/i.test(match)) return 'redacted-secret';
      if (/telegram:/i.test(match)) return 'telegram:sha256-redacted';
      return 'sha256-redacted';
    });
  }
  return output;
}

export function assertNotificationRedacted(text) {
  const rendered = String(text ?? '');
  const failures = [];
  for (const pattern of RAW_SECRET_PATTERNS) {
    pattern.lastIndex = 0;
    if (pattern.test(rendered)) failures.push(pattern.toString());
  }
  if (failures.length > 0) {
    throw new WorkNotificationTemplateError('NOTIFICATION_REDACTION_FAILED', 'Notification contains raw private identifier or secret-like content', {
      failures
    });
  }
  return true;
}

export function renderTerminalNotification({ run, milestone, status, gates = [], artifacts = [], next = null, safetyBoundary = null, failure = null, hold = null, abort = null }) {
  const finalStatus = status ?? milestone?.status ?? run?.status;
  const title = milestone?.name ?? run?.title ?? 'Lifecycle milestone';
  const lines = [];

  lines.push(`${finalStatus} — ${title}`);

  if (finalStatus === 'PASS') {
    lines.push('Gates:');
    lines.push(...formatGates(gates.length ? gates : milestone?.hard_gates));
    lines.push('Artifacts:');
    lines.push(...formatList(artifacts.length ? artifacts : milestone?.artifacts));
    lines.push('Next:');
    lines.push(`• ${next ?? 'Awaiting next milestone or operator instruction.'}`);
  } else if (finalStatus === 'FAIL') {
    lines.push('Failed gates:');
    lines.push(...formatFailedGates(gates.length ? gates : milestone?.hard_gates));
    lines.push('Evidence:');
    lines.push(...formatList(artifacts.length ? artifacts : milestone?.artifacts));
    lines.push('Action taken:');
    lines.push(`• ${failure?.action_taken ?? 'Stopped before unsafe continuation; no production apply implied.'}`);
    lines.push('Next:');
    lines.push(`• ${next ?? failure?.next ?? 'Repair failed gate, then rerun focused validation.'}`);
  } else if (finalStatus === 'HOLD') {
    lines.push('Blocked on:');
    lines.push(`• ${hold?.reason ?? run?.hold?.reason ?? 'Missing input, approval, dependency, or validation.'}`);
    lines.push('Current state:');
    lines.push(...formatList(artifacts.length ? artifacts : milestone?.artifacts));
    lines.push('Needed from operator:');
    lines.push(`• ${hold?.needed_from_operator ?? run?.hold?.needed_from_operator ?? next ?? 'Resume or explicitly defer.'}`);
  } else if (finalStatus === 'ABORT') {
    lines.push('Reason:');
    lines.push(`• ${abort?.reason ?? run?.abort?.reason ?? 'Aborted by operator, runtime, policy, timeout, or supersession.'}`);
    lines.push('State:');
    lines.push(...formatList(artifacts.length ? artifacts : milestone?.artifacts));
  } else if (finalStatus === 'SUPERSEDED') {
    lines.push('Reason:');
    lines.push(`• Replaced by ${run?.superseded_by ?? milestone?.superseded_by ?? 'a newer run'}.`);
    lines.push('State:');
    lines.push(...formatList(artifacts.length ? artifacts : milestone?.artifacts));
  } else {
    lines.push('State:');
    lines.push(`• ${finalStatus ?? 'UNKNOWN'}`);
  }

  lines.push('Safety boundary:');
  lines.push(`• ${formatSafetyBoundary(safetyBoundary ?? run?.safety_boundary)}`);

  const redacted = redactNotificationText(lines.join('\n'));
  assertNotificationRedacted(redacted);
  return redacted;
}

function formatGates(gates = []) {
  if (!Array.isArray(gates) || gates.length === 0) return ['• No gate details recorded.'];
  return gates.map((gate) => `• ${gate.name ?? gate.id ?? 'gate'}: ${gate.status ?? 'UNKNOWN'}${gate.reason ? ` — ${gate.reason}` : ''}`);
}

function formatFailedGates(gates = []) {
  const failed = Array.isArray(gates) ? gates.filter((gate) => gate.status === 'FAIL' || gate.status === 'HOLD') : [];
  if (failed.length === 0) return ['• No failed gate details recorded.'];
  return formatGates(failed);
}

function formatList(values = []) {
  if (!Array.isArray(values) || values.length === 0) return ['• None recorded.'];
  return values.map((value) => `• ${value}`);
}

function formatSafetyBoundary(boundary) {
  if (!boundary) return 'No safety boundary recorded.';
  const forbidden = Array.isArray(boundary.forbidden_mutations) ? boundary.forbidden_mutations.join(', ') : 'not recorded';
  return `Forbidden without approval: ${forbidden}`;
}
