import { createHash } from "node:crypto";
import type { CronJob } from "../types.js";
import type {
  CronGuardedJobStateSnapshot,
  CronGuardedUpdateCaller,
  CronGuardedUpdateRequest,
} from "./state.js";

const REQUEST_KEYS = new Set(["jobId", "job_id", "patch", "preconditions", "executionPolicy", "execution_policy", "reason", "approval"]);
const PATCH_KEYS = new Set(["enabled"]);
const PRECONDITION_KEYS = new Set([
  "expectedEnabled",
  "expected_enabled",
  "expectedRevision",
  "expected_revision",
  "expectedDefinitionSha",
  "expected_definition_sha",
]);
const EXECUTION_POLICY_KEYS = new Set(["runImmediately", "run_immediately", "catchUp", "catch_up"]);
const APPROVAL_KEYS = new Set([
  "approvalId",
  "approval_id",
  "nonce",
  "toolName",
  "tool_name",
  "action",
  "gatewayMethod",
  "gateway_method",
  "sessionKey",
  "session_key",
  "adminIdentity",
  "admin_identity",
  "jobId",
  "job_id",
  "enabled",
  "expectedDefinitionSha",
  "expected_definition_sha",
  "expectedRevision",
  "expected_revision",
  "requestDigest",
  "request_digest",
  "expiresAtMs",
  "expires_at_ms",
]);

const FORBIDDEN_PATCH_HINTS = new Set([
  "name",
  "schedule",
  "command",
  "payload",
  "timezone",
  "tz",
  "owner",
  "delivery",
  "retry",
  "notification",
  "notifications",
  "memoryTarget",
  "memory_target",
  "sessionTarget",
  "session_target",
  "wakeMode",
  "wake_mode",
  "agentId",
  "agent_id",
  "sessionKey",
  "session_key",
  "description",
  "deleteAfterRun",
  "delete_after_run",
  "failureAlert",
  "failure_alert",
  "state",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function readString(record: Record<string, unknown>, camel: string, snake = camel): string | undefined {
  const value = record[camel] ?? record[snake];
  return typeof value === "string" ? value : undefined;
}

function readBoolean(record: Record<string, unknown>, camel: string, snake = camel): boolean | undefined {
  const value = record[camel] ?? record[snake];
  return typeof value === "boolean" ? value : undefined;
}

function readNumber(record: Record<string, unknown>, camel: string, snake = camel): number | undefined {
  const value = record[camel] ?? record[snake];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function assertKnownKeys(record: Record<string, unknown>, allowed: ReadonlySet<string>, label: string): void {
  for (const key of Object.keys(record)) {
    if (!allowed.has(key)) {
      const hint = FORBIDDEN_PATCH_HINTS.has(key) ? "; guarded updates only permit patch.enabled" : "";
      throw new Error(`${label} contains unknown field: ${key}${hint}`);
    }
  }
}

export function canonicalizeForSha(value: unknown): string {
  if (value === undefined) {
    return "null";
  }
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((entry) => canonicalizeForSha(entry)).join(",")}]`;
  }
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .filter((key) => record[key] !== undefined)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalizeForSha(record[key])}`)
    .join(",")}}`;
}

export function sha256Hex(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function computeCronJobDefinitionSha(job: CronJob): string {
  return sha256Hex(
    canonicalizeForSha({
      id: job.id,
      name: job.name,
      schedule: job.schedule,
      command: (job as unknown as { command?: unknown }).command ?? null,
      payload: job.payload,
      timezone: (job.schedule as { tz?: unknown }).tz ?? null,
      owner: {
        agentId: job.agentId ?? null,
        sessionKey: job.sessionKey ?? null,
        sessionTarget: job.sessionTarget,
      },
      delivery: job.delivery ?? null,
      retry: (job as unknown as { retry?: unknown }).retry ?? null,
      notification: job.failureAlert ?? null,
      memoryTarget:
        (job as unknown as { memoryTarget?: unknown; memory_target?: unknown }).memoryTarget ??
        (job as unknown as { memory_target?: unknown }).memory_target ??
        null,
      description: job.description ?? null,
      deleteAfterRun: job.deleteAfterRun ?? null,
      wakeMode: job.wakeMode,
    }),
  );
}

export function computeCronJobStateDigest(job: CronJob): string {
  return sha256Hex(canonicalizeForSha(job.state ?? {}));
}

export function computeGuardedUpdateRequestDigest(request: CronGuardedUpdateRequest): string {
  return sha256Hex(
    canonicalizeForSha({
      toolName: "cron",
      action: "update",
      gatewayMethod: "cron.guarded_update",
      jobId: request.jobId,
      patch: request.patch,
      preconditions: request.preconditions,
      executionPolicy: request.executionPolicy,
      reason: request.reason,
    }),
  );
}

export function snapshotGuardedJobState(job: CronJob): CronGuardedJobStateSnapshot {
  return {
    enabled: job.enabled,
    revision: String(job.updatedAtMs),
    definitionSha: computeCronJobDefinitionSha(job),
    stateDigest: computeCronJobStateDigest(job),
    nextRunAtMs: job.state.nextRunAtMs,
    lastRunAtMs: job.state.lastRunAtMs,
    runningAtMs: job.state.runningAtMs,
  };
}

export function normalizeGuardedUpdateRequest(value: unknown): CronGuardedUpdateRequest {
  if (!isRecord(value)) {
    throw new Error("guarded cron update request must be an object");
  }
  assertKnownKeys(value, REQUEST_KEYS, "guarded cron update request");
  const jobId = readString(value, "jobId", "job_id");
  if (!jobId) {
    throw new Error("guarded cron update requires job_id");
  }
  if (!isRecord(value.patch)) {
    throw new Error("guarded cron update requires patch object");
  }
  assertKnownKeys(value.patch, PATCH_KEYS, "guarded cron update patch");
  const enabled = readBoolean(value.patch, "enabled");
  if (Object.keys(value.patch).length !== 1 || typeof enabled !== "boolean") {
    throw new Error("guarded cron update patch must contain only enabled:boolean");
  }
  const preconditionsRaw = value.preconditions;
  if (!isRecord(preconditionsRaw)) {
    throw new Error("guarded cron update requires preconditions object");
  }
  assertKnownKeys(preconditionsRaw, PRECONDITION_KEYS, "guarded cron update preconditions");
  const expectedEnabled = readBoolean(preconditionsRaw, "expectedEnabled", "expected_enabled");
  const expectedRevision = readString(preconditionsRaw, "expectedRevision", "expected_revision");
  const expectedDefinitionSha = readString(
    preconditionsRaw,
    "expectedDefinitionSha",
    "expected_definition_sha",
  );
  if (typeof expectedEnabled !== "boolean") {
    throw new Error("guarded cron update requires preconditions.expected_enabled");
  }
  if (!expectedDefinitionSha || !/^[a-f0-9]{64}$/.test(expectedDefinitionSha)) {
    throw new Error("guarded cron update requires lowercase sha256 preconditions.expected_definition_sha");
  }
  const executionPolicyRaw = value.executionPolicy ?? value.execution_policy;
  if (!isRecord(executionPolicyRaw)) {
    throw new Error("guarded cron update requires execution_policy object");
  }
  assertKnownKeys(executionPolicyRaw, EXECUTION_POLICY_KEYS, "guarded cron update execution_policy");
  const runImmediately = readBoolean(executionPolicyRaw, "runImmediately", "run_immediately");
  const catchUp = readBoolean(executionPolicyRaw, "catchUp", "catch_up");
  if (runImmediately !== false || catchUp !== false || Object.keys(executionPolicyRaw).length !== 2) {
    throw new Error("guarded cron update requires execution_policy.run_immediately=false and catch_up=false");
  }
  const reason = readString(value, "reason")?.trim();
  if (!reason) {
    throw new Error("guarded cron update requires non-empty reason");
  }
  if (reason.length > 500) {
    throw new Error("guarded cron update reason is too long");
  }
  const request: CronGuardedUpdateRequest = {
    jobId,
    patch: { enabled },
    preconditions: {
      expectedEnabled,
      expectedRevision,
      expectedDefinitionSha,
    },
    executionPolicy: { runImmediately: false, catchUp: false },
    reason,
  };
  if (value.approval !== undefined) {
    if (!isRecord(value.approval)) {
      throw new Error("guarded cron update approval must be an object");
    }
    assertKnownKeys(value.approval, APPROVAL_KEYS, "guarded cron update approval");
    const approval = {
      approvalId: readString(value.approval, "approvalId", "approval_id") ?? "",
      nonce: readString(value.approval, "nonce") ?? "",
      toolName: readString(value.approval, "toolName", "tool_name") as "cron",
      action: readString(value.approval, "action") as "update",
      gatewayMethod: readString(value.approval, "gatewayMethod", "gateway_method") as "cron.guarded_update",
      sessionKey: readString(value.approval, "sessionKey", "session_key") ?? "",
      adminIdentity: readString(value.approval, "adminIdentity", "admin_identity") ?? "",
      jobId: readString(value.approval, "jobId", "job_id") ?? "",
      enabled: readBoolean(value.approval, "enabled") ?? false,
      expectedDefinitionSha:
        readString(value.approval, "expectedDefinitionSha", "expected_definition_sha") ?? "",
      expectedRevision: readString(value.approval, "expectedRevision", "expected_revision"),
      requestDigest: readString(value.approval, "requestDigest", "request_digest") ?? "",
      expiresAtMs: readNumber(value.approval, "expiresAtMs", "expires_at_ms") ?? Number.NaN,
    };
    request.approval = approval;
  }
  return request;
}

export function assertAuthorizedGuardedUpdateCaller(caller?: CronGuardedUpdateCaller): void {
  if (!caller?.authenticated) {
    throw new Error("cron.guarded_update denied: unauthenticated caller");
  }
  if (!caller.adminSchedulerEnabledState) {
    throw new Error("cron.guarded_update denied: missing administrative scheduler scope");
  }
  if (caller.sharedOrGroupSession) {
    throw new Error("cron.guarded_update denied: shared/group sessions are not authorized");
  }
}

export function assertGuardedUpdateApproval(params: {
  request: CronGuardedUpdateRequest;
  caller: CronGuardedUpdateCaller;
  requestDigest: string;
  nowMs: number;
  usedNonces: ReadonlySet<string>;
}): void {
  assertAuthorizedGuardedUpdateCaller(params.caller);
  const approval = params.request.approval;
  if (!approval) {
    throw new Error("cron.guarded_update requires approval");
  }
  if (approval.toolName !== "cron" || approval.action !== "update") {
    throw new Error("cron.guarded_update approval tool/action binding mismatch");
  }
  if (approval.gatewayMethod !== "cron.guarded_update") {
    throw new Error("cron.guarded_update approval method binding mismatch");
  }
  if (approval.sessionKey !== params.caller.sessionKey) {
    throw new Error("cron.guarded_update approval session binding mismatch");
  }
  if (approval.adminIdentity !== params.caller.adminIdentity) {
    throw new Error("cron.guarded_update approval admin binding mismatch");
  }
  if (approval.jobId !== params.request.jobId) {
    throw new Error("cron.guarded_update approval job binding mismatch");
  }
  if (approval.enabled !== params.request.patch.enabled) {
    throw new Error("cron.guarded_update approval enabled binding mismatch");
  }
  if (approval.expectedDefinitionSha !== params.request.preconditions.expectedDefinitionSha) {
    throw new Error("cron.guarded_update approval definition SHA binding mismatch");
  }
  if (approval.expectedRevision !== params.request.preconditions.expectedRevision) {
    throw new Error("cron.guarded_update approval revision binding mismatch");
  }
  if (approval.requestDigest !== params.requestDigest) {
    throw new Error("cron.guarded_update approval request digest mismatch");
  }
  if (!Number.isFinite(approval.expiresAtMs) || approval.expiresAtMs < params.nowMs) {
    throw new Error("cron.guarded_update approval expired");
  }
  if (!approval.nonce || params.usedNonces.has(approval.nonce)) {
    throw new Error("cron.guarded_update approval nonce already used");
  }
}
