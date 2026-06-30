import fs from 'node:fs';
import crypto from 'node:crypto';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r3_packaging_bundle_singleton_repair';
const typesPath='/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js';
const commandsPath='/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js';
const hookPath='/home/stickai/.openclaw/workspace/hooks/ge2-register/handler.js';
const [typesMod, commandsMod, hookMod] = await Promise.all([
  import('file://' + typesPath + '?r3=' + Date.now()),
  import('file://' + commandsPath + '?r3=' + Date.now()),
  import('file://' + hookPath + '?r3=' + Date.now())
]);
const register = typesMod.p;
const stateKey = Symbol.for('openclaw.pluginCommandsState');
const before = commandsMod.r();
const command = { name:'ge2_r3_diag_probe', description:'GE2-R3 local diagnostic probe', acceptsArgs:false, requireAuth:true, handler: async()=>({text:'diag'}) };
const reg = register('ge2-r3-diag', command, { pluginName:'GE2 R3 diagnostic', pluginRoot:dir });
const after = commandsMod.r();
const report={generatedAt:new Date().toISOString(), imports:{types:typeof register, commandsList:typeof commandsMod.r, hookDefault:typeof hookMod.default}, processHasState:Object.prototype.hasOwnProperty.call(process,stateKey), globalHasState:Object.prototype.hasOwnProperty.call(globalThis,stateKey), sameStateObject:process[stateKey]===globalThis[stateKey], bridgeTarget:process[stateKey]?.bridgeTarget ?? null, reg, beforeCount:before.length, afterCount:after.length, probeVisible:after.some(c=>c.name==='ge2_r3_diag_probe'), hashes:{types:crypto.createHash('sha256').update(fs.readFileSync(typesPath)).digest('hex'), hook:crypto.createHash('sha256').update(fs.readFileSync(hookPath)).digest('hex')}};
fs.writeFileSync(dir+'/local_patch_validation.json', JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
