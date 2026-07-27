import { enqueueCommandInLane } from "../../process/command-queue.js";
import { CommandLane } from "../../process/lanes.js";
import { normalizeLowercaseStringOrEmpty } from "../../shared/string-coerce.js";
import {
  completeTaskRunByRunId,
  createRunningTaskRun,
  failTaskRunByRunId,
} from "../../tasks/detached-task-runtime.js";
import { createCronRunDiagnosticsFromError } from "../run-diagnostics.js";
import { createCronExecutionId } from "../run-id.js";
import type { CronJob, CronJobCreate, CronJobPatch } from "../types.js";
import {
  assertAuthorizedGuardedUpdateCaller,
  assertGuardedUpdateApproval,
  computeCronJobDefinitionSha,
  computeGuardedUpdateRequestDigest,
  normalizeGuardedUpdateInternalCommand,
  snapshotGuardedJobState,
} from "./guarded-update.js";
import {
  applyJobPatch,
  assertSupportedJobSpec,
  computeJobNextRunAtMs,
  createJob,
  findJobOrThrow,
  hasScheduledNextRunAtMs,
  isJobEnabled,
  isJobDue,
  nextWakeAtMs,
  recomputeNextRuns,
  recomputeNextRunsForMaintenance,
} from "./jobs.js";
import type {
  CronJobsEnabledFilter,
  CronJobsSortBy,
  CronListPageOptions,
  CronListPageResult,
  CronSortDir,
} from "./list-page-types.js";
import { locked } from "./locked.js";
import type {
  GuardedCronInternalCommand,
  CronGuardedUpdateReceipt,
  CronGuardedUpdateRequest,
  CronGuardedUpdateResult,
  CronServiceState,
} from "./state.js";
import { ensureLoaded, persist, warnIfDisabled } from "./store.js";
import {
  applyJobResult,
  armTimer,
  emit,
  executeJobCoreWithTimeout,
  normalizeCronRunErrorText,
  runMissedJobs,
  stopTimer,
  wake,
} from "./timer.js";

const STARTUP_INTERRUPTED_ERROR = "cron: job interrupted by gateway restart";

type GuardedUpdateTestHooks = {
  failPersistBeforeWriteOnce?: boolean;
  failPostconditionAfterWriteOnce?: boolean;
  failReloadVerificationOnce?: boolean;
  failRollbackPersistOnce?: boolean;
};

let guardedUpdateTestHooks: GuardedUpdateTestHooks | undefined;

export function setGuardedUpdateTestHooksForTest(hooks?: GuardedUpdateTestHooks): void {
  guardedUpdateTestHooks = hooks;
}

function consumeGuardedUpdateTestHook(name: keyof GuardedUpdateTestHooks): boolean {
  if (guardedUpdateTestHooks?.[name] !== true) {
    return false;
  }
  guardedUpdateTestHooks[name] = false;
  return true;
}

type InterruptedStartupRun = {
  jobId: string;
  runAtMs: number;
  durationMs: number;
};

function markInterruptedStartupRun(params: {
  state: CronServiceState;
  job: CronJob;
  runningAtMs: number;
  nowMs: number;
}): InterruptedStartupRun {
  const { job, runningAtMs, nowMs } = params;
  const previousErrors =
    typeof job.state.consecutiveErrors === "number" && Number.isFinite(job.state.consecutiveErrors)
      ? Math.max(0, Math.floor(job.state.consecutiveErrors))
      : 0;

  params.state.deps.log.warn(
    { jobId: job.id, runningAtMs },
    "cron: marking interrupted running job failed on startup",
  );

  job.state.runningAtMs = undefined;
  job.state.lastRunAtMs = runningAtMs;
  job.state.lastRunStatus = "error";
  job.state.lastStatus = "error";
  job.state.lastError = STARTUP_INTERRUPTED_ERROR;
  job.state.lastDurationMs = Math.max(0, nowMs - runningAtMs);
  job.state.consecutiveErrors = previousErrors + 1;
  job.state.lastDelivered = false;
  job.state.lastDeliveryStatus = "unknown";
  job.state.lastDeliveryError = STARTUP_INTERRUPTED_ERROR;
  job.state.nextRunAtMs = undefined;
  job.updatedAtMs = nowMs;

  if (job.schedule.kind === "at") {
    job.enabled = false;
  }

  return {
    jobId: job.id,
    runAtMs: runningAtMs,
    durationMs: job.state.lastDurationMs,
  };
}

function mergeManualRunSnapshotAfterReload(params: {
  state: CronServiceState;
  jobId: string;
  snapshot: {
    enabled: boolean;
    updatedAtMs: number;
    state: CronJob["state"];
  } | null;
  removed: boolean;
}) {
  if (!params.state.store) {
    return;
  }
  if (params.removed) {
    params.state.store.jobs = params.state.store.jobs.filter((job) => job.id !== params.jobId);
    return;
  }
  if (!params.snapshot) {
    return;
  }
  const reloaded = params.state.store.jobs.find((job) => job.id === params.jobId);
  if (!reloaded) {
    return;
  }
  reloaded.enabled = params.snapshot.enabled;
  reloaded.updatedAtMs = params.snapshot.updatedAtMs;
  reloaded.state = params.snapshot.state;
}

async function ensureLoadedForRead(state: CronServiceState) {
  await ensureLoaded(state, { skipRecompute: true });
  if (!state.store) {
    return;
  }
  // Use the maintenance-only version so that read-only operations never
  // advance a past-due nextRunAtMs without executing the job (#16156).
  const changed = recomputeNextRunsForMaintenance(state);
  if (changed) {
    await persist(state);
  }
}

export async function start(state: CronServiceState) {
  if (!state.deps.cronEnabled) {
    state.deps.log.info({ enabled: false }, "cron: disabled");
    return;
  }

  const interruptedJobIds = new Set<string>();
  const interruptedRuns: InterruptedStartupRun[] = [];
  let markedAnyInterruptedRun = false;
  await locked(state, async () => {
    await ensureLoaded(state, { skipRecompute: true });
    const jobs = state.store?.jobs ?? [];
    for (const job of jobs) {
      job.state ??= {};
      if (typeof job.state.runningAtMs === "number") {
        const nowMs = state.deps.nowMs();
        const interrupted = markInterruptedStartupRun({
          state,
          job,
          runningAtMs: job.state.runningAtMs,
          nowMs,
        });
        interruptedJobIds.add(job.id);
        interruptedRuns.push(interrupted);
        markedAnyInterruptedRun = true;
      }
    }
    if (markedAnyInterruptedRun || jobs.length > 0) {
      await persist(state, markedAnyInterruptedRun ? undefined : { stateOnly: true });
    }
  });

  await runMissedJobs(state, {
    skipJobIds: interruptedJobIds.size > 0 ? interruptedJobIds : undefined,
    deferAgentTurnJobs: true,
  });

  await locked(state, async () => {
    // Startup catch-up already persisted the latest in-memory store state, and
    // this path runs before the scheduler begins servicing regular timer ticks.
    // Avoid an extra reload/write cycle on startup.
    await ensureLoaded(state, { skipRecompute: true });
    const changed = recomputeNextRunsForMaintenance(state, { recomputeExpired: true });
    if (changed) {
      await persist(state);
    }
    for (const interrupted of interruptedRuns) {
      const job = state.store?.jobs.find((entry) => entry.id === interrupted.jobId);
      emit(state, {
        jobId: interrupted.jobId,
        action: "finished",
        job,
        status: "error",
        error: STARTUP_INTERRUPTED_ERROR,
        delivered: false,
        deliveryStatus: "unknown",
        deliveryError: STARTUP_INTERRUPTED_ERROR,
        runAtMs: interrupted.runAtMs,
        durationMs: interrupted.durationMs,
        nextRunAtMs: job?.state.nextRunAtMs,
      });
    }
    armTimer(state);
    state.deps.log.info(
      {
        enabled: true,
        jobs: state.store?.jobs.length ?? 0,
        nextWakeAtMs: nextWakeAtMs(state) ?? null,
      },
      "cron: started",
    );
  });
}

export function stop(state: CronServiceState) {
  stopTimer(state);
}

export async function status(state: CronServiceState) {
  return await locked(state, async () => {
    await ensureLoadedForRead(state);
    return {
      enabled: state.deps.cronEnabled,
      storePath: state.deps.storePath,
      jobs: state.store?.jobs.length ?? 0,
      nextWakeAtMs: state.deps.cronEnabled ? (nextWakeAtMs(state) ?? null) : null,
    };
  });
}

export async function list(state: CronServiceState, opts?: { includeDisabled?: boolean }) {
  return await locked(state, async () => {
    await ensureLoadedForRead(state);
    const includeDisabled = opts?.includeDisabled === true;
    const jobs = (state.store?.jobs ?? []).filter((j) => includeDisabled || isJobEnabled(j));
    return jobs.toSorted((a, b) => (a.state.nextRunAtMs ?? 0) - (b.state.nextRunAtMs ?? 0));
  });
}

function resolveEnabledFilter(opts?: CronListPageOptions): CronJobsEnabledFilter {
  if (opts?.enabled === "all" || opts?.enabled === "enabled" || opts?.enabled === "disabled") {
    return opts.enabled;
  }
  return opts?.includeDisabled ? "all" : "enabled";
}

function sortJobs(jobs: CronJob[], sortBy: CronJobsSortBy, sortDir: CronSortDir) {
  const dir = sortDir === "desc" ? -1 : 1;
  return jobs.toSorted((a, b) => {
    let cmp = 0;
    if (sortBy === "name") {
      const aName = typeof a.name === "string" ? a.name : "";
      const bName = typeof b.name === "string" ? b.name : "";
      cmp = aName.localeCompare(bName, undefined, { sensitivity: "base" });
    } else if (sortBy === "updatedAtMs") {
      cmp = a.updatedAtMs - b.updatedAtMs;
    } else {
      const aNext = a.state.nextRunAtMs;
      const bNext = b.state.nextRunAtMs;
      if (typeof aNext === "number" && typeof bNext === "number") {
        cmp = aNext - bNext;
      } else if (typeof aNext === "number") {
        cmp = -1;
      } else if (typeof bNext === "number") {
        cmp = 1;
      } else {
        cmp = 0;
      }
    }
    if (cmp !== 0) {
      return cmp * dir;
    }
    const aId = typeof a.id === "string" ? a.id : "";
    const bId = typeof b.id === "string" ? b.id : "";
    return aId.localeCompare(bId);
  });
}

export async function listPage(state: CronServiceState, opts?: CronListPageOptions) {
  return await locked(state, async () => {
    await ensureLoadedForRead(state);
    const query = normalizeLowercaseStringOrEmpty(opts?.query);
    const enabledFilter = resolveEnabledFilter(opts);
    const sortBy = opts?.sortBy ?? "nextRunAtMs";
    const sortDir = opts?.sortDir ?? "asc";
    const source = state.store?.jobs ?? [];
    const filtered = source.filter((job) => {
      if (enabledFilter === "enabled" && !isJobEnabled(job)) {
        return false;
      }
      if (enabledFilter === "disabled" && isJobEnabled(job)) {
        return false;
      }
      if (!query) {
        return true;
      }
      const haystack = normalizeLowercaseStringOrEmpty(
        [job.name, job.description ?? "", job.agentId ?? ""].join(" "),
      );
      return haystack.includes(query);
    });
    const sorted = sortJobs(filtered, sortBy, sortDir);
    const total = sorted.length;
    const offset = Math.max(0, Math.min(total, Math.floor(opts?.offset ?? 0)));
    const defaultLimit = total === 0 ? 50 : total;
    const limit = Math.max(1, Math.min(200, Math.floor(opts?.limit ?? defaultLimit)));
    const jobs = sorted.slice(offset, offset + limit);
    const nextOffset = offset + jobs.length;
    return {
      jobs,
      total,
      offset,
      limit,
      hasMore: nextOffset < total,
      nextOffset: nextOffset < total ? nextOffset : null,
    } satisfies CronListPageResult;
  });
}

export async function add(state: CronServiceState, input: CronJobCreate) {
  return await locked(state, async () => {
    warnIfDisabled(state, "add");
    await ensureLoaded(state);
    const job = createJob(state, input);
    state.store?.jobs.push(job);

    // Defensive: recompute all next-run times to ensure consistency
    recomputeNextRuns(state);

    await persist(state);
    armTimer(state);

    state.deps.log.info(
      {
        jobId: job.id,
        jobName: job.name,
        nextRunAtMs: job.state.nextRunAtMs,
        schedulerNextWakeAtMs: nextWakeAtMs(state) ?? null,
        timerArmed: state.timer !== null,
        cronEnabled: state.deps.cronEnabled,
      },
      "cron: job added",
    );

    emit(state, {
      jobId: job.id,
      action: "added",
      job,
      nextRunAtMs: job.state.nextRunAtMs,
    });
    return job;
  });
}

async function updateLoadedJobCore(state: CronServiceState, id: string, patch: CronJobPatch) {
  const job = findJobOrThrow(state, id);
  const now = state.deps.nowMs();
  const nextJob = structuredClone(job);
  applyJobPatch(nextJob, patch, { defaultAgentId: state.deps.defaultAgentId });
  if (nextJob.schedule.kind === "every") {
    const anchor = nextJob.schedule.anchorMs;
    if (typeof anchor !== "number" || !Number.isFinite(anchor)) {
      const patchSchedule = patch.schedule;
      const fallbackAnchorMs =
        patchSchedule?.kind === "every"
          ? now
          : typeof nextJob.createdAtMs === "number" && Number.isFinite(nextJob.createdAtMs)
            ? nextJob.createdAtMs
            : now;
      nextJob.schedule = {
        ...nextJob.schedule,
        anchorMs: Math.max(0, Math.floor(fallbackAnchorMs)),
      };
    }
  }
  const scheduleChanged = patch.schedule !== undefined;
  const enabledChanged = patch.enabled !== undefined;

  if (scheduleChanged && nextJob.schedule.kind === "cron" && !isJobEnabled(nextJob)) {
    computeJobNextRunAtMs({ ...nextJob, enabled: true }, now);
  }

  nextJob.updatedAtMs = now;
  if (scheduleChanged || enabledChanged) {
    if (isJobEnabled(nextJob)) {
      nextJob.state.nextRunAtMs = computeJobNextRunAtMs(nextJob, now);
    } else {
      nextJob.state.nextRunAtMs = undefined;
      nextJob.state.runningAtMs = undefined;
    }
  } else if (isJobEnabled(nextJob) && !hasScheduledNextRunAtMs(nextJob.state.nextRunAtMs)) {
    nextJob.state.nextRunAtMs = computeJobNextRunAtMs(nextJob, now);
  }

  if (state.store) {
    const index = state.store.jobs.findIndex((entry) => entry.id === id);
    if (index >= 0) {
      state.store.jobs[index] = nextJob;
    }
  }

  await persist(state);
  armTimer(state);
  emit(state, {
    jobId: id,
    action: "updated",
    job: nextJob,
    nextRunAtMs: nextJob.state.nextRunAtMs,
  });
  return nextJob;
}

export async function update(state: CronServiceState, id: string, patch: CronJobPatch) {
  return await locked(state, async () => {
    warnIfDisabled(state, "update");
    await ensureLoaded(state, { skipRecompute: true });
    return await updateLoadedJobCore(state, id, patch);
  });
}

function verifyGuardedPreconditions(params: {
  job: CronJob;
  request: CronGuardedUpdateRequest;
  currentDefinitionSha: string;
}) {
  if (params.job.id !== params.request.jobId) {
    throw new Error("cron guarded update immutable job id mismatch");
  }
  if (params.job.enabled !== params.request.preconditions.expectedEnabled) {
    throw new Error("cron guarded update precondition failed: expected_enabled mismatch");
  }
  const revision = String(params.job.updatedAtMs);
  if (
    params.request.preconditions.expectedRevision !== undefined &&
    params.request.preconditions.expectedRevision !== revision
  ) {
    throw new Error("cron guarded update precondition failed: expected_revision mismatch");
  }
  if (params.request.preconditions.expectedDefinitionSha !== params.currentDefinitionSha) {
    throw new Error("cron guarded update precondition failed: expected_definition_sha mismatch");
  }
  if (typeof params.job.state.runningAtMs === "number") {
    throw new Error("cron guarded update rejected: job is currently running");
  }
  if (
    params.request.executionPolicy.runImmediately !== false ||
    params.request.executionPolicy.catchUp !== false
  ) {
    throw new Error("cron guarded update requires no-run/no-catch-up execution policy");
  }
}

function createPredictedGuardedAfter(params: {
  before: CronJob;
  request: CronGuardedUpdateRequest;
  now: number;
}) {
  const predicted = structuredClone(params.before);
  predicted.enabled = params.request.patch.enabled;
  predicted.updatedAtMs = params.now;
  if (predicted.enabled) {
    predicted.state.nextRunAtMs = computeJobNextRunAtMs(predicted, params.now);
  } else {
    predicted.state.nextRunAtMs = undefined;
    predicted.state.runningAtMs = undefined;
  }
  return predicted;
}

function createGuardedReceipt(params: {
  request: CronGuardedUpdateRequest;
  caller: GuardedCronInternalCommand["caller"];
  approval?: GuardedCronInternalCommand["approval"];
  requestDigest: string;
  before: CronJob;
  predictedAfter: CronJob;
  after?: CronJob;
  dryRun: boolean;
  changed: boolean;
  now: number;
  persistenceCompleted?: boolean;
  reloadVerification?: boolean;
  rollbackAttempted?: boolean;
  rollbackCompleted?: boolean;
  finalDurableState?: CronGuardedUpdateReceipt["finalDurableState"];
}): CronGuardedUpdateReceipt {
  const beforeSnapshot = snapshotGuardedJobState(params.before);
  const predictedAfterSnapshot = snapshotGuardedJobState(params.predictedAfter);
  const afterSnapshot = params.after ? snapshotGuardedJobState(params.after) : undefined;
  const terminal = params.dryRun
    ? params.changed
      ? "CRON_UPDATE_VALIDATION_PASS"
      : "CRON_UPDATE_VALIDATION_IDEMPOTENT"
    : params.changed
      ? "CRON_UPDATE_APPLIED"
      : "CRON_UPDATE_ALREADY_DESIRED_STATE";
  const finalSnapshot = afterSnapshot ?? predictedAfterSnapshot;
  const rollbackRequest: CronGuardedUpdateRequest | undefined = params.dryRun
    ? undefined
    : {
        jobId: params.request.jobId,
        patch: { enabled: params.before.enabled },
        preconditions: {
          expectedEnabled: finalSnapshot.enabled,
          expectedRevision: finalSnapshot.revision,
          expectedDefinitionSha: finalSnapshot.definitionSha,
        },
        executionPolicy: { runImmediately: false, catchUp: false },
        reason: `rollback guarded cron update ${params.requestDigest}`,
      };
  return {
    schema: params.dryRun
      ? "stickbot.openclaw.cron-update-validation-receipt.v1"
      : "stickbot.openclaw.cron-update-receipt.v1",
    terminal,
    gatewayMethod: params.dryRun ? "cron.validate_update" : "cron.guarded_update",
    jobId: params.request.jobId,
    requestDigest: params.requestDigest,
    caller: params.caller,
    approval: params.dryRun ? undefined : params.approval,
    before: beforeSnapshot,
    predictedAfter: predictedAfterSnapshot,
    after: afterSnapshot,
    preconditions: params.request.preconditions,
    preconditionResults: {
      expectedEnabled: true,
      expectedRevision:
        params.request.preconditions.expectedRevision === undefined ? undefined : true,
      expectedDefinitionSha: true,
    },
    changedFields: params.changed ? ["enabled"] : [],
    preservedFieldDigestBefore: beforeSnapshot.definitionSha,
    preservedFieldDigestAfter: finalSnapshot.definitionSha,
    nonTargetFieldDigestBefore: beforeSnapshot.definitionSha,
    nonTargetFieldDigestAfter: finalSnapshot.definitionSha,
    definitionShaBefore: beforeSnapshot.definitionSha,
    definitionShaAfter: finalSnapshot.definitionSha,
    revisionBefore: beforeSnapshot.revision,
    revisionAfter: finalSnapshot.revision,
    mutation: !params.dryRun && params.changed,
    persistenceCompleted: params.persistenceCompleted === true,
    reloadVerification: params.reloadVerification === true,
    rollbackAttempted: params.rollbackAttempted === true,
    rollbackCompleted: params.rollbackCompleted === true,
    finalDurableState:
      params.finalDurableState ??
      (params.dryRun ? "dry-run" : params.changed ? "verified-success" : "unchanged-noop"),
    runTriggered: false,
    catchUpTriggered: false,
    rollbackRequest,
    completedAtMs: params.now,
  };
}

function replaceStoreJobOrThrow(state: CronServiceState, id: string, job: CronJob): void {
  if (!state.store) {
    throw new Error("cron guarded update requires loaded store");
  }
  const index = state.store.jobs.findIndex((entry) => entry.id === id);
  if (index < 0) {
    throw new Error("cron guarded update target disappeared from loaded store");
  }
  state.store.jobs[index] = job;
}

function assertGuardedEnabledOnlyPostconditions(params: {
  before: CronJob;
  after: CronJob;
  request: CronGuardedUpdateRequest;
  currentDefinitionSha: string;
}): void {
  if (params.after.enabled !== params.request.patch.enabled) {
    throw new Error(
      "cron guarded update verification failed: enabled state mismatch after mutation",
    );
  }
  if (computeCronJobDefinitionSha(params.after) !== params.currentDefinitionSha) {
    throw new Error("cron guarded update verification failed: omitted fields changed");
  }
  if (params.after.state.lastRunAtMs !== params.before.state.lastRunAtMs) {
    throw new Error("cron guarded update verification failed: run was triggered");
  }
  if (params.after.state.runningAtMs !== params.before.state.runningAtMs) {
    throw new Error("cron guarded update verification failed: running state changed");
  }
}

async function reloadGuardedStoreForVerification(state: CronServiceState): Promise<void> {
  await ensureLoaded(state, { forceReload: true, skipRecompute: true });
}

async function rollbackGuardedUpdateOrThrow(params: {
  state: CronServiceState;
  beforeStore: NonNullable<CronServiceState["store"]>;
  before: CronJob;
  reason: unknown;
}): Promise<never> {
  try {
    if (consumeGuardedUpdateTestHook("failRollbackPersistOnce")) {
      throw new Error("injected guarded update rollback persistence failure");
    }
    params.state.store = structuredClone(params.beforeStore);
    await persist(params.state);
    await reloadGuardedStoreForVerification(params.state);
    const restored = findJobOrThrow(params.state, params.before.id);
    if (computeCronJobDefinitionSha(restored) !== computeCronJobDefinitionSha(params.before)) {
      throw new Error("rollback verification failed: definition SHA mismatch");
    }
    if (restored.enabled !== params.before.enabled) {
      throw new Error("rollback verification failed: enabled mismatch");
    }
    if (restored.state.lastRunAtMs !== params.before.state.lastRunAtMs) {
      throw new Error("rollback verification failed: lastRunAtMs mismatch");
    }
    throw params.reason;
  } catch (rollbackError) {
    if (rollbackError === params.reason) {
      throw rollbackError;
    }
    throw new Error(
      `cron guarded update rollback failed after postcondition failure: ${String(rollbackError)}`,
      { cause: rollbackError },
    );
  }
}

async function guardedUpdateLoadedCore(params: {
  state: CronServiceState;
  rawCommand: unknown;
  dryRun: boolean;
}): Promise<CronGuardedUpdateResult> {
  const command = normalizeGuardedUpdateInternalCommand(params.rawCommand);
  const request = command.request;
  const requestDigest = computeGuardedUpdateRequestDigest(request);
  if (!params.dryRun) {
    assertGuardedUpdateApproval({
      request,
      caller: command.caller,
      approval: command.approval,
      requestDigest,
      nowMs: params.state.deps.nowMs(),
      usedNonces: params.state.usedGuardedUpdateApprovalNonces,
    });
  } else {
    assertAuthorizedGuardedUpdateCaller(command.caller);
  }

  return await locked(params.state, async () => {
    warnIfDisabled(params.state, params.dryRun ? "validateGuardedUpdate" : "guardedUpdate");
    await ensureLoaded(params.state, { skipRecompute: true });
    if (!params.state.store) {
      throw new Error("cron guarded update requires loaded store");
    }
    const beforeStore = structuredClone(params.state.store);
    const before = structuredClone(findJobOrThrow(params.state, request.jobId));
    const currentDefinitionSha = computeCronJobDefinitionSha(before);
    verifyGuardedPreconditions({ job: before, request, currentDefinitionSha });
    const now = params.state.deps.nowMs();
    const predictedAfter = createPredictedGuardedAfter({ before, request, now });
    const changed = before.enabled !== request.patch.enabled;
    if (computeCronJobDefinitionSha(predictedAfter) !== currentDefinitionSha) {
      throw new Error("cron guarded update definition preservation failed before mutation");
    }

    if (params.dryRun) {
      return {
        ok: true,
        dryRun: true,
        changed,
        receipt: createGuardedReceipt({
          request,
          caller: command.caller,
          requestDigest,
          before,
          predictedAfter,
          dryRun: true,
          changed,
          now,
          persistenceCompleted: false,
          reloadVerification: false,
          finalDurableState: "dry-run",
        }),
      };
    }

    if (command.approval) {
      if (params.state.usedGuardedUpdateApprovalNonces.has(command.approval.nonce)) {
        throw new Error("cron.guarded_update approval nonce already used");
      }
      params.state.usedGuardedUpdateApprovalNonces.add(command.approval.nonce);
    }

    if (!changed) {
      return {
        ok: true,
        dryRun: false,
        changed,
        receipt: createGuardedReceipt({
          request,
          caller: command.caller,
          approval: command.approval,
          requestDigest,
          before,
          predictedAfter,
          after: before,
          dryRun: false,
          changed,
          now,
          persistenceCompleted: false,
          reloadVerification: true,
          finalDurableState: "unchanged-noop",
        }),
      };
    }

    try {
      const nextStore = structuredClone(beforeStore);
      params.state.store = nextStore;
      replaceStoreJobOrThrow(params.state, request.jobId, predictedAfter);

      if (consumeGuardedUpdateTestHook("failPersistBeforeWriteOnce")) {
        throw new Error("injected guarded update persistence failure before write");
      }
      await persist(params.state);
      if (consumeGuardedUpdateTestHook("failReloadVerificationOnce")) {
        throw new Error("injected guarded update reload verification failure");
      }
      await reloadGuardedStoreForVerification(params.state);
      const reread = structuredClone(findJobOrThrow(params.state, request.jobId));
      if (consumeGuardedUpdateTestHook("failPostconditionAfterWriteOnce")) {
        throw new Error("injected guarded update postcondition failure after write");
      }
      assertGuardedEnabledOnlyPostconditions({
        before,
        after: reread,
        request,
        currentDefinitionSha,
      });

      armTimer(params.state);
      emit(params.state, {
        jobId: request.jobId,
        action: "updated",
        job: reread,
        nextRunAtMs: reread.state.nextRunAtMs,
      });

      return {
        ok: true,
        dryRun: false,
        changed,
        receipt: createGuardedReceipt({
          request,
          caller: command.caller,
          approval: command.approval,
          requestDigest,
          before,
          predictedAfter,
          after: reread,
          dryRun: false,
          changed,
          now,
          persistenceCompleted: true,
          reloadVerification: true,
          finalDurableState: "verified-success",
        }),
      };
    } catch (error) {
      return await rollbackGuardedUpdateOrThrow({
        state: params.state,
        beforeStore,
        before,
        reason: error,
      });
    }
  });
}

export async function validateGuardedUpdate(
  state: CronServiceState,
  command: GuardedCronInternalCommand | unknown,
): Promise<CronGuardedUpdateResult> {
  return await guardedUpdateLoadedCore({ state, rawCommand: command, dryRun: true });
}

export async function guardedUpdate(
  state: CronServiceState,
  command: GuardedCronInternalCommand | unknown,
): Promise<CronGuardedUpdateResult> {
  return await guardedUpdateLoadedCore({ state, rawCommand: command, dryRun: false });
}

export async function remove(state: CronServiceState, id: string) {
  return await locked(state, async () => {
    warnIfDisabled(state, "remove");
    await ensureLoaded(state);
    const before = state.store?.jobs.length ?? 0;
    if (!state.store) {
      return { ok: false, removed: false } as const;
    }
    const removedJob = state.store.jobs.find((j) => j.id === id);
    state.store.jobs = state.store.jobs.filter((j) => j.id !== id);
    const removed = (state.store.jobs.length ?? 0) !== before;
    await persist(state);
    armTimer(state);
    if (removed) {
      emit(state, { jobId: id, action: "removed", job: removedJob });
    }
    return { ok: true, removed } as const;
  });
}

type PreparedManualRun =
  | {
      ok: true;
      ran: false;
      reason: "already-running" | "not-due" | "invalid-spec";
    }
  | {
      ok: true;
      ran: true;
      jobId: string;
      runId?: string;
      taskRunId?: string;
      startedAt: number;
      executionJob: CronJob;
    }
  | { ok: false };

type ManualRunDisposition =
  | Extract<PreparedManualRun, { ran: false }>
  | { ok: true; runnable: true };

type ManualRunPreflightResult =
  | { ok: false }
  | Extract<PreparedManualRun, { ran: false }>
  | {
      ok: true;
      runnable: true;
      job: CronJob;
      now: number;
    };

let nextManualRunId = 1;

async function skipInvalidPersistedManualRun(params: {
  state: CronServiceState;
  job: CronJob;
  mode?: "due" | "force";
  error: unknown;
}) {
  const endedAt = params.state.deps.nowMs();
  const errorText = normalizeCronRunErrorText(params.error);
  const diagnostics = createCronRunDiagnosticsFromError("cron-preflight", errorText, {
    severity: "warn",
    nowMs: params.state.deps.nowMs,
  });
  const shouldDelete = applyJobResult(
    params.state,
    params.job,
    {
      status: "skipped",
      error: errorText,
      diagnostics,
      startedAt: endedAt,
      endedAt,
    },
    { preserveSchedule: params.mode === "force" },
  );

  emit(params.state, {
    jobId: params.job.id,
    action: "finished",
    status: "skipped",
    error: errorText,
    diagnostics,
    runAtMs: endedAt,
    durationMs: params.job.state.lastDurationMs,
    nextRunAtMs: params.job.state.nextRunAtMs,
    deliveryStatus: params.job.state.lastDeliveryStatus,
    deliveryError: params.job.state.lastDeliveryError,
  });

  if (shouldDelete && params.state.store) {
    params.state.store.jobs = params.state.store.jobs.filter((entry) => entry.id !== params.job.id);
    emit(params.state, { jobId: params.job.id, action: "removed" });
  }

  recomputeNextRunsForMaintenance(params.state, { recomputeExpired: true });
  await persist(params.state);
  armTimer(params.state);
}

function tryCreateManualTaskRun(params: {
  state: CronServiceState;
  job: CronJob;
  startedAt: number;
}): string | undefined {
  const runId = createCronExecutionId(params.job.id, params.startedAt);
  try {
    createRunningTaskRun({
      runtime: "cron",
      sourceId: params.job.id,
      ownerKey: "",
      scopeKind: "system",
      childSessionKey: params.job.sessionKey,
      agentId: params.job.agentId,
      runId,
      label: params.job.name,
      task: params.job.name || params.job.id,
      deliveryStatus: "not_applicable",
      notifyPolicy: "silent",
      startedAt: params.startedAt,
      lastEventAt: params.startedAt,
    });
    return runId;
  } catch (error) {
    params.state.deps.log.warn(
      { jobId: params.job.id, error },
      "cron: failed to create task ledger record",
    );
    return undefined;
  }
}

function tryFinishManualTaskRun(
  state: CronServiceState,
  params: {
    taskRunId?: string;
    coreResult: Awaited<ReturnType<typeof executeJobCoreWithTimeout>>;
    endedAt: number;
  },
): void {
  if (!params.taskRunId) {
    return;
  }
  try {
    if (params.coreResult.status === "ok" || params.coreResult.status === "skipped") {
      completeTaskRunByRunId({
        runId: params.taskRunId,
        runtime: "cron",
        endedAt: params.endedAt,
        lastEventAt: params.endedAt,
        terminalSummary: params.coreResult.summary ?? undefined,
      });
      return;
    }
    failTaskRunByRunId({
      runId: params.taskRunId,
      runtime: "cron",
      status:
        normalizeCronRunErrorText(params.coreResult.error) === "cron: job execution timed out"
          ? "timed_out"
          : "failed",
      endedAt: params.endedAt,
      lastEventAt: params.endedAt,
      error:
        params.coreResult.status === "error"
          ? normalizeCronRunErrorText(params.coreResult.error)
          : undefined,
      terminalSummary: params.coreResult.summary ?? undefined,
    });
  } catch (error) {
    state.deps.log.warn(
      { runId: params.taskRunId, jobStatus: params.coreResult.status, error },
      "cron: failed to update task ledger record",
    );
  }
}

async function inspectManualRunPreflight(
  state: CronServiceState,
  id: string,
  mode?: "due" | "force",
): Promise<ManualRunPreflightResult> {
  return await locked(state, async () => {
    warnIfDisabled(state, "run");
    await ensureLoaded(state, { skipRecompute: true });
    // Normalize job tick state (clears stale runningAtMs markers) before
    // checking if already running, so a stale marker from a crashed Phase-1
    // persist does not block manual triggers for up to STUCK_RUN_MS (#17554).
    recomputeNextRunsForMaintenance(state);
    const job = findJobOrThrow(state, id);
    try {
      assertSupportedJobSpec(job);
    } catch (error) {
      await skipInvalidPersistedManualRun({ state, job, mode, error });
      return { ok: true, ran: false, reason: "invalid-spec" as const };
    }
    if (typeof job.state.runningAtMs === "number") {
      return { ok: true, ran: false, reason: "already-running" as const };
    }
    const now = state.deps.nowMs();
    const due = isJobDue(job, now, { forced: mode === "force" });
    if (!due) {
      return { ok: true, ran: false, reason: "not-due" as const };
    }
    return { ok: true, runnable: true, job, now } as const;
  });
}

async function inspectManualRunDisposition(
  state: CronServiceState,
  id: string,
  mode?: "due" | "force",
): Promise<ManualRunDisposition | { ok: false }> {
  const result = await inspectManualRunPreflight(state, id, mode);
  if (!result.ok) {
    return result;
  }
  if ("reason" in result) {
    return result;
  }
  return { ok: true, runnable: true } as const;
}

async function prepareManualRun(
  state: CronServiceState,
  id: string,
  mode?: "due" | "force",
  opts?: { runId?: string },
): Promise<PreparedManualRun> {
  const preflight = await inspectManualRunPreflight(state, id, mode);
  if (!preflight.ok) {
    return preflight;
  }
  if ("reason" in preflight) {
    return {
      ok: true,
      ran: false,
      reason: preflight.reason,
    } as const;
  }
  return await locked(state, async () => {
    // Reserve this run under lock, then execute outside lock so read ops
    // (`list`, `status`) stay responsive while the run is in progress.
    const job = findJobOrThrow(state, id);
    if (typeof job.state.runningAtMs === "number") {
      return { ok: true, ran: false, reason: "already-running" as const };
    }
    job.state.runningAtMs = preflight.now;
    job.state.lastError = undefined;
    // Persist the running marker before releasing lock so timer ticks that
    // force-reload from disk cannot start the same job concurrently.
    await persist(state);
    emit(state, { jobId: job.id, action: "started", job, runAtMs: preflight.now });
    const taskRunId = tryCreateManualTaskRun({
      state,
      job,
      startedAt: preflight.now,
    });
    const executionJob = structuredClone(job);
    return {
      ok: true,
      ran: true,
      jobId: job.id,
      runId: opts?.runId ?? taskRunId,
      taskRunId,
      startedAt: preflight.now,
      executionJob,
    } as const;
  });
}

async function finishPreparedManualRun(
  state: CronServiceState,
  prepared: Extract<PreparedManualRun, { ran: true }>,
  mode?: "due" | "force",
): Promise<void> {
  const executionJob = prepared.executionJob;
  const startedAt = prepared.startedAt;
  const jobId = prepared.jobId;
  const taskRunId = prepared.taskRunId;
  const runId = prepared.runId;

  let coreResult: Awaited<ReturnType<typeof executeJobCoreWithTimeout>>;
  try {
    coreResult = await executeJobCoreWithTimeout(state, executionJob);
  } catch (err) {
    coreResult = { status: "error", error: normalizeCronRunErrorText(err) };
  }
  const endedAt = state.deps.nowMs();
  tryFinishManualTaskRun(state, {
    taskRunId,
    coreResult,
    endedAt,
  });

  await locked(state, async () => {
    await ensureLoaded(state, { skipRecompute: true });
    const job = state.store?.jobs.find((entry) => entry.id === jobId);
    if (!job) {
      return;
    }

    const shouldDelete = applyJobResult(
      state,
      job,
      {
        status: coreResult.status,
        error: coreResult.error,
        diagnostics: coreResult.diagnostics,
        delivered: coreResult.delivered,
        startedAt,
        endedAt,
      },
      { preserveSchedule: mode === "force" },
    );

    emit(state, {
      jobId: job.id,
      action: "finished",
      job,
      status: coreResult.status,
      error: coreResult.error,
      summary: coreResult.summary,
      diagnostics: coreResult.diagnostics,
      delivered: coreResult.delivered,
      deliveryStatus: job.state.lastDeliveryStatus,
      deliveryError: job.state.lastDeliveryError,
      delivery: coreResult.delivery,
      sessionId: coreResult.sessionId,
      sessionKey: coreResult.sessionKey,
      runId,
      runAtMs: startedAt,
      durationMs: job.state.lastDurationMs,
      nextRunAtMs: job.state.nextRunAtMs,
      model: coreResult.model,
      provider: coreResult.provider,
      usage: coreResult.usage,
    });

    if (shouldDelete && state.store) {
      state.store.jobs = state.store.jobs.filter((entry) => entry.id !== job.id);
      emit(state, { jobId: job.id, action: "removed", job });
    }

    // Manual runs should not advance other due jobs without executing them.
    // Use maintenance-only recompute to repair missing values while
    // preserving existing past-due nextRunAtMs entries for future timer ticks.
    const postRunSnapshot = shouldDelete
      ? null
      : {
          enabled: job.enabled,
          updatedAtMs: job.updatedAtMs,
          state: structuredClone(job.state),
        };
    const postRunRemoved = shouldDelete;
    // Isolated Telegram send can persist target writeback directly to disk.
    // Reload before final persist so manual `cron run` keeps those changes.
    await ensureLoaded(state, { forceReload: true, skipRecompute: true });
    mergeManualRunSnapshotAfterReload({
      state,
      jobId,
      snapshot: postRunSnapshot,
      removed: postRunRemoved,
    });
    recomputeNextRunsForMaintenance(state, { recomputeExpired: true });
    await persist(state);
    armTimer(state);
  });
}

export async function run(
  state: CronServiceState,
  id: string,
  mode?: "due" | "force",
  opts?: { runId?: string },
) {
  const prepared = await prepareManualRun(state, id, mode, opts);
  if (!prepared.ok || !prepared.ran) {
    return prepared;
  }
  await finishPreparedManualRun(state, prepared, mode);
  return { ok: true, ran: true } as const;
}

export async function enqueueRun(state: CronServiceState, id: string, mode?: "due" | "force") {
  const disposition = await inspectManualRunDisposition(state, id, mode);
  if (!disposition.ok || !("runnable" in disposition && disposition.runnable)) {
    return disposition;
  }

  const runId = `manual:${id}:${state.deps.nowMs()}:${nextManualRunId++}`;
  void enqueueCommandInLane(
    CommandLane.Cron,
    async () => {
      const result = await run(state, id, mode, { runId });
      if (result.ok && "ran" in result && !result.ran) {
        state.deps.log.info(
          { jobId: id, runId, reason: result.reason },
          "cron: queued manual run skipped before execution",
        );
      }
      return result;
    },
    {
      warnAfterMs: 5_000,
      onWait: (waitMs, queuedAhead) => {
        state.deps.log.warn(
          { jobId: id, runId, waitMs, queuedAhead },
          "cron: queued manual run waiting for an execution slot",
        );
      },
    },
  ).catch((err) => {
    state.deps.log.error(
      { jobId: id, runId, err: String(err) },
      "cron: queued manual run background execution failed",
    );
  });
  return { ok: true, enqueued: true, runId } as const;
}

export function wakeNow(
  state: CronServiceState,
  opts: { mode: "now" | "next-heartbeat"; text: string },
) {
  return wake(state, opts);
}
