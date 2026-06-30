import fs from 'node:fs';
import crypto from 'node:crypto';
const manifestPath = "/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/install_manifest_20260630T0715Z.json";
function sha256(bytes){return crypto.createHash('sha256').update(bytes).digest('hex')}
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
const results=[];
for (const change of manifest.changes){
  const backup=fs.readFileSync(change.backup);
  fs.writeFileSync(change.target, backup);
  const restored=fs.readFileSync(change.target);
  results.push({target:change.target, restored_sha256:sha256(restored), expected_sha256:change.before_sha256, ok:sha256(restored)===change.before_sha256});
}
console.log(JSON.stringify({manifest_id: manifest.manifest_id, ok: results.every(r=>r.ok), results}, null, 2));
