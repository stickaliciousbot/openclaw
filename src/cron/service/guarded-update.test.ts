import fs from "node:fs/promises";
import { afterEach, describe, expect, it } from "vitest";
import { setupCronServiceSuite, withCronServiceForTest } from "../service.test-harness.js";
import type { CronJob } from "../types.js";
import {
  computeCronJobDefinitionSha,
  computeGuardedUpdateRequestDigest,
} from "./guarded-update.js";
import { setGuardedUpdateTestHooksForTest } from "./ops.js";
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

async function readStoredJob(storePath: string, jobId: string): Promise<Record<string, unknown>> {
  const raw = JSON.parse(await fs.readFile(storePath, "utf-8")) as { jobs?: unknown[] };
  const job = raw.jobs?.find(
    (entry): entry is Record<string, unknown> =>
      !!entry && typeof entry === "object" && (entry as { id?: unknown }).id === jobId,
  );
  if (!job) {
    throw new Error(`stored job not found: ${jobId}`);
  }
  return job;
}

function stripEnabledRevisionAndState(job: CronJob): unknown {
  const clone = structuredClone(job) as Record<string, unknown>;
  delete clone.enabled;
  delete clone.updatedAtMs;
  delete clone.state;
  return clone;
}

afterEach(() => {
  setGuardedUpdateTestHooksForTest(undefined);
});

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

  it("preserves explicit delivery none through enabled-only persistence and inverse rollback", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, storePath }) => {
        const job = await cron.add({
          name: "protected memory writer with explicit none delivery",
          enabled: false,
          schedule: { kind: "cron", expr: "0 0 1 1 *", tz: "UTC" },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
          delivery: { mode: "none" },
          description: "optional metadata must survive",
        });
        const before = structuredClone(cron.getJob(job.id)!);
        const storedBefore = await readStoredJob(storePath, job.id);
        expect(storedBefore.delivery).toEqual({ mode: "none" });

        const request = requestFor(job, true);
        const result = await cron.guardedUpdate(commandFor(request, approvalFor(request)));
        const after = cron.getJob(job.id)!;
        const storedAfter = await readStoredJob(storePath, job.id);

        expect(after.enabled).toBe(true);
        expect(after.delivery).toEqual({ mode: "none" });
        expect(storedAfter.delivery).toEqual({ mode: "none" });
        expect(stripEnabledRevisionAndState(after)).toEqual(stripEnabledRevisionAndState(before));
        expect(result.receipt.persistenceCompleted).toBe(true);
        expect(result.receipt.reloadVerification).toBe(true);
        expect(result.receipt.finalDurableState).toBe("verified-success");
        expect(result.receipt.nonTargetFieldDigestAfter).toBe(
          result.receipt.nonTargetFieldDigestBefore,
        );

        const rollback = result.receipt.rollbackRequest!;
        const rollbackResult = await cron.guardedUpdate(
          commandFor(rollback, approvalFor(rollback, "nonce-rollback-explicit-none")),
        );
        const restored = cron.getJob(job.id)!;
        const storedRestored = await readStoredJob(storePath, job.id);
        expect(restored.enabled).toBe(false);
        expect(storedRestored.delivery).toEqual({ mode: "none" });
        expect(stripEnabledRevisionAndState(restored)).toEqual(
          stripEnabledRevisionAndState(before),
        );
        expect(rollbackResult.receipt.finalDurableState).toBe("verified-success");
      },
    );
  });

  it("preserves omitted delivery as omitted", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, storePath }) => {
        const job = await cron.add({
          name: "writer with omitted delivery",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
        });
        const storedBefore = await readStoredJob(storePath, job.id);
        expect(Object.hasOwn(storedBefore, "delivery")).toBe(false);
        const request = requestFor(job, true);
        await cron.guardedUpdate(commandFor(request, approvalFor(request, "nonce-omitted")));
        const storedAfter = await readStoredJob(storePath, job.id);
        expect(Object.hasOwn(storedAfter, "delivery")).toBe(false);
      },
    );
  });

  it("preserves non-default delivery, schedule, payload, and optional metadata", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, storePath }) => {
        const job = await cron.add({
          name: "writer with webhook delivery",
          description: "metadata survives",
          enabled: false,
          schedule: { kind: "cron", expr: "15 3 * * *", tz: "UTC", staggerMs: 0 },
          sessionTarget: "main",
          wakeMode: "now",
          payload: { kind: "systemEvent", text: "append memory" },
          delivery: { mode: "webhook", to: "http://127.0.0.1:9/fixture", bestEffort: true },
          deleteAfterRun: true,
        });
        const before = structuredClone(cron.getJob(job.id)!);
        const storedBefore = await readStoredJob(storePath, job.id);
        const request = requestFor(job, true);
        await cron.guardedUpdate(commandFor(request, approvalFor(request, "nonce-non-default")));
        const after = cron.getJob(job.id)!;
        const storedAfter = await readStoredJob(storePath, job.id);
        expect(stripEnabledRevisionAndState(after)).toEqual(stripEnabledRevisionAndState(before));
        expect(storedAfter.delivery).toEqual(storedBefore.delivery);
        expect(storedAfter.schedule).toEqual(storedBefore.schedule);
        expect(storedAfter.payload).toEqual(storedBefore.payload);
        expect(storedAfter.description).toEqual(storedBefore.description);
        expect(storedAfter.deleteAfterRun).toEqual(storedBefore.deleteAfterRun);
      },
    );
  });

  it("denies missing approval without mutating explicit delivery", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, storePath }) => {
        const job = await cron.add({
          name: "approval required writer",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
          delivery: { mode: "none" },
        });
        const before = await readStoredJob(storePath, job.id);
        const request = requestFor(job, true);
        await expect(cron.guardedUpdate(commandFor(request))).rejects.toThrow(/requires approval/);
        expect(await readStoredJob(storePath, job.id)).toEqual(before);
      },
    );
  });

  it("restores exact pre-state after injected persistence, reload, and postcondition failures", async () => {
    for (const [hook, message] of [
      ["failPersistBeforeWriteOnce", /persistence failure/],
      ["failReloadVerificationOnce", /reload verification failure/],
      ["failPostconditionAfterWriteOnce", /postcondition failure/],
    ] as const) {
      await withCronServiceForTest(
        { makeStorePath, logger, cronEnabled: true },
        async ({ cron, storePath }) => {
          const job = await cron.add({
            name: `rollback fixture ${hook}`,
            enabled: false,
            schedule: { kind: "every", everyMs: 60_000 },
            sessionTarget: "main",
            wakeMode: "next-heartbeat",
            payload: { kind: "systemEvent", text: "append memory" },
            delivery: { mode: "none" },
          });
          const beforeMemory = structuredClone(cron.getJob(job.id)!);
          const beforeStore = await readStoredJob(storePath, job.id);
          setGuardedUpdateTestHooksForTest({ [hook]: true });
          const request = requestFor(job, true);
          await expect(
            cron.guardedUpdate(commandFor(request, approvalFor(request, `nonce-${hook}`))),
          ).rejects.toThrow(message);
          const afterMemory = cron.getJob(job.id)!;
          const afterStore = await readStoredJob(storePath, job.id);
          expect(afterMemory.enabled).toBe(beforeMemory.enabled);
          expect(stripEnabledRevisionAndState(afterMemory)).toEqual(
            stripEnabledRevisionAndState(beforeMemory),
          );
          expect(afterStore).toEqual(beforeStore);
        },
      );
    }
  });

  it("emits explicit rollback-failed terminal when rollback persistence fails", async () => {
    await withCronServiceForTest({ makeStorePath, logger, cronEnabled: true }, async ({ cron }) => {
      const job = await cron.add({
        name: "rollback failure fixture",
        enabled: false,
        schedule: { kind: "every", everyMs: 60_000 },
        sessionTarget: "main",
        wakeMode: "next-heartbeat",
        payload: { kind: "systemEvent", text: "append memory" },
        delivery: { mode: "none" },
      });
      setGuardedUpdateTestHooksForTest({
        failPostconditionAfterWriteOnce: true,
        failRollbackPersistOnce: true,
      });
      const request = requestFor(job, true);
      await expect(
        cron.guardedUpdate(commandFor(request, approvalFor(request, "nonce-rollback-failed"))),
      ).rejects.toThrow(/rollback failed/);
    });
  });

  it("serializes concurrent guarded enabled updates without corrupting unrelated fields", async () => {
    await withCronServiceForTest(
      { makeStorePath, logger, cronEnabled: true },
      async ({ cron, storePath }) => {
        const job = await cron.add({
          name: "concurrent protected memory writer",
          enabled: false,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "main",
          wakeMode: "next-heartbeat",
          payload: { kind: "systemEvent", text: "append memory" },
          delivery: { mode: "none" },
        });
        const beforeStore = await readStoredJob(storePath, job.id);
        const reqA = requestFor(job, true);
        const reqB = requestFor(job, true);
        const settled = await Promise.allSettled([
          cron.guardedUpdate(commandFor(reqA, approvalFor(reqA, "nonce-concurrent-a"))),
          cron.guardedUpdate(commandFor(reqB, approvalFor(reqB, "nonce-concurrent-b"))),
        ]);
        expect(settled.filter((entry) => entry.status === "fulfilled")).toHaveLength(1);
        expect(settled.filter((entry) => entry.status === "rejected")).toHaveLength(1);
        const storedAfter = await readStoredJob(storePath, job.id);
        expect(storedAfter.delivery).toEqual(beforeStore.delivery);
        expect(storedAfter.payload).toEqual(beforeStore.payload);
        expect(storedAfter.schedule).toEqual(beforeStore.schedule);
      },
    );
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
        cron.validateGuardedUpdate(
          commandFor({ ...base, patch: { enabled: true, schedule: {} } } as never),
        ),
      ).rejects.toThrow(/only permit|unknown field/);
      await expect(
        cron.validateGuardedUpdate(
          commandFor({
            ...base,
            executionPolicy: { runImmediately: true, catchUp: false },
          } as never),
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
