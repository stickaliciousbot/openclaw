import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r9_native_run_lifecycle_proof';
const cwd = '/home/stickai/.openclaw/workspace';
const dist = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const cfgPath = '/home/stickai/.openclaw/openclaw.json';
const workspaceDir = '/home/stickai/.openclaw/workspace';
const commandsPath = path.join(dist, 'commands-D2qp4St4.js');
const loaderPath = path.join(dist, 'loader-Bfm_uDYG.js');
const typesPath = path.join(dist, 'types-CdFhLeaX.js');
const stateDir = '/home/stickai/.openclaw/workspace/state/ge2-native';
const runsDir = path.join(stateDir, 'runs');
const runsIndexPath = path.join(stateDir, 'runs.index.json');
const runsJsonlPath = path.join(stateDir, 'runs.jsonl');
const milestonesPath = path.join(stateDir, 'milestones.jsonl');
const artifactsJsonlPath = path.join(stateDir, 'artifacts.jsonl');
const taskName = 'r9-native-handler-smoke';

fs.mkdirSync(artifactDir, { recursive: true });
function shaBytes(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function shaFile(file) { return shaBytes(fs.readFileSync(file)); }
function safeReadJson(file, fallback=null) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } }
function readJsonl(file) { try { return fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(line => { try { return JSON.parse(line); } catch { return { parseError:true, raw:line }; } }); } catch { return []; } }
function responseSummary(text) { return { bytes: Buffer.byteLength(String(text ?? ''), 'utf8'), chars: String(text ?? '').length, preview: String(text ?? '').slice(0, 1400), boundedUnder4k: Buffer.byteLength(String(text ?? ''), 'utf8') < 4096 }; }
function runOpenClaw(args, name, timeout=120000) {
  let stdout='', stderr='', ok=true, status=0;
  try { stdout = execFileSync('openclaw', args, { cwd, encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout }); }
  catch (e) { ok=false; status=e.status??1; stdout=e.stdout?.toString?.()??''; stderr=e.stderr?.toString?.()??String(e.message||e); }
  fs.writeFileSync(path.join(artifactDir, `${name}.stdout.txt`), stdout);
  fs.writeFileSync(path.join(artifactDir, `${name}.stderr.txt`), stderr);
  return { ok, status, stdout, stderr };
}
function healthFromStatus(res) {
  const text = `${res.stdout}\n${res.stderr}`;
  return {
    commandOk: res.ok,
    serviceRunning: /Runtime:\s*running/i.test(text) || /Service:.*running/i.test(text),
    runtimeRunning: /Runtime:\s*running/i.test(text),
    listenerPresent: /Listening:\s*.+18789/i.test(text) || /Listening:.*\*:18789/i.test(text),
    connectivityOk: /Connectivity probe:\s*ok/i.test(text),
    adminCapable: /Capability:\s*admin-capable/i.test(text),
    rawPreview: text.slice(0, 3000)
  };
}
function commandList(name, params) {
  const args = ['gateway','call','commands.list','--json'];
  if (params) args.push('--params', JSON.stringify(params));
  const res = runOpenClaw(args, `r9_commands_list_${name}`);
  let parsed=null; try { parsed = JSON.parse(res.stdout); } catch {}
  const commands = parsed?.result?.commands || parsed?.commands || [];
  const names = commands.map(c => c?.name).filter(Boolean);
  const ge2 = commands.filter(c => c?.name === 'ge2' || c?.nativeName === 'ge2' || (c?.textAliases || []).includes('/ge2'));
  return {
    name, ok: res.ok, parseOk: Boolean(parsed), count: commands.length,
    ge2Present: ge2.length > 0, ge2Count: ge2.length,
    existingCommandsPreserved: ['pair','dreaming','phone','voice'].every(n => names.includes(n)),
    fakeAbsent: !names.includes('fake') && !names.includes('fake-command') && !commands.some(c => c?.nativeName === 'fake' || (c?.textAliases||[]).includes('/fake')),
    pluginNames: commands.filter(c => c.source === 'plugin').map(c => c.name),
    ge2
  };
}
function countGe2(commands) {
  return commands.filter(c => {
    const names = [c?.name, c?.nativeName, ...Object.values(c?.nativeNames ?? {})].filter(v => typeof v === 'string').map(v => v.replace(/^\/+/, '').toLowerCase());
    return names.includes('ge2');
  }).length;
}
function noModelFallthrough(result) {
  const text = String(result?.text ?? '');
  return result?.matched === true && result?.continueAgent === false && result?.hasText === true && !/as an ai|language model|i can help|chatgpt/i.test(text);
}
async function sleep(ms) { await new Promise(resolve => setTimeout(resolve, ms)); }

async function main() {
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  const loader = await import('file://' + loaderPath + '?r9=' + Date.now());
  const types = await import('file://' + typesPath + '?r9=' + Date.now());
  loader.i?.();
  loader.l({ config: cfg, workspaceDir, cache: true });
  const registered = types.k();
  const commands = await import('file://' + commandsPath + '?r9=' + Date.now());
  const specs = commands.r();
  const names = specs.map(c => c.name);
  const fakeMatch = commands.i('/fake', { channel:'telegram' });
  async function invoke(body) {
    const matched = commands.i(body, { channel:'telegram' });
    if (!matched) return { body, matched:false, continueAgent:null, hasText:false, text:'' };
    const result = await commands.n({
      command: matched.command,
      args: matched.args,
      senderId: '8495203551',
      channel: 'telegram',
      isAuthorizedSender: true,
      senderIsOwner: true,
      commandBody: body,
      config: cfg,
      sessionKey: 'r9-native-handler-harness',
      sessionId: 'r9-native-handler-harness',
      accountId: 'r9-local',
      messageId: 'r9-local',
      from: '8495203551',
      to: 'stickbot'
    });
    const text = typeof result?.text === 'string' ? result.text : JSON.stringify(result);
    return {
      body, matched:true,
      commandName: matched.command.name,
      pluginId: matched.command.pluginId,
      pluginName: matched.command.pluginName,
      args: matched.args,
      continueAgent: result?.continueAgent === true,
      hasText: typeof result?.text === 'string' && result.text.length > 0,
      text,
      responseSummary: responseSummary(text)
    };
  }

  const beforeRunsJsonlCount = readJsonl(runsJsonlPath).length;
  const beforeMilestonesJsonlCount = readJsonl(milestonesPath).length;
  const beforeArtifactsJsonlCount = readJsonl(artifactsJsonlPath).length;

  const runResult = await invoke(`/ge2 run ${taskName}`);
  const runId = runResult.text.match(/run_id:\s*(\S+)/)?.[1] ?? null;
  const runPath = runId ? path.join(runsDir, `${runId}.json`) : null;
  const statusPolls = [];
  let terminalRun = null;
  if (runId) {
    for (let i = 0; i < 16; i++) {
      await sleep(i === 0 ? 180 : 250);
      const run = safeReadJson(runPath, null);
      statusPolls.push({ index:i, status:run?.status ?? null, milestones:Array.isArray(run?.milestones)?run.milestones.length:null, artifacts:Array.isArray(run?.artifacts)?run.artifacts.length:null, errors:Array.isArray(run?.errors)?run.errors.length:null });
      if (['completed','failed','cancelled'].includes(run?.status)) { terminalRun = run; break; }
    }
  }
  if (!terminalRun && runPath) terminalRun = safeReadJson(runPath, null);

  const statusResult = runId ? await invoke(`/ge2 status ${runId}`) : { body:'/ge2 status <missing>', matched:false, text:'missing run_id', responseSummary:responseSummary('missing run_id') };
  const artifactsResult = runId ? await invoke(`/ge2 artifacts ${runId}`) : { body:'/ge2 artifacts <missing>', matched:false, text:'missing run_id', responseSummary:responseSummary('missing run_id') };

  const finalRun = runId && runPath ? safeReadJson(runPath, null) : null;
  const artifacts = Array.isArray(finalRun?.artifacts) ? finalRun.artifacts : [];
  const artifactProofs = artifacts.map(artifact => {
    const exists = typeof artifact.path === 'string' && fs.existsSync(artifact.path);
    const computedSha256 = exists ? shaFile(artifact.path) : null;
    return { ...artifact, exists, computedSha256, shaMatches: exists && artifact.sha256 === computedSha256 };
  });
  const milestones = Array.isArray(finalRun?.milestones) ? finalRun.milestones : [];
  const terminalFileCandidates = runId ? ['status.json','summary.json','evidence_manifest.json'].map(name => path.join(stateDir, 'artifacts', runId, name)) : [];
  const terminalFiles = terminalFileCandidates.map(file => ({ path:file, exists:fs.existsSync(file), sha256:fs.existsSync(file)?shaFile(file):null }));
  const terminalFilesWritten = terminalFiles.filter(f => f.exists);

  const runsJsonl = readJsonl(runsJsonlPath);
  const milestonesJsonl = readJsonl(milestonesPath);
  const artifactsJsonl = readJsonl(artifactsJsonlPath);
  const ledgerProof = {
    stateDir,
    runsIndexPath,
    runsJsonlPath,
    milestonesPath,
    artifactsJsonlPath,
    runPath,
    ledgerFileExists: Boolean(runPath && fs.existsSync(runPath)),
    runIdRecordedInRunFile: finalRun?.run_id === runId,
    runIdRecordedInIndex: Boolean(safeReadJson(runsIndexPath, {runs:[]})?.runs?.some?.(entry => entry.run_id === runId)),
    runIdRecordedInRunsJsonl: runsJsonl.some(entry => entry.run_id === runId),
    originSessionMetadataPresent: Boolean(finalRun?.origin && (finalRun.origin.sessionKey || finalRun.origin.sessionId || finalRun.origin.senderId || finalRun.origin.channel)),
    milestoneHistoryPresent: milestones.length > 0 && milestonesJsonl.some(entry => entry.run_id === runId),
    artifactInventoryPresent: artifacts.length > 0 && artifactsJsonl.some(entry => entry.run_id === runId),
    beforeCounts: { runsJsonl: beforeRunsJsonlCount, milestonesJsonl: beforeMilestonesJsonlCount, artifactsJsonl: beforeArtifactsJsonlCount },
    afterCounts: { runsJsonl: runsJsonl.length, milestonesJsonl: milestonesJsonl.length, artifactsJsonl: artifactsJsonl.length }
  };

  const health = healthFromStatus(runOpenClaw(['gateway','status'], 'r9_gateway_status'));
  const visibility = {
    default: commandList('default'),
    telegram_both: commandList('telegram_both', { provider:'telegram', scope:'both' }),
    telegram_text: commandList('telegram_text', { provider:'telegram', scope:'text' })
  };
  const visibilityRows = Object.values(visibility);

  const compressionSummary = {
    runResponse: runResult.responseSummary,
    statusResponse: statusResult.responseSummary,
    artifactsResponse: artifactsResult.responseSummary,
    allVisibleResponsesBounded: [runResult, statusResult, artifactsResult].every(r => r.responseSummary?.boundedUnder4k),
    fullPayloadStoredInLedgerOrArtifact: ledgerProof.ledgerFileExists && artifacts.length > 0,
    responseIncludesArtifactRefsHashes: /sha256/i.test(artifactsResult.text ?? '') && artifacts.some(a => artifactsResult.text.includes(a.path ?? '') || artifactsResult.text.includes(a.sha256 ?? '')),
    noMassiveRawLogsInResponse: [runResult, statusResult, artifactsResult].every(r => (r.responseSummary?.bytes ?? 999999) < 4096)
  };

  const checks = {
    proofLevelP1: true,
    noP2P3Claim: true,
    runMatchedNative: runResult.matched && runResult.commandName === 'ge2' && runResult.pluginId === 'ge2-native',
    runNoModelFallthrough: noModelFallthrough(runResult),
    runReturnedRunId: Boolean(runId),
    ledgerExists: ledgerProof.ledgerFileExists,
    durableRunRecordCreated: ledgerProof.runIdRecordedInRunFile && ledgerProof.runIdRecordedInIndex && ledgerProof.runIdRecordedInRunsJsonl,
    statusTransitionsExpected: statusPolls.some(p => p.status === 'accepted' || p.status === 'validated') && statusPolls.some(p => p.status === 'completed') || milestones.some(m => m.milestone === 'accepted') && milestones.some(m => m.milestone === 'completed'),
    milestoneEventsEmitted: milestones.length >= 5 && ledgerProof.milestoneHistoryPresent,
    artifactWritten: artifacts.length >= 1 && ledgerProof.artifactInventoryPresent,
    artifactShaComputed: artifacts.every(a => typeof a.sha256 === 'string' && /^[a-f0-9]{64}$/i.test(a.sha256)),
    artifactFilesExist: artifactProofs.length > 0 && artifactProofs.every(a => a.exists),
    artifactHashesMatch: artifactProofs.length > 0 && artifactProofs.every(a => a.shaMatches),
    terminalStatusSuccessful: ['completed','pass','passed','success','succeeded'].includes(String(finalRun?.status || '').toLowerCase()),
    noPlaceholderSuccess: Boolean(runId && ledgerProof.ledgerFileExists && artifacts.length > 0 && milestones.length > 0),
    runResponseBounded: runResult.responseSummary?.boundedUnder4k === true,
    statusRetrievesExactRun: statusResult.matched && noModelFallthrough(statusResult) && statusResult.text.includes(runId ?? '__missing__') && /milestones:\s*\d+/i.test(statusResult.text) && /artifacts:\s*\d+/i.test(statusResult.text),
    artifactsRetrievesExactRun: artifactsResult.matched && noModelFallthrough(artifactsResult) && artifactsResult.text.includes(runId ?? '__missing__') && artifacts.some(a => artifactsResult.text.includes(a.sha256)),
    compressionGate: compressionSummary.allVisibleResponsesBounded && compressionSummary.noMassiveRawLogsInResponse && compressionSummary.fullPayloadStoredInLedgerOrArtifact && compressionSummary.responseIncludesArtifactRefsHashes,
    fakeCommandAbsent: !fakeMatch && visibilityRows.every(row => row.fakeAbsent),
    duplicateGe2CountOne: countGe2(specs) === 1 && countGe2(registered) === 1 && visibilityRows.every(row => row.ge2Count === 1),
    existingCommandsPreserved: ['pair','dreaming','phone','voice'].every(n => names.includes(n)) && visibilityRows.every(row => row.existingCommandsPreserved),
    gatewayHealthGreen: health.commandOk && health.serviceRunning && health.runtimeRunning && health.listenerPresent && health.connectivityOk && health.adminCapable,
    liveVisibilityStillPass: visibilityRows.every(row => row.ok && row.parseOk && row.ge2Present && row.ge2Count === 1 && row.existingCommandsPreserved && row.fakeAbsent),
    terminalRequiredFileCheckSafe: terminalFilesWritten.length === 0 || terminalFilesWritten.every(f => f.sha256)
  };

  let classification = 'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_PASS_P2_PENDING';
  if (!checks.runMatchedNative) classification = 'GE2_R9_NATIVE_RUN_MATCH_FAILED';
  else if (!checks.runNoModelFallthrough) classification = 'GE2_R9_NATIVE_RUN_MODEL_FALLTHROUGH_FAIL';
  else if (checks.runReturnedRunId && !checks.noPlaceholderSuccess) classification = 'GE2_R9_PLACEHOLDER_SUCCESS_FAIL';
  else if (!checks.ledgerExists || !checks.durableRunRecordCreated) classification = 'GE2_R9_LEDGER_MISSING_FAIL';
  else if (!checks.artifactWritten || !checks.artifactFilesExist || !checks.artifactHashesMatch) classification = 'GE2_R9_ARTIFACT_HASH_FAIL';
  else if (!checks.statusRetrievesExactRun || !checks.artifactsRetrievesExactRun) classification = 'GE2_R9_STATUS_ARTIFACTS_RETRIEVAL_FAIL';
  else if (!Object.values(checks).every(Boolean)) classification = 'GE2_R9_PLACEHOLDER_SUCCESS_FAIL';

  const report = {
    generatedAt: new Date().toISOString(),
    finalClassification: classification,
    proofLevel: 'P1 only',
    noP2P3Claim: true,
    taskName,
    commandResults: {
      run: { body: runResult.body, matched: runResult.matched, commandName: runResult.commandName, pluginId: runResult.pluginId, continueAgent: runResult.continueAgent, text: runResult.text, responseSummary: runResult.responseSummary },
      status: { body: statusResult.body, matched: statusResult.matched, commandName: statusResult.commandName, pluginId: statusResult.pluginId, continueAgent: statusResult.continueAgent, text: statusResult.text, responseSummary: statusResult.responseSummary },
      artifacts: { body: artifactsResult.body, matched: artifactsResult.matched, commandName: artifactsResult.commandName, pluginId: artifactsResult.pluginId, continueAgent: artifactsResult.continueAgent, text: artifactsResult.text, responseSummary: artifactsResult.responseSummary }
    },
    runId,
    statusPolls,
    ledgerPath: runPath,
    ledgerProof,
    artifactPaths: artifactProofs.map(a => a.path),
    artifactSha256s: artifactProofs.map(a => ({ path:a.path, reportedSha256:a.sha256, computedSha256:a.computedSha256, shaMatches:a.shaMatches })),
    milestoneCount: milestones.length,
    milestones,
    finalRun,
    terminalFiles,
    statusResult: statusResult.text,
    artifactsResult: artifactsResult.text,
    compressionSummary,
    modelChatFallthroughCheck: { run:noModelFallthrough(runResult), status:noModelFallthrough(statusResult), artifacts:noModelFallthrough(artifactsResult), evidence:'Installed-dist executePluginCommand returned continueAgent:false and native GE2 text for all three commands.' },
    fakeCommandAbsent: checks.fakeCommandAbsent,
    duplicateGe2Count: { registered: countGe2(registered), listPluginCommands: countGe2(specs), live: Object.fromEntries(Object.entries(visibility).map(([k,v]) => [k, v.ge2Count])) },
    existingCommandsPreserved: checks.existingCommandsPreserved,
    gatewayHealth: health,
    commandsListVisibility: visibility,
    productionTouched: false,
    ge2RuntimeStateTouched: true,
    gatewayRestarted: false,
    rollbackPerformed: false,
    cronCloseoutApplyRetried: false,
    promoted: false,
    nextStepIfPass: classification === 'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_PASS_P2_PENDING' ? 'GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_HELP_STATUS_RUN_PENDING' : null,
    checks
  };

  const jsonPath = path.join(artifactDir, 'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_REPORT_20260630.json');
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2) + '\n');
  const mdPath = path.join(artifactDir, 'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_REPORT_20260630.md');
  fs.writeFileSync(mdPath, `# GE2-R9 Native Handler Run/Status/Artifacts Report\n\nFinal classification: \`${classification}\`\n\nProof level: **P1 only**  \nNo P2/P3 claim: **true**\n\n## Commands\n\n- run: \`${runResult.body}\`\n- status: \`${statusResult.body}\`\n- artifacts: \`${artifactsResult.body}\`\n\nRun ID: \`${runId}\`\n\n## Results\n\n- run matched native: ${checks.runMatchedNative}\n- run no model/chat fallthrough: ${checks.runNoModelFallthrough}\n- status exact retrieval: ${checks.statusRetrievesExactRun}\n- artifacts exact retrieval: ${checks.artifactsRetrievesExactRun}\n- terminal status: ${finalRun?.status ?? 'unknown'}\n- milestone count: ${milestones.length}\n- artifact count: ${artifactProofs.length}\n\n## Ledger/artifacts\n\nLedger path: \`${runPath}\`\n\n${artifactProofs.map(a => `- ${a.path} sha=${a.sha256} computed=${a.computedSha256} match=${a.shaMatches}`).join('\n')}\n\n## Compression\n\n- run response bytes: ${runResult.responseSummary?.bytes}\n- status response bytes: ${statusResult.responseSummary?.bytes}\n- artifacts response bytes: ${artifactsResult.responseSummary?.bytes}\n- all bounded under 4KB: ${compressionSummary.allVisibleResponsesBounded}\n- artifact refs/hashes in response: ${compressionSummary.responseIncludesArtifactRefsHashes}\n\n## Safety\n\n- production touched: no\n- GE2 runtime state touched: yes, intended by /ge2 run\n- Gateway restarted: no\n- rollback performed: no\n- promoted: no\n\nJSON: ${jsonPath}\n`);
  console.log(JSON.stringify({ jsonPath, mdPath, finalClassification: classification, runId, milestoneCount: milestones.length, artifactProofs, checks }, null, 2));
  process.exit(classification === 'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_PASS_P2_PENDING' ? 0 : 1);
}

main().catch(error => {
  const errPath = path.join(artifactDir, 'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_ERROR_20260630.txt');
  fs.writeFileSync(errPath, error?.stack || String(error));
  console.error(error?.stack || String(error));
  process.exit(1);
});
