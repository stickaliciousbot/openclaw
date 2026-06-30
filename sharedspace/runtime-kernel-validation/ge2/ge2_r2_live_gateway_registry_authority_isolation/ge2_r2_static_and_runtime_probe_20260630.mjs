import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const dir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r2_live_gateway_registry_authority_isolation';
fs.mkdirSync(dir,{recursive:true});
const dist = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const commandsPath = path.join(dist,'commands-D2qp4St4.js');
const typesPath = path.join(dist,'types-CdFhLeaX.js');
const serverPath = path.join(dist,'server-methods-Dw6hzI_j.js');

function run(label,args,timeout=120000){
  try { return { label, ok:true, stdout: execFileSync('openclaw', args, {cwd:'/home/stickai/.openclaw/workspace', encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout}) }; }
  catch(e){ return { label, ok:false, status:e.status??null, stdout:e.stdout?.toString?.()??'', stderr:e.stderr?.toString?.()??String(e.message||e) }; }
}
function parseJson(s){ try{return JSON.parse(s)}catch{return null} }
function snippet(file, needle, before=5, after=8){
  const lines=fs.readFileSync(file,'utf8').split('\n');
  const i=lines.findIndex(l=>l.includes(needle));
  if(i<0) return null;
  return {file, needle, startLine:Math.max(1,i+1-before), endLine:Math.min(lines.length,i+1+after), text:lines.slice(Math.max(0,i-before), Math.min(lines.length,i+1+after)).join('\n')};
}

const gatewayStatus = run('gateway status',['gateway','status'],180000);
const commandsDefault = run('commands.list default',['gateway','call','commands.list','--json'],150000);
const commandsTelegram = run('commands.list telegram both',['gateway','call','commands.list','--json','--params','{"provider":"telegram","scope":"both"}'],150000);
const commandsNativeTelegram = run('commands.list telegram native',['gateway','call','commands.list','--json','--params','{"provider":"telegram","scope":"native"}'],150000);
const pluginsList = run('plugins list cli process',['plugins','list','--json']);
const pluginsInspect = run('plugins inspect ge2 cli process',['plugins','inspect','ge2-command','--json']);

const runtimeImports = await Promise.all([
  import('file://' + typesPath),
  import('file://' + commandsPath)
]);
const [typesMod, commandsMod] = runtimeImports;
const registrar = typesMod.p;
const pluginCommandsProxy = typesMod.A;
const beforeKeys = Array.from(pluginCommandsProxy.keys());
const testCommand = {
  name: 'ge2_r2_diag_identity_probe',
  description: 'GE2-R2 diagnostic identity probe command, local process only',
  acceptsArgs: false,
  requireAuth: true,
  handler: async () => ({text:'diag'})
};
let regResult = null;
try { regResult = registrar('ge2-r2-diag', testCommand, { pluginName:'GE2 R2 diagnostic', pluginRoot:dir }); } catch(e) { regResult = {ok:false,error:String(e.message||e)}; }
const afterKeys = Array.from(pluginCommandsProxy.keys());
const localList = commandsMod.r();
const localIdentityProbe = {
  registrarExport: 'types-CdFhLeaX.js export p',
  pluginCommandsExport: 'types-CdFhLeaX.js export A',
  commandsListExport: 'commands-D2qp4St4.js export r',
  beforeKeys,
  regResult,
  afterKeys,
  localListHasProbe: localList.some(c=>c.name==='ge2_r2_diag_identity_probe'),
  localListProbe: localList.find(c=>c.name==='ge2_r2_diag_identity_probe')||null,
  note: 'This proves commands-D2qp4St4.js and types-CdFhLeaX.js share the same global singleton registry within a single Node process. It does not mutate the running Gateway process.'
};

const cmdJson = parseJson(commandsDefault.stdout);
const commands = cmdJson?.commands || cmdJson?.result?.commands || [];
const pluginEntries = commands.filter(c=>c.source==='plugin');
const ge2Live = commands.find(c=>c.name==='ge2' || c.nativeName==='ge2' || (Array.isArray(c.textAliases)&&c.textAliases.includes('/ge2'))) || null;
const pluginsJson = parseJson(pluginsList.stdout);
const plugins = pluginsJson?.plugins || (Array.isArray(pluginsJson)?pluginsJson:[]);
const ge2PluginCli = plugins.find(p=>p.id==='ge2-command'||String(p.source||'').includes('ge2-command')) || null;
const statusText = gatewayStatus.stdout || '';
const pid = statusText.match(/Runtime: running \(pid (\d+)/)?.[1] || null;

const logPath='/tmp/openclaw/openclaw-2026-06-30.log';
let ge2Log=[]; let startupLog=[];
try {
  const lines=fs.readFileSync(logPath,'utf8').split('\n').filter(Boolean);
  ge2Log=lines.filter(l=>/ge2|GE2|plugin command|Registered plugin command|ge2-command/.test(l)).slice(-200);
  startupLog=lines.filter(l=>l.includes('loading configuration')||l.includes('plugins')||l.includes('extension')||l.includes('ge2-command')||l.includes('Registered plugin command')).slice(-250);
} catch(e) { ge2Log=[`log read failed: ${e.message}`]; }

const report = {
  generatedAt: new Date().toISOString(),
  runningGateway: { pid, healthOk:/Connectivity probe: ok/.test(statusText) || /Warm-up/.test(statusText), statusText },
  authorityPath: {
    serverMethod: snippet(serverPath, 'const commandsHandlers = { "commands.list"'),
    buildResult: snippet(serverPath, 'function buildCommandsListResult'),
    buildPluginEntries: snippet(serverPath, 'function buildPluginCommandEntries'),
    listPluginCommands: snippet(commandsPath, 'function listPluginCommands'),
    pluginCommandsImport: snippet(commandsPath, 'import { A as pluginCommands'),
    registryState: snippet(typesPath, 'const PLUGIN_COMMAND_STATE_KEY'),
    registrar: snippet(typesPath, 'function registerPluginCommand')
  },
  localRegistryIdentityProbe: localIdentityProbe,
  liveCommands: {
    defaultOk: commandsDefault.ok,
    count: commands.length,
    ge2Present: Boolean(ge2Live),
    ge2: ge2Live,
    pluginEntries,
    fakePresent: commands.some(c=>c.name==='ge2-r1-fake-unregistered')
  },
  surfaceChecks: {
    telegramBoth: parseJson(commandsTelegram.stdout),
    telegramNative: parseJson(commandsNativeTelegram.stdout)
  },
  cliPluginManagerSnapshot: {
    ok: pluginsList.ok,
    ge2PluginDiscovered: Boolean(ge2PluginCli),
    ge2Plugin: ge2PluginCli,
    inspect: parseJson(pluginsInspect.stdout)
  },
  logs: { ge2Log, startupLog },
  conclusionDraft: {
    commandsListReadsLiveMutableRegistry: true,
    registryObjectIdentityWithinLoadedBundle: localIdentityProbe.localListHasProbe === true,
    cliPluginManagerSnapshotIsNotProofOfRunningGatewayActivation: Boolean(ge2PluginCli) && !ge2Live,
    exactLossPointCandidate: 'ge2-command is visible to CLI plugin manager snapshot/load, but no evidence it is activated into the running Gateway process pluginCommands singleton consumed by commands.list.'
  }
};

fs.writeFileSync(path.join(dir,'ge2_r2_static_and_runtime_probe_20260630.json'), JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(dir,'before_after_commands_list_evidence.json'), JSON.stringify({generatedAt:report.generatedAt, before:'GE2-R1 commands.list ge2Present false', after:report.liveCommands, surfaces:report.surfaceChecks},null,2)+'\n');
console.log(JSON.stringify({pid, ge2Live:Boolean(ge2Live), pluginEntries:pluginEntries.map(c=>c.name), cliPluginGe2:Boolean(ge2PluginCli), localIdentityProbe:localIdentityProbe.localListHasProbe},null,2));
