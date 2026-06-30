#!/usr/bin/env node
import fs from 'node:fs';
const target = "/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js";
const snapshot = "/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/install_snapshots_20260630T0812Z/loader-Bfm_uDYG.js";
const tmp = target + '.restore-' + Date.now() + '-' + process.pid + '.tmp';
fs.copyFileSync(snapshot, tmp);
fs.renameSync(tmp, target);
console.log('restored ' + target + ' from ' + snapshot);
