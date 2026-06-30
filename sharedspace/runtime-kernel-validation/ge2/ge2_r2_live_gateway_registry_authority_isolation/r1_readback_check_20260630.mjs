import fs from 'node:fs';
import path from 'node:path';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r2_live_gateway_registry_authority_isolation';
fs.mkdirSync(dir,{recursive:true});
const src='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair/status.json';
const dst=path.join(dir,'ge2_r1_readback.json');
const s=JSON.parse(fs.readFileSync(src,'utf8'));
fs.writeFileSync(dst, JSON.stringify({generatedAt:new Date().toISOString(), source:src, r1:s, verified:{classification:s.classification==='GE2_R1_COMMAND_REGISTRY_VISIBILITY_REPAIR_BLOCKED', ge2Present:s.liveCommandsList?.ge2Present===true, ge2Absent:s.liveCommandsList?.ge2Present===false, pluginGe2:s.pluginRegistry?.ge2PluginDiscovered===true}}, null, 2)+'\n');
console.log(JSON.stringify({classification:s.classification, ge2Present:s.liveCommandsList?.ge2Present, pluginGe2:s.pluginRegistry?.ge2PluginDiscovered, dst},null,2));
