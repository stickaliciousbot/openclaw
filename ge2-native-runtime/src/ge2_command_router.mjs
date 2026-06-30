import crypto from 'node:crypto';

const SUPPORTED_SUBCOMMANDS = new Set([
  'run',
  'status',
  'artifacts',
  'cancel',
  'help'
]);

function invalid(code, message, usageHint) {
  return {
    ok: false,
    error: {
      code,
      message,
      usageHint: usageHint || null
    }
  };
}

function tokenize(input) {
  const trimmed = String(input || '').trim();
  if (!trimmed) return [];
  return trimmed.split(/\s+/).filter(Boolean);
}

export function parseGe2CommandInput(input, options = {}) {
  const raw = String(input || '').trim();
  const allowBare = options.allowBare !== false;

  let body = raw;
  if (raw.toLowerCase().startsWith('/ge2')) {
    body = raw.replace(/^\/ge2\b/i, '').trim();
  } else if (!allowBare) {
    return invalid('NOT_GE2_COMMAND', 'Input is not a /ge2 command.');
  }

  if (!body) {
    return {
      ok: true,
      subcommand: 'help',
      args: {}
    };
  }

  const parts = tokenize(body);
  const subcommand = String(parts[0] || '').toLowerCase();
  const rest = body.slice(parts[0].length).trim();

  if (!SUPPORTED_SUBCOMMANDS.has(subcommand)) {
    return invalid(
      'UNKNOWN_SUBCOMMAND',
      `Unknown /ge2 subcommand: "${subcommand}".`,
      '/ge2 help'
    );
  }

  if (subcommand === 'help') {
    return { ok: true, subcommand, args: {} };
  }

  if (subcommand === 'run') {
    if (!rest) {
      return invalid(
        'MISSING_TASK',
        'Missing required task for /ge2 run.',
        '/ge2 run <task>'
      );
    }
    return {
      ok: true,
      subcommand,
      args: {
        task: rest
      }
    };
  }

  if (subcommand === 'status') {
    return {
      ok: true,
      subcommand,
      args: {
        run_id: rest || null
      }
    };
  }

  if (subcommand === 'artifacts' || subcommand === 'cancel') {
    if (!rest) {
      return invalid(
        'MISSING_RUN_ID',
        `Missing required run_id for /ge2 ${subcommand}.`,
        `/ge2 ${subcommand} <run_id>`
      );
    }
    return {
      ok: true,
      subcommand,
      args: {
        run_id: rest
      }
    };
  }

  return invalid('UNHANDLED_SUBCOMMAND', 'Unhandled subcommand parser branch.');
}

export function buildGe2Envelope({
  input,
  origin,
  requestId
} = {}) {
  const parsed = parseGe2CommandInput(input, { allowBare: true });
  if (!parsed.ok) {
    return parsed;
  }

  const normalizedOrigin = {
    surface: origin?.surface || null,
    channel: origin?.channel || null,
    sessionKey: origin?.sessionKey || null,
    sessionId: origin?.sessionId || null,
    accountId: origin?.accountId || null,
    messageId: origin?.messageId || null,
    senderId: origin?.senderId || null
  };

  return {
    ok: true,
    envelope: {
      command: 'ge2',
      subcommand: parsed.subcommand,
      args: parsed.args,
      origin: normalizedOrigin,
      requestId: requestId || crypto.randomUUID()
    }
  };
}

export function ge2HelpText() {
  return [
    'GE2 native commands:',
    '/ge2 run <task>',
    '/ge2 status',
    '/ge2 status <run_id>',
    '/ge2 artifacts <run_id>',
    '/ge2 cancel <run_id>',
    '/ge2 help'
  ].join('\n');
}
