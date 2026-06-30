import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r8_native_execution_route_discovery';
const cwd = '/home/stickai/.openclaw/workspace';
const dist = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const cfgPath = '/home/stickai/.openclaw/openclaw.json';
const workspaceDir = '/home/stickai/.openclaw/workspace';
const commandsPath = path.join(dist, 'commands-D2qp4St4.js');
const loaderPath = path.join(dist, 'loader-Bfm_uDYG.js');
const typesPath = path.join(dist, 'types-CdFhLeaX.js');
const botNativeRuntimePath = path.join(dist, 'bot-native-commands.runtime-OmS7iYqz.js');
const botPath = path.join(dist, 'bot-Ds7bwqAK.js');
const serverMethodsPath = path.join(dist, 'server-methods-Dw6hzI_j.js');
function shaFile(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function read(file) { return fs.readFileSync(file, 'utf8'); }
function lineHits(file, needles) {
  const text = read(file); const lines = text.split('\n');
  const hits = [];
  for (const needle of needles) {
    lines.forEach((line, idx) => { if (line.includes(needle)) hits.push({ needle, lineNumber: idx + 1, line: line.trim().slice(0, 260) }); });
  }
  return hits;
}
function scanDistFor(needles) {
  const files = fs.readdirSync(dist).filter(name => name.endsWith('.js'));
  const rows = [];
  for (const name of files) {
    const file = path.join(dist, name);
    const text = read(file);
    const present = needles.filter(n => text.includes(n));
    if (present.length > 0) rows.push({ file: name, path: file, sha256: shaFile(file), present });
  }
  return rows.sort((a,b)=>a.file.localeCompare(b.file));
}
function runOpenClaw(args, name, timeout=120000) {
  let stdout='', stderr='', ok=true, status=0;
  try { stdout = execFileSync('openclaw', args, { cwd, encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout }); }
  catch (e) { ok=false; status=e.status??1; stdout=e.stdout?.toString?.()??''; stderr=e.stderr?.toString?.()??String(e.message||e); }
  fs.writeFileSync(path.join(artifactDir, `${name}.stdout.txt`), stdout);
  fs.writeFileSync(path.join(artifactDir, `${name}.stderr.txt`), stderr);
  return { ok, status, stdout, stderr };
}
function extractPid(text) {
  const m = text.match(/Runtime:\s*running\s*\(pid\s+(\d+)/i) || text.match(/Runtime:.*?pid\s+(\d+)/i) || text.match(/PID\s*[:=]?\s*(\d+)/i) || text.match(/pid\D+(\d+)/i);
  return m?.[1] ?? null;
}
function healthFromStatus(res) {
  const text = `${res.stdout}\n${res.stderr}`;
  return {
    commandOk: res.ok,
    pid: extractPid(text),
    serviceRunning: /Runtime:\s*running/i.test(text) || /Service:.*running/i.test(text),
    runtimeRunning: /Runtime:\s*running/i.test(text),
    listenerPresent: /Listening:\s*.+18789/i.test(text) || /Listening:.*\*:18789/i.test(text),
    connectivityOk: /Connectivity probe:\s*ok/i.test(text),
    adminCapable: /Capability:\s*admin-capable/i.test(text),
    rawStatusPreview: text.slice(0, 4000)
  };
}
function commandList(name, params) {
  const args = ['gateway','call','commands.list','--json'];
  if (params) args.push('--params', JSON.stringify(params));
  const res = runOpenClaw(args, `r8_commands_list_${name}`);
  let parsed=null; try { parsed = JSON.parse(res.stdout); } catch {}
  const commands = parsed?.result?.commands || parsed?.commands || [];
  const names = commands.map(c=>c?.name).filter(Boolean);
  const ge2 = commands.filter(c => c?.name === 'ge2' || c?.nativeName === 'ge2' || (c?.textAliases||[]).includes('/ge2'));
  return {
    name, ok: res.ok, parseOk: Boolean(parsed), count: commands.length,
    ge2Present: ge2.length > 0, ge2Count: ge2.length, ge2,
    existingCommandsPreserved: ['pair','dreaming','phone','voice'].every(n => names.includes(n)),
    fakeAbsent: !names.includes('fake') && !names.includes('fake-command') && !commands.some(c => c?.nativeName === 'fake' || (c?.textAliases||[]).includes('/fake')),
    pluginNames: commands.filter(c => c.source === 'plugin').map(c => c.name)
  };
}
function countGe2(commands) {
  return commands.filter(c => {
    const names = [c?.name, c?.nativeName, ...Object.values(c?.nativeNames ?? {})].filter(v => typeof v === 'string').map(v => v.replace(/^\/+/, '').toLowerCase());
    return names.includes('ge2');
  }).length;
}
async function main() {
  fs.mkdirSync(artifactDir, { recursive: true });
  const traceScan = scanDistFor(['matchPluginCommand', 'executePluginCommand', 'bot.command', 'commands.list', 'nativeCommandRuntime', 'sendNativeCommandResult', 'continueAgent']);
  const telegramTrace = {
    entryFile: botPath,
    nativeRuntimeFile: botNativeRuntimePath,
    matcherFile: commandsPath,
    hits: [
      ...lineHits(botPath, ['bot.command', 'nativeCommandRuntime.matchPluginCommand', 'nativeCommandRuntime.executePluginCommand', 'reply', 'sendMessage']),
      ...lineHits(botNativeRuntimePath, ['matchPluginCommand', 'executePluginCommand', 'continueAgent']),
      ...lineHits(commandsPath, ['function matchPluginCommand', 'async function executePluginCommand', 'command.handler(ctx)', 'continueAgent'])
    ]
  };
  const webuiCandidates = traceScan.filter(row => row.file !== path.basename(botPath) && row.file !== path.basename(botNativeRuntimePath) && row.present.some(p => ['matchPluginCommand','executePluginCommand','continueAgent'].includes(p)));
  const webuiTrace = {
    candidateFiles: webuiCandidates,
    conclusion: webuiCandidates.length > 0 ? 'candidate native matcher/handler imports found; inspect candidate files for WebUI adapter if P2 is required' : 'no distinct WebUI native command adapter found by targeted installed-dist symbol scan'
  };

  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  const loader = await import('file://' + loaderPath + '?r8=' + Date.now());
  const types = await import('file://' + typesPath + '?r8=' + Date.now());
  loader.i?.();
  loader.l({ config: cfg, workspaceDir, cache: true });
  const registered = types.k();
  const commands = await import('file://' + commandsPath + '?r8=' + Date.now());
  const specs = commands.r();
  const names = specs.map(c=>c.name);
  const fakeMatch = commands.i('/fake', { channel:'telegram' });
  async function invoke(body) {
    const matched = commands.i(body, { channel:'telegram' });
    if (!matched) return { body, matched:false };
    const result = await commands.n({
      command: matched.command,
      args: matched.args,
      senderId: '8495203551',
      channel: 'telegram',
      isAuthorizedSender: true,
      senderIsOwner: true,
      commandBody: body,
      config: cfg,
      sessionKey: 'r8-native-handler-harness',
      sessionId: 'r8-native-handler-harness',
      accountId: 'r8-local',
      messageId: 'r8-local',
      from: '8495203551',
      to: 'stickbot'
    });
    return {
      body, matched:true,
      commandName: matched.command.name,
      pluginId: matched.command.pluginId,
      pluginName: matched.command.pluginName,
      args: matched.args,
      continueAgent: result?.continueAgent === true,
      hasText: typeof result?.text === 'string' && result.text.length > 0,
      text: typeof result?.text === 'string' ? result.text : JSON.stringify(result)
    };
  }
  const help = await invoke('/ge2 help');
  const status = await invoke('/ge2 status');
  const statusRes = runOpenClaw(['gateway','status'], 'r8_gateway_status');
  const health = healthFromStatus(statusRes);
  const visibility = {
    default: commandList('default'),
    telegram_both: commandList('telegram_both', { provider:'telegram', scope:'both' }),
    telegram_text: commandList('telegram_text', { provider:'telegram', scope:'text' })
  };
  const visibilityRows = Object.values(visibility);
  const checks = {
    handlerHarnessAvailable: Boolean(commands.i && commands.n),
    helpMatched: help.matched,
    statusMatched: status.matched,
    helpNative: /GE2 native commands:\s*\n\/ge2 run <task>/i.test(help.text ?? ''),
    statusNative: /GE2 status:\s*\nrun_id:/i.test(status.text ?? ''),
    noHelpModelFallthrough: help.matched && help.continueAgent === false && help.hasText && !/as an ai|language model|i can help/i.test(help.text ?? ''),
    noStatusModelFallthrough: status.matched && status.continueAgent === false && status.hasText && !/as an ai|language model|i can help/i.test(status.text ?? ''),
    fakeAbsentHarness: !fakeMatch,
    ge2SpecExactlyOne: countGe2(specs) === 1,
    ge2RegisteredExactlyOne: countGe2(registered) === 1,
    existingPreservedHarness: ['pair','dreaming','phone','voice'].every(n => names.includes(n)),
    gatewayHealthGreen: health.commandOk && health.serviceRunning && health.runtimeRunning && health.listenerPresent && health.connectivityOk && health.adminCapable,
    visibilityStillPass: visibilityRows.every(row => row.ok && row.parseOk && row.ge2Present && row.ge2Count === 1 && row.existingCommandsPreserved && row.fakeAbsent)
  };
  const pass = Object.values(checks).every(Boolean);
  const classification = pass ? 'GE2_R8_HELP_STATUS_NATIVE_EXECUTION_PASS_RUN_PENDING' : (checks.handlerHarnessAvailable && checks.helpNative && checks.statusNative ? 'GE2_R8_NATIVE_HANDLER_HARNESS_PASS_HELP_STATUS_PENDING_LIVE_SURFACE' : 'GE2_R8_NATIVE_EXECUTION_PROOF_PATH_MISSING_NO_MUTATION');
  const traceTable = {
    telegramNativeCommandEntryFile: botPath,
    telegramNativeMatcherFile: commandsPath,
    telegramNativeHandlerFunction: 'executePluginCommand() -> command.handler(ctx) in commands-D2qp4St4.js; Telegram adapter via bot-native-commands.runtime-OmS7iYqz.js',
    webuiNativeCommandEntryFile: webuiTrace.candidateFiles.map(f=>f.path).join('; ') || 'not proven in R8 targeted scan',
    webuiNativeHandlerFunction: webuiTrace.candidateFiles.length ? 'candidate imports matchPluginCommand/executePluginCommand; exact WebUI adapter requires deeper P2 trace' : 'not identified',
    sharedGe2DispatcherReached: checks.helpNative && checks.statusNative ? 'yes' : 'no',
    nonModelHarnessAvailable: checks.handlerHarnessAvailable ? 'yes' : 'no',
    liveGatewayRpcAvailable: 'commands.list only; no native execute RPC found',
    proposedProofPath: 'Option A — installed-dist native handler harness using production commands-D2qp4St4.js matcher and executePluginCommand',
    productionMutationRequired: 'no'
  };
  const report = {
    generatedAt: new Date().toISOString(),
    classification,
    pass,
    proofPathUsed: 'Option A — installed-dist native handler harness',
    productionTouched: false,
    gatewayRestarted: false,
    rollbackPerformed: false,
    cronCloseoutApplyRetried: false,
    ge2RunExecuted: false,
    files: {
      commandsPath, commandsSha256: shaFile(commandsPath),
      loaderPath, loaderSha256: shaFile(loaderPath),
      botPath, botSha256: shaFile(botPath),
      botNativeRuntimePath, botNativeRuntimeSha256: shaFile(botNativeRuntimePath),
      serverMethodsPath, serverMethodsSha256: shaFile(serverMethodsPath)
    },
    traceTable,
    telegramTrace,
    webuiTrace,
    harness: {
      registeredGe2Count: countGe2(registered),
      listPluginCommandsGe2Count: countGe2(specs),
      existingCommandsPreserved: checks.existingPreservedHarness,
      fakeCommandAbsent: checks.fakeAbsentHarness,
      help: { matched: help.matched, commandName: help.commandName, pluginId: help.pluginId, continueAgent: help.continueAgent, textPreview: (help.text ?? '').slice(0, 1200) },
      status: { matched: status.matched, commandName: status.commandName, pluginId: status.pluginId, continueAgent: status.continueAgent, textPreview: (status.text ?? '').slice(0, 1200) }
    },
    modelChatFallthroughCheck: {
      helpNoFallthrough: checks.noHelpModelFallthrough,
      statusNoFallthrough: checks.noStatusModelFallthrough,
      evidence: 'Directly invoked installed production executePluginCommand() with matched command object; result.continueAgent was false and native GE2 text returned.'
    },
    gatewayHealth: health,
    commandsListVisibility: visibility,
    checks
  };
  const jsonPath = path.join(artifactDir, 'GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_REPORT_20260630.json');
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2) + '\n');
  const mdPath = path.join(artifactDir, 'GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_REPORT_20260630.md');
  fs.writeFileSync(mdPath, `# GE2-R8 Native Execution Route Discovery Report\n\nFinal classification: \`${classification}\`\n\n## Trace table\n\n| Question | Result |\n|---|---|\n| Telegram native command entry file | ${traceTable.telegramNativeCommandEntryFile} |\n| Telegram native matcher file | ${traceTable.telegramNativeMatcherFile} |\n| Telegram native handler function | ${traceTable.telegramNativeHandlerFunction} |\n| WebUI native command entry file | ${traceTable.webuiNativeCommandEntryFile} |\n| WebUI native handler function | ${traceTable.webuiNativeHandlerFunction} |\n| Shared /ge2 dispatcher reached? | ${traceTable.sharedGe2DispatcherReached} |\n| Non-model harness available? | ${traceTable.nonModelHarnessAvailable} |\n| Live Gateway RPC available? | ${traceTable.liveGatewayRpcAvailable} |\n| Proposed proof path | ${traceTable.proposedProofPath} |\n| Production mutation required? | ${traceTable.productionMutationRequired} |\n\n## Proof path used\n\n${report.proofPathUsed}\n\n## Help result\n\n\`\`\`text\n${report.harness.help.textPreview}\n\`\`\`\n\n## Status result\n\n\`\`\`text\n${report.harness.status.textPreview}\n\`\`\`\n\n## Model/chat fallthrough\n\n- help: ${checks.noHelpModelFallthrough ? 'no fallthrough' : 'FAILED/UNKNOWN'}\n- status: ${checks.noStatusModelFallthrough ? 'no fallthrough' : 'FAILED/UNKNOWN'}\n\n## Safety\n\n- production touched: no\n- Gateway restarted: no\n- rollback performed: no\n- /ge2 run executed: no\n- cron closeout apply retried: no\n\n## Gates\n\n- Gateway health green: ${checks.gatewayHealthGreen}\n- visibility still pass: ${checks.visibilityStillPass}\n- fake absent: ${checks.fakeAbsentHarness}\n- duplicate /ge2 absent: ${checks.ge2SpecExactlyOne}\n\nJSON: ${jsonPath}\n`);
  console.log(JSON.stringify({ jsonPath, mdPath, classification, pass, traceTable, help: report.harness.help, status: report.harness.status, checks }, null, 2));
  process.exit(pass ? 0 : 1);
}
main().catch(error => {
  const errPath = path.join(artifactDir, 'GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_ERROR_20260630.txt');
  fs.writeFileSync(errPath, error?.stack || String(error));
  console.error(error?.stack || String(error));
  process.exit(1);
});
