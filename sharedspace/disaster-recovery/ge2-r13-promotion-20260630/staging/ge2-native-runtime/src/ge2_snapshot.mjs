import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

function isoStamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

async function exists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

export async function snapshotBeforeWrite(targetPath, snapshotRoot) {
  await fs.mkdir(snapshotRoot, { recursive: true });

  const hasTarget = await exists(targetPath);
  if (!hasTarget) {
    return {
      target: targetPath,
      backup: null,
      action: 'created'
    };
  }

  const backupName = `${path.basename(targetPath)}.${isoStamp()}.bak`;
  const backupPath = path.join(snapshotRoot, backupName);
  await fs.copyFile(targetPath, backupPath);

  const digest = crypto
    .createHash('sha256')
    .update(await fs.readFile(backupPath))
    .digest('hex');

  return {
    target: targetPath,
    backup: backupPath,
    action: 'modified',
    backup_sha256: digest
  };
}

export async function writeSnapshotManifest(manifestPath, manifest) {
  const dir = path.dirname(manifestPath);
  await fs.mkdir(dir, { recursive: true });
  const payload = {
    manifest_id: manifest.manifest_id || crypto.randomUUID(),
    created_at: manifest.created_at || new Date().toISOString(),
    changes: Array.isArray(manifest.changes) ? manifest.changes : []
  };
  await fs.writeFile(manifestPath, JSON.stringify(payload, null, 2) + '\n', 'utf-8');
  return payload;
}
