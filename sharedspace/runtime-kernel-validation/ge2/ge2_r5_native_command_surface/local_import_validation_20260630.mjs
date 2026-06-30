import crypto from 'node:crypto';
import fs from 'node:fs';
const target='/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js';
const mod=await import('file://' + target + '?ge2r5=' + Date.now());
const commands=mod.r();
const ge2=commands.find(c=>c.name==='ge2');
const match=mod.i('/ge2 status',{channel:'telegram'});
console.log(JSON.stringify({
  target,
  sha256: crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex'),
  exports:Object.keys(mod).sort(),
  commandCount:commands.length,
  ge2Present:Boolean(ge2),
  ge2,
  matchPresent:Boolean(match),
  matchCommand:match?.command ? {name:match.command.name, description:match.command.description, acceptsArgs:match.command.acceptsArgs, requireAuth:match.command.requireAuth, pluginId:match.command.pluginId, pluginName:match.command.pluginName} : null,
  matchArgs:match?.args ?? null,
  markers:{start:fs.readFileSync(target,'utf8').includes('GE2_R5_NATIVE_COMMAND_SURFACE_START'),end:fs.readFileSync(target,'utf8').includes('GE2_R5_NATIVE_COMMAND_SURFACE_END')}
},null,2));
