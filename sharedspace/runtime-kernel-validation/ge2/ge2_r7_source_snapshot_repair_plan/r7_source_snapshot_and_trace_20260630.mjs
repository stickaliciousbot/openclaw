import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const root = '/home/stickai/.openclaw/workspace';
const artifactDir = path.join(root, 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan');
const snapshotDir = path.join(artifactDir, 'snapshots_20260630T0800Z');
const dist = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const targets = {
  types: path.join(dist, 'types-CdFhLeaX.js'),
  loader: path.join(dist, 'loader-Bfm_uDYG.js'),
  serverMethods: path.join(dist, 'server-methods-Dw6hzI_j.js'),
  commands: path.join(dist, 'commands-D2qp4St4.js')
};
fs.mkdirSync(snapshotDir, { recursive: true });
function sha(data) { return crypto.createHash('sha256').update(data).digest('hex'); }
function shaFile(file) { return sha(fs.readFileSync(file)); }
function lineOf(text, needle, from = 0) {
  const idx = text.indexOf(needle, from);
  if (idx < 0) return null;
  return { idx, line: text.slice(0, idx).split('\n').length };
}
function excerpt(text, needle, radius = 10, occurrence = 0) {
  let from = 0; let hit = null;
  for (let i = 0; i <= occurrence; i++) {
    hit = lineOf(text, needle, from);
    if (!hit) return null;
    from = hit.idx + needle.length;
  }
  const lines = text.split('\n');
  return { line: hit.line, excerpt: lines.slice(Math.max(0, hit.line - radius - 1), Math.min(lines.length, hit.line + radius)).join('\n') };
}
function allExcerpts(text, needle, radius = 5, max = 30) {
  const out = []; let from = 0;
  for (let i = 0; i < max; i++) {
    const hit = lineOf(text, needle, from);
    if (!hit) break;
    const lines = text.split('\n');
    out.push({ line: hit.line, excerpt: lines.slice(Math.max(0, hit.line - radius - 1), Math.min(lines.length, hit.line + radius)).join('\n') });
    from = hit.idx + needle.length;
  }
  return out;
}
function imports(text) { return [...text.matchAll(/from\s+"(\.\/[^"]+)"/g)].map(m => m[1]).sort(); }
function exportLine(text) { return excerpt(text, 'export {', 8); }
function snapshot(label, file) {
  const bytes = fs.readFileSync(file);
  const dest = path.join(snapshotDir, path.basename(file));
  fs.writeFileSync(dest, bytes);
  return { label, source: file, snapshot: dest, sha256: sha(bytes), size: bytes.length };
}
const snapshots = Object.entries(targets).map(([label, file]) => snapshot(label, file));
const src = Object.fromEntries(Object.entries(targets).map(([k, f]) => [k, fs.readFileSync(f, 'utf8')]));
const report = {
  generatedAt: new Date().toISOString(),
  classification: 'GE2_R7_SOURCE_SNAPSHOT_REPAIR_PLAN_NO_PRODUCTION_MUTATION',
  productionMutation: false,
  gatewayRestart: false,
  liveGe2Smoke: false,
  cronCloseoutApply: false,
  snapshots,
  inspected: {
    types: {
      path: targets.types,
      sha256: shaFile(targets.types),
      imports: imports(src.types),
      pluginCommandsState: excerpt(src.types, 'PLUGIN_COMMAND_STATE_KEY', 14),
      createPluginCommandState: excerpt(src.types, 'const createPluginCommandState', 20),
      pluginCommandsProxy: excerpt(src.types, 'const pluginCommands = new Proxy', 18),
      clearPluginCommands: excerpt(src.types, 'function clearPluginCommands', 12),
      restorePluginCommands: excerpt(src.types, 'function restorePluginCommands', 16),
      listRegisteredPluginCommands: excerpt(src.types, 'function listRegisteredPluginCommands', 12),
      exports: exportLine(src.types)
    },
    loader: {
      path: targets.loader,
      sha256: shaFile(targets.loader),
      imports: imports(src.loader).filter(i => /type|command|plugin|runtime|registry|loader/i.test(i)),
      importRegistryFns: excerpt(src.loader, 'clearPluginCommands', 6),
      registerCommand: excerpt(src.loader, 'const registerCommand =', 42),
      clearPluginCommandsHits: allExcerpts(src.loader, 'clearPluginCommands', 5),
      restorePluginCommandsHits: allExcerpts(src.loader, 'restorePluginCommands', 5),
      setActivePluginRegistryHits: allExcerpts(src.loader, 'setActivePluginRegistry', 5),
      activateGlobalSideEffectsHits: allExcerpts(src.loader, 'activateGlobalSideEffects', 5),
      registryCommandsPush: excerpt(src.loader, 'registry.commands.push', 18),
      pluginCatalogRelatedHits: allExcerpts(src.loader, 'commands', 2, 20)
    },
    serverMethods: {
      path: targets.serverMethods,
      sha256: shaFile(targets.serverMethods),
      imports: imports(src.serverMethods).filter(i => /commands|registry|plugin|runtime/i.test(i)),
      commandsListHandler: excerpt(src.serverMethods, '"commands.list"', 16),
      buildCommandsListResult: excerpt(src.serverMethods, 'function buildCommandsListResult', 36),
      buildPluginCommandEntries: excerpt(src.serverMethods, 'function buildPluginCommandEntries', 36),
      collectActiveRegistryPluginCommandEntries: excerpt(src.serverMethods, 'function collectActiveRegistryPluginCommandEntries', 46),
      listPluginCommandsImport: excerpt(src.serverMethods, 'listPluginCommands', 7)
    },
    commands: {
      path: targets.commands,
      sha256: shaFile(targets.commands),
      imports: imports(src.commands).filter(i => /type|command|plugin|registry|runtime/i.test(i)),
      r5Marker: excerpt(src.commands, 'GE2_R5_NATIVE_COMMAND_SURFACE_START', 10),
      ensureNativeGe2CommandRegistered: excerpt(src.commands, 'function ensureNativeGe2CommandRegistered', 34),
      ensureNativeGe2CommandRegisteredCall: excerpt(src.commands, 'ensureNativeGe2CommandRegistered();', 8),
      listActiveRegistryPluginCommands: excerpt(src.commands, 'function listActiveRegistryPluginCommands', 28),
      listEffectivePluginCommands: excerpt(src.commands, 'function listEffectivePluginCommands', 28),
      matchPluginCommand: excerpt(src.commands, 'function matchPluginCommand', 34),
      listPluginCommands: excerpt(src.commands, 'function listPluginCommands', 20),
      exports: exportLine(src.commands)
    }
  }
};
const targetSelection = [
  {
    candidateFile: targets.types,
    role: 'Registry storage/API: owns pluginCommands state, clear/restore/listRegistered APIs.',
    needsPatch: 'no for first R7 patch',
    why: 'It is lower-level shared state. Patching storage would broaden behavior globally. It confirms lifecycle cache/reset source but not the minimal durable GE2 registration site.'
  },
  {
    candidateFile: targets.loader,
    role: 'Plugin lifecycle: clears/restores/registers plugin commands, pushes registry.commands, sets active registry.',
    needsPatch: 'likely yes after exact call-order proof',
    why: 'This is where durable command records like pair/dreaming/phone/voice enter registry.commands and pluginCommands. R5 top-level registration is lost because this lifecycle rebuilds registry state.'
  },
  {
    candidateFile: targets.serverMethods,
    role: 'RPC commands.list handler and formatter.',
    needsPatch: 'no',
    why: 'It already imports the patched command chunk and lists plugin commands. Hardcoding GE2 here would violate design and duplicate descriptors on list calls.'
  },
  {
    candidateFile: targets.commands,
    role: 'Slash matcher/native command execution and plugin command list helpers; contains R5 GE2 handler patch.',
    needsPatch: 'no additional patch until loader lifecycle target proven',
    why: 'Local matching/handler works. Live imports it. Missing visibility is lifecycle/cache exclusion, not command handler absence.'
  }
];
report.targetSelection = targetSelection;
report.recommendedR7PatchPlan = {
  finalTargetProven: 'target class proven, exact loader function/call order still requires one more pre-patch trace before mutation',
  recommendedTargetClass: 'loader-Bfm_uDYG.js lifecycle path around clearPluginCommands/restorePluginCommands/registerCommand/registry.commands.push/setActivePluginRegistry',
  patchShape: 'Prefer durable registration through existing registerCommand lifecycle using a GE2 command definition so both pluginCommands and registry.commands/pluginCatalog.commands include ge2. Do not hardcode in server-methods and do not duplicate descriptors per commands.list call.',
  prePatchNeeded: [
    'Identify exact function enclosing clearPluginCommands/restorePluginCommands/setActivePluginRegistry and whether a post-restore registration hook can add ge2 once.',
    'Confirm command ownership/reserved-name validation requirements; R5 used pluginId ge2-native but reserved ownership may require plugin id matching command name if using registerPluginCommand with ownership=reserved.',
    'Decide whether GE2 should be registered as bundled/reserved plugin id ge2 or non-reserved plugin id ge2-native with requireAuth true and no ownership claim.'
  ],
  rollbackPlan: 'Use snapshots in snapshots_20260630T0800Z plus generated manifest/reverser before any production patch.'
};
const reportPath = path.join(artifactDir, 'r7_source_snapshot_trace_report_20260630.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
const md = `# GE2-R7 Source/Snapshot Repair Plan — 2026-06-30\n\nClassification: \`${report.classification}\`\n\nProduction mutation: **false**\nGateway restart: **false**\nLive /ge2 smoke: **false**\n\n## Snapshots\n\n${snapshots.map(s => `- ${s.label}: ${s.source} -> ${s.snapshot} (${s.sha256})`).join('\n')}\n\n## Target-selection table\n\n| Candidate file | Role | Needs patch? | Why / why not |\n|---|---|---|---|\n${targetSelection.map(r => `| ${r.candidateFile} | ${r.role} | ${r.needsPatch} | ${r.why} |`).join('\n')}\n\n## Recommendation\n\n${report.recommendedR7PatchPlan.patchShape}\n\nExact final mutation target is not yet authorized as a single file/function; one more pre-patch call-order trace inside \`loader-Bfm_uDYG.js\` is required before production mutation.\n`;
const mdPath = path.join(artifactDir, 'GE2_R7_SOURCE_SNAPSHOT_REPAIR_PLAN.md');
fs.writeFileSync(mdPath, md);
const manifest = {
  generatedAt: new Date().toISOString(),
  classification: report.classification,
  productionMutation: false,
  allExist: [reportPath, mdPath, ...snapshots.map(s => s.snapshot)].every(f => fs.existsSync(f)),
  files: [
    { path: reportPath, sha256: shaFile(reportPath) },
    { path: mdPath, sha256: shaFile(mdPath) },
    ...snapshots.map(s => ({ path: s.snapshot, source: s.source, sha256: shaFile(s.snapshot) }))
  ]
};
const manifestPath = path.join(artifactDir, 'r7_source_snapshot_manifest_20260630.json');
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ reportPath, mdPath, manifestPath, allExist: manifest.allExist, targetSelection, recommendation: report.recommendedR7PatchPlan }, null, 2));
