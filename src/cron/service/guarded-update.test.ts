import { describe, expect, it } from "vitest";
import { setupCronServiceSuite, withCronServiceForTest } from "../service.test-harness.js";
import type { CronJob } from "../types.js";
import {
  computeCronJobDefinitionSha,
  computeGuardedUpdateRequestDigest,
} from "./guarded-update.js";
import type { CronGuardedUpdateCaller, CronGuardedUpdateRequest } from "./state.js";

const { logger, makeStorePath } = setupCronServiceSuite({
  prefix: "openclaw-cron-guarded-update-",
  baseTimeIso: "2026-07-27T04:00:00.000Z",
});

const adminCaller: CronGuardedUpdateCaller = {
  sessionKey: "agent:main:telegram:direct:8495203551",
  authenticatedIdentity: "stick",
  isAdmin: true,
  capabilities: ["admin.scheduler.enabled-state"],
  connectionId: "conn-admin",
  channelKind: "direct",
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
    authenticatedIdentity: adminCaller.authenticatedIdentity!,
    jobId: request.jobId,
    enabled: request.patch.enabled,
    expectedEnabled: request.preconditions.expectedEnabled,
    expectedDefinitionSha: request.preconditions.expectedDefinitionSha,
    expectedRevision: request.preconditions.expectedRevision,
    runImmediately: false as const,
    catchUp: false as const,
    requestDigest: computeGuardedUpdateRequestDigest(request),
    expiresAtMs: Date.now() + 60_000,
  };
}

function commandFor(request: CronGuardedUpdateRequest, approval?: ReturnType<typeof approvalFor>) {
  return { request, caller: adminCaller, ...(approval ? { approval } : {}) };
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
        const result = await cron.validateGuardedUpdate(commandFor(request));

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
        const result = await cron.guardedUpdate(commandFor(base, approvalFor(base)));

        expect(result.dryRun).toBe(false);
        expect(result.changed).toBe(true);
        expect(result.receipt.schema).toBe("stickbot.openclaw.cron-update-receipt.v1");
        expect(result.receipt.terminal).toBe("CRON_UPDATE_APPLIED");
        expect(result.receipt.definitionShaAfter).toBe(result.receipt.definitionShaBefore);
        expect(result.receipt.rollbackRequest?.patch.enabled).toBe(false);
        expect(result.receipt.rollbackRequest?.executionPolicy).toEqual({
          runImmediately: false,
          catchUp: false,
        });
        expect(cron.getJob(job.id)?.enabled).toBe(true);
        expect(enqueueSystemEvent).not.toHaveBeenCalled();
        expect(requestHeartbeat).not.toHaveBeenCalled();
      },
    );
  });

  it("applies true to false", async () => {
    await withCronServiceForTest({ makeStorePath, logger, cronEnabled: true }, async ({ cron }) => {
      const job = await cron.add({
        name: "protected memory writer",
        enabled: true,
        schedule: { kind: "every", everyMs: 60_000 },
        sessionTarget: "main",
        wakeMode: "next-heartbeat",
        payload: { kind: "systemEvent", text: "append memory" },
      });
      const base = requestFor(job, false);
      const result = await cron.guardedUpdate(commandFor(base, approvalFor(base, "nonce-disable")));
      expect(result.changed).toBe(true);
      expect(cron.getJob(job.id)?.enabled).toBe(false);
    });
  });

  it("returns idempotent desired-state receipt and still consumes approval", async () => {
    await withCronServiceForTest({ makeStorePath, logger, cronEnabled: true }, async ({ cron }) => {
      const job = await cron.add({
        name: "protected memory writer",
        enabled: false,
        schedule: { kind: "every", everyMs: 60_000 },
        sessionTarget: "main",
        wakeMode: "next-heartbeat",
        payload: { kind: "systemEvent", text: "append memory" },
      });
      const base = requestFor(job, false);
      const request = commandFor(base, approvalFor(base, "nonce-idempotent"));
      const result = await cron.guardedUpdate(request);
      expect(result.changed).toBe(false);
      expect(result.receipt.terminal).toBe("CRON_UPDATE_ALREADY_DESIRED_STATE");
      await expect(cron.guardedUpdate(request)).rejects.toThrow(/nonce already used/);
    });
  });

  it("rejects precondition, broad patch, policy, caller, approval replay, and cross-session failures", async () => {
    await withCronServiceForTest({ makeStorePath, logger, cronEnabled: true }, async ({ cron }) => {
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
        cron.validateGuardedUpdate(
          commandFor({ ...base, preconditions: { ...base.preconditions, expectedEnabled: true } }),
        ),
      ).rejects.toThrow(/expected_enabled mismatch/);
      await expect(
        cron.validateGuardedUpdate(
          commandFor({
            ...base,
            preconditions: { ...base.preconditions, expectedRevision: "stale" },
          }),
        ),
      ).rejects.toThrow(/expected_revision mismatch/);
      await expect(
        cron.validateGuardedUpdate(
          commandFor({
            ...base,
            preconditions: { ...base.preconditions, expectedDefinitionSha: "0".repeat(64) },
          }),
        ),
      ).rejects.toThrow(/expected_definition_sha mismatch/);
      await expect(
        cron.validateGuardedUpdate(commandFor({ ...base, patch: { enabled: true, schedule: {} } })),
      ).rejects.toThrow(/only permit|unknown field/);
      await expect(
        cron.validateGuardedUpdate(
          commandFor({ ...base, executionPolicy: { runImmediately: true, catchUp: false } }),
        ),
      ).rejects.toThrow(/execution_policy|no-run/);
      await expect(
        cron.validateGuardedUpdate({ request: base, caller: { ...adminCaller, isAdmin: false } }),
      ).rejects.toThrow(/administrative scheduler scope/);
      await expect(
        cron.validateGuardedUpdate({ request: base, caller: { ...adminCaller, capabilities: [] } }),
      ).rejects.toThrow(/administrative scheduler scope/);
      await expect(
        cron.validateGuardedUpdate({
          request: base,
          caller: { ...adminCaller, channelKind: "group" },
        }),
      ).rejects.toThrow(/shared\/group/);
      await expect(
        cron.validateGuardedUpdate({
          request: base,
          caller: { ...adminCaller, channelKind: "shared" },
        }),
      ).rejects.toThrow(/shared\/group/);
      await expect(
        cron.validateGuardedUpdate({ request: base, caller: { ...adminCaller, sessionKey: "" } }),
      ).rejects.toThrow(/incomplete trusted Gateway caller context/);

      const request = commandFor(base, approvalFor(base, "nonce-replay"));
      await cron.guardedUpdate(request);
      await expect(cron.guardedUpdate(request)).rejects.toThrow(/nonce already used/);
      const jobAfter = cron.getJob(job.id)!;
      const crossBase = requestFor(jobAfter, false);
      await expect(
        cron.guardedUpdate({
          request: crossBase,
          approval: approvalFor(crossBase, "nonce-cross"),
          caller: { ...adminCaller, sessionKey: "agent:main:telegram:direct:other" },
        }),
      ).rejects.toThrow(/session binding mismatch/);
      await expect(
        cron.guardedUpdate({
          request: crossBase,
          approval: approvalFor(crossBase, "nonce-admin"),
          caller: { ...adminCaller, authenticatedIdentity: "other-admin" },
        }),
      ).rejects.toThrow(/admin binding mismatch/);
    });
  });
});
