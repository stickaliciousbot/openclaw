#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const AUDIO_EXTENSIONS = new Set(['.wav', '.webm', '.ogg', '.opus', '.mp3', '.flac', '.m4a', '.aac']);
const SOURCE_EXTENSIONS = new Set(['.js', '.mjs', '.cjs', '.json', '.md', '.html', '.css', '.sh', '.py', '.txt']);
const DEFAULT_MIN_AGE_MINUTES = 15;
const MANIFEST_SCHEMA = 'stickbot.tars.generated-audio-audit.v1';
const PASS_STAGE = 'STICKBOT_TARS_GENERATED_AUDIO_AUDIT_STAGE_PASS';
const PASS_DELETE = 'STICKBOT_TARS_GENERATED_AUDIO_AUDIT_DELETE_PASS';
const HOLD = 'STICKBOT_TARS_GENERATED_AUDIO_AUDIT_HOLD';
const FAIL = 'STICKBOT_TARS_GENERATED_AUDIO_AUDIT_FAIL';

const scriptPath = fileURLToPath(import.meta.url);
const projectRoot = path.resolve(path.dirname(scriptPath), '..');
const workspaceRoot = path.resolve(projectRoot, '../..');
const runtimeRoot = process.env.STICKBOT_TARS_RUNTIME_ROOT || '/home/stickai/stickbot-voice';

function parseArgs(argv) {
  const args = {
    deleteMode: false,
    manifest: null,
    confirmDelete: false,
    stdoutOnly: false,
    jsonOnly: false,
    mdOnly: false,
    includeRuntimeOutput: true,
    minAgeMinutes: DEFAULT_MIN_AGE_MINUTES,
    outputDir: null,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--delete') args.deleteMode = true;
    else if (arg === '--manifest') args.manifest = argv[++i];
    else if (arg === '--confirm-delete') args.confirmDelete = true;
    else if (arg === '--stdout-only') args.stdoutOnly = true;
    else if (arg === '--json') args.jsonOnly = true;
    else if (arg === '--md') args.mdOnly = true;
    else if (arg === '--no-runtime-output') args.includeRuntimeOutput = false;
    else if (arg === '--min-age-minutes') args.minAgeMinutes = Number(argv[++i]);
    else if (arg === '--output-dir') args.outputDir = argv[++i];
    else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!Number.isFinite(args.minAgeMinutes) || args.minAgeMinutes < 0) {
    throw new Error('--min-age-minutes must be a non-negative number');
  }

  return args;
}

function printHelp() {
  console.log(`Stickbot-TARS generated audio auditor\n\nUsage:\n  npm run audit:generated-audio\n  npm run audit:generated-audio -- --min-age-minutes 60\n  npm run audit:generated-audio -- --json --stdout-only\n  npm run audit:generated-audio -- --delete --manifest artifacts/generated-audio-audits/latest.json --confirm-delete\n\nDefault mode audits and stages a deletion manifest only. It does not delete files.\nDelete mode requires a prior PASS manifest plus --confirm-delete.\n`);
}

function toPosix(p) {
  return p.split(path.sep).join('/');
}

function rel(abs) {
  if (abs.startsWith(projectRoot + path.sep) || abs === projectRoot) {
    return toPosix(path.relative(projectRoot, abs));
  }
  if (abs.startsWith(workspaceRoot + path.sep) || abs === workspaceRoot) {
    return toPosix(path.relative(workspaceRoot, abs));
  }
  return abs;
}

function isInside(child, parent) {
  const relative = path.relative(parent, child);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

async function pathExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function listFilesRecursive(root) {
  const files = [];
  async function walk(dir) {
    let entries;
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch (error) {
      if (error.code === 'ENOENT') return;
      throw error;
    }
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === '.venv' || entry.name === 'venv') continue;
        await walk(full);
      } else if (entry.isFile()) {
        files.push(full);
      }
    }
  }
  await walk(root);
  return files;
}

async function sha256File(absPath) {
  const data = await fs.readFile(absPath);
  return crypto.createHash('sha256').update(data).digest('hex');
}

function buildScanRoots({ includeRuntimeOutput }) {
  const roots = [
    path.join(projectRoot, 'data/audio/input'),
    path.join(projectRoot, 'data/audio/normalized'),
    path.join(projectRoot, 'data/audio/output'),
    path.join(projectRoot, 'data/generated'),
    path.join(projectRoot, 'data/captured'),
    path.join(projectRoot, 'data/tmp'),
    path.join(projectRoot, 'exports'),
  ];
  if (includeRuntimeOutput) roots.push(path.join(runtimeRoot, 'output'));
  return roots.map((root) => path.resolve(root));
}

function buildProtectedRoots() {
  return [
    path.join(runtimeRoot, 'speakers'),
    path.join(runtimeRoot, 'xtts_models'),
    path.join(runtimeRoot, 'stt_models'),
    path.join(runtimeRoot, 'tools'),
    path.join(runtimeRoot, 'certs'),
    path.join(projectRoot, 'src'),
    path.join(projectRoot, 'public'),
    path.join(projectRoot, 'scripts'),
    path.join(projectRoot, 'safety'),
    path.join(projectRoot, 'test'),
  ].map((root) => path.resolve(root));
}

async function gitTrackedSet() {
  try {
    const { stdout } = await execFileAsync('git', ['ls-files', '-z'], { cwd: projectRoot, maxBuffer: 32 * 1024 * 1024 });
    return new Set(stdout.split('\0').filter(Boolean));
  } catch {
    return new Set();
  }
}

async function sourceFilesForReferenceScan() {
  // This scan is intentionally limited to executable dependency surfaces.
  // Documentation/evidence references do not make generated audio a live dependency,
  // but runtime scripts do: deleting default smoke fixtures would break validation.
  const roots = [
    path.join(projectRoot, 'server.js'),
    path.join(projectRoot, 'package.json'),
    path.join(projectRoot, 'public'),
    path.join(projectRoot, 'src'),
    path.join(projectRoot, 'safety'),
    path.join(projectRoot, 'scripts'),
  ];
  const out = [];
  for (const root of roots) {
    if (!(await pathExists(root))) continue;
    const st = await fs.stat(root);
    if (st.isFile()) out.push(root);
    else {
      const files = await listFilesRecursive(root);
      out.push(...files.filter((file) => SOURCE_EXTENSIONS.has(path.extname(file).toLowerCase())));
    }
  }
  return out.sort((a, b) => a.localeCompare(b));
}

async function exactSourceReferences(candidates) {
  const basenames = new Map();
  for (const candidate of candidates) {
    const base = path.basename(candidate.absPath);
    if (!basenames.has(base)) basenames.set(base, []);
    basenames.get(base).push(candidate.absPath);
  }

  const refs = new Map(candidates.map((candidate) => [candidate.absPath, []]));
  const files = await sourceFilesForReferenceScan();
  for (const file of files) {
    let text;
    try {
      text = await fs.readFile(file, 'utf8');
    } catch {
      continue;
    }
    for (const [base, paths] of basenames.entries()) {
      if (!text.includes(base)) continue;
      const sourceRel = rel(file);
      for (const candidatePath of paths) refs.get(candidatePath).push(sourceRel);
    }
  }
  return refs;
}

async function openFileSet(candidateAbsPaths) {
  const wanted = new Set();
  for (const absPath of candidateAbsPaths) {
    try {
      const st = await fs.stat(absPath);
      wanted.add(`${st.dev}:${st.ino}`);
    } catch {
      // Missing candidates are handled elsewhere.
    }
  }

  const open = new Map(candidateAbsPaths.map((p) => [p, []]));
  const inodeToPaths = new Map();
  for (const absPath of candidateAbsPaths) {
    try {
      const st = await fs.stat(absPath);
      const key = `${st.dev}:${st.ino}`;
      if (!inodeToPaths.has(key)) inodeToPaths.set(key, []);
      inodeToPaths.get(key).push(absPath);
    } catch {
      // ignore
    }
  }

  let procEntries;
  try {
    procEntries = await fs.readdir('/proc', { withFileTypes: true });
  } catch (error) {
    return { open, scanError: `PROC_SCAN_FAILED:${error.code || error.message}` };
  }

  for (const entry of procEntries) {
    if (!entry.isDirectory() || !/^\d+$/.test(entry.name)) continue;
    const pid = entry.name;
    const fdDir = path.join('/proc', pid, 'fd');
    let fds;
    try {
      fds = await fs.readdir(fdDir);
    } catch {
      continue;
    }
    for (const fd of fds) {
      const fdPath = path.join(fdDir, fd);
      let st;
      try {
        st = await fs.stat(fdPath);
      } catch {
        continue;
      }
      const key = `${st.dev}:${st.ino}`;
      if (!wanted.has(key)) continue;
      const paths = inodeToPaths.get(key) || [];
      for (const candidatePath of paths) {
        open.get(candidatePath).push({ pid: Number(pid), fd });
      }
    }
  }
  return { open, scanError: null };
}

async function collectCandidates(args) {
  const scanRoots = buildScanRoots(args);
  const protectedRoots = buildProtectedRoots();
  const existingScanRoots = [];
  const rootErrors = [];
  const candidates = [];

  for (const root of scanRoots) {
    if (!(await pathExists(root))) continue;
    if (protectedRoots.some((protectedRoot) => isInside(root, protectedRoot))) {
      rootErrors.push({ root: rel(root), error: 'SCAN_ROOT_INSIDE_PROTECTED_ROOT' });
      continue;
    }
    existingScanRoots.push(root);
    const files = await listFilesRecursive(root);
    for (const absPath of files) {
      const ext = path.extname(absPath).toLowerCase();
      if (!AUDIO_EXTENSIONS.has(ext)) continue;
      const st = await fs.stat(absPath);
      candidates.push({ absPath, st, scanRoot: root });
    }
  }

  candidates.sort((a, b) => a.absPath.localeCompare(b.absPath));
  return { candidates, existingScanRoots, rootErrors, protectedRoots };
}

function classifyCandidate(candidate, context) {
  const reasons = [];
  const blockers = [];
  const warnings = [];
  const absPath = candidate.absPath;
  const relPath = rel(absPath);
  const ext = path.extname(absPath).toLowerCase();
  const ageMs = context.nowMs - candidate.st.mtimeMs;
  const ageMinutes = Math.max(0, ageMs / 60000);

  if (!AUDIO_EXTENSIONS.has(ext)) blockers.push('NOT_AUDIO_EXTENSION');
  if (!context.existingScanRoots.some((root) => isInside(absPath, root))) blockers.push('OUTSIDE_ALLOWLISTED_SCAN_ROOT');
  if (context.protectedRoots.some((root) => isInside(absPath, root))) blockers.push('INSIDE_PROTECTED_ROOT');
  if (relPath.includes('/node_modules/') || relPath.startsWith('node_modules/')) blockers.push('NODE_MODULES_PATH');
  if (relPath.includes('/.git/') || relPath.startsWith('.git/')) blockers.push('GIT_INTERNAL_PATH');
  if (relPath.includes('/mnt/c/') || absPath.startsWith('/mnt/c/')) blockers.push('MNT_C_PATH_FORBIDDEN');
  if (context.gitTracked.has(toPosix(path.relative(projectRoot, absPath)))) blockers.push('GIT_TRACKED_FILE');
  if (ageMinutes < context.minAgeMinutes) blockers.push(`TOO_RECENT_UNDER_${context.minAgeMinutes}_MINUTES`);

  const sourceRefs = context.sourceRefs.get(absPath) || [];
  if (sourceRefs.length > 0) blockers.push('REFERENCED_BY_EXECUTABLE_SOURCE');

  const openRefs = context.openFiles.get(absPath) || [];
  if (openRefs.length > 0) blockers.push('OPEN_BY_PROCESS');

  if (candidate.st.size === 0) warnings.push('ZERO_BYTE_AUDIO_ARTIFACT');
  if (relPath.startsWith('exports/')) reasons.push('EXPORT_BUNDLE_AUDIO');
  else if (relPath.startsWith('data/audio/output/')) reasons.push('PROJECT_GENERATED_TTS_OUTPUT');
  else if (relPath.startsWith('data/audio/input/')) reasons.push('PROJECT_CAPTURED_MIC_AUDIO');
  else if (relPath.startsWith('data/audio/normalized/')) reasons.push('PROJECT_NORMALIZED_STT_AUDIO');
  else if (absPath.startsWith(path.join(runtimeRoot, 'output') + path.sep)) reasons.push('RUNTIME_GENERATED_AUDIO_OUTPUT');
  else reasons.push('ALLOWLISTED_GENERATED_AUDIO_ROOT');

  return {
    path: relPath,
    absolutePath: absPath,
    scanRoot: rel(candidate.scanRoot),
    sizeBytes: candidate.st.size,
    mtimeMs: Math.trunc(candidate.st.mtimeMs),
    mtimeIso: candidate.st.mtime.toISOString(),
    ageMinutes: Number(ageMinutes.toFixed(3)),
    sha256: candidate.sha256,
    stagedForDeletion: blockers.length === 0,
    reasons,
    blockers,
    warnings,
    sourceReferences: sourceRefs,
    openFileReferences: openRefs,
  };
}

function summarize(files, rootErrors, procScanError) {
  const staged = files.filter((file) => file.stagedForDeletion);
  const blocked = files.filter((file) => !file.stagedForDeletion);
  const totalBytes = files.reduce((sum, file) => sum + file.sizeBytes, 0);
  const stagedBytes = staged.reduce((sum, file) => sum + file.sizeBytes, 0);
  const blockedBytes = blocked.reduce((sum, file) => sum + file.sizeBytes, 0);
  const classification = rootErrors.length || procScanError ? HOLD : PASS_STAGE;
  return {
    classification,
    fileCount: files.length,
    stagedCount: staged.length,
    protectedSkippedCount: blocked.length,
    blockedCount: blocked.length,
    totalBytes,
    stagedBytes,
    blockedBytes,
    rootErrorCount: rootErrors.length,
    procScanError: procScanError || null,
    deleteRequires: ['--delete', '--manifest <PASS manifest>', '--confirm-delete'],
  };
}

function manifestHash(manifestWithoutHash) {
  const stable = JSON.stringify(manifestWithoutHash);
  return crypto.createHash('sha256').update(stable).digest('hex');
}

async function buildAuditManifest(args) {
  const now = new Date();
  const { candidates, existingScanRoots, rootErrors, protectedRoots } = await collectCandidates(args);
  for (const candidate of candidates) {
    candidate.sha256 = await sha256File(candidate.absPath);
  }

  const sourceRefs = await exactSourceReferences(candidates);
  const { open: openFiles, scanError: procScanError } = await openFileSet(candidates.map((candidate) => candidate.absPath));
  const gitTracked = await gitTrackedSet();

  const context = {
    nowMs: now.getTime(),
    minAgeMinutes: args.minAgeMinutes,
    existingScanRoots,
    protectedRoots,
    sourceRefs,
    openFiles,
    gitTracked,
  };

  const files = candidates.map((candidate) => classifyCandidate(candidate, context));
  const summary = summarize(files, rootErrors, procScanError);
  const baseManifest = {
    schema: MANIFEST_SCHEMA,
    generatedAt: now.toISOString(),
    mode: 'stage-only-no-delete',
    projectRoot,
    runtimeRoot,
    guardrails: {
      deterministicSortedPaths: true,
      deletionDefault: false,
      deleteRequiresManifest: true,
      deleteRequiresConfirmFlag: true,
      scanRootsAllowlisted: true,
      protectedRootsDenied: true,
      gitTrackedFilesBlocked: true,
      executableSourceReferencesBlocked: true,
      openProcessFilesBlocked: true,
      minAgeMinutes: args.minAgeMinutes,
      noMntC: true,
    },
    scanRoots: existingScanRoots.map(rel),
    protectedRoots: protectedRoots.map(rel),
    rootErrors,
    summary,
    files,
  };
  return { ...baseManifest, manifestSha256: manifestHash(baseManifest) };
}

function renderMarkdown(manifest, deleteResult = null) {
  const staged = manifest.files.filter((file) => file.stagedForDeletion);
  const blocked = manifest.files.filter((file) => !file.stagedForDeletion);
  const lines = [];
  lines.push('# Stickbot-TARS generated audio audit');
  lines.push('');
  lines.push(`Generated: ${manifest.generatedAt}`);
  lines.push(`Schema: \`${manifest.schema}\``);
  lines.push(`Classification: \`${manifest.summary.classification}\``);
  lines.push(`Manifest SHA256: \`${manifest.manifestSha256}\``);
  lines.push('');
  lines.push('## Summary');
  lines.push('');
  lines.push(`- files scanned: ${manifest.summary.fileCount}`);
  lines.push(`- staged for deletion: ${manifest.summary.stagedCount}`);
  lines.push(`- protected/skipped: ${manifest.summary.protectedSkippedCount ?? manifest.summary.blockedCount}`);
  lines.push(`- total bytes: ${manifest.summary.totalBytes}`);
  lines.push(`- staged bytes: ${manifest.summary.stagedBytes}`);
  lines.push(`- blocked bytes: ${manifest.summary.blockedBytes}`);
  lines.push(`- min age minutes: ${manifest.guardrails.minAgeMinutes}`);
  if (manifest.summary.procScanError) lines.push(`- proc scan error: ${manifest.summary.procScanError}`);
  if (deleteResult) {
    lines.push(`- delete classification: \`${deleteResult.classification}\``);
    lines.push(`- deleted files: ${deleteResult.deletedCount}`);
    lines.push(`- deleted bytes: ${deleteResult.deletedBytes}`);
  }
  lines.push('');
  lines.push('## Guardrails');
  lines.push('');
  lines.push('- Stage/audit mode never deletes files.');
  lines.push('- Delete mode requires `--delete --manifest <PASS manifest> --confirm-delete`.');
  lines.push('- Candidates must be under allowlisted generated-audio roots.');
  lines.push('- Git-tracked files, protected roots, executable source/script references, and open files are blocked.');
  lines.push('- Runtime speaker reference, models, tools, certs, source, tests, and app dependencies are never scan roots.');
  lines.push('');
  lines.push('## Scan roots');
  lines.push('');
  for (const root of manifest.scanRoots) lines.push(`- \`${root}\``);
  lines.push('');
  lines.push('## Staged files');
  lines.push('');
  if (!staged.length) lines.push('_None._');
  for (const file of staged) {
    lines.push(`- \`${file.path}\` (${file.sizeBytes} bytes, sha256 \`${file.sha256.slice(0, 16)}…\`)`);
  }
  lines.push('');
  lines.push('## Protected/skipped files');
  lines.push('');
  if (!blocked.length) lines.push('_None._');
  for (const file of blocked) {
    lines.push(`- \`${file.path}\` — ${file.blockers.join(', ') || 'blocked'}`);
  }
  lines.push('');
  return `${lines.join('\n').trimEnd()}\n`;
}

async function writeOutputs(manifest, args, markdown, deleteResult = null) {
  if (args.stdoutOnly) {
    if (args.mdOnly) process.stdout.write(markdown);
    else process.stdout.write(`${JSON.stringify(deleteResult ? { manifest, deleteResult } : manifest, null, 2)}\n`);
    return { json: null, markdown: null, latestJson: null, latestMarkdown: null };
  }

  const stamp = manifest.generatedAt.replace(/[:.]/g, '-');
  const baseDir = args.outputDir
    ? path.resolve(projectRoot, args.outputDir)
    : path.join(projectRoot, 'artifacts/generated-audio-audits', stamp);
  await fs.mkdir(baseDir, { recursive: true });
  const jsonPath = path.join(baseDir, deleteResult ? 'delete-result.json' : 'stage-manifest.json');
  const mdPath = path.join(baseDir, deleteResult ? 'delete-result.md' : 'stage-manifest.md');
  await fs.writeFile(jsonPath, `${JSON.stringify(deleteResult ? { manifest, deleteResult } : manifest, null, 2)}\n`);
  await fs.writeFile(mdPath, markdown);

  const latestJson = path.join(projectRoot, 'artifacts/generated-audio-audits/latest.json');
  const latestMarkdown = path.join(projectRoot, 'artifacts/generated-audio-audits/latest.md');
  await fs.mkdir(path.dirname(latestJson), { recursive: true });
  await fs.writeFile(latestJson, `${JSON.stringify(deleteResult ? { manifest, deleteResult } : manifest, null, 2)}\n`);
  await fs.writeFile(latestMarkdown, markdown);

  return {
    json: rel(jsonPath),
    markdown: rel(mdPath),
    latestJson: rel(latestJson),
    latestMarkdown: rel(latestMarkdown),
  };
}

async function readManifest(manifestPath) {
  const abs = path.resolve(projectRoot, manifestPath);
  const parsed = JSON.parse(await fs.readFile(abs, 'utf8'));
  if (parsed.schema !== MANIFEST_SCHEMA) throw new Error(`Manifest schema mismatch: ${parsed.schema}`);
  const { manifestSha256, ...withoutHash } = parsed;
  const actualHash = manifestHash(withoutHash);
  if (manifestSha256 !== actualHash) throw new Error(`Manifest hash mismatch: expected ${manifestSha256}, got ${actualHash}`);
  return parsed;
}

async function deleteFromManifest(args) {
  if (!args.manifest) throw new Error('--delete requires --manifest <path>');
  if (!args.confirmDelete) throw new Error('--delete requires --confirm-delete');
  const manifest = await readManifest(args.manifest);
  if (manifest.summary.classification !== PASS_STAGE) {
    throw new Error(`Refusing delete: manifest classification is ${manifest.summary.classification}, expected ${PASS_STAGE}`);
  }

  const staged = manifest.files.filter((file) => file.stagedForDeletion);
  const candidateAbsPaths = staged.map((file) => file.absolutePath);
  const { open: openFiles, scanError } = await openFileSet(candidateAbsPaths);
  if (scanError) throw new Error(`Refusing delete: ${scanError}`);

  const deleted = [];
  const refused = [];
  for (const file of staged) {
    const absPath = file.absolutePath;
    const reasons = [];
    if ((openFiles.get(absPath) || []).length > 0) reasons.push('OPEN_BY_PROCESS_AT_DELETE_TIME');
    try {
      const st = await fs.stat(absPath);
      const sha = await sha256File(absPath);
      if (st.size !== file.sizeBytes) reasons.push('SIZE_CHANGED');
      if (Math.trunc(st.mtimeMs) !== file.mtimeMs) reasons.push('MTIME_CHANGED');
      if (sha !== file.sha256) reasons.push('SHA256_CHANGED');
      const scanRoots = manifest.scanRoots.map((root) => path.resolve(projectRoot, root));
      if (!scanRoots.some((root) => isInside(absPath, root))) reasons.push('NO_LONGER_UNDER_MANIFEST_SCAN_ROOT');
      if (reasons.length) {
        refused.push({ path: file.path, reasons });
        continue;
      }
      await fs.unlink(absPath);
      deleted.push({ path: file.path, sizeBytes: file.sizeBytes, sha256: file.sha256 });
    } catch (error) {
      if (error.code === 'ENOENT') refused.push({ path: file.path, reasons: ['MISSING_AT_DELETE_TIME'] });
      else refused.push({ path: file.path, reasons: [`DELETE_ERROR:${error.code || error.message}`] });
    }
  }

  const deleteResult = {
    classification: refused.length ? HOLD : PASS_DELETE,
    deletedCount: deleted.length,
    deletedBytes: deleted.reduce((sum, file) => sum + file.sizeBytes, 0),
    refusedCount: refused.length,
    deleted,
    refused,
  };
  const markdown = renderMarkdown(manifest, deleteResult);
  const outputs = await writeOutputs(manifest, args, markdown, deleteResult);
  return { manifest, deleteResult, outputs };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.deleteMode) {
    const { deleteResult, outputs } = await deleteFromManifest(args);
    console.log(JSON.stringify({ classification: deleteResult.classification, ...deleteResult, outputs }, null, 2));
    process.exit(deleteResult.classification === PASS_DELETE ? 0 : 3);
  }

  const manifest = await buildAuditManifest(args);
  const markdown = renderMarkdown(manifest);
  const outputs = await writeOutputs(manifest, args, markdown);
  console.log(JSON.stringify({ classification: manifest.summary.classification, summary: manifest.summary, outputs }, null, 2));
  process.exit(manifest.summary.classification === PASS_STAGE ? 0 : 3);
}

main().catch((error) => {
  console.error(JSON.stringify({ classification: FAIL, error: error.message }, null, 2));
  process.exit(2);
});
