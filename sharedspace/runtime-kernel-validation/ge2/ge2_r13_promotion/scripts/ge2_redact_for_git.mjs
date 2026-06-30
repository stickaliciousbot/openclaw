import fs from 'node:fs';
const redactions=[
 ['sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/r6_refined_registry_lifecycle_trace_20260630.json','sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/sanitized/r6_refined_registry_lifecycle_trace_20260630.REDACTED.json'],
 ['sharedspace/runtime-kernel-validation/ge2/ge2_r4_authoritative_rpc_command_list_builder_bridge/preimage__home__stickai__.npm-global__lib__node_modules__openclaw__dist__server-methods-Dw6hzI_j.js','sharedspace/runtime-kernel-validation/ge2/ge2_r4_authoritative_rpc_command_list_builder_bridge/sanitized/preimage_server-methods-Dw6hzI_j.REDACTED.js'],
 ['sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/install_snapshots_20260630T0812Z/loader-Bfm_uDYG.js','sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/sanitized/install_snapshot_loader-Bfm_uDYG.REDACTED.js']
];
for(const [src,dst] of redactions){
 if(!fs.existsSync(src)) continue;
 let txt=fs.readFileSync(src,'utf8');
 txt=txt.replace(/sk-[A-Za-z0-9_-]{20,}/g,'sk-[REDACTED_SECRET_LIKE_VALUE]');
 txt=txt.replace(/gh[pousr]_[A-Za-z0-9_]{20,}/g,'gh_[REDACTED_SECRET_LIKE_VALUE]');
 fs.mkdirSync(dst.split('/').slice(0,-1).join('/'),{recursive:true});
 fs.writeFileSync(dst,txt);
}
console.log(JSON.stringify({redacted:redactions.map(r=>r[1]).filter(fs.existsSync)},null,2));
