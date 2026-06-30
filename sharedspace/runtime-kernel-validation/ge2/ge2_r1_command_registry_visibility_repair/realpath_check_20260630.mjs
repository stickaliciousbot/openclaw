import fs from 'node:fs';
for (const p of ['/home/stickai/.npm-global/lib/node_modules/openclaw','/home/stickai/.npm-global/lib/node_modules/openclaw/dist','/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js']) {
  console.log(`${p} -> ${fs.realpathSync(p)}`);
}
