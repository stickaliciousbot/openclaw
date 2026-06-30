import {
  buildGe2Envelope,
  ge2HelpText
} from '../../ge2-native-runtime/src/ge2_command_router.mjs';
import { resolveGe2Dispatcher } from '../../ge2-native-runtime/src/ge2_dispatcher.mjs';

const WORKSPACE_ROOT = '/home/stickai/.openclaw/workspace';

function formatStatus(run) {
  const lines = [];
  lines.push(`run_id: ${run.run_id}`);
  lines.push(`status: ${run.status}`);
  lines.push(`task: ${run.task || '<none>'}`);
  lines.push(`started_at: ${run.started_at}`);
  lines.push(`updated_at: ${run.updated_at}`);
  lines.push(`milestones: ${run.milestones?.length || 0}`);
  lines.push(`artifacts: ${run.artifacts?.length || 0}`);

  if (run.errors?.length) {
    const latestError = run.errors[run.errors.length - 1];
    lines.push(`latest_error: ${latestError?.message || 'unknown'}`);
  }

  return lines.join('\n');
}

function formatCommandResult(result) {
  if (!result || typeof result !== 'object') {
    return '⚠️ GE2 returned an empty result.';
  }

  if (!result.ok && result.error?.message) {
    return `⚠️ ${result.error.message}`;
  }

  switch (result.kind) {
    case 'help':
      return ge2HelpText();

    case 'run_accepted':
      return [
        '✅ GE2 run accepted',
        `run_id: ${result.run_id}`,
        `task: ${result.task}`,
        '',
        `Check progress: /ge2 status ${result.run_id}`,
        `Artifacts: /ge2 artifacts ${result.run_id}`,
        `Cancel: /ge2 cancel ${result.run_id}`
      ].join('\n');

    case 'status':
      return formatStatus(result.run);

    case 'artifacts': {
      const artifacts = Array.isArray(result.artifacts) ? result.artifacts : [];
      if (!artifacts.length) {
        return `No artifacts for run_id: ${result.run_id}`;
      }

      return [
        `Artifacts for ${result.run_id}:`,
        ...artifacts.map(
          (artifact, index) =>
            `${index + 1}. ${artifact.name || 'artifact'}\n   path: ${artifact.path}\n   sha256: ${artifact.sha256}`
        )
      ].join('\n');
    }

    case 'cancel_requested':
      return `🛑 Cancel requested for ${result.run_id}. Check status with /ge2 status ${result.run_id}`;

    default:
      return `GE2 response:\n${JSON.stringify(result, null, 2)}`;
  }
}

function buildOriginFromCtx(ctx) {
  return {
    surface: ctx?.channel || null,
    channel: ctx?.channel || null,
    sessionKey: ctx?.sessionKey || null,
    sessionId: ctx?.sessionId || null,
    accountId: ctx?.accountId || null,
    messageId: null,
    senderId: ctx?.senderId || null
  };
}

function createGe2CommandDefinition() {
  const dispatcher = resolveGe2Dispatcher({
    stateDir: `${WORKSPACE_ROOT}/state/ge2-native`,
    artifactDir: `${WORKSPACE_ROOT}/state/ge2-native/artifacts`
  });

  return {
    name: 'ge2',
    nativeNames: {
      default: 'ge2',
      telegram: 'ge2'
    },
    description: 'Run GE2 native command operations (run/status/artifacts/cancel).',
    acceptsArgs: true,
    requireAuth: true,
    nativeProgressMessages: {
      default: 'GE2 accepted. Dispatching native run pipeline…',
      telegram: 'GE2 accepted, dispatching…'
    },
    handler: async (ctx) => {
      const commandInput =
        typeof ctx?.commandBody === 'string' && ctx.commandBody.trim()
          ? ctx.commandBody
          : `/ge2 ${String(ctx?.args || '').trim()}`;

      const envelopeResult = buildGe2Envelope({
        input: commandInput,
        origin: buildOriginFromCtx(ctx)
      });

      if (!envelopeResult.ok) {
        return {
          text: `⚠️ ${envelopeResult.error.message}\n${
            envelopeResult.error.usageHint || '/ge2 help'
          }`
        };
      }

      const dispatchResult = await dispatcher.dispatch(envelopeResult.envelope);
      return {
        text: formatCommandResult(dispatchResult)
      };
    }
  };
}

export default {
  id: 'ge2-command',
  name: 'GE2 Command',
  version: '0.0.2',
  register(api) {
    api.registerCommand(createGe2CommandDefinition());
  }
};
