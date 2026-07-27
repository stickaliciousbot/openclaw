import { describe, expect, it } from "vitest";
import {
  validateCronAddParams,
  validateCronGuardedUpdateParams,
  validateCronListParams,
  validateCronRemoveParams,
  validateCronRunParams,
  validateCronRunsParams,
  validateCronUpdateParams,
  validateCronValidateGuardedUpdateParams,
} from "./index.js";

const minimalAddParams = {
  name: "daily-summary",
  schedule: { kind: "every", everyMs: 60_000 },
  sessionTarget: "main",
  wakeMode: "next-heartbeat",
  payload: { kind: "systemEvent", text: "tick" },
} as const;

const guardedValidationParams = {
  job_id: "job-1",
  patch: { enabled: true },
  preconditions: {
    expected_enabled: false,
    expected_revision: "123",
    expected_definition_sha: "a".repeat(64),
  },
  execution_policy: { run_immediately: false, catch_up: false },
  reason: "protected memory writer resume",
} as const;

const guardedUpdateParams = {
  ...guardedValidationParams,
  approval: {
    approval_id: "approval-1",
    nonce: "nonce-1",
    tool_name: "cron",
    action: "update",
    gateway_method: "cron.guarded_update",
    session_key: "agent:main:telegram:direct:8495203551",
    admin_identity: "stick",
    job_id: "job-1",
    enabled: true,
    expected_definition_sha: "a".repeat(64),
    expected_revision: "123",
    request_digest: "b".repeat(64),
    expires_at_ms: 1_800_000_000_000,
  },
} as const;

describe("cron protocol validators", () => {
  it("accepts minimal add params", () => {
    expect(validateCronAddParams(minimalAddParams)).toBe(true);
  });

  it("accepts current and custom session targets", () => {
    expect(
      validateCronAddParams({
        ...minimalAddParams,
        sessionTarget: "current",
        payload: { kind: "agentTurn", message: "tick" },
      }),
    ).toBe(true);
    expect(
      validateCronAddParams({
        ...minimalAddParams,
        sessionTarget: "session:project-alpha",
        payload: { kind: "agentTurn", message: "tick" },
      }),
    ).toBe(true);
    expect(
      validateCronUpdateParams({
        id: "job-1",
        patch: { sessionTarget: "session:project-alpha" },
      }),
    ).toBe(true);
  });

  it("rejects add params when required scheduling fields are missing", () => {
    const { wakeMode: _wakeMode, ...withoutWakeMode } = minimalAddParams;
    expect(validateCronAddParams(withoutWakeMode)).toBe(false);
  });

  it("accepts update params for id and jobId selectors", () => {
    expect(validateCronUpdateParams({ id: "job-1", patch: { enabled: false } })).toBe(true);
    expect(validateCronUpdateParams({ jobId: "job-2", patch: { enabled: true } })).toBe(true);
  });

  it("preserves broad cron.update schema compatibility", () => {
    expect(
      validateCronUpdateParams({
        id: "job-1",
        patch: {
          schedule: { kind: "every", everyMs: 120_000 },
          payload: { kind: "systemEvent", text: "tick" },
          delivery: { mode: "announce", channel: "telegram", to: "123" },
        },
      }),
    ).toBe(true);
  });

  it("accepts guarded validation and guarded update params", () => {
    expect(validateCronValidateGuardedUpdateParams(guardedValidationParams)).toBe(true);
    expect(validateCronGuardedUpdateParams(guardedUpdateParams)).toBe(true);
  });

  it("rejects invalid guarded update shapes", () => {
    expect(
      validateCronValidateGuardedUpdateParams({
        ...guardedValidationParams,
        patch: { enabled: true, schedule: { kind: "every", everyMs: 1_000 } },
      }),
    ).toBe(false);
    expect(
      validateCronValidateGuardedUpdateParams({
        ...guardedValidationParams,
        execution_policy: { run_immediately: true, catch_up: false },
      }),
    ).toBe(false);
    expect(
      validateCronValidateGuardedUpdateParams({
        ...guardedValidationParams,
        execution_policy: { run_immediately: false, catch_up: true },
      }),
    ).toBe(false);
    expect(
      validateCronValidateGuardedUpdateParams({
        ...guardedValidationParams,
        preconditions: { expected_enabled: false },
      }),
    ).toBe(false);
    expect(validateCronValidateGuardedUpdateParams({ patch: { enabled: true } })).toBe(false);
    expect(validateCronGuardedUpdateParams(guardedValidationParams)).toBe(false);
  });

  it("accepts delivery threadId on add and update params", () => {
    expect(
      validateCronAddParams({
        ...minimalAddParams,
        delivery: {
          mode: "announce",
          channel: "telegram",
          to: "-100123",
          threadId: 42,
        },
      }),
    ).toBe(true);
    expect(
      validateCronUpdateParams({
        id: "job-1",
        patch: {
          delivery: {
            mode: "announce",
            channel: "telegram",
            to: "-100123",
            threadId: "topic-42",
          },
        },
      }),
    ).toBe(true);
    expect(
      validateCronUpdateParams({
        id: "job-1",
        patch: {
          delivery: {
            threadId: 42,
          },
        },
      }),
    ).toBe(true);
  });

  it("accepts remove params for id and jobId selectors", () => {
    expect(validateCronRemoveParams({ id: "job-1" })).toBe(true);
    expect(validateCronRemoveParams({ jobId: "job-2" })).toBe(true);
  });

  it("accepts run params mode for id and jobId selectors", () => {
    expect(validateCronRunParams({ id: "job-1", mode: "force" })).toBe(true);
    expect(validateCronRunParams({ jobId: "job-2", mode: "due" })).toBe(true);
  });

  it("accepts list paging/filter/sort params", () => {
    expect(
      validateCronListParams({
        includeDisabled: true,
        limit: 50,
        offset: 0,
        query: "daily",
        enabled: "all",
        sortBy: "nextRunAtMs",
        sortDir: "asc",
      }),
    ).toBe(true);
    expect(validateCronListParams({ offset: -1 })).toBe(false);
  });

  it("enforces runs limit minimum for id and jobId selectors", () => {
    expect(validateCronRunsParams({ id: "job-1", limit: 1 })).toBe(true);
    expect(validateCronRunsParams({ jobId: "job-2", limit: 1 })).toBe(true);
    expect(validateCronRunsParams({ id: "job-1", limit: 0 })).toBe(false);
    expect(validateCronRunsParams({ jobId: "job-2", limit: 0 })).toBe(false);
  });

  it("rejects cron.runs path traversal ids", () => {
    expect(validateCronRunsParams({ id: "../job-1" })).toBe(false);
    expect(validateCronRunsParams({ id: "nested/job-1" })).toBe(false);
    expect(validateCronRunsParams({ jobId: "..\\job-2" })).toBe(false);
    expect(validateCronRunsParams({ jobId: "nested\\job-2" })).toBe(false);
  });

  it("accepts runs paging/filter/sort params", () => {
    expect(
      validateCronRunsParams({
        id: "job-1",
        limit: 50,
        offset: 0,
        status: "error",
        query: "timeout",
        sortDir: "desc",
      }),
    ).toBe(true);
    expect(validateCronRunsParams({ id: "job-1", offset: -1 })).toBe(false);
  });

  it("accepts all-scope runs with multi-select filters", () => {
    expect(
      validateCronRunsParams({
        scope: "all",
        limit: 25,
        statuses: ["ok", "error"],
        deliveryStatuses: ["delivered", "not-requested"],
        query: "fail",
        sortDir: "desc",
      }),
    ).toBe(true);
    expect(
      validateCronRunsParams({
        scope: "job",
        statuses: [],
      }),
    ).toBe(false);
  });
});
