import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import crypto from 'node:crypto';
const outDir='sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke';
fs.mkdirSync(outDir,{recursive:true});
function call(method, params={}){
  const s=execFileSync('openclaw',['gateway','call',method,'--json','--params',JSON.stringify(params)],{encoding:'utf8',maxBuffer:10*1024*1024});
  return JSON.parse(s);
}
function commandSummary(provider){
  const data=call('commands.list',{provider,scope:'text'});
  const names=data.commands.map(c=>c.name);
  const ge2=data.commands.filter(c=>c.name==='ge2'||(c.textAliases||[]).includes('/ge2'));
  const fake=data.commands.filter(c=>c.name==='ge2-fake'||(c.textAliases||[]).includes('/ge2-fake'));
  const preserve=['pair','dreaming','phone','voice'].map(name=>({name,present:names.includes(name)||data.commands.some(c=>(c.textAliases||[]).includes('/'+name))}));
  return {provider,count:data.commands.length,ge2Count:ge2.length,ge2:ge2.map(c=>({name:c.name,pluginId:c.pluginId,source:c.source,scope:c.scope,textAliases:c.textAliases,acceptsArgs:c.acceptsArgs,category:c.category,description:c.description})),fakeCount:fake.length,preserve};
}
const status=execFileSync('openclaw',['gateway','status'],{encoding:'utf8',maxBuffer:1024*1024});
const report={
  generatedAt:new Date().toISOString(),
  gatewayStatusText:status,
  commands:{telegram:commandSummary('telegram'),webchat:commandSummary('webchat')},
  routeFindings:{
    telegram:{
      installedDist:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-Ds7bwqAK.js',
      nativeRuntime:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-native-commands.runtime-OmS7iYqz.js',
      ingress:'Telegram Bot API update -> createTelegramBot/registerTelegramNativeCommands -> bot.handleUpdate in running Gateway',
      recognizer:'matchPluginCommand(commandBody)',
      executor:'executePluginCommand(...)',
      responseDelivery:'Telegram reply/send path via deliverReplies/recordSentMessage',
      sentLedger:'/home/stickai/.openclaw/agents/main/sessions/sessions.json.telegram-sent-messages.json',
      directSessionKey:'agent:main:telegram:direct:8495203551',
      p3Availability:'requires real operator-sent Telegram inbound /ge2 message; assistant must not spoof inbound or send outbound bot command as substitute'
    },
    webuiGateway:{
      installedDist:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/chat-BUK7LXQw.js',
      serverChat:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-chat-BK0Ftt9y.js',
      commandHandlers:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-handlers.runtime-DlESKC_s.js',
      ingress:'Gateway RPC chat.send -> dispatchInboundMessage/get-reply command routing in running Gateway',
      requiredParams:['sessionKey','message','idempotencyKey'],
      recognizer:'commands-handlers.runtime handlePluginCommand / matchPluginCommand(commandBodyNormalized)',
      executor:'executePluginCommand(...)',
      responseDelivery:'chat transcript + nodeSendToSession live chat event',
      transcriptPath:'session transcript under /home/stickai/.openclaw/agents/main/sessions/',
      p3Availability:'rendered browser WebUI unavailable on host; raw chat.send live RPC was accepted but /ge2 help returned authorization gate, not GE2 help'
    }
  },
  liveProbeResults:{
    browserStart:'failed: No supported browser found (Chrome/Brave/Edge/Chromium)',
    webuiGatewayChatSend:{
      sessionKey:'agent:main:main',
      commands:['/ge2 help'],
      result:'accepted by chat.send, transcript response was authorization gate: ⚠️ This command requires authorization.',
      modelFallthrough:'not observed; response provider/model gateway-injected with zero token usage',
      ge2NativeExecution:'not proven because auth gate blocked before GE2 help response'
    },
    telegramSessionInternalChatSend:{
      sessionKey:'agent:main:telegram:direct:8495203551',
      command:'/ge2 help',
      result:'not counted as P3; internal chat.send against current direct session is not real external Telegram inbound and polluted active transcript; stopped route'
    }
  },
  productionBoundary:{productionPatch:false,gatewayRestarted:false,rollbackPerformed:false,cronApply:false,promotion:false},
  classification:'GE2_R11_REAL_INBOUND_BLOCKED_P2_PASS_ONLY'
};
const jsonPath=`${outDir}/GE2_R11_PHASE1_REAL_INBOUND_ENTRYPOINTS_AND_BLOCKERS_20260630.json`;
const mdPath=`${outDir}/GE2_R11_PHASE1_REAL_INBOUND_ENTRYPOINTS_AND_BLOCKERS_20260630.md`;
fs.writeFileSync(jsonPath,JSON.stringify(report,null,2));
const sha=crypto.createHash('sha256').update(fs.readFileSync(jsonPath)).digest('hex');
fs.writeFileSync(mdPath,`# GE2 R11 Phase 1 / safe live-probe report\n\nFinal classification: \`${report.classification}\`\n\nProof level: P3 attempted for safe WebUI/Gateway live RPC only; P3 **not passed**. P2 remains valid.\n\n## Routes identified\n\n### Telegram real inbound\n- Ingress: ${report.routeFindings.telegram.ingress}\n- Recognizer: ${report.routeFindings.telegram.recognizer}\n- Executor: ${report.routeFindings.telegram.executor}\n- Response delivery: ${report.routeFindings.telegram.responseDelivery}\n- Direct session key: \`${report.routeFindings.telegram.directSessionKey}\`\n- Sent ledger: \`${report.routeFindings.telegram.sentLedger}\`\n- P3 blocker: ${report.routeFindings.telegram.p3Availability}\n\n### WebUI/Gateway live inbound\n- Ingress: ${report.routeFindings.webuiGateway.ingress}\n- Required chat.send params: ${report.routeFindings.webuiGateway.requiredParams.map(x=>'`'+x+'`').join(', ')}\n- Recognizer: ${report.routeFindings.webuiGateway.recognizer}\n- Executor: ${report.routeFindings.webuiGateway.executor}\n- Response delivery: ${report.routeFindings.webuiGateway.responseDelivery}\n- P3 blocker: ${report.routeFindings.webuiGateway.p3Availability}\n\n## Command visibility\n\n- Telegram /ge2 count: ${report.commands.telegram.ge2Count}\n- Webchat /ge2 count: ${report.commands.webchat.ge2Count}\n- Telegram fake count: ${report.commands.telegram.fakeCount}\n- Webchat fake count: ${report.commands.webchat.fakeCount}\n- Existing command preservation (telegram): ${report.commands.telegram.preserve.map(x=>`${x.name}=${x.present?'present':'missing'}`).join(', ')}\n- Existing command preservation (webchat): ${report.commands.webchat.preserve.map(x=>`${x.name}=${x.present?'present':'missing'}`).join(', ')}\n\n## Safe live probes\n\n- Browser WebUI: ${report.liveProbeResults.browserStart}\n- chat.send /ge2 help: ${report.liveProbeResults.webuiGatewayChatSend.result}\n- Model/chat fallthrough: ${report.liveProbeResults.webuiGatewayChatSend.modelFallthrough}\n- Native GE2 execution: ${report.liveProbeResults.webuiGatewayChatSend.ge2NativeExecution}\n\n## Boundary\n\n- Production patch: no\n- Gateway restart: no\n- Rollback: no\n- Cron apply: no\n- Promotion: no\n\n## SHA\n\nJSON report SHA256: \`${sha}\`\n`);
console.log(JSON.stringify({jsonPath,mdPath,sha,classification:report.classification},null,2));
