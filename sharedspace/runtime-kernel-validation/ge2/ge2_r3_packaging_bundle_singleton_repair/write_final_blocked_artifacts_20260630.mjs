import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r3_packaging_bundle_singleton_repair';
fs.mkdirSync(dir,{recursive:true});
function sha(file){return fs.existsSync(file)?crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'):null}
function readJson(file){try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch(e){return {parseError:String(e?.message||e)}}}
function run(args, timeout=120000){try{return {ok:true, status:0, stdout:execFileSync('openclaw',args,{cwd:'/home/stickai/.openclaw/workspace',encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout})}}catch(e){return{ok:false,status:e.status??null,stdout:e.stdout?.toString?.()??'',stderr:e.stderr?.toString?.()??String(e.message||e)}}}
const status=run(['gateway','status'],120000);
fs.writeFileSync(path.join(dir,'gateway_status_final.txt'),status.stdout||status.stderr||'');
const plugins=run(['plugins','list','--json'],120000);
fs.writeFileSync(path.join(dir,'plugins_list_final.json'),plugins.stdout||plugins.stderr||'');
const commandsSummary=readJson(path.join(dir,'commands_list_after_restart_summary.json'));
const doctorLogPath=path.join(dir,'doctor_noninteractive_timeout_excerpt.txt');
fs.writeFileSync(doctorLogPath, `openclaw doctor --non-interactive was started during GE2-R3 final verification and was SIGKILLed by the 240s command timeout after warning output. No doctor fix command was run. See turn transcript/process log for full console excerpt.\n`);
const pluginParsed = (()=>{try{return JSON.parse(plugins.stdout)}catch{return null}})();
const pluginList = Array.isArray(pluginParsed) ? pluginParsed : (pluginParsed?.plugins||[]);
const ge2Plugin = pluginList.find(p=>p.id==='ge2-command') || null;
const surfaceResults = Array.isArray(commandsSummary.results)?commandsSummary.results:[];
const allGe2Present = surfaceResults.length>0 && surfaceResults.every(r=>r.ge2Present===true);
const allFakeAbsent = surfaceResults.length>0 && surfaceResults.every(r=>r.fakePresent===false);
const allCorePluginNamesPreserved = surfaceResults.length>0 && surfaceResults.every(r=>['pair','dreaming','phone','voice'].every(n=>(r.pluginNames||[]).includes(n)));
const ge2InPluginNames = surfaceResults.every(r=>(r.pluginNames||[]).includes('ge2'));
const statusPid = /pid (\d+)/.exec(status.stdout||'')?.[1] ?? null;
const files = {
  types:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js',
  commands:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js',
  hook:'/home/stickai/.openclaw/workspace/hooks/ge2-register/handler.js',
  commandsParser:path.join(dir,'parse_live_commands_after_restart_20260630.mjs'),
  preRepairSnapshot:path.join(dir,'pre_repair_snapshot.json'),
  commandsBridgeSnapshot:path.join(dir,'commands_bridge_target_snapshot.json'),
  localFallbackValidation:path.join(dir,'local_fallback_bridge_validation.json'),
  restartHold:path.join(dir,'restart_hold_20260630T0629Z.json')
};
const final = {
  generatedAt:new Date().toISOString(),
  classification:'GE2_R3_BLOCKED_LIVE_COMMANDS_LIST_OMITS_GE2_AFTER_SINGLETON_AND_EFFECTIVE_REGISTRY_BRIDGE',
  pass:false,
  passCriterion:'live Gateway RPC commands.list exposes /ge2',
  gateway:{previousPidBeforeSecondRestart:'295400', finalPid:statusPid, healthOk:/Connectivity probe: ok/.test(status.stdout||''), adminCapable:/Capability: admin-capable/.test(status.stdout||''), statusExit:status.status},
  commandSurfaces:{summaryFile:path.join(dir,'commands_list_after_restart_summary.json'), surfaceResults, allGe2Present, allFakeAbsent, allCorePluginNamesPreserved, ge2InPluginNames},
  pluginManager:{ge2Loaded:ge2Plugin?.status==='loaded', ge2Commands:ge2Plugin?.commands||[], source:ge2Plugin?.source||null, contradiction:'plugin manager reports ge2-command loaded with commands:[ge2], but live commands.list surfaces omit /ge2'},
  executionSurface:{attempted:false, reason:'Not attempted as success evidence because R3 public visibility hard gate failed; invoking /ge2 through a user-facing channel would risk external side effects and could not override commands.list omission.'},
  negativeChecks:{fakeAbsent:allFakeAbsent, unrelatedPluginCommandsPreserved:allCorePluginNamesPreserved, unrelatedPluginNamesExpected:['pair','dreaming','phone','voice']},
  doctor:{command:'openclaw doctor --non-interactive', result:'timeout_SIGKILL_after_warnings_no_fix_applied', timeoutSeconds:240, evidenceFile:doctorLogPath},
  files:Object.fromEntries(Object.entries(files).map(([k,v])=>[k,{path:v, exists:fs.existsSync(v), sha256:sha(v)}])),
  nextRecommendedScope:'GE2-R3 remains blocked. Next diagnostic should prove why getActivePluginRegistry().commands is not visible to commands-D2qp4St4.js in live RPC, or move the narrow bridge to the authoritative server-methods command-list construction after extracting active registry entries there. Do not start GE2-R4 automatically.',
  noR4Started:true,
  cronCloseoutRetry:false
};
fs.writeFileSync(path.join(dir,'final_blocked_summary.json'),JSON.stringify(final,null,2)+'\n');
const md = `# GE2-R3 Final Classification\n\nClassification: \`${final.classification}\`\n\nPASS: **NO**\n\nHard gate: live Gateway RPC \`commands.list\` must expose \`/ge2\`. It did not.\n\n## Evidence\n\n- Gateway final PID: \`${statusPid}\`; health/connectivity/admin: ${final.gateway.healthOk && final.gateway.adminCapable ? 'PASS' : 'FAIL'}\n- Live command surfaces: ${surfaceResults.map(r=>`${r.name}: count=${r.count}, ge2Present=${r.ge2Present}, fakePresent=${r.fakePresent}, pluginNames=${(r.pluginNames||[]).join(',')}`).join('; ')}\n- Plugin manager: ge2-command status=\`${ge2Plugin?.status||'missing'}\`, commands=${JSON.stringify(ge2Plugin?.commands||[])}\n- Negative checks: fake absent=${allFakeAbsent}; pair/dreaming/phone/voice preserved=${allCorePluginNamesPreserved}\n- Command execution surface: not attempted as success evidence because public visibility gate failed.\n- Doctor: \`openclaw doctor --non-interactive\` timed out/SIGKILL after warning output; no fix was run.\n\n## Conclusion\n\nThe singleton bridge and effective-registry bridge did not satisfy R3. Live RPC still omits \`/ge2\` while plugin manager and hook-side registration report it. R3 remains blocked; R4 was not started.\n`;
fs.writeFileSync(path.join(dir,'GE2_R3_FINAL_BLOCKED.md'),md);
const manifest=Object.entries(files).map(([name,meta])=>({name,path:meta.path||meta, exists:fs.existsSync(meta.path||meta), sha256:sha(meta.path||meta)}));
manifest.push({name:'final_blocked_summary',path:path.join(dir,'final_blocked_summary.json'),exists:true,sha256:sha(path.join(dir,'final_blocked_summary.json'))});
manifest.push({name:'final_markdown',path:path.join(dir,'GE2_R3_FINAL_BLOCKED.md'),exists:true,sha256:sha(path.join(dir,'GE2_R3_FINAL_BLOCKED.md'))});
manifest.push({name:'gateway_status_final',path:path.join(dir,'gateway_status_final.txt'),exists:true,sha256:sha(path.join(dir,'gateway_status_final.txt'))});
manifest.push({name:'plugins_list_final',path:path.join(dir,'plugins_list_final.json'),exists:true,sha256:sha(path.join(dir,'plugins_list_final.json'))});
fs.writeFileSync(path.join(dir,'final_file_manifest_20260630.json'),JSON.stringify({generatedAt:new Date().toISOString(), allExist:manifest.every(x=>x.exists), count:manifest.length, manifest},null,2)+'\n');
console.log(JSON.stringify({classification:final.classification, pass:false, finalPid:statusPid, healthOk:final.gateway.healthOk, adminCapable:final.gateway.adminCapable, surfaceResults:surfaceResults.map(r=>({name:r.name,count:r.count,ge2Present:r.ge2Present,fakePresent:r.fakePresent,pluginNames:r.pluginNames})), ge2Plugin:{status:ge2Plugin?.status, commands:ge2Plugin?.commands, source:ge2Plugin?.source}, manifestAllExist:manifest.every(x=>x.exists)},null,2));
