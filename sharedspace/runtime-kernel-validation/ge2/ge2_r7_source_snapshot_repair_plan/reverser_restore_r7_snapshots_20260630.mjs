#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const restores = [
  {
    label: 'loader',
    source: '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js',
    snapshot: '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/loader-Bfm_uDYG.js',
    sha256: 'ff2d89b04d1d5f7fb727f586a78fe92e0b52ffbe43a484551475cf140b53feb0'
  },
  {
    label: 'commands',
    source: '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js',
    snapshot: '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/commands-D2qp4St4.js',
    sha256: '660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb'
  },
  {
    label: 'types',
    source: '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js',
    snapshot: '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/types-CdFhLeaX.js',
    sha256: '864d569218baa6a23bfaa48547947e503ea2343929e5f78171af4e031dad202f'
  },
  {
    label: 'serverMethods',
    source: '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js',
    snapshot: '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/server-methods-Dw6hzI_j.js',
    sha256: '638aa2dbf4cc7a9758b0d3f5679ec745e329e0f8f164408731a2107357993986'
  }
];

const selected = new Set(process.argv.slice(2));
const plan = selected.size > 0 ? restores.filter((entry) => selected.has(entry.label) || selected.has(path.basename(entry.source))) : restores;
if (plan.length === 0) {
  console.error('No matching restore targets. Pass one of: ' + restores.map((entry) => entry.label).join(', '));
  process.exit(2);
}
for (const entry of plan) {
  if (!fs.existsSync(entry.snapshot)) {
    console.error(`Snapshot missing for ${entry.label}: ${entry.snapshot}`);
    process.exit(3);
  }
}
for (const entry of plan) {
  const bytes = fs.readFileSync(entry.snapshot);
  const tmp = `${entry.source}.restore-${Date.now()}-${process.pid}.tmp`;
  fs.writeFileSync(tmp, bytes, { mode: 0o644 });
  fs.renameSync(tmp, entry.source);
  console.log(`restored ${entry.label}: ${entry.source}`);
}
