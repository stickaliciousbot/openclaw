import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan';
const cfgPath = '/home/stickai/.openclaw/openclaw.json';
const workspaceDir = '/home/stickai/.openclaw/workspace';
const loaderPath = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js';
const typesPath = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js';
const commandsPath = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js';
function shaFile(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function countGe2Commands(commands) {
  return commands.filter((command) => {
    if (!command || typeof command !== 'object') return false;
    const names = [command.name, command.nativeName, ...Object.values(command.nativeNames ?? {})].filter((value) => typeof value === 'string').map((value) => value.trim().toLowerCase().replace(/^\/+/, ''));
    return names.includes('ge2');
  }).length;
}
function commandNames(commands) { return commands.map((command) => command?.name).filter(Boolean); }
function requiredPresent(names) { return ['pair','dreaming','phone','voice'].every((name) => names.includes(name)); }
function fakeAbsent(names) { return !names.includes('fake') && !names.includes('/fake'); }
function textOf(result) { return typeof result?.text === 'string' ? result.text : JSON.stringify(result); }
async function execCommand(matchPluginCommand, executePluginCommand, body, cfg) {
  const matched = matchPluginCommand(body, { channel: 'telegram' });
  if (!matched) return { body, matched: false };
  const executed = await executePluginCommand({
    command: matched.command,
    args: matched.args,
    senderId: 'r7-local-validation',
    channel: 'telegram',
    isAuthorizedSender: true,
    senderIsOwner: true,
    commandBody: body,
    config: cfg,
    sessionKey: 'r7-local-validation',
    sessionId: 'r7-local-validation',
    accountId: 'local',
    messageId: 'local-r7'
  });
  return { body, matched: true, commandName: matched.command.name, args: matched.args, text: textOf(executed), raw: executed };
}
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const loader = await import('file://' + loaderPath + '?r7local=' + Date.now());
const types = await import('file://' + typesPath + '?r7local=' + Date.now());
loader.i?.(); // clearPluginLoaderCache export alias
const registryNormal = loader.l({ config: cfg, workspaceDir, cache: true });
const registeredNormal = types.k();
const normalNames = commandNames(registeredNormal);
const registryNormalCommands = Array.isArray(registryNormal?.commands) ? registryNormal.commands.map((entry) => entry.command) : [];
const normal = {
  pluginCommandsCount: registeredNormal.length,
  ge2PluginCommandCount: countGe2Commands(registeredNormal),
  ge2RegistryCommandCount: countGe2Commands(registryNormalCommands),
  existingCommandsPreserved: requiredPresent(normalNames),
  fakeAbsent: fakeAbsent(normalNames),
  names: normalNames.filter((name) => ['ge2','pair','dreaming','phone','voice','fake'].includes(name)).sort()
};
loader.r?.(); // clearActivatedPluginRuntimeState export alias, leaves loader cache intact
const afterClearCount = types.k().length;
const registryRestored = loader.l({ config: cfg, workspaceDir, cache: true });
const registeredRestored = types.k();
const restoredNames = commandNames(registeredRestored);
const registryRestoredCommands = Array.isArray(registryRestored?.commands) ? registryRestored.commands.map((entry) => entry.command) : [];
const restored = {
  afterClearCount,
  pluginCommandsCount: registeredRestored.length,
  ge2PluginCommandCount: countGe2Commands(registeredRestored),
  ge2RegistryCommandCount: countGe2Commands(registryRestoredCommands),
  existingCommandsPreserved: requiredPresent(restoredNames),
  fakeAbsent: fakeAbsent(restoredNames),
  names: restoredNames.filter((name) => ['ge2','pair','dreaming','phone','voice','fake'].includes(name)).sort()
};
const commands = await import('file://' + commandsPath + '?r7local=' + Date.now());
const listSpecs = commands.r();
const listSpecNames = commandNames(listSpecs);
const matcher = {
  listPluginCommandsGe2Count: countGe2Commands(listSpecs),
  listPluginCommandsExistingPreserved: requiredPresent(listSpecNames),
  listPluginCommandsFakeAbsent: fakeAbsent(listSpecNames),
  matchGe2Help: Boolean(commands.i('/ge2 help', { channel: 'telegram' })),
  matchGe2Status: Boolean(commands.i('/ge2 status', { channel: 'telegram' })),
  matchFake: Boolean(commands.i('/fake', { channel: 'telegram' }))
};
const help = await execCommand(commands.i, commands.n, '/ge2 help', cfg);
const status = await execCommand(commands.i, commands.n, '/ge2 status', cfg);
const run = await execCommand(commands.i, commands.n, '/ge2 run r7-local-validation', cfg);
const runId = typeof run.text === 'string' ? run.text.match(/run_id:\s*(\S+)/)?.[1] : undefined;
const artifacts = runId ? await execCommand(commands.i, commands.n, `/ge2 artifacts ${runId}`, cfg) : { body: '/ge2 artifacts <run_id>', matched: false, skipped: 'missing run_id from run output' };
const dispatch = {
  help: { matched: help.matched, nativeText: /GE2|ge2/i.test(help.text ?? ''), textPreview: (help.text ?? '').slice(0, 500) },
  status: { matched: status.matched, nativeText: /GE2 status|No GE2|GE2/i.test(status.text ?? ''), textPreview: (status.text ?? '').slice(0, 500) },
  run: { matched: run.matched, nativeText: /GE2 run accepted|run_id:/i.test(run.text ?? ''), runId, textPreview: (run.text ?? '').slice(0, 500) },
  artifacts: { matched: artifacts.matched, nativeText: /GE2 artifacts/i.test(artifacts.text ?? ''), textPreview: (artifacts.text ?? '').slice(0, 500) }
};
const checks = {
  markerStart: fs.readFileSync(loaderPath, 'utf8').includes('GE2_R7_COMMAND_REGISTRY_LIFECYCLE_START'),
  markerEnd: fs.readFileSync(loaderPath, 'utf8').includes('GE2_R7_COMMAND_REGISTRY_LIFECYCLE_END'),
  normalGe2ExactlyOnePlugin: normal.ge2PluginCommandCount === 1,
  normalGe2ExactlyOneRegistry: normal.ge2RegistryCommandCount === 1,
  normalExistingPreserved: normal.existingCommandsPreserved,
  normalFakeAbsent: normal.fakeAbsent,
  restoredGe2ExactlyOnePlugin: restored.ge2PluginCommandCount === 1,
  restoredGe2ExactlyOneRegistry: restored.ge2RegistryCommandCount === 1,
  restoredExistingPreserved: restored.existingCommandsPreserved,
  restoredFakeAbsent: restored.fakeAbsent,
  matcherGe2ExactlyOne: matcher.listPluginCommandsGe2Count === 1,
  matcherExistingPreserved: matcher.listPluginCommandsExistingPreserved,
  matcherFakeAbsent: matcher.listPluginCommandsFakeAbsent,
  matcherHelp: matcher.matchGe2Help,
  matcherStatus: matcher.matchGe2Status,
  fakeDoesNotMatch: matcher.matchFake === false,
  helpNative: dispatch.help.matched && dispatch.help.nativeText,
  statusNative: dispatch.status.matched && dispatch.status.nativeText,
  runNative: dispatch.run.matched && dispatch.run.nativeText,
  artifactsNative: dispatch.artifacts.matched && dispatch.artifacts.nativeText
};
const pass = Object.values(checks).every(Boolean);
const report = {
  generatedAt: new Date().toISOString(),
  classification: pass ? 'GE2_R7_LOCAL_REGISTRY_VALIDATION_PASS_RESTART_READY' : 'GE2_R7_LOCAL_REGISTRY_VALIDATION_FAILED_NO_RESTART',
  pass,
  gatewayRestartPerformed: false,
  productionPatchInstalled: true,
  loaderSha256: shaFile(loaderPath),
  normal,
  restored,
  matcher,
  dispatch,
  checks
};
const outPath = path.join(artifactDir, 'local_validation_ge2_r7_lifecycle_20260630.json');
fs.writeFileSync(outPath, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ outPath, classification: report.classification, pass, checks, dispatch }, null, 2));
process.exit(pass ? 0 : 1);
