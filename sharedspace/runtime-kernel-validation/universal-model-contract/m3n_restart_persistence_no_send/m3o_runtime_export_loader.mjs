import fs from 'node:fs/promises';

export async function load(url, context, defaultLoad) {
  const target = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/agent-runner.runtime-DESbFJnG.js';
  if (url === new URL('file://' + target).href) {
    const source = await fs.readFile(target, 'utf8');
    return {
      format: 'module',
      shortCircuit: true,
      source: `${source}\nexport { maybeRunUmcV1ShadowObserveOnly, runM3EnvelopeSupervisor };\n`,
    };
  }
  return defaultLoad(url, context, defaultLoad);
}
