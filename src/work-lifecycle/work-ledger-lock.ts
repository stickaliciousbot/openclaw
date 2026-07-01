// OpenClaw Stickbot Work Lifecycle Ledger — M1 lock helper
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { mkdir, open, rm } from 'node:fs/promises';
import { dirname } from 'node:path';

export class WorkLedgerLockError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkLedgerLockError';
    this.code = code;
    this.details = details;
  }
}

export async function acquireWorkLedgerLock(lockPath, { staleMs = 0 } = {}) {
  await mkdir(dirname(lockPath), { recursive: true });
  const payload = JSON.stringify({ pid: process.pid, acquiredAt: new Date().toISOString() });

  try {
    const handle = await open(lockPath, 'wx');
    try {
      await handle.writeFile(`${payload}\n`, 'utf8');
      await handle.sync();
    } finally {
      await handle.close();
    }
    return createReleaseHandle(lockPath);
  } catch (error) {
    if (error?.code !== 'EEXIST') {
      throw new WorkLedgerLockError('LOCK_ACQUIRE_FAILED', `Failed to acquire lock ${lockPath}`, {
        lockPath,
        causeCode: error?.code,
        causeMessage: error?.message
      });
    }

    if (staleMs > 0) {
      // Stale lock reclamation is intentionally deferred until M2/M6. For M1, detect only.
      throw new WorkLedgerLockError('LOCK_EXISTS_STALE_CHECK_DEFERRED', `Lock exists and stale reclamation is deferred for ${lockPath}`, {
        lockPath,
        staleMs
      });
    }

    throw new WorkLedgerLockError('LOCK_EXISTS', `Lock already exists for ${lockPath}`, { lockPath });
  }
}

function createReleaseHandle(lockPath) {
  let released = false;
  return {
    lockPath,
    async release() {
      if (released) return false;
      released = true;
      await rm(lockPath, { force: true });
      return true;
    }
  };
}

export async function withWorkLedgerLock(lockPath, fn, options = {}) {
  const lock = await acquireWorkLedgerLock(lockPath, options);
  try {
    return await fn(lock);
  } finally {
    await lock.release();
  }
}
