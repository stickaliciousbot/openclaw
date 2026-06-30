import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const dir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair';
const required = ['status.json','summary.json','investigation_report.md','registrar_path_report.json','command_list_path_report.json','registry_identity_report.json','registration_loss_point_report.json','implementation_diff_summary.md','modified_files_manifest.json','registrar_direct_test_report.json','live_commands_list_test_report.json','restart_durability_test_report.json','permission_visibility_test_report.json','negative_command_visibility_test_report.json','unrelated_command_diff_report.json','mutation_scope_report.json','rollback_readiness.json','GE2_R1_COMMAND_REGISTRY_VISIBILITY_REPAIR.md'];
const report = required.map((name) => {
  const p = path.join(dir, name);
  const b = fs.existsSync(p) ? fs.readFileSync(p) : null;
  return { name, exists: Boolean(b), bytes: b ? b.length : 0, sha256: b ? crypto.createHash('sha256').update(b).digest('hex') : null };
});
const manifestPath = path.join(dir, 'final_file_manifest_20260630.json');
fs.writeFileSync(manifestPath, JSON.stringify({ generatedAt: new Date().toISOString(), dir, files: report }, null, 2) + '\n');
console.log(JSON.stringify({ allExist: report.every((r) => r.exists), count: report.length, missing: report.filter((r) => !r.exists).map((r) => r.name), manifest: manifestPath }, null, 2));
