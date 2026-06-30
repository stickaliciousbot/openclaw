import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

function sanitizeName(name) {
  return String(name || 'artifact.bin').replace(/[^a-zA-Z0-9._-]/g, '_');
}

export async function sha256File(filePath) {
  const data = await fs.readFile(filePath);
  return crypto.createHash('sha256').update(data).digest('hex');
}

export async function writeArtifact(options = {}) {
  const baseDir = String(options.baseDir || './state/ge2/artifacts');
  const runId = String(options.runId || '').trim();
  const name = sanitizeName(options.name || 'artifact.json');
  const contentType = options.contentType || 'application/json';

  if (!runId) {
    throw new Error('writeArtifact requires runId');
  }

  const runDir = path.join(baseDir, runId);
  await fs.mkdir(runDir, { recursive: true });

  const filePath = path.join(runDir, name);
  const bytes = Buffer.isBuffer(options.content)
    ? options.content
    : Buffer.from(
        typeof options.content === 'string'
          ? options.content
          : JSON.stringify(options.content ?? null, null, 2),
        'utf-8'
      );

  await fs.writeFile(filePath, bytes);

  const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');

  return {
    kind: options.kind || 'artifact',
    run_id: runId,
    name,
    path: filePath,
    sha256,
    size: bytes.length,
    contentType,
    created_at: new Date().toISOString()
  };
}
