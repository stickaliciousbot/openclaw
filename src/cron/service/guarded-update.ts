import { createHash } from "node:crypto";
import type { CronJob } from "../types.js";
import type {
  CronGuardedJobStateSnapshot,
  GuardedCronCallerContext,
  GuardedCronInternalCommand,
  CronGuardedUpdateRequest,
  VerifiedGuardedCronApproval,
} from "./state.js";

const REQUEST_KEYS = new Set([
  "jobId",
  "job_id",
  "patch",
  "preconditions",
  "executionPolicy",
  "execution_policy",
  "reason",
]);
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
  "authenticatedIdentity",
  "authenticated_identity",
  "adminIdentity",
  "admin_identity",
  "jobId",
  "job_id",
  "enabled",
  "expectedEnabled",
  "expected_enabled",
  "expectedDefinitionSha",
  "expected_definition_sha",
  "expectedRevision",
  "expected_revision",
  "runImmediately",
  "run_immediately",
  "catchUp",
  "catch_up",
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

function readString(
  record: Record<string, unknown>,
  camel: string,
  snake = camel,
): string | undefined {
  const value = record[camel] ?? record[snake];
  return typeof value === "string" ? value : undefined;
}

function readBoolean(
  record: Record<string, unknown>,
  camel: string,
  snake = camel,
): boolean | undefined {
  const value = record[camel] ?? record[snake];
  return typeof value === "boolean" ? value : undefined;
}

function readNumber(
  record: Record<string, unknown>,
  camel: string,
  snake = camel,
): number | undefined {
  const value = record[camel] ?? record[snake];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function assertKnownKeys(
  record: Record<string, unknown>,
  allowed: ReadonlySet<string>,
  label: string,
): void {
  for (const key of Object.keys(record)) {
    if (!allowed.has(key)) {
      const hint = FORBIDDEN_PATCH_HINTS.has(key)
        ? "; guarded updates only permit patch.enabled"
        : "";
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
    throw new Error(
      "guarded cron update requires lowercase sha256 preconditions.expected_definition_sha",
    );
  }
  const executionPolicyRaw = value.executionPolicy ?? value.execution_policy;
  if (!isRecord(executionPolicyRaw)) {
    throw new Error("guarded cron update requires execution_policy object");
  }
  assertKnownKeys(
    executionPolicyRaw,
    EXECUTION_POLICY_KEYS,
    "guarded cron update execution_policy",
  );
  const runImmediately = readBoolean(executionPolicyRaw, "runImmediately", "run_immediately");
  const catchUp = readBoolean(executionPolicyRaw, "catchUp", "catch_up");
  if (
    runImmediately !== false ||
    catchUp !== false ||
    Object.keys(executionPolicyRaw).length !== 2
  ) {
    throw new Error(
      "guarded cron update requires execution_policy.run_immediately=false and catch_up=false",
    );
  }
  const reason = readString(value, "reason")?.trim();
  if (!reason) {
    throw new Error("guarded cron update requires non-empty reason");
  }
  if (reason.length > 500) {
    throw new Error("guarded cron update reason is too long");
  }
  return {
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
}

export function normalizeVerifiedGuardedCronApproval(
  value: unknown,
  caller: GuardedCronCallerContext,
): VerifiedGuardedCronApproval {
  if (!isRecord(value)) {
    throw new Error("guarded cron update approval must be an object");
  }
  assertKnownKeys(value, APPROVAL_KEYS, "guarded cron update approval");
  const expectedEnabled = readBoolean(value, "expectedEnabled", "expected_enabled");
  const runImmediately = readBoolean(value, "runImmediately", "run_immediately");
  const catchUp = readBoolean(value, "catchUp", "catch_up");
  if (typeof expectedEnabled !== "boolean") {
    throw new Error("guarded cron update approval requires expected_enabled binding");
  }
  if (runImmediately !== false || catchUp !== false) {
    throw new Error("guarded cron update approval requires no-run/no-catch-up binding");
  }
  return {
    approvalId: readString(value, "approvalId", "approval_id") ?? "",
    nonce: readString(value, "nonce") ?? "",
    toolName: readString(value, "toolName", "tool_name") as "cron",
    action: readString(value, "action") as "update",
    gatewayMethod: readString(value, "gatewayMethod", "gateway_method") as "cron.guarded_update",
    sessionKey: readString(value, "sessionKey", "session_key") ?? caller.sessionKey,
    authenticatedIdentity:
      readString(value, "authenticatedIdentity", "authenticated_identity") ??
      readString(value, "adminIdentity", "admin_identity") ??
      caller.authenticatedIdentity,
    jobId: readString(value, "jobId", "job_id") ?? "",
    enabled: readBoolean(value, "enabled") ?? false,
    expectedEnabled,
    expectedDefinitionSha:
      readString(value, "expectedDefinitionSha", "expected_definition_sha") ?? "",
    expectedRevision: readString(value, "expectedRevision", "expected_revision"),
    runImmediately,
    catchUp,
    requestDigest: readString(value, "requestDigest", "request_digest") ?? "",
    expiresAtMs: readNumber(value, "expiresAtMs", "expires_at_ms") ?? Number.NaN,
  };
}

export function assertAuthorizedGuardedUpdateCaller(caller?: GuardedCronCallerContext): void {
  if (!caller) {
    throw new Error("cron.guarded_update denied: unauthenticated caller");
  }
  if (!caller.sessionKey || !caller.authenticatedIdentity) {
    throw new Error("cron.guarded_update denied: incomplete trusted Gateway caller context");
  }
  if (!caller.isAdmin || !caller.capabilities.includes("admin.scheduler.enabled-state")) {
    throw new Error("cron.guarded_update denied: missing administrative scheduler scope");
  }
  if (caller.channelKind !== "direct") {
    throw new Error("cron.guarded_update denied: shared/group sessions are not authorized");
  }
}

export function normalizeGuardedUpdateInternalCommand(value: unknown): GuardedCronInternalCommand {
  if (!isRecord(value)) {
    throw new Error("guarded cron internal command must be an object");
  }
  const request = normalizeGuardedUpdateRequest(value.request);
  const callerRaw = value.caller;
  if (!isRecord(callerRaw)) {
    throw new Error("guarded cron internal command requires trusted caller context");
  }
  const capabilitiesRaw = callerRaw.capabilities;
  const caller: GuardedCronCallerContext = {
    sessionKey: typeof callerRaw.sessionKey === "string" ? callerRaw.sessionKey : "",
    authenticatedIdentity:
      typeof callerRaw.authenticatedIdentity === "string" ? callerRaw.authenticatedIdentity : "",
    isAdmin: callerRaw.isAdmin === true,
    capabilities: Array.isArray(capabilitiesRaw)
      ? capabilitiesRaw.filter((entry): entry is string => typeof entry === "string")
      : [],
    connectionId: typeof callerRaw.connectionId === "string" ? callerRaw.connectionId : undefined,
    channelKind:
      callerRaw.channelKind === "direct" ||
      callerRaw.channelKind === "group" ||
      callerRaw.channelKind === "shared" ||
      callerRaw.channelKind === "system"
        ? callerRaw.channelKind
        : "shared",
  };
  const approval =
    value.approval === undefined
      ? undefined
      : normalizeVerifiedGuardedCronApproval(value.approval, caller);
  return { request, caller, approval };
}

export function assertGuardedUpdateApproval(params: {
  request: CronGuardedUpdateRequest;
  caller: GuardedCronCallerContext;
  approval?: VerifiedGuardedCronApproval;
  requestDigest: string;
  nowMs: number;
  usedNonces: ReadonlySet<string>;
}): void {
  assertAuthorizedGuardedUpdateCaller(params.caller);
  const approval = params.approval;
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
  if (approval.authenticatedIdentity !== params.caller.authenticatedIdentity) {
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
  if (approval.expectedEnabled !== params.request.preconditions.expectedEnabled) {
    throw new Error("cron.guarded_update approval expected-enabled binding mismatch");
  }
  if (approval.runImmediately !== false || approval.catchUp !== false) {
    throw new Error("cron.guarded_update approval execution-policy binding mismatch");
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
