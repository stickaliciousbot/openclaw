import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root='/home/stickai/.openclaw/workspace';
const dir=path.join(root,'sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity');
const dist='/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const files={
  serverMethods:path.join(dist,'server-methods-Dw6hzI_j.js'),
  commands:path.join(dist,'commands-D2qp4St4.js'),
  types:path.join(dist,'types-CdFhLeaX.js'),
  loader:path.join(dist,'loader-Bfm_uDYG.js'),
  telegramBot:path.join(dist,'bot-Ds7bwqAK.js'),
  telegramNative:path.join(dist,'bot-native-commands.runtime-OmS7iYqz.js'),
  handlers:path.join(dist,'commands-handlers.runtime-DlESKC_s.js'),
  registryList:path.join(dist,'commands-registry-list-Cmkm0No9.js'),
  registryData:path.join(dist,'commands-registry.data-DH_mSWlJ.js')
};
function sha(f){return crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')}
function linesAround(text, needle, radius=6){const idx=text.indexOf(needle); if(idx<0)return null; const lines=text.split('\n'); const line=text.slice(0,idx).split('\n').length; return {line, excerpt:lines.slice(Math.max(0,line-radius-1), Math.min(lines.length,line+radius)).join('\n')};}
function allHits(text, needle){let idx=0,h=[]; while((idx=text.indexOf(needle,idx))!==-1){h.push(linesAround(text.slice(0), needle, 2)); idx+=needle.length; if(h.length>50)break;} return h;}
function imports(text){return [...text.matchAll(/from\s+"(\.\/[^"]+)"/g)].map(m=>m[1]);}
const read=Object.fromEntries(Object.entries(files).map(([k,f])=>[k,fs.readFileSync(f,'utf8')]));
const report={
  generatedAt:new Date().toISOString(),
  classification:'GE2_R6_REFINED_COMMAND_PATH_IMPORTED_PATCHED_CHUNK_BUT_REGISTRY_LIFECYCLE_EXCLUDES_GE2',
  mutation:false,
  correction:'The earlier preliminary note that commands.list did not point to the patched chunk was too broad because it selected an agents CLI string candidate. The actual Gateway RPC server-methods chunk does import the patched commands-D2qp4St4.js.',
  actualCommandsListPath:{
    file:files.serverMethods,
    sha256:sha(files.serverMethods),
    symbols:{commandsList:linesAround(read.serverMethods,'"commands.list"'),buildCommandsListResult:linesAround(read.serverMethods,'function buildCommandsListResult'),buildPluginCommandEntries:linesAround(read.serverMethods,'function buildPluginCommandEntries'),listPluginCommandsImport:linesAround(read.serverMethods,'listPluginCommands')},
    imports:imports(read.serverMethods).filter(i=>i.includes('commands')||i.includes('registry')),
    importsPatchedChunk:imports(read.serverMethods).includes('./commands-D2qp4St4.js')
  },
  patchedCommandChunk:{
    file:files.commands,
    sha256:sha(files.commands),
    expectedSha256:'660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb',
    markers:{r5:read.commands.includes('GE2_R5_NATIVE_COMMAND_SURFACE_START'),ensureRegistration:read.commands.includes('ensureNativeGe2CommandRegistered'),matchPluginCommand:read.commands.includes('function matchPluginCommand'),listEffectivePluginCommands:read.commands.includes('function listEffectivePluginCommands')},
    topLevelRegistration:linesAround(read.commands,'ensureNativeGe2CommandRegistered();'),
    listEffectivePluginCommands:linesAround(read.commands,'function listEffectivePluginCommands'),
    listPluginCommands:linesAround(read.commands,'function listPluginCommands'),
    matchPluginCommand:linesAround(read.commands,'function matchPluginCommand')
  },
  registryStateAndReset:{
    typesFile:files.types,
    typesSha256:sha(files.types),
    pluginCommandsState:linesAround(read.types,'PLUGIN_COMMAND_STATE_KEY'),
    clearPluginCommands:linesAround(read.types,'function clearPluginCommands'),
    restorePluginCommands:linesAround(read.types,'function restorePluginCommands'),
    loaderFile:files.loader,
    loaderSha256:sha(files.loader),
    loaderImportsClearRestore:linesAround(read.loader,'clearPluginCommands'),
    registerCommand:linesAround(read.loader,'const registerCommand ='),
    clearHits:['clearPluginCommands();','clearPluginCommandsForPlugin','restorePluginCommands('].map(n=>({needle:n,hit:linesAround(read.loader,n)}))
  },
  telegramCommandPath:{
    botFile:files.telegramBot,
    botSha256:sha(files.telegramBot),
    pluginCatalogCommandsLoop:linesAround(read.telegramBot,'for (const pluginCommand of pluginCatalog.commands)'),
    loadNativeRuntime:linesAround(read.telegramBot,'loadTelegramNativeCommandRuntime'),
    matchAndExecute:linesAround(read.telegramBot,'nativeCommandRuntime.matchPluginCommand(commandBody)'),
    nativeRuntimeFile:files.telegramNative,
    nativeRuntimeSha256:sha(files.telegramNative),
    nativeRuntimeImports:imports(read.telegramNative).filter(i=>i.includes('commands')),
    nativeRuntimeExports:linesAround(read.telegramNative,'export {')
  },
  commandsHandlersTextPath:{
    handlersFile:files.handlers,
    handlersSha256:sha(files.handlers),
    imports:imports(read.handlers).filter(i=>i.includes('commands')),
    resolveTextCommand:linesAround(read.handlers,'resolveTextCommand'),
    matchPluginCommand:linesAround(read.handlers,'matchPluginCommand')
  },
  conclusion:'The actual Gateway RPC commands.list path imports the patched command chunk, and Telegram native command runtime also imports the patched command chunk for matching/execution. Because live commands.list still omits /ge2 after PID turnover, the R5 top-level pluginCommands.set(/ge2) is not durable through plugin registry lifecycle: it is likely cleared/rebuilt by loader registry activation, or Telegram native command catalog is snapshotted before that ad-hoc registration. The next confirmed patch target should be the plugin loader/registry activation path that builds registry.commands and pluginCommands, not another arbitrary command file and not plugin-manager bridges.',
  nextNoMutationTarget:'Design R7 as a snapshot-first patch to register ge2 through the same loader/registerCommand lifecycle or bundled plugin ownership path that produces pair/dreaming/phone/voice, after proving exact call order. No patch in R6.'
};
fs.writeFileSync(path.join(dir,'r6_refined_registry_lifecycle_trace_20260630.json'), JSON.stringify(report,null,2)+'\n');
const md=`# GE2-R6 Refined Registry Lifecycle Trace\n\nClassification: \`${report.classification}\`\n\nMutation: **false**\n\n## Correction\n\n${report.correction}\n\n## Actual commands.list path\n\n- File: \`${files.serverMethods}\`\n- Imports patched chunk: **${report.actualCommandsListPath.importsPatchedChunk}**\n- Patched chunk SHA: \`${report.patchedCommandChunk.sha256}\`\n- R5 marker present: **${report.patchedCommandChunk.markers.r5}**\n\n## Telegram/native matching path\n\n- Telegram bot registers native plugin commands from \`pluginCatalog.commands\`.\n- Handler calls \`nativeCommandRuntime.matchPluginCommand(commandBody)\`.\n- \`bot-native-commands.runtime-OmS7iYqz.js\` imports \`./commands-D2qp4St4.js\`.\n\n## Diagnosis\n\n${report.conclusion}\n\n## Hard stop\n\nNo rollback, no live \`/ge2\` smoke, no cron closeout apply, no plugin-manager bridge patch, and no production mutation were performed.\n`;
fs.writeFileSync(path.join(dir,'GE2_R6_REFINED_REGISTRY_LIFECYCLE_TRACE.md'), md);
console.log(JSON.stringify({classification:report.classification,importsPatchedChunk:report.actualCommandsListPath.importsPatchedChunk,patchedSha:report.patchedCommandChunk.sha256,r5Marker:report.patchedCommandChunk.markers.r5,conclusion:report.conclusion},null,2));
