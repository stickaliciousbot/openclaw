import { describe, expect, it } from "vitest";
import {
  computeCronJobDefinitionSha,
  computeGuardedUpdateRequestDigest,
} from "./guarded-update.js";
import { setupCronServiceSuite, withCronServiceForTest } from "../service.test-harness.js";
import type { CronGuardedUpdateCaller, CronGuardedUpdateRequest } from "./state.js";
import type { CronJob } from "../types.js";

const { logger, makeStorePath } = setupCronServiceSuite({
  prefix: "openclaw-cron-guarded-update-",
  baseTimeIso: "2026-07-27T04:00:00.000Z",
});

const adminCaller: CronGuardedUpdateCaller = {
  sessionKey: "agent:main:telegram:direct:8495203551",
  adminIdentity: "stick",
  adminSchedulerEnabledState: true,
  sharedOrGroupSession: false,
  authenticated: true,
};

function requestFor(job: CronJob, enabled: boolean): CronGuardedUpdateRequest {
  return {
    jobId: job.id,
    patch: { enabled },
    preconditions: {
      expectedEnabled: job.enabled,
      expectedRevision: String(job.updatedAtMs),
      expectedDefinitionSha: computeCronJobDefinitionSha(job),
    },
    executionPolicy: { runImmediately: false, catchUp: false },
    reason: "protected memory writer enabled-state restoration",
  };
}

function approvalFor(request: CronGuardedUpdateRequest, nonce = "nonce-1") {
  return {
    approvalId: "approval-1",
    nonce,
    toolName: "cron" as const,
    action: "update" as const,
    gatewayMethod: "cron.guarded_update" as const,
    sessionKey: adminCaller.sessionKey!,
    adminIdentity: adminCaller.adminIdentity!,
    jobId: request.jobId,
    enabled: request.patch.enabled,
    expectedDefinitionSha: request.preconditions.expectedDefinitionSha,
    expectedRevision: request.preconditions.expectedRevision,
    requestDigest: computeGuardedUpdateRequestDigest(request),
    expiresAtMs: Date.now() + 60_000,
  };
}

describe("guarded cron enabled-state update", () => {
  it("validates false to true without mutation, run, or catch-up", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, enqueueSystemEvent, requestHeartbeat }) => {
        const job = await cron.add({
          name: "protected memory writer",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
        });
        const request = requestFor(job, true);
        const result = await cron.validateGuardedUpdate(request, adminCaller);

        expect(result.dryRun).toBe(true);
        expect(result.changed).toBe(true);
        expect(result.receipt.schema).toBe("stickbot.openclaw.cron-update-validation-receipt.v1");
        expect(result.receipt.terminal).toBe("CRON_UPDATE_VALIDATION_PASS");
        expect(result.receipt.mutation).toBe(false);
        expect(result.receipt.runTriggered).toBe(false);
        expect(result.receipt.catchUpTriggered).toBe(false);
        expect(result.receipt.changedFields).toEqual(["enabled"]);
        expect(cron.getJob(job.id)?.enabled).toBe(false);
        expect(enqueueSystemEvent).not.toHaveBeenCalled();
        expect(requestHeartbeat).not.toHaveBeenCalled();
      },
    );
  });

  it("applies false to true and returns an inverse rollback request", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, enqueueSystemEvent, requestHeartbeat }) => {
        const job = await cron.add({
          name: "protected memory writer",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
        });
        const base = requestFor(job, true);
        const result = await cron.guardedUpdate({ ...base, approval: approvalFor(base) }, adminCaller);

        expect(result.dryRun).toBe(false);
        expect(result.changed).toBe(true);
        expect(result.receipt.schema).toBe("stickbot.openclaw.cron-update-receipt.v1");
        expect(result.receipt.terminal).toBe("CRON_UPDATE_APPLIED");
        expect(result.receipt.definitionShaAfter).toBe(result.receipt.definitionShaBefore);
        expect(result.receipt.rollbackRequest?.patch.enabled).toBe(false);
        expect(result.receipt.rollbackRequest?.executionPolicy).toEqual({ runImmediately: false, catchUp: false });
        expect(cron.getJob(job.id)?.enabled).toBe(true);
        expect(enqueueSystemEvent).not.toHaveBeenCalled();
        expect(requestHeartbeat).not.toHaveBeenCalled();
      },
    );
  });

  it("applies true to false", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron }) => {
        const job = await cron.add({
          name: "protected memory writer",
          enabled: true,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
        });
        const base = requestFor(job, false);
        const result = await cron.guardedUpdate(
          { ...base, approval: approvalFor(base, "nonce-disable") },
          adminCaller,
        );
        expect(result.changed).toBe(true);
        expect(cron.getJob(job.id)?.enabled).toBe(false);
      },
    );
  });

  it("returns idempotent desired-state receipt and still consumes approval", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron }) => {
        const job = await cron.add({
          name: "protected memory writer",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
        });
        const base = requestFor(job, false);
        const request = { ...base, approval: approvalFor(base, "nonce-idempotent") };
        const result = await cron.guardedUpdate(request, adminCaller);
        expect(result.changed).toBe(false);
        expect(result.receipt.terminal).toBe("CRON_UPDATE_ALREADY_DESIRED_STATE");
        await expect(cron.guardedUpdate(request, adminCaller)).rejects.toThrow(/nonce already used/);
      },
    );
  });

  it("rejects precondition, broad patch, policy, caller, approval replay, and cross-session failures", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron }) => {
        const job = await cron.add({
          name: "protected memory writer",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
        });
        const base = requestFor(job, true);

        await expect(
          cron.validateGuardedUpdate({ ...base, preconditions: { ...base.preconditions, expectedEnabled: true } }, adminCaller),
        ).rejects.toThrow(/expected_enabled mismatch/);
        await expect(
          cron.validateGuardedUpdate({ ...base, preconditions: { ...base.preconditions, expectedRevision: "stale" } }, adminCaller),
        ).rejects.toThrow(/expected_revision mismatch/);
        await expect(
          cron.validateGuardedUpdate({ ...base, preconditions: { ...base.preconditions, expectedDefinitionSha: "0".repeat(64) } }, adminCaller),
        ).rejects.toThrow(/expected_definition_sha mismatch/);
        await expect(
          cron.validateGuardedUpdate({ ...base, patch: { enabled: true, schedule: {} } }, adminCaller),
        ).rejects.toThrow(/only permit|unknown field/);
        await expect(
          cron.validateGuardedUpdate({ ...base, executionPolicy: { runImmediately: true, catchUp: false } }, adminCaller),
        ).rejects.toThrow(/execution_policy|no-run/);
        await expect(
          cron.validateGuardedUpdate(base, { ...adminCaller, adminSchedulerEnabledState: false }),
        ).rejects.toThrow(/administrative scheduler scope/);
        await expect(
          cron.validateGuardedUpdate(base, { ...adminCaller, sharedOrGroupSession: true }),
        ).rejects.toThrow(/shared\/group/);

        const request = { ...base, approval: approvalFor(base, "nonce-replay") };
        await cron.guardedUpdate(request, adminCaller);
        await expect(cron.guardedUpdate(request, adminCaller)).rejects.toThrow(/nonce already used/);
        const jobAfter = cron.getJob(job.id)!;
        const crossBase = requestFor(jobAfter, false);
        await expect(
          cron.guardedUpdate(
            { ...crossBase, approval: approvalFor(crossBase, "nonce-cross") },
            { ...adminCaller, sessionKey: "agent:main:telegram:direct:other" },
          ),
        ).rejects.toThrow(/session binding mismatch/);
      },
    );
  });
});
