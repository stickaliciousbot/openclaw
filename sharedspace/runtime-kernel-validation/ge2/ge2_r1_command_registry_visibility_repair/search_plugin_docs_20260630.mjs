import fs from 'node:fs';
import path from 'node:path';
const roots = ['/home/stickai/.npm-global/lib/node_modules/openclaw/docs', '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk'];
const needles = ['plugins.load.paths', '.openclaw/extensions', 'Plugin Load Paths'];
const hits = [];
function walk(dir, depth = 0) {
  if (depth > 5 || hits.length >= 80) return;
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const entry of entries) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, depth + 1);
    else if (/\.(md|ts|js|json|d\.ts)$/.test(entry.name)) {
      let text = '';
      try { text = fs.readFileSync(p, 'utf8'); } catch { continue; }
      for (const needle of needles) {
        const idx = text.indexOf(needle);
        if (idx >= 0) hits.push({ file: p, needle, excerpt: text.slice(Math.max(0, idx - 160), idx + 240) });
      }
    }
  }
}
for (const root of roots) walk(root);
console.log(JSON.stringify(hits, null, 2));
