// OpenClaw Stickbot Work Lifecycle Ledger — M1 durable sidecar store
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { appendFile, mkdir, open, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { randomUUID } from 'node:crypto';

const TEXT_ENCODING = 'utf8';

export class WorkLedgerStoreError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkLedgerStoreError';
    this.code = code;
    this.details = details;
  }
}

export function createWorkLedgerPaths(rootDir, runId) {
  if (!rootDir || typeof rootDir !== 'string') {
    throw new WorkLedgerStoreError('INVALID_ROOT', 'rootDir must be a non-empty string');
  }
  if (!runId || typeof runId !== 'string') {
    throw new WorkLedgerStoreError('INVALID_RUN_ID', 'runId must be a non-empty string');
  }

  return {
    rootDir,
    runId,
    runPath: join(rootDir, 'runs', `${runId}.json`),
    eventPath: join(rootDir, 'events', `${runId}.jsonl`),
    notificationPath: join(rootDir, 'notifications', `${runId}.jsonl`),
    outboxDir: join(rootDir, 'outbox'),
    lockPath: join(rootDir, 'locks', `${runId}.lock`),
    activeRunsIndexPath: join(rootDir, 'indexes', 'active-runs.json')
  };
}

export async function ensureWorkLedgerDirs(rootDir) {
  const dirs = ['runs', 'events', 'notifications', 'outbox', 'locks', 'indexes'];
  await Promise.all(dirs.map((dir) => mkdir(join(rootDir, dir), { recursive: true })));
}

async function fsyncFile(path) {
  const handle = await open(path, 'r');
  try {
    await handle.sync();
  } finally {
    await handle.close();
  }
}

async function fsyncDirectory(path) {
  const handle = await open(path, 'r');
  try {
    await handle.sync();
  } catch (error) {
    // Some filesystems reject directory fsync. Preserve best-effort atomic rename semantics.
    if (!['EINVAL', 'EISDIR', 'ENOTSUP', 'EPERM'].includes(error?.code)) {
      throw error;
    }
  } finally {
    await handle.close();
  }
}

export async function atomicWriteJson(path, value) {
  const tmpPath = `${path}.tmp-${process.pid}-${Date.now()}-${randomUUID()}`;
  const content = `${JSON.stringify(value, null, 2)}\n`;

  try {
    await mkdir(dirname(path), { recursive: true });
    await writeFile(tmpPath, content, { encoding: TEXT_ENCODING, flag: 'wx' });
    await fsyncFile(tmpPath);
    await rename(tmpPath, path);
    await fsyncDirectory(dirname(path));
  } catch (error) {
    await rm(tmpPath, { force: true }).catch(() => {});
    throw new WorkLedgerStoreError('ATOMIC_WRITE_FAILED', `Failed atomic JSON write for ${path}`, {
      path,
      causeCode: error?.code,
      causeMessage: error?.message
    });
  }
}

export async function readJsonFile(path) {
  try {
    return JSON.parse(await readFile(path, TEXT_ENCODING));
  } catch (error) {
    throw new WorkLedgerStoreError('READ_JSON_FAILED', `Failed to read JSON file ${path}`, {
      path,
      causeCode: error?.code,
      causeMessage: error?.message
    });
  }
}

export async function writeRunSummary(rootDir, runRecord) {
  if (!runRecord?.run_id) {
    throw new WorkLedgerStoreError('INVALID_RUN_RECORD', 'runRecord.run_id is required');
  }
  const paths = createWorkLedgerPaths(rootDir, runRecord.run_id);
  await ensureWorkLedgerDirs(rootDir);
  await atomicWriteJson(paths.runPath, runRecord);
  return paths.runPath;
}

export async function readRunSummary(rootDir, runId) {
  const paths = createWorkLedgerPaths(rootDir, runId);
  return readJsonFile(paths.runPath);
}

export async function appendJsonLine(path, value) {
  await mkdir(dirname(path), { recursive: true });
  const line = `${JSON.stringify(value)}\n`;
  await appendFile(path, line, { encoding: TEXT_ENCODING });
}

export async function appendLifecycleEvent(rootDir, event) {
  if (!event?.run_id) {
    throw new WorkLedgerStoreError('INVALID_EVENT', 'event.run_id is required');
  }
  const paths = createWorkLedgerPaths(rootDir, event.run_id);
  await ensureWorkLedgerDirs(rootDir);
  await appendJsonLine(paths.eventPath, event);
  return paths.eventPath;
}

export async function readJsonLines(path, { quarantineCorrupt = false } = {}) {
  let text;
  try {
    text = await readFile(path, TEXT_ENCODING);
  } catch (error) {
    if (error?.code === 'ENOENT') {
      return [];
    }
    throw new WorkLedgerStoreError('READ_JSONL_FAILED', `Failed to read JSONL file ${path}`, {
      path,
      causeCode: error?.code,
      causeMessage: error?.message
    });
  }

  const records = [];
  const corrupt = [];
  const lines = text.split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    try {
      records.push(JSON.parse(line));
    } catch (error) {
      if (!quarantineCorrupt) {
        throw new WorkLedgerStoreError('CORRUPT_JSONL_LINE', `Corrupt JSONL line ${index + 1} in ${path}`, {
          path,
          lineNumber: index + 1,
          causeMessage: error?.message
        });
      }
      corrupt.push({ lineNumber: index + 1, line });
    }
  }

  if (quarantineCorrupt && corrupt.length > 0) {
    const quarantinePath = `${path}.corrupt-${Date.now()}.json`;
    await atomicWriteJson(quarantinePath, { path, corrupt });
  }

  return records;
}

export async function readLifecycleEvents(rootDir, runId, options = {}) {
  const paths = createWorkLedgerPaths(rootDir, runId);
  return readJsonLines(paths.eventPath, options);
}
