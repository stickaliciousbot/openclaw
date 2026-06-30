import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import {
  buildGe2Envelope,
  ge2HelpText
} from '../../ge2-native-runtime/src/ge2_command_router.mjs';
import { resolveGe2Dispatcher } from '../../ge2-native-runtime/src/ge2_dispatcher.mjs';

const WORKSPACE_ROOT = '/home/stickai/.openclaw/workspace';
const OPENCLAW_DIST = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const LOG_PATH = `${WORKSPACE_ROOT}/sharedspace/ge2-register.log`;
const REGISTER_ONCE_KEY = Symbol.for('openclaw.ge2.native.command.registered');

async function appendLog(payload) {
  try {
    await fs.mkdir(path.dirname(LOG_PATH), { recursive: true });
    await fs.appendFile(
      LOG_PATH,
      JSON.stringify({ timestamp: new Date().toISOString(), ...payload }) + '\n',
      'utf-8'
    );
  } catch {
    // best effort logging only
  }
}

async function resolveRegisterPluginCommand() {
  const distEntries = await fs.readdir(OPENCLAW_DIST);
  const typesFiles = distEntries
    .filter((name) => name.startsWith('types-') && name.endsWith('.js'))
    .sort();

  if (!typesFiles.length) {
    throw new Error('OpenClaw types module not found in dist/');
  }

  const inspected = [];
  for (const typesFile of typesFiles) {
    const moduleUrl = pathToFileURL(path.join(OPENCLAW_DIST, typesFile)).href;
    const mod = await import(moduleUrl);
    const registerFn = mod.registerPluginCommand || mod.p;
    inspected.push(typesFile);

    if (typeof registerFn === 'function') {
      return registerFn;
    }
  }

  throw new Error(
    `registerPluginCommand export not found in OpenClaw types modules: ${inspected.join(', ')}`
  );
}

async function resolveVisibleCommandRegistry() {
  const commandsModuleUrl = pathToFileURL(
    path.join(OPENCLAW_DIST, 'commands-D2qp4St4.js')
  ).href;
  const mod = await import(commandsModuleUrl);
  const listPluginCommands = mod.listPluginCommands || mod.r;
  if (typeof listPluginCommands !== 'function') {
    throw new Error('listPluginCommands export not found in OpenClaw commands module');
  }
  return { listPluginCommands };
}

function getPluginCommandBridgeState() {
  const key = Symbol.for('openclaw.pluginCommandsState');
  const processStore = typeof process === 'object' && process !== null ? process : null;
  const globalHasState = Object.prototype.hasOwnProperty.call(globalThis, key);
  const processHasState = processStore ? Object.prototype.hasOwnProperty.call(processStore, key) : false;
  return {
    bridgeTarget: 'process[Symbol.for(openclaw.pluginCommandsState)]',
    globalHasState,
    processHasState,
    sameStateObject: processStore && globalHasState && processHasState ? globalThis[key] === processStore[key] : null
  };
}

async function getGe2RegistryState() {
  const { listPluginCommands } = await resolveVisibleCommandRegistry();
  const commands = listPluginCommands();
  const ge2 = commands.find((command) => command?.name === 'ge2') || null;
  return {
    visible: Boolean(ge2),
    ge2,
    pluginCommandCount: Array.isArray(commands) ? commands.length : null,
    bridge: getPluginCommandBridgeState()
  };
}

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
        `✅ GE2 run accepted`,
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

async function createGe2CommandDefinition() {
  const dispatcher = resolveGe2Dispatcher({
    stateDir: `${WORKSPACE_ROOT}/state/ge2-native`,
    artifactDir: `${WORKSPACE_ROOT}/state/ge2-native/artifacts`
  });

  return {
    name: 'ge2',
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

async function registerNativeGe2Command(options = {}) {
  const beforeRegistry = await getGe2RegistryState();
  if (globalThis[REGISTER_ONCE_KEY] === true && beforeRegistry.visible) {
    return {
      ok: true,
      alreadyRegistered: true,
      registry: beforeRegistry,
      phase: options.phase || 'register'
    };
  }

  const registerPluginCommand = await resolveRegisterPluginCommand();
  const commandDefinition = await createGe2CommandDefinition();
  const registration = registerPluginCommand(
    'ge2-native-command',
    commandDefinition,
    {
      pluginName: 'GE2 Native Command',
      pluginRoot: WORKSPACE_ROOT
    }
  );

  if (!registration?.ok) {
    const msg = String(registration?.error || 'unknown error');
    if (msg.includes('already registered')) {
      globalThis[REGISTER_ONCE_KEY] = true;
      const registry = await getGe2RegistryState();
      return {
        ok: registry.visible,
        alreadyRegistered: true,
        registry,
        phase: options.phase || 'register',
        ...registry.visible ? {} : { error: 'already registered but not visible in commands registry' }
      };
    }
    return {
      ok: false,
      error: msg,
      registry: beforeRegistry,
      phase: options.phase || 'register'
    };
  }

  globalThis[REGISTER_ONCE_KEY] = true;
  const afterRegistry = await getGe2RegistryState();
  return {
    ok: afterRegistry.visible,
    alreadyRegistered: false,
    registry: afterRegistry,
    phase: options.phase || 'register',
    ...afterRegistry.visible ? {} : { error: 'registration ok but not visible in commands registry' }
  };
}

function schedulePostStartupGe2Verification(event) {
  if (event?.type !== 'gateway' || event?.action !== 'startup') return;
  for (const delayMs of [3000, 10000]) {
    setTimeout(() => {
      registerNativeGe2Command({ phase: `post-startup-${delayMs}ms` })
        .then((result) => appendLog({
          invoked: true,
          type: event?.type ?? null,
          action: event?.action ?? null,
          registration: result
        }))
        .catch((error) => appendLog({
          invoked: true,
          type: event?.type ?? null,
          action: event?.action ?? null,
          registration: {
            ok: false,
            phase: `post-startup-${delayMs}ms`,
            error: error instanceof Error ? error.message : String(error)
          }
        }));
    }, delayMs);
  }
}

export default async function ge2Register(event) {
  try {
    const result = await registerNativeGe2Command({ phase: 'startup-immediate' });
    await appendLog({
      invoked: true,
      type: event?.type ?? null,
      action: event?.action ?? null,
      registration: result
    });
    schedulePostStartupGe2Verification(event);

    if (!result.ok) {
      event?.messages?.push?.(`⚠️ GE2 native registration failed: ${result.error}`);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await appendLog({
      invoked: true,
      type: event?.type ?? null,
      action: event?.action ?? null,
      registration: { ok: false, error: message }
    });
    event?.messages?.push?.(`⚠️ GE2 native registration failed: ${message}`);
  }
}
