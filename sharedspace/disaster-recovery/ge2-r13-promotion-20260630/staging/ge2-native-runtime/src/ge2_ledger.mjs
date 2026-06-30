import fs from 'node:fs/promises';
import path from 'node:path';

function nowIso() {
  return new Date().toISOString();
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJson(filePath, fallback) {
  if (!(await exists(filePath))) {
    return fallback;
  }

  const raw = await fs.readFile(filePath, 'utf-8');
  if (!raw.trim()) return fallback;

  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

async function writeJsonAtomic(filePath, value) {
  const tmp = `${filePath}.tmp-${process.pid}-${Date.now()}`;
  await fs.writeFile(tmp, JSON.stringify(value, null, 2) + '\n', 'utf-8');
  await fs.rename(tmp, filePath);
}

export class Ge2Ledger {
  constructor(options = {}) {
    this.rootDir = options.rootDir || './state/ge2-native';
    this.runsDir = path.join(this.rootDir, 'runs');
    this.runsIndexPath = path.join(this.rootDir, 'runs.index.json');
    this.runsJsonlPath = path.join(this.rootDir, 'runs.jsonl');
    this.milestonesPath = path.join(this.rootDir, 'milestones.jsonl');
    this.artifactsPath = path.join(this.rootDir, 'artifacts.jsonl');
    this.errorsPath = path.join(this.rootDir, 'errors.jsonl');
    this._writeQueue = Promise.resolve();
  }

  async ensure() {
    await fs.mkdir(this.rootDir, { recursive: true });
    await fs.mkdir(this.runsDir, { recursive: true });

    if (!(await exists(this.runsIndexPath))) {
      await writeJsonAtomic(this.runsIndexPath, {
        version: 1,
        updated_at: nowIso(),
        runs: []
      });
    }

    for (const p of [
      this.runsJsonlPath,
      this.milestonesPath,
      this.artifactsPath,
      this.errorsPath
    ]) {
      if (!(await exists(p))) {
        await fs.writeFile(p, '', 'utf-8');
      }
    }
  }

  async _enqueueWrite(operation) {
    this._writeQueue = this._writeQueue.then(operation, operation);
    return this._writeQueue;
  }

  async _appendJsonl(filePath, record) {
    await this.ensure();
    const line = JSON.stringify({ ...record, recorded_at: nowIso() }) + '\n';
    await this._enqueueWrite(() => fs.appendFile(filePath, line, 'utf-8'));
  }

  runPath(runId) {
    return path.join(this.runsDir, `${runId}.json`);
  }

  async getRun(runId) {
    await this.ensure();
    return readJson(this.runPath(runId), null);
  }

  async getLatestRun() {
    const runs = await this.listRuns(1);
    return runs[0] || null;
  }

  async listRuns(limit = 20) {
    await this.ensure();
    const index = await readJson(this.runsIndexPath, { runs: [] });
    const runs = Array.isArray(index.runs) ? index.runs : [];
    return runs.slice(0, Math.max(0, Number(limit) || 20));
  }

  async _upsertRunIndex(runSummary) {
    await this.ensure();
    await this._enqueueWrite(async () => {
      const index = await readJson(this.runsIndexPath, {
        version: 1,
        updated_at: nowIso(),
        runs: []
      });

      const runs = Array.isArray(index.runs) ? index.runs : [];
      const filtered = runs.filter((entry) => entry.run_id !== runSummary.run_id);
      filtered.unshift(runSummary);

      await writeJsonAtomic(this.runsIndexPath, {
        version: 1,
        updated_at: nowIso(),
        runs: filtered
      });
    });
  }

  async createRun(run) {
    await this.ensure();

    const fullRun = {
      run_id: run.run_id,
      status: run.status || 'accepted',
      task: run.task || null,
      origin: run.origin || {},
      requestId: run.requestId || null,
      started_at: run.started_at || nowIso(),
      updated_at: run.updated_at || nowIso(),
      milestones: Array.isArray(run.milestones) ? run.milestones : [],
      artifacts: Array.isArray(run.artifacts) ? run.artifacts : [],
      errors: Array.isArray(run.errors) ? run.errors : [],
      cancel_requested: Boolean(run.cancel_requested)
    };

    await this._enqueueWrite(async () => {
      await writeJsonAtomic(this.runPath(fullRun.run_id), fullRun);
    });

    await this._upsertRunIndex({
      run_id: fullRun.run_id,
      status: fullRun.status,
      task: fullRun.task,
      started_at: fullRun.started_at,
      updated_at: fullRun.updated_at,
      artifacts_count: fullRun.artifacts.length,
      milestones_count: fullRun.milestones.length,
      errors_count: fullRun.errors.length,
      cancel_requested: fullRun.cancel_requested
    });

    await this._appendJsonl(this.runsJsonlPath, {
      type: 'run_created',
      run_id: fullRun.run_id,
      status: fullRun.status,
      task: fullRun.task
    });

    return fullRun;
  }

  async updateRun(runId, patch) {
    await this.ensure();

    const existing = await this.getRun(runId);
    if (!existing) {
      throw new Error(`Run not found: ${runId}`);
    }

    const next = {
      ...existing,
      ...patch,
      run_id: existing.run_id,
      updated_at: nowIso(),
      milestones: Array.isArray(patch?.milestones)
        ? patch.milestones
        : existing.milestones,
      artifacts: Array.isArray(patch?.artifacts)
        ? patch.artifacts
        : existing.artifacts,
      errors: Array.isArray(patch?.errors) ? patch.errors : existing.errors
    };

    await this._enqueueWrite(async () => {
      await writeJsonAtomic(this.runPath(runId), next);
    });

    await this._upsertRunIndex({
      run_id: next.run_id,
      status: next.status,
      task: next.task,
      started_at: next.started_at,
      updated_at: next.updated_at,
      artifacts_count: next.artifacts.length,
      milestones_count: next.milestones.length,
      errors_count: next.errors.length,
      cancel_requested: Boolean(next.cancel_requested)
    });

    await this._appendJsonl(this.runsJsonlPath, {
      type: 'run_updated',
      run_id: next.run_id,
      status: next.status,
      cancel_requested: Boolean(next.cancel_requested)
    });

    return next;
  }

  async appendMilestone(runId, milestoneRecord) {
    const run = await this.getRun(runId);
    if (!run) {
      throw new Error(`Run not found: ${runId}`);
    }

    const milestones = [...run.milestones, milestoneRecord];
    await this.updateRun(runId, { milestones });

    await this._appendJsonl(this.milestonesPath, {
      run_id: runId,
      ...milestoneRecord
    });

    return milestoneRecord;
  }

  async appendArtifact(runId, artifactRecord) {
    const run = await this.getRun(runId);
    if (!run) {
      throw new Error(`Run not found: ${runId}`);
    }

    const artifacts = [...run.artifacts, artifactRecord];
    await this.updateRun(runId, { artifacts });

    await this._appendJsonl(this.artifactsPath, {
      run_id: runId,
      ...artifactRecord
    });

    return artifactRecord;
  }

  async appendError(runId, errorRecord) {
    const run = await this.getRun(runId);
    if (!run) {
      throw new Error(`Run not found: ${runId}`);
    }

    const errors = [...run.errors, errorRecord];
    await this.updateRun(runId, { errors });

    await this._appendJsonl(this.errorsPath, {
      run_id: runId,
      ...errorRecord
    });

    return errorRecord;
  }

  async listArtifacts(runId) {
    const run = await this.getRun(runId);
    return run?.artifacts || [];
  }

  async requestCancel(runId) {
    const run = await this.getRun(runId);
    if (!run) return null;

    return this.updateRun(runId, {
      cancel_requested: true
    });
  }

  async isCancelRequested(runId) {
    const run = await this.getRun(runId);
    return Boolean(run?.cancel_requested);
  }
}
