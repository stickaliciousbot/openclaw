import crypto from 'node:crypto';
import path from 'node:path';
import { Ge2Ledger } from './ge2_ledger.mjs';
import { Ge2Runtime, Ge2CancelledError } from './ge2_runtime.mjs';
import {
  createMilestone,
  GE2_MILESTONES,
  isValidMilestone
} from './ge2_milestones.mjs';

function nowIso() {
  return new Date().toISOString();
}

function runId() {
  const stamp = nowIso().replace(/[-:TZ.]/g, '').slice(0, 14);
  return `ge2-${stamp}-${crypto.randomUUID().slice(0, 8)}`;
}

export class Ge2Dispatcher {
  constructor(options = {}) {
    const stateDir = options.stateDir || './state/ge2-native';
    const artifactDir =
      options.artifactDir || path.join(stateDir, 'artifacts');

    this.ledger = options.ledger || new Ge2Ledger({ rootDir: stateDir });
    this.runtime =
      options.runtime || new Ge2Runtime({ ledger: this.ledger, artifactDir });
    this.activeRuns = new Map();
  }

  async dispatch(envelope) {
    if (!envelope || envelope.command !== 'ge2') {
      throw new Error('Invalid GE2 envelope');
    }

    switch (envelope.subcommand) {
      case 'run':
        return this.run(envelope);
      case 'status':
        return this.status(envelope.args?.run_id || null);
      case 'artifacts':
        return this.artifacts(envelope.args?.run_id || null);
      case 'cancel':
        return this.cancel(envelope.args?.run_id || null);
      case 'help':
        return { ok: true, kind: 'help' };
      default:
        throw new Error(`Unsupported GE2 subcommand: ${envelope.subcommand}`);
    }
  }

  async run(envelope) {
    const task = String(envelope.args?.task || '').trim();
    if (!task) {
      return {
        ok: false,
        kind: 'error',
        error: {
          code: 'MISSING_TASK',
          message: 'Task is required for /ge2 run.'
        }
      };
    }

    const id = runId();
    const run = await this.ledger.createRun({
      run_id: id,
      status: GE2_MILESTONES.ACCEPTED,
      task,
      origin: envelope.origin || {},
      requestId: envelope.requestId || null,
      started_at: nowIso(),
      updated_at: nowIso(),
      milestones: [],
      artifacts: [],
      errors: []
    });

    const emitMilestone = async (milestone) => {
      if (!isValidMilestone(milestone.milestone)) {
        throw new Error(`Invalid milestone: ${milestone.milestone}`);
      }

      await this.ledger.appendMilestone(run.run_id, milestone);
      await this.ledger.updateRun(run.run_id, {
        status: milestone.milestone
      });
    };

    await emitMilestone(
      createMilestone(GE2_MILESTONES.ACCEPTED, 'Run accepted by dispatcher')
    );
    await emitMilestone(
      createMilestone(
        GE2_MILESTONES.VALIDATED,
        'Command validated and queued for execution'
      )
    );

    const controller = new AbortController();
    const runtimePromise = this.#runInBackground({
      run,
      controller,
      emitMilestone
    });

    this.activeRuns.set(run.run_id, {
      controller,
      runtimePromise,
      started_at: nowIso()
    });

    runtimePromise.finally(() => {
      this.activeRuns.delete(run.run_id);
    });

    return {
      ok: true,
      kind: 'run_accepted',
      run_id: run.run_id,
      status: GE2_MILESTONES.ACCEPTED,
      task,
      started_at: run.started_at
    };
  }

  async #runInBackground({ run, controller, emitMilestone }) {
    try {
      const runtimeResult = await this.runtime.executeRun(run, {
        emitMilestone,
        signal: controller.signal
      });

      for (const artifact of runtimeResult.artifacts || []) {
        await this.ledger.appendArtifact(run.run_id, artifact);
      }

      await emitMilestone(
        createMilestone(GE2_MILESTONES.COMPLETED, 'Run completed successfully')
      );
    } catch (error) {
      if (error instanceof Ge2CancelledError) {
        await emitMilestone(
          createMilestone(GE2_MILESTONES.CANCELLED, error.message)
        );
        return;
      }

      const message = error instanceof Error ? error.message : String(error);
      await this.ledger.appendError(run.run_id, {
        code: 'RUNTIME_ERROR',
        message,
        at: nowIso()
      });

      await emitMilestone(
        createMilestone(GE2_MILESTONES.FAILED, message)
      );
    }
  }

  async status(runId) {
    const run = runId
      ? await this.ledger.getRun(runId)
      : await this.ledger.getLatestRun();

    if (!run) {
      return {
        ok: false,
        kind: 'not_found',
        error: {
          code: 'RUN_NOT_FOUND',
          message: runId
            ? `Run not found: ${runId}`
            : 'No GE2 runs found in ledger.'
        }
      };
    }

    return {
      ok: true,
      kind: 'status',
      run
    };
  }

  async artifacts(runId) {
    const id = String(runId || '').trim();
    if (!id) {
      return {
        ok: false,
        kind: 'error',
        error: {
          code: 'MISSING_RUN_ID',
          message: 'run_id is required for /ge2 artifacts.'
        }
      };
    }

    const run = await this.ledger.getRun(id);
    if (!run) {
      return {
        ok: false,
        kind: 'not_found',
        error: {
          code: 'RUN_NOT_FOUND',
          message: `Run not found: ${id}`
        }
      };
    }

    return {
      ok: true,
      kind: 'artifacts',
      run_id: id,
      artifacts: run.artifacts || []
    };
  }

  async cancel(runId) {
    const id = String(runId || '').trim();
    if (!id) {
      return {
        ok: false,
        kind: 'error',
        error: {
          code: 'MISSING_RUN_ID',
          message: 'run_id is required for /ge2 cancel.'
        }
      };
    }

    const run = await this.ledger.requestCancel(id);
    if (!run) {
      return {
        ok: false,
        kind: 'not_found',
        error: {
          code: 'RUN_NOT_FOUND',
          message: `Run not found: ${id}`
        }
      };
    }

    const active = this.activeRuns.get(id);
    if (active?.controller && !active.controller.signal.aborted) {
      active.controller.abort();
    }

    return {
      ok: true,
      kind: 'cancel_requested',
      run_id: id,
      status: run.status,
      cancel_requested: true
    };
  }
}

const GE2_DISPATCHER_SINGLETON = Symbol.for('openclaw.ge2.dispatcher');

export function resolveGe2Dispatcher(options = {}) {
  const globalScope = globalThis;
  if (!globalScope[GE2_DISPATCHER_SINGLETON]) {
    globalScope[GE2_DISPATCHER_SINGLETON] = new Ge2Dispatcher(options);
  }
  return globalScope[GE2_DISPATCHER_SINGLETON];
}
