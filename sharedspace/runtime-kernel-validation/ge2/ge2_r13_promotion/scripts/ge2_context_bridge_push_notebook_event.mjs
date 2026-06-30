import fs from 'node:fs';
const path='sharedspace/context-bridge/events.jsonl';
const eventId='evt-20260630T110200Z-ge2-r13-notebook-memory-push-handoff';
const lines=fs.existsSync(path)?fs.readFileSync(path,'utf8').split(/\n/).filter(Boolean):[];
let maxContext=0; let exists=false; let parsed=0;
for (const line of lines){ const e=JSON.parse(line); parsed++; if(Number.isFinite(e.context_version)) maxContext=Math.max(maxContext,e.context_version); if(e.event_id===eventId) exists=true; }
if(!exists){
 const event={
  agent_id:'main', channel:'operator', context_version:maxContext+1,
  dedupe_key:'dk-ge2-r13-notebook-memory-push-handoff-20260630T1102Z',
  entity_id:'ge2-native-command-surface', event_id:eventId,
  event_type:'ge2_r13_notebook_memory_push_handoff', memory_id:'memory/2026-06-30-ge2-r13-push-blocked-handoff-preserved.md',
  payload:{
   classification:'GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED',
   notebook:'sharedspace/runtime-kernel-validation/ge2/GE2_IMPLEMENTATION_DIAGNOSE_AND_REPAIR_NOTEBOOK_20260630.md',
   hardstopVerification:'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED_20260630.md',
   r13Bundle:'sharedspace/disaster-recovery/ge2-r13-promotion-20260630/ge2-r13-promotion-20260630.tar.gz',
   r13BundleSha256:'b7509076f20dc5dc906a7343c92bb8d0bb5dee1d894242abbe2460b19c7a0f8c',
   issueFixLearnings:['hook success is not live command proof','commands.list visibility precedes live smoke','P1/P2/P3 are distinct proof levels','loader registry lifecycle is durable command authority','selective staging required from dirty workspace'],
   pushRequest:'stage and push GE2 source/hooks/docs/evidence/memory only; exclude unrelated dirty files and secrets'
  },
  reducer_version:1,
  source_refs:['sharedspace/runtime-kernel-validation/ge2/GE2_IMPLEMENTATION_DIAGNOSE_AND_REPAIR_NOTEBOOK_20260630.md','memory/lessons-learned-ge2-native-command-surface-promotion-2026-06-30.md','MEMORY.md','memory/2026-06-30.md'],
  status:'PASS',
  summary:'GE2 R13 final notebook, memories, lessons, and push handoff prepared after hard-stop recheck.',
  ts:'2026-06-30T11:02:00Z'
 };
 fs.appendFileSync(path,JSON.stringify(event)+'\n');
 maxContext++;
}
let reparsed=0; for(const [i,line] of fs.readFileSync(path,'utf8').split(/\n/).entries()){ if(!line.trim()) continue; try{JSON.parse(line); reparsed++;}catch(e){throw new Error(`parse failed line ${i+1}: ${e.message}`);} }
console.log(JSON.stringify({ok:true,eventId,contextVersion:maxContext,parsedEvents:reparsed,already:exists},null,2));
