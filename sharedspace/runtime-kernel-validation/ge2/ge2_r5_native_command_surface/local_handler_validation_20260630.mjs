import fs from 'node:fs';
const target='/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js';
const mod=await import('file://' + target + '?handler=' + Date.now());
async function call(body){
  const match=mod.i(body,{channel:'telegram'});
  if(!match) return {body, matched:false};
  const result=await match.command.handler({
    args: match.args,
    commandBody: body,
    channel:'telegram',
    senderId:'telegram:8495203551',
    isAuthorizedSender:true,
    sessionKey:'agent:main:telegram:direct:8495203551',
    sessionId:'ge2-r5-local-validation',
    accountId:'default'
  });
  return {body, matched:true, result};
}
const help=await call('/ge2 help');
const statusBefore=await call('/ge2 status');
const run=await call('/ge2 run r5-local-validation');
const runId=/run_id: (ge2-[^\n]+)/.exec(run.result?.text||'')?.[1] ?? null;
await new Promise(r=>setTimeout(r,800));
const statusAfter=runId ? await call('/ge2 status '+runId) : null;
const artifacts=runId ? await call('/ge2 artifacts '+runId) : null;
const summary={help,statusBefore,run,runId,statusAfter,artifacts,stateIndexExists:fs.existsSync('/home/stickai/.openclaw/workspace/state/ge2-native/runs.index.json')};
console.log(JSON.stringify(summary,null,2));
