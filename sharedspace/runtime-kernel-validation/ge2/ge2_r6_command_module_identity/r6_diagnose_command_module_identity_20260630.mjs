import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const root = '/home/stickai/.openclaw/workspace';
const artifactDir = path.join(root, 'sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity');
const distRoot = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist';
const patchedPath = path.join(distRoot, 'commands-D2qp4St4.js');
const expectedPatchedSha = '660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb';
fs.mkdirSync(artifactDir, { recursive: true });

function sha256(data) { return crypto.createHash('sha256').update(data).digest('hex'); }
function shaFile(file) { try { return sha256(fs.readFileSync(file)); } catch { return null; } }
function exists(file) { try { fs.accessSync(file); return true; } catch { return false; } }
function write(name, content) { const p = path.join(artifactDir, name); fs.writeFileSync(p, content); return p; }
function run(name, cmd, args, timeout = 120000) {
  const stdoutPath = path.join(artifactDir, `${name}.stdout.txt`);
  const stderrPath = path.join(artifactDir, `${name}.stderr.txt`);
  try {
    const stdout = execFileSync(cmd, args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout });
    fs.writeFileSync(stdoutPath, stdout);
    fs.writeFileSync(stderrPath, '');
    return { ok: true, code: 0, stdout, stderr: '', stdoutPath, stderrPath, command: [cmd, ...args].join(' ') };
  } catch (e) {
    const stdout = e.stdout?.toString?.() ?? '';
    const stderr = e.stderr?.toString?.() ?? String(e.message || e);
    fs.writeFileSync(stdoutPath, stdout);
    fs.writeFileSync(stderrPath, stderr);
    return { ok: false, code: e.status ?? null, stdout, stderr, stdoutPath, stderrPath, command: [cmd, ...args].join(' ') };
  }
}
function parsePid(text) { return /pid\s+(\d+)/i.exec(text)?.[1] ?? null; }
function parseVersion(text) { return text.trim().split(/\n/).filter(Boolean).slice(0, 5); }
function parseCommandsList(raw) {
  let parsed = null;
  try { parsed = JSON.parse(raw); } catch {}
  const commands = parsed?.result?.commands || parsed?.commands || [];
  return { parsed, commands };
}
function callCommandsList(name, params) {
  const args = ['gateway', 'call', 'commands.list', '--json'];
  if (params) args.push('--params', JSON.stringify(params));
  const res = run(`commands_list_${name}`, 'openclaw', args, 120000);
  const { commands } = parseCommandsList(res.stdout);
  const ge2Entries = commands.filter((c) => c?.name === 'ge2' || c?.nativeName === 'ge2' || (c?.textAliases || []).includes('/ge2'));
  const pluginEntries = commands.filter((c) => c?.source === 'plugin');
  return {
    name,
    params: params ?? null,
    ok: res.ok,
    code: res.code,
    count: commands.length,
    ge2Present: ge2Entries.length > 0,
    ge2Entries,
    fakePresent: commands.some((c) => ['fake', 'fake-command'].includes(c?.name) || ['fake', 'fake-command'].includes(c?.nativeName)),
    pluginNames: pluginEntries.map((c) => c.name),
    corePluginCommandsPresent: ['pair', 'dreaming', 'phone', 'voice'].every((n) => pluginEntries.some((c) => c.name === n)),
    stdoutPath: res.stdoutPath,
    stderrPath: res.stderrPath
  };
}
function lineOf(text, needle) {
  const idx = text.indexOf(needle);
  return idx >= 0 ? text.slice(0, idx).split('\n').length : null;
}
function excerpt(text, needle, radius = 260) {
  const idx = text.indexOf(needle);
  if (idx < 0) return null;
  return text.slice(Math.max(0, idx - radius), Math.min(text.length, idx + needle.length + radius));
}
function importEdges(text) {
  return [...text.matchAll(/from\s+"(\.\/[^"]+)"/g)].map((m) => m[1]).sort();
}
function scanDist() {
  const files = fs.readdirSync(distRoot).filter((f) => f.endsWith('.js')).sort();
  const needles = [
    'GE2_R5_NATIVE_COMMAND_SURFACE_START',
    'ensureNativeGe2CommandRegistered',
    'matchPluginCommand',
    'executePluginCommand',
    'listPluginCommands',
    'listEffectivePluginCommands',
    'pluginCommands',
    'pluginCommands.clear',
    'clearPluginCommands',
    'restorePluginCommands',
    'registerCommand',
    'commands.list',
    'buildCommandsListResult',
    'buildPluginCommandEntries',
    'getChatCommands',
    'buildBuiltinChatCommands',
    'resolveTextCommand',
    'maybeResolveTextAlias',
    'normalizeCommandBody',
    'pair',
    'dreaming',
    'phone',
    'voice'
  ];
  const hits = [];
  for (const f of files) {
    const full = path.join(distRoot, f);
    const text = fs.readFileSync(full, 'utf8');
    const symbols = needles.filter((n) => text.includes(n));
    if (!symbols.length) continue;
    hits.push({
      file: f,
      path: full,
      sha256: shaFile(full),
      size: fs.statSync(full).size,
      symbols,
      lines: Object.fromEntries(symbols.map((n) => [n, lineOf(text, n)])),
      imports: importEdges(text).filter((imp) => /command|registry|plugin|server-method/i.test(imp)),
      hasR5Marker: text.includes('GE2_R5_NATIVE_COMMAND_SURFACE_START')
    });
  }
  return hits;
}
function inspectFile(file) {
  const text = fs.readFileSync(file, 'utf8');
  return {
    path: file,
    exists: true,
    sha256: shaFile(file),
    size: fs.statSync(file).size,
    markers: {
      r5Start: text.includes('GE2_R5_NATIVE_COMMAND_SURFACE_START'),
      ensureNativeGe2CommandRegistered: text.includes('ensureNativeGe2CommandRegistered'),
      ge2Dispatcher: text.includes('Ge2Dispatcher'),
      matchPluginCommand: text.includes('matchPluginCommand'),
      listPluginCommands: text.includes('listPluginCommands'),
      pluginCommandsClear: text.includes('pluginCommands.clear') || text.includes('clearPluginCommands')
    },
    imports: importEdges(text),
    exports: (() => {
      const match = text.match(/export\s+\{([^}]+)\}/);
      return match ? match[1].split(',').map((s) => s.trim()).filter(Boolean) : [];
    })()
  };
}
function inspectProc(pid) {
  if (!pid) return null;
  const base = `/proc/${pid}`;
  function read(rel) { try { return fs.readFileSync(path.join(base, rel), 'utf8').replace(/\0/g, ' ').trim(); } catch { return null; } }
  function link(rel) { try { return fs.readlinkSync(path.join(base, rel)); } catch { return null; } }
  return { pid, cmdline: read('cmdline'), cwd: link('cwd'), exe: link('exe') };
}

const version = run('openclaw_version', 'openclaw', ['--version'], 60000);
const status = run('gateway_status', 'openclaw', ['gateway', 'status'], 120000);
const livePid = parsePid(status.stdout || status.stderr || '');
const matrix = [
  callCommandsList('default', null),
  callCommandsList('telegram_both', { provider: 'telegram', scope: 'both' }),
  callCommandsList('telegram_text', { provider: 'telegram', scope: 'text' })
];
const pluginList = run('plugins_list', 'openclaw', ['plugins', 'list', '--json'], 120000);
let pluginsParsed = null;
try { pluginsParsed = JSON.parse(pluginList.stdout); } catch {}
const pluginRows = Array.isArray(pluginsParsed) ? pluginsParsed : (pluginsParsed?.plugins || []);
const ge2Plugin = pluginRows.find((p) => p.id === 'ge2-command') || null;
const distHits = scanDist();
const commandMatcherCandidates = distHits.filter((h) => h.symbols.some((s) => ['matchPluginCommand', 'executePluginCommand', 'listPluginCommands', 'listEffectivePluginCommands', 'pluginCommands'].includes(s)));
const commandListCandidates = distHits.filter((h) => h.symbols.some((s) => ['commands.list', 'buildCommandsListResult', 'buildPluginCommandEntries'].includes(s)));
const cacheResetCandidates = distHits.filter((h) => h.symbols.some((s) => ['pluginCommands.clear', 'clearPluginCommands', 'restorePluginCommands'].includes(s)));
const knownNameCandidates = distHits.filter((h) => ['pair', 'dreaming', 'phone', 'voice'].some((name) => h.symbols.includes(name)));
const serverMethods = commandListCandidates.find((h) => h.symbols.includes('commands.list')) || null;
let serverMethodsText = '';
try { if (serverMethods) serverMethodsText = fs.readFileSync(serverMethods.path, 'utf8'); } catch {}
const serverMethodsCommandImports = serverMethods ? importEdges(serverMethodsText).filter((imp) => imp.includes('commands') || imp.includes('registry')) : [];
const commandImportResolutions = serverMethodsCommandImports.map((imp) => {
  const resolved = path.resolve(path.dirname(serverMethods.path), imp);
  const withJs = resolved.endsWith('.js') ? resolved : `${resolved}.js`;
  return { import: imp, resolved: withJs, exists: exists(withJs), sha256: shaFile(withJs), isPatchedTarget: withJs === patchedPath };
});

const traceTable = [
  { question: 'Current OpenClaw version', evidence: parseVersion(version.stdout || version.stderr).join(' | '), result: version.ok ? 'captured' : 'failed' },
  { question: 'Gateway PID/health/admin', evidence: `pid=${livePid}; connectivityOk=${/Connectivity probe:\s*ok/i.test(status.stdout)}; adminCapable=${/admin-capable/i.test(status.stdout)}`, result: (livePid && /Connectivity probe:\s*ok/i.test(status.stdout) && /admin-capable/i.test(status.stdout)) ? 'PASS' : 'FAIL' },
  { question: 'Live commands.list baseline', evidence: matrix.map((m) => `${m.name}:count=${m.count},ge2=${m.ge2Present},fake=${m.fakePresent},plugins=${m.pluginNames.join('|')}`).join('; '), result: matrix.every((m) => !m.ge2Present && !m.fakePresent && m.corePluginCommandsPresent) ? 'R5_BLOCK_REPRODUCED' : 'DIFFERENT_STATE' },
  { question: 'Patched chunk on disk', evidence: `${patchedPath}; sha=${shaFile(patchedPath)}; expected=${expectedPatchedSha}`, result: shaFile(patchedPath) === expectedPatchedSha ? 'ON_DISK_PATCH_PRESENT' : 'SHA_MISMATCH' },
  { question: 'commands.list serving chunk', evidence: serverMethods ? `${serverMethods.file}; symbols=${serverMethods.symbols.join('|')}` : 'not found', result: serverMethods ? 'CANDIDATE_FOUND' : 'NOT_FOUND' },
  { question: 'commands.list imports patched command chunk', evidence: commandImportResolutions.map((r) => `${r.import}->${path.basename(r.resolved)} sha=${r.sha256} patched=${r.isPatchedTarget}`).join('; '), result: commandImportResolutions.some((r) => r.isPatchedTarget && r.sha256 === expectedPatchedSha) ? 'STATIC_IMPORT_EDGE_TO_PATCHED_CHUNK' : 'NO_STATIC_IMPORT_EDGE_TO_PATCHED_CHUNK' },
  { question: 'Command matcher chunk candidates', evidence: commandMatcherCandidates.map((h) => `${h.file}${h.hasR5Marker ? '[R5]' : ''}:${h.symbols.join('|')}`).join('; '), result: commandMatcherCandidates.length ? 'CANDIDATES_FOUND' : 'NOT_FOUND' },
  { question: 'Registry cache/reset candidates', evidence: cacheResetCandidates.map((h) => `${h.file}:${h.symbols.join('|')}`).join('; '), result: cacheResetCandidates.length ? 'CACHE_OR_RESET_PATHS_FOUND' : 'NONE_FOUND' },
  { question: 'Plugin manager GE2 state', evidence: ge2Plugin ? `status=${ge2Plugin.status}; commands=${JSON.stringify(ge2Plugin.commands)}; source=${ge2Plugin.source}` : 'missing', result: ge2Plugin?.status === 'loaded' ? 'GE2_PLUGIN_MANAGER_LOADED' : 'NOT_LOADED' }
];

const report = {
  generatedAt: new Date().toISOString(),
  classification: 'GE2_R6_COMMAND_MODULE_IDENTITY_DIAGNOSIS_ONLY',
  mutation: false,
  forbiddenActionsHonored: {
    rollback: false,
    liveGe2Smoke: false,
    cronCloseoutApply: false,
    pluginManagerBridgePatch: false,
    productionPatch: false
  },
  productionState: {
    version: { ok: version.ok, code: version.code, lines: parseVersion(version.stdout || version.stderr), stdoutPath: version.stdoutPath, stderrPath: version.stderrPath },
    gateway: { ok: status.ok, livePid, healthOk: /Connectivity probe:\s*ok/i.test(status.stdout), adminCapable: /admin-capable/i.test(status.stdout), process: inspectProc(livePid), stdoutPath: status.stdoutPath, stderrPath: status.stderrPath },
    commandsListMatrix: matrix,
    pluginManager: { ge2Plugin, stdoutPath: pluginList.stdoutPath, stderrPath: pluginList.stderrPath }
  },
  patchedTarget: { expectedPatchedSha, ...inspectFile(patchedPath), shaMatchesExpected: shaFile(patchedPath) === expectedPatchedSha },
  serverMethodsCandidate: serverMethods,
  serverMethodsCommandImports,
  commandImportResolutions,
  commandMatcherCandidates,
  commandListCandidates,
  cacheResetCandidates,
  knownNameCandidates,
  traceTable,
  preliminaryConclusion: (() => {
    const edge = commandImportResolutions.some((r) => r.isPatchedTarget && r.sha256 === expectedPatchedSha);
    const visible = matrix.every((m) => m.ge2Present);
    const reset = cacheResetCandidates.length > 0;
    if (edge && !visible && reset) return 'STATIC_COMMANDS_LIST_IMPORT_EDGE_POINTS_TO_PATCHED_CHUNK_BUT_LIVE_OUTPUT_OMITS_GE2; likely command registry state is cleared/rebuilt after module top-level R5 registration, or commands.list uses effective registry after reset. Next inspect cache/reset call order, not blind-patch another file.';
    if (!edge && !visible) return 'commands.list static import edge does not point to patched chunk; locate alternate imported command chunk before any patch.';
    if (visible) return 'Unexpected: /ge2 visible; R5/R6 state changed and live dispatch validation may be next, but user forbade live /ge2 smoke in this run.';
    return 'Inconclusive; use trace table and candidates.';
  })()
};
const reportPath = write('r6_command_module_identity_report_20260630.json', JSON.stringify(report, null, 2) + '\n');
const md = `# GE2-R6 Command Module Identity Diagnosis — 2026-06-30\n\nClassification: \`${report.classification}\`\n\nMutation: **false**\n\n## Trace table\n\n| Question | Result | Evidence |\n|---|---|---|\n${traceTable.map((r) => `| ${r.question} | ${r.result} | ${String(r.evidence).replace(/\|/g, '/').replace(/\n/g, ' ')} |`).join('\n')}\n\n## Preliminary conclusion\n\n${report.preliminaryConclusion}\n\n## Hard stop\n\nNo rollback, no live \`/ge2\` smoke, no cron closeout apply, and no production patch were performed.\n`;
const mdPath = write('GE2_R6_COMMAND_MODULE_IDENTITY_DIAGNOSIS.md', md);
const manifestPath = write('r6_file_manifest_20260630.json', JSON.stringify({ generatedAt: new Date().toISOString(), allExist: [reportPath, mdPath].every(exists), files: [{ path: reportPath, sha256: shaFile(reportPath) }, { path: mdPath, sha256: shaFile(mdPath) }] }, null, 2) + '\n');
console.log(JSON.stringify({ reportPath, mdPath, manifestPath, livePid, ge2Visible: matrix.map((m) => ({ name: m.name, ge2Present: m.ge2Present, count: m.count })), preliminaryConclusion: report.preliminaryConclusion }, null, 2));
