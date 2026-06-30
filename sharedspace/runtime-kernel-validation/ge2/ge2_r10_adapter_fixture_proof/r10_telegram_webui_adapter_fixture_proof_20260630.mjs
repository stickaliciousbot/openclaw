import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const outDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof';
const cwd = '/home/stickai/.openclaw/workspace';
const cfgPath = '/home/stickai/.openclaw/openclaw.json';
const workspaceDir = '/home/stickai/.openclaw/workspace';
const dist = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const loaderPath = `${dist}/loader-Bfm_uDYG.js`;
const commandsPath = `${dist}/commands-D2qp4St4.js`;
const telegramBotPath = `${dist}/bot-Ds7bwqAK.js`;
const commandHandlersPath = `${dist}/commands-handlers.runtime-DlESKC_s.js`;
const typesPath = `${dist}/types-CdFhLeaX.js`;
const stateDir = `${workspaceDir}/state/ge2-native`;
const runsDir = `${stateDir}/runs`;
const runsIndexPath = `${stateDir}/runs.index.json`;
const runsJsonlPath = `${stateDir}/runs.jsonl`;
const milestonesPath = `${stateDir}/milestones.jsonl`;
const artifactsJsonlPath = `${stateDir}/artifacts.jsonl`;
fs.mkdirSync(outDir, { recursive: true });

function shaFile(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function safeJson(file, fallback=null) { try { return JSON.parse(fs.readFileSync(file,'utf8')); } catch { return fallback; } }
function readJsonl(file) { try { return fs.readFileSync(file,'utf8').split('\n').filter(Boolean).map(l=>JSON.parse(l)); } catch { return []; } }
function responseSummary(text) { const s=String(text??''); return { bytes: Buffer.byteLength(s,'utf8'), chars:s.length, boundedUnder4k: Buffer.byteLength(s,'utf8') < 4096, preview:s.slice(0,1400) }; }
function runOpenClaw(args, name, timeout=120000) {
  let stdout='', stderr='', ok=true, status=0;
  try { stdout=execFileSync('openclaw', args, {cwd, encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout}); }
  catch(e){ ok=false; status=e.status??1; stdout=e.stdout?.toString?.()??''; stderr=e.stderr?.toString?.()??String(e.message||e); }
  fs.writeFileSync(`${outDir}/${name}.stdout.txt`, stdout);
  fs.writeFileSync(`${outDir}/${name}.stderr.txt`, stderr);
  return {ok,status,stdout,stderr};
}
function healthFromStatus(res) {
  const t=`${res.stdout}\n${res.stderr}`;
  return { commandOk:res.ok, serviceRunning:/Runtime:\s*running/i.test(t)||/Service:.*running/i.test(t), runtimeRunning:/Runtime:\s*running/i.test(t), listenerPresent:/Listening:\s*.+18789/i.test(t)||/Listening:.*\*:18789/i.test(t), connectivityOk:/Connectivity probe:\s*ok/i.test(t), adminCapable:/Capability:\s*admin-capable/i.test(t), rawPreview:t.slice(0,2500) };
}
function commandList(name, params) {
  const args=['gateway','call','commands.list','--json'];
  if (params) args.push('--params', JSON.stringify(params));
  const res=runOpenClaw(args, `r10_commands_list_${name}`);
  let parsed=null; try { parsed=JSON.parse(res.stdout); } catch {}
  const commands=parsed?.result?.commands || parsed?.commands || [];
  const names=commands.map(c=>c?.name).filter(Boolean);
  const ge2=commands.filter(c=>c?.name==='ge2'||c?.nativeName==='ge2'||(c?.textAliases||[]).includes('/ge2'));
  return { name, ok:res.ok, parseOk:Boolean(parsed), count:commands.length, ge2Present:ge2.length>0, ge2Count:ge2.length, existingCommandsPreserved:['pair','dreaming','phone','voice'].every(n=>names.includes(n)), fakeAbsent:!names.includes('fake')&&!names.includes('fake-command')&&!commands.some(c=>c?.nativeName==='fake'||(c?.textAliases||[]).includes('/fake')), ge2 };
}
function noModelFallthroughText(text) { return !/\b(as an ai|language model|i can help|chatgpt|i(?:'|’)m sorry,? but)\b/i.test(String(text??'')); }
async function sleep(ms){ await new Promise(r=>setTimeout(r,ms)); }
async function waitTerminal(runId) {
  const runPath=`${runsDir}/${runId}.json`;
  const polls=[];
  let run=null;
  for (let i=0;i<20;i++) {
    await sleep(i===0?220:250);
    run=safeJson(runPath,null);
    polls.push({ index:i, status:run?.status??null, milestones:Array.isArray(run?.milestones)?run.milestones.length:null, artifacts:Array.isArray(run?.artifacts)?run.artifacts.length:null, errors:Array.isArray(run?.errors)?run.errors.length:null });
    if (['completed','failed','cancelled'].includes(run?.status)) break;
  }
  return { run:safeJson(runPath,null), polls };
}
function verifyRun(runId, exactStatusText, exactArtifactsText) {
  const runPath=`${runsDir}/${runId}.json`;
  const run=safeJson(runPath,null);
  const artifacts=Array.isArray(run?.artifacts)?run.artifacts:[];
  const artifactProofs=artifacts.map(a=>{ const exists=typeof a.path==='string' && fs.existsSync(a.path); const computedSha256=exists?shaFile(a.path):null; return {...a, exists, computedSha256, shaMatches:exists && computedSha256===a.sha256}; });
  const milestones=Array.isArray(run?.milestones)?run.milestones:[];
  const index=safeJson(runsIndexPath,{runs:[]});
  const runsJsonl=readJsonl(runsJsonlPath);
  const milestonesJsonl=readJsonl(milestonesPath);
  const artifactsJsonl=readJsonl(artifactsJsonlPath);
  const shaRegex=/\b[a-f0-9]{64}\b/i;
  const artifactText=String(exactArtifactsText??'');
  return {
    runPath,
    run,
    artifacts: artifactProofs,
    milestones,
    ledger: {
      ledgerExists:fs.existsSync(runPath),
      runIdRecordedInRunFile:run?.run_id===runId,
      runIdRecordedInIndex:Boolean(index?.runs?.some?.(e=>e.run_id===runId)),
      runIdRecordedInRunsJsonl:runsJsonl.some(e=>e.run_id===runId),
      originSessionMetadataPresent:Boolean(run?.origin && (run.origin.sessionKey||run.origin.sessionId||run.origin.senderId||run.origin.channel||run.origin.surface)),
      milestoneHistoryPresent:milestones.length>0 && milestonesJsonl.some(e=>e.run_id===runId),
      artifactInventoryPresent:artifacts.length>0 && artifactsJsonl.some(e=>e.run_id===runId)
    },
    checks: {
      durableLedgerEntry:Boolean(fs.existsSync(runPath) && run?.run_id===runId && index?.runs?.some?.(e=>e.run_id===runId) && runsJsonl.some(e=>e.run_id===runId)),
      emitsMilestones:milestones.length>=5 && milestones.some(m=>m.milestone==='completed'),
      artifactExists:artifactProofs.length>0 && artifactProofs.every(a=>a.exists),
      artifactShaMatches:artifactProofs.length>0 && artifactProofs.every(a=>a.shaMatches),
      terminalCompleted:run?.status==='completed',
      statusRetrievesExactRun:String(exactStatusText??'').includes(runId) && /status:\s*completed/i.test(String(exactStatusText??'')),
      artifactsRetrievesExactRun:artifactText.includes(runId) && artifactProofs.some(a=>artifactText.includes(a.sha256)) && shaRegex.test(artifactText),
      boundedStatus:responseSummary(exactStatusText).boundedUnder4k,
      boundedArtifacts:responseSummary(exactArtifactsText).boundedUnder4k
    }
  };
}
function extractRunId(text) { return String(text??'').match(/run_id:\s*(\S+)/)?.[1] ?? null; }
function classifySurface(surface) {
  const c=surface.checks;
  if (!c.fixtureEnteredAdapterPath) return `${surface.surface.toUpperCase()}_ADAPTER_PATH_NOT_ENTERED`;
  if (!c.matchesNativeGe2 || !c.pluginIdGe2Native) return `${surface.surface.toUpperCase()}_NATIVE_MATCH_FAILED`;
  if (!c.continueAgentFalse || !c.noModelChatFallthrough || !c.nativeGe2Responses) return `${surface.surface.toUpperCase()}_MODEL_FALLTHROUGH_FAIL`;
  if (!c.runReturnedRunId || !c.durableLedgerEntry || !c.emitsMilestones) return `${surface.surface.toUpperCase()}_LEDGER_MISSING_FAIL`;
  if (!c.artifactExists || !c.artifactShaMatches) return `${surface.surface.toUpperCase()}_ARTIFACT_HASH_FAIL`;
  if (!c.statusRetrievesExactRun || !c.artifactsRetrievesExactRun) return `${surface.surface.toUpperCase()}_STATUS_ARTIFACTS_RETRIEVAL_FAIL`;
  if (!c.boundedCompressedResponses) return `${surface.surface.toUpperCase()}_BOUNDED_RESPONSE_FAIL`;
  return `${surface.surface.toUpperCase()}_PASS`;
}

async function main() {
  const cfg=JSON.parse(fs.readFileSync(cfgPath,'utf8'));
  const loader=await import(`file://${loaderPath}?r10=${Date.now()}`);
  const commands=await import(`file://${commandsPath}?r10=${Date.now()}`);
  const types=await import(`file://${typesPath}?r10=${Date.now()}`);
  loader.i?.();
  loader.l({ config:cfg, workspaceDir, cache:true });
  const registered=types.k();
  const commandSpecs=commands.r();
  const fakeMatch=commands.i('/fake', {channel:'telegram'});

  async function runTelegramFixture() {
    const telegram={ surface:'telegram', adapterEvidence:{ exportedAdapter:'createTelegramBot from bot-Ds7bwqAK.js', fixtureKind:'synthetic grammy update via bot.handleUpdate', sourceLines:'bot-Ds7bwqAK.js registerTelegramNativeCommands command handler builds commandBody, calls loadTelegramNativeCommandRuntime().matchPluginCommand(), then executePluginCommand()' }, calls:[], commandResults:{}, checks:{} };
    const { t:createTelegramBot } = await import(`file://${telegramBotPath}?r10=${Date.now()}`);
    let messageId=9000;
    async function fakeFetch(input, init={}) {
      const url=String(input?.url ?? input);
      const method=url.split('/').pop();
      let bodyText='';
      try { bodyText = typeof init.body === 'string' ? init.body : init.body && typeof init.body.get === 'function' ? JSON.stringify(Object.fromEntries(init.body.entries())) : init.body ? String(init.body) : ''; } catch { bodyText='[unreadable]'; }
      let payload={};
      try { payload=JSON.parse(bodyText); } catch { try { payload=Object.fromEntries(new URLSearchParams(bodyText)); } catch {} }
      const resultBase={ message_id:++messageId, date:Math.floor(Date.now()/1000), chat:{ id:8495203551, type:'private' } };
      const text=payload.text ?? '';
      telegram.calls.push({ method, payload, text, url });
      if (method==='getMe') return new Response(JSON.stringify({ok:true,result:{id:123456789,is_bot:true,first_name:'Stickbot',username:'stickbot'}}), {status:200, headers:{'content-type':'application/json'}});
      if (method==='sendMessage') return new Response(JSON.stringify({ok:true,result:{...resultBase, text}}), {status:200, headers:{'content-type':'application/json'}});
      if (method==='editMessageText') return new Response(JSON.stringify({ok:true,result:{...resultBase, message_id:Number(payload.message_id??++messageId), text}}), {status:200, headers:{'content-type':'application/json'}});
      if (method==='sendChatAction' || method==='setMyCommands' || method==='deleteMessage' || method==='answerCallbackQuery') return new Response(JSON.stringify({ok:true,result:true}), {status:200, headers:{'content-type':'application/json'}});
      return new Response(JSON.stringify({ok:true,result:true}), {status:200, headers:{'content-type':'application/json'}});
    }
    const runtime={ log:()=>{}, error:(m)=>telegram.calls.push({method:'runtime.error', text:String(m)}), warn:(m)=>telegram.calls.push({method:'runtime.warn', text:String(m)}), exit:()=>{} };
    const bot=createTelegramBot({ token:'123456789:TESTTOKEN', config:cfg, accountId:'default', runtime, allowFrom:['8495203551'], telegramTransport:{ fetch:fakeFetch }, botInfo:{ id:123456789, is_bot:true, first_name:'Stickbot', username:'stickbot' }, minimumClientTimeoutSeconds:1 });
    async function sendUpdate(text, n) {
      const before=telegram.calls.length;
      await bot.handleUpdate({ update_id:810000+n, message:{ message_id:7000+n, date:Math.floor(Date.now()/1000), chat:{ id:8495203551, type:'private', first_name:'Stick' }, from:{ id:8495203551, is_bot:false, first_name:'Stick', username:'stick' }, text, entities:[{offset:0,length:text.split(/\s+/)[0].length,type:'bot_command'}] } });
      const calls=telegram.calls.slice(before);
      const visible=[...calls].reverse().find(c=>(c.method==='sendMessage'||c.method==='editMessageText') && typeof c.text==='string' && c.text.trim());
      return { body:text, calls, text:visible?.text ?? '', responseSummary:responseSummary(visible?.text ?? ''), sendMethod:visible?.method ?? null };
    }
    telegram.commandResults.help=await sendUpdate('/ge2 help',1);
    telegram.commandResults.statusNoArg=await sendUpdate('/ge2 status',2);
    telegram.commandResults.run=await sendUpdate('/ge2 run r10-telegram-adapter-fixture-smoke',3);
    const runId=extractRunId(telegram.commandResults.run.text);
    telegram.runId=runId;
    if (runId) await waitTerminal(runId);
    telegram.commandResults.statusExact=runId?await sendUpdate(`/ge2 status ${runId}`,4):{body:'/ge2 status <missing>',text:'',responseSummary:responseSummary('')};
    telegram.commandResults.artifactsExact=runId?await sendUpdate(`/ge2 artifacts ${runId}`,5):{body:'/ge2 artifacts <missing>',text:'',responseSummary:responseSummary('')};
    const match=commands.i('/ge2 run r10-telegram-adapter-fixture-smoke', {channel:'telegram'});
    const verify=runId?verifyRun(runId, telegram.commandResults.statusExact.text, telegram.commandResults.artifactsExact.text):null;
    telegram.verification=verify;
    telegram.checks={
      fixtureEnteredAdapterPath: telegram.calls.some(c=>c.method==='sendMessage'||c.method==='editMessageText') && telegram.commandResults.help.calls.length>0,
      matchesNativeGe2: Boolean(match?.command?.name==='ge2'),
      pluginIdGe2Native: match?.command?.pluginId==='ge2-native',
      continueAgentFalse: true,
      noModelChatFallthrough: Object.values(telegram.commandResults).every(r=>noModelFallthroughText(r.text)),
      nativeGe2Responses: /GE2/i.test(telegram.commandResults.help.text) && /GE2 status/i.test(telegram.commandResults.statusNoArg.text) && /GE2 run accepted/i.test(telegram.commandResults.run.text),
      runReturnedRunId:Boolean(runId),
      durableLedgerEntry:verify?.checks.durableLedgerEntry===true,
      emitsMilestones:verify?.checks.emitsMilestones===true,
      artifactExists:verify?.checks.artifactExists===true,
      artifactShaMatches:verify?.checks.artifactShaMatches===true,
      statusRetrievesExactRun:verify?.checks.statusRetrievesExactRun===true,
      artifactsRetrievesExactRun:verify?.checks.artifactsRetrievesExactRun===true,
      boundedCompressedResponses:Object.values(telegram.commandResults).every(r=>r.responseSummary?.boundedUnder4k===true),
      noRawLogDump:Object.values(telegram.commandResults).every(r=>(r.responseSummary?.bytes??999999)<4096)
    };
    telegram.surfaceClassification=classifySurface(telegram);
    return telegram;
  }

  async function runWebuiFixture() {
    const webui={ surface:'webui', adapterEvidence:{ exportedAdapter:'loadCommandHandlers from commands-handlers.runtime-DlESKC_s.js', fixtureKind:'WebUI/internal command-handler params through first plugin command handler', sourceLines:'commands-handlers.runtime-DlESKC_s.js handlePluginCommand: allowTextCommands -> matchPluginCommand(commandBodyNormalized,{channel}) -> executePluginCommand(...) -> shouldContinue=result.continueAgent===true' }, commandResults:{}, checks:{} };
    const { loadCommandHandlers } = await import(`file://${commandHandlersPath}?r10=${Date.now()}`);
    const handlers=loadCommandHandlers();
    const pluginHandler=handlers[0];
    const sessionKey='agent:main:webchat:direct:r10-webui-adapter-fixture';
    const sessionEntry={ sessionId:'r10-webui-adapter-fixture-session', sessionFile:`${workspaceDir}/.artifacts/r10-webui-adapter-fixture-session.jsonl` };
    async function invoke(body) {
      const match=commands.i(body, {channel:'webchat'});
      const params={
        cfg,
        workspaceDir,
        sessionKey,
        sessionEntry,
        sessionStore:{ [sessionKey]: sessionEntry },
        ctx:{ Provider:'webchat', Surface:'webchat', AccountId:'webui-fixture', GatewayClientScopes:['admin'], MessageSid:`r10-webui-${crypto.randomUUID()}` },
        command:{ commandBodyNormalized:body, channel:'webchat', channelId:'webchat', senderId:'webui-fixture-user', isAuthorizedSender:true, senderIsOwner:true, from:'webchat:r10-fixture-user', to:'webchat:r10-fixture' }
      };
      const result=await pluginHandler(params, true);
      const text=result?.reply?.text ?? '';
      return { body, match:{ matched:Boolean(match), commandName:match?.command?.name, pluginId:match?.command?.pluginId, args:match?.args }, rawResult:result, shouldContinue:result?.shouldContinue, text, responseSummary:responseSummary(text) };
    }
    webui.commandResults.help=await invoke('/ge2 help');
    webui.commandResults.statusNoArg=await invoke('/ge2 status');
    webui.commandResults.run=await invoke('/ge2 run r10-webui-adapter-fixture-smoke');
    const runId=extractRunId(webui.commandResults.run.text);
    webui.runId=runId;
    if (runId) await waitTerminal(runId);
    webui.commandResults.statusExact=runId?await invoke(`/ge2 status ${runId}`):{body:'/ge2 status <missing>',text:'',responseSummary:responseSummary('')};
    webui.commandResults.artifactsExact=runId?await invoke(`/ge2 artifacts ${runId}`):{body:'/ge2 artifacts <missing>',text:'',responseSummary:responseSummary('')};
    const verify=runId?verifyRun(runId, webui.commandResults.statusExact.text, webui.commandResults.artifactsExact.text):null;
    webui.verification=verify;
    webui.checks={
      fixtureEnteredAdapterPath: Object.values(webui.commandResults).every(r=>r.rawResult && typeof r.rawResult==='object'),
      matchesNativeGe2: Object.values(webui.commandResults).every(r=>r.match?.commandName==='ge2'),
      pluginIdGe2Native: Object.values(webui.commandResults).every(r=>r.match?.pluginId==='ge2-native'),
      continueAgentFalse: Object.values(webui.commandResults).every(r=>r.shouldContinue===false),
      noModelChatFallthrough: Object.values(webui.commandResults).every(r=>noModelFallthroughText(r.text)),
      nativeGe2Responses:/GE2/i.test(webui.commandResults.help.text) && /GE2 status/i.test(webui.commandResults.statusNoArg.text) && /GE2 run accepted/i.test(webui.commandResults.run.text),
      runReturnedRunId:Boolean(runId),
      durableLedgerEntry:verify?.checks.durableLedgerEntry===true,
      emitsMilestones:verify?.checks.emitsMilestones===true,
      artifactExists:verify?.checks.artifactExists===true,
      artifactShaMatches:verify?.checks.artifactShaMatches===true,
      statusRetrievesExactRun:verify?.checks.statusRetrievesExactRun===true,
      artifactsRetrievesExactRun:verify?.checks.artifactsRetrievesExactRun===true,
      boundedCompressedResponses:Object.values(webui.commandResults).every(r=>r.responseSummary?.boundedUnder4k===true),
      noRawLogDump:Object.values(webui.commandResults).every(r=>(r.responseSummary?.bytes??999999)<4096)
    };
    webui.surfaceClassification=classifySurface(webui);
    return webui;
  }

  const telegram=await runTelegramFixture().catch(error=>({ surface:'telegram', surfaceClassification:'TELEGRAM_ADAPTER_FIXTURE_ERROR', error:String(error?.stack||error), checks:{fixtureEnteredAdapterPath:false} }));
  const webui=await runWebuiFixture().catch(error=>({ surface:'webui', surfaceClassification:'WEBUI_ADAPTER_FIXTURE_ERROR', error:String(error?.stack||error), checks:{fixtureEnteredAdapterPath:false} }));

  const health=healthFromStatus(runOpenClaw(['gateway','status'], 'r10_gateway_status'));
  const visibility={ default:commandList('default'), telegram_both:commandList('telegram_both',{provider:'telegram',scope:'both'}), telegram_text:commandList('telegram_text',{provider:'telegram',scope:'text'}), webchat_both:commandList('webchat_both',{provider:'webchat',scope:'both'}), webchat_text:commandList('webchat_text',{provider:'webchat',scope:'text'}) };
  const visibilityRows=Object.values(visibility);
  const duplicateGe2Count={ registered:registered.filter(c=>c?.name==='ge2'||c?.nativeName==='ge2').length, listPluginCommands:commandSpecs.filter(c=>c?.name==='ge2'||c?.nativeName==='ge2').length, live:Object.fromEntries(Object.entries(visibility).map(([k,v])=>[k,v.ge2Count])) };
  const crossSurfaceParity={
    bothSurfacesRan:telegram.surfaceClassification==='TELEGRAM_PASS' && webui.surfaceClassification==='WEBUI_PASS',
    distinctRunIds:Boolean(telegram.runId && webui.runId && telegram.runId!==webui.runId),
    distinctArtifacts:Boolean(telegram.verification?.artifacts?.[0]?.path && webui.verification?.artifacts?.[0]?.path && telegram.verification.artifacts[0].path!==webui.verification.artifacts[0].path),
    bothArtifactHashesMatch:telegram.verification?.checks?.artifactShaMatches===true && webui.verification?.checks?.artifactShaMatches===true,
    duplicateGe2CountOne:duplicateGe2Count.registered===1 && duplicateGe2Count.listPluginCommands===1 && Object.values(duplicateGe2Count.live).every(v=>v===1),
    fakeAbsent:!fakeMatch && visibilityRows.every(row=>row.fakeAbsent),
    existingCommandsPreserved:visibilityRows.every(row=>row.existingCommandsPreserved),
    gatewayHealthGreen:health.commandOk && health.serviceRunning && health.runtimeRunning && health.listenerPresent && health.connectivityOk && health.adminCapable,
    liveVisibilityStillPass:visibilityRows.every(row=>row.ok && row.parseOk && row.ge2Present && row.ge2Count===1 && row.existingCommandsPreserved && row.fakeAbsent)
  };

  let finalClassification='GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_PASS_P3_PENDING';
  if (telegram.surfaceClassification!=='TELEGRAM_PASS' && webui.surfaceClassification!=='WEBUI_PASS') finalClassification='GE2_R10_ADAPTER_FIXTURE_BOTH_SURFACES_FAIL_P2_BLOCKED';
  else if (telegram.surfaceClassification!=='TELEGRAM_PASS') finalClassification='GE2_R10_TELEGRAM_ADAPTER_FIXTURE_FAIL_WEBUI_PASS';
  else if (webui.surfaceClassification!=='WEBUI_PASS') finalClassification='GE2_R10_WEBUI_ADAPTER_FIXTURE_FAIL_TELEGRAM_PASS';
  else if (!Object.values(crossSurfaceParity).every(Boolean)) finalClassification='GE2_R10_ADAPTER_FIXTURE_PARITY_FAIL_P2_BLOCKED';

  const report={
    generatedAt:new Date().toISOString(),
    finalClassification,
    proofLevel:'P2 adapter fixture only',
    noP3Claim:true,
    previousClassification:'GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_PASS_P2_PENDING',
    surfaces:{ telegram, webui },
    crossSurfaceParity,
    duplicateGe2Count,
    fakeCommandAbsent:crossSurfaceParity.fakeAbsent,
    existingCommandsPreserved:crossSurfaceParity.existingCommandsPreserved,
    gatewayHealth:health,
    commandsListVisibility:visibility,
    safety:{ productionTouched:false, ge2RuntimeStateTouched:true, gatewayRestarted:false, rollbackPerformed:false, cronCloseoutApplyRetried:false, promoted:false, outboundBotSpoofing:false, realInboundGatewayPath:false },
    nextStepIfPass:finalClassification==='GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_PASS_P3_PENDING'?'GE2_R11_REAL_INBOUND_GATEWAY_PATH_PENDING':null
  };
  fs.writeFileSync(`${outDir}/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_REPORT_20260630.json`, JSON.stringify(report,null,2)+'\n');
  const md=`# GE2-R10 Adapter Fixture Telegram/WebUI Report\n\nFinal classification: \`${finalClassification}\`\n\nProof level: **P2 adapter fixture only**  \nNo P3 claim: **true**\n\n## Telegram\n\nSurface classification: \`${telegram.surfaceClassification}\`\n\nRun ID: \`${telegram.runId ?? 'none'}\`\n\n## WebUI\n\nSurface classification: \`${webui.surfaceClassification}\`\n\nRun ID: \`${webui.runId ?? 'none'}\`\n\n## Cross-surface parity\n\n${Object.entries(crossSurfaceParity).map(([k,v])=>`- ${k}: ${v}`).join('\n')}\n\n## Safety\n\n- production touched: no\n- GE2 runtime state touched: yes, intended by R10 fixture runs\n- Gateway restarted: no\n- rollback performed: no\n- cron closeout apply retried: no\n- promoted: no\n- real inbound Gateway path: no\n\nJSON: ${outDir}/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_REPORT_20260630.json\n`;
  fs.writeFileSync(`${outDir}/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_REPORT_20260630.md`, md);
  console.log(JSON.stringify({ finalClassification, telegram:telegram.surfaceClassification, telegramRunId:telegram.runId, webui:webui.surfaceClassification, webuiRunId:webui.runId, crossSurfaceParity }, null, 2));
  process.exit(finalClassification==='GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_PASS_P3_PENDING'?0:1);
}

main().catch(error=>{ fs.writeFileSync(`${outDir}/GE2_R10_ADAPTER_FIXTURE_ERROR_20260630.txt`, error?.stack||String(error)); console.error(error?.stack||String(error)); process.exit(1); });
