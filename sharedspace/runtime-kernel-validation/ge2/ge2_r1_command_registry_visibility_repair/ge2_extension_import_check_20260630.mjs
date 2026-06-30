const mod = await import('/home/stickai/.openclaw/workspace/.openclaw/extensions/ge2-command/index.mjs');
const plugin = mod.default ?? mod;
const registered = [];
plugin.register({ registerCommand(command) { registered.push(command); } });
const ge2 = registered.find((command) => command.name === 'ge2');
console.log(JSON.stringify({
  pluginId: plugin.id,
  pluginName: plugin.name,
  version: plugin.version,
  registeredCount: registered.length,
  ge2Present: Boolean(ge2),
  ge2: ge2 ? {
    name: ge2.name,
    nativeNames: ge2.nativeNames,
    description: ge2.description,
    acceptsArgs: ge2.acceptsArgs,
    requireAuth: ge2.requireAuth,
    handlerType: typeof ge2.handler
  } : null
}, null, 2));
