import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { acquireWorkLedgerLock, withWorkLedgerLock } from './work-ledger-lock.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-ledger-lock-test-'));
}

test('acquireWorkLedgerLock serializes concurrent writers', async () => {
  const root = await tempRoot();
  try {
    const lockPath = join(root, 'locks', 'work.lock');
    const lock = await acquireWorkLedgerLock(lockPath);
    await assert.rejects(() => acquireWorkLedgerLock(lockPath), /Lock already exists/);
    assert.equal(await lock.release(), true);
    assert.equal(await lock.release(), false);
    const reacquired = await acquireWorkLedgerLock(lockPath);
    assert.equal(await reacquired.release(), true);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('withWorkLedgerLock releases lock after callback failure', async () => {
  const root = await tempRoot();
  try {
    const lockPath = join(root, 'locks', 'work.lock');
    await assert.rejects(
      () => withWorkLedgerLock(lockPath, async () => {
        throw new Error('boom');
      }),
      /boom/
    );
    const lock = await acquireWorkLedgerLock(lockPath);
    assert.equal(await lock.release(), true);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
