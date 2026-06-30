import fs from 'node:fs';
const dir='/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
for (const f of fs.readdirSync(dir).filter(f=>f.endsWith('.js'))) {
  const s=fs.readFileSync(`${dir}/${f}`,'utf8');
  const hits=['matchPluginCommand','executePluginCommand','getPluginCommandSpecs'].filter(t=>s.includes(t));
  if (hits.length) console.log(`${f}\t${hits.join(',')}`);
}
