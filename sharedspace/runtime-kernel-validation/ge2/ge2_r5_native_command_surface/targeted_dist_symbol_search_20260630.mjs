import fs from 'node:fs';
import path from 'node:path';
const root='/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const needles=[
  'resolveTextCommand',
  'maybeResolveTextAlias',
  'normalizeCommandBody',
  'findCommandByNativeName',
  'command.key === "status"',
  "command.key === 'status'",
  'case "status"',
  "case 'status'",
  'switch (command.key)',
  'switch(command.key)',
  'commandBody',
  'matchPluginCommand',
  'executePluginCommand'
];
const files=fs.readdirSync(root).filter(f=>f.endsWith('.js')).sort();
const hits=[];
for(const f of files){
  const p=path.join(root,f);
  const s=fs.readFileSync(p,'utf8');
  for(const n of needles){
    let idx=s.indexOf(n);
    while(idx!==-1){
      const line=s.slice(0,idx).split('\n').length;
      hits.push({file:f,line,needle:n,excerpt:s.slice(Math.max(0,idx-120),Math.min(s.length,idx+220)).replace(/\s+/g,' ').trim()});
      idx=s.indexOf(n,idx+n.length);
      if(hits.length>500) break;
    }
  }
}
console.log(JSON.stringify({root,fileCount:files.length,hits},null,2));
