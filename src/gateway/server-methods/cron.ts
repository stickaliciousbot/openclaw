import { randomUUID } from "node:crypto";
import type { OpenClawConfig } from "../../config/types.openclaw.js";
import { resolveCronDeliveryPreviews } from "../../cron/delivery-preview.js";
import { normalizeCronJobCreate, normalizeCronJobPatch } from "../../cron/normalize.js";
import {
  readCronRunLogEntriesPage,
  readCronRunLogEntriesPageAll,
  resolveCronRunLogPath,
} from "../../cron/run-log.js";
import {
  assertAuthorizedGuardedUpdateCaller,
  computeGuardedUpdateActionDigest,
  computeGuardedUpdateRequestDigest,
  normalizeGuardedUpdateRequest,
  normalizeVerifiedGuardedCronApproval,
} from "../../cron/service/guarded-update.js";
import { applyJobPatch } from "../../cron/service/jobs.js";
import type {
  GuardedCronCallerContext,
  GuardedCronInternalCommand,
} from "../../cron/service/state.js";
import { isInvalidCronSessionTargetIdError } from "../../cron/session-target.js";
import type { CronDelivery, CronJob, CronJobCreate, CronJobPatch } from "../../cron/types.js";
import { validateScheduleTimestamp } from "../../cron/validate-timestamp.js";
import { formatErrorMessage } from "../../infra/errors.js";
import type { ExecApprovalDecision } from "../../infra/exec-approvals.js";
import {
  resolveTargetPrefixedChannel,
  validateTargetProviderPrefix,
} from "../../infra/outbound/channel-target-prefix.js";
import type { PluginApprovalRequestPayload } from "../../infra/plugin-approvals.js";
import { DEFAULT_PLUGIN_APPROVAL_TIMEOUT_MS } from "../../infra/plugin-approvals.js";
import { listConfiguredAnnounceChannelIdsForConfig } from "../../plugins/channel-plugin-ids.js";
import { normalizeMessageChannel } from "../../utils/message-channel.js";
import { ADMIN_SCOPE } from "../method-scopes.js";
import {
  ErrorCodes,
  errorShape,
  formatValidationErrors,
  validateCronApprovalResolveParams,
  validateCronAddParams,
  validateCronGuardedUpdateParams,
  validateCronListParams,
  validateCronRemoveParams,
  validateCronRunParams,
  validateCronRunsParams,
  validateCronStatusParams,
  validateCronUpdateParams,
  validateCronValidateGuardedUpdateParams,
  validateWakeParams,
} from "../protocol/index.js";
import type {
  GatewayClient,
  GatewayRequestContext,
  GatewayRequestHandlers,
  RespondFn,
} from "./types.js";

const CRON_GUARDED_UPDATE_APPROVAL_TIMEOUT_MS = DEFAULT_PLUGIN_APPROVAL_TIMEOUT_MS;

type CronGuardedUpdateApprovalPayload = PluginApprovalRequestPayload & {
  approvalKind: "cron.guarded_update";
  gatewayMethod: "cron.guarded_update";
  action: "update";
  requestDigest: string;
  actionDigest: string;
  jobId: string;
  enabled: boolean;
  expectedEnabled: boolean;
  expectedDefinitionSha: string;
  expectedRevision?: string;
  runImmediately: false;
  catchUp: false;
  reason: string;
  callerSessionKey: string;
  callerAuthenticatedIdentity: string;
  callerConnectionId?: string;
  callerChannelKind: GuardedCronCallerContext["channelKind"];
  callerCapabilities: readonly string[];
  eligibleSurfaces: readonly ["control-ui"];
};

function isCronGuardedUpdateApprovalPayload(
  value: PluginApprovalRequestPayload,
): value is CronGuardedUpdateApprovalPayload {
  const record = value as Record<string, unknown>;
  return (
    record.approvalKind === "cron.guarded_update" &&
    record.gatewayMethod === "cron.guarded_update" &&
    record.action === "update" &&
    typeof record.requestDigest === "string" &&
    typeof record.actionDigest === "string" &&
    typeof record.callerSessionKey === "string" &&
    typeof record.callerAuthenticatedIdentity === "string"
  );
}

function findPendingCronGuardedUpdateApproval(params: {
  manager: NonNullable<GatewayRequestContext["pluginApprovalManager"]>;
  requestDigest: string;
  caller: GuardedCronCallerContext;
}) {
  return params.manager.listPendingRecords().find((record) => {
    const request = record.request;
    return (
      isCronGuardedUpdateApprovalPayload(request) &&
      request.requestDigest === params.requestDigest &&
      request.actionDigest ===
        computeGuardedUpdateActionDigest({
          request: normalizeGuardedUpdateRequest({
            job_id: request.jobId,
            patch: { enabled: request.enabled },
            preconditions: {
              expected_enabled: request.expectedEnabled,
              expected_definition_sha: request.expectedDefinitionSha,
              expected_revision: request.expectedRevision,
            },
            execution_policy: { run_immediately: false, catch_up: false },
            reason: request.reason,
          }),
          caller: params.caller,
          requestDigest: params.requestDigest,
        }) &&
      request.callerSessionKey === params.caller.sessionKey &&
      request.callerAuthenticatedIdentity === params.caller.authenticatedIdentity
    );
  });
}

function buildCronGuardedUpdateApprovalPayload(params: {
  command: GuardedCronInternalCommand;
  requestDigest: string;
  actionDigest: string;
  jobName?: string;
}): CronGuardedUpdateApprovalPayload {
  const { request, caller } = params.command;
  return {
    approvalKind: "cron.guarded_update",
    pluginId: "openclaw.cron",
    title: "Cron guarded update approval required",
    description: [
      `Approval kind: cron.guarded_update`,
      `Target job ID: ${request.jobId}`,
      `Target job name: ${params.jobName ?? request.jobId}`,
      `Change: enabled:${String(request.preconditions.expectedEnabled)} → ${String(
        request.patch.enabled,
      )}`,
      "run_immediately=false",
      "catch_up=false",
      `Reason: ${request.reason}`,
    ].join("\n"),
    severity: "warning",
    toolName: "cron",
    toolCallId: request.jobId,
    allowedDecisions: ["allow-once", "deny"],
    sessionKey: caller.sessionKey,
    gatewayMethod: "cron.guarded_update",
    action: "update",
    requestDigest: params.requestDigest,
    actionDigest: params.actionDigest,
    jobId: request.jobId,
    enabled: request.patch.enabled,
    expectedEnabled: request.preconditions.expectedEnabled,
    expectedDefinitionSha: request.preconditions.expectedDefinitionSha,
    expectedRevision: request.preconditions.expectedRevision,
    runImmediately: false,
    catchUp: false,
    reason: request.reason,
    callerSessionKey: caller.sessionKey,
    callerAuthenticatedIdentity: caller.authenticatedIdentity,
    callerConnectionId: caller.connectionId,
    callerChannelKind: caller.channelKind,
    callerCapabilities: caller.capabilities,
    eligibleSurfaces: ["control-ui"],
  };
}

function mintVerifiedCronGuardedUpdateApproval(params: {
  approvalId: string;
  command: GuardedCronInternalCommand;
  requestDigest: string;
  actionDigest: string;
  expiresAtMs: number;
}) {
  const { request, caller } = params.command;
  return {
    approvalKind: "cron.guarded_update" as const,
    approvalId: params.approvalId,
    nonce: `cron:${randomUUID()}`,
    toolName: "cron" as const,
    action: "update" as const,
    gatewayMethod: "cron.guarded_update" as const,
    sessionKey: caller.sessionKey,
    authenticatedIdentity: caller.authenticatedIdentity,
    jobId: request.jobId,
    enabled: request.patch.enabled,
    expectedEnabled: request.preconditions.expectedEnabled,
    expectedDefinitionSha: request.preconditions.expectedDefinitionSha,
    expectedRevision: request.preconditions.expectedRevision,
    runImmediately: false as const,
    catchUp: false as const,
    requestDigest: params.requestDigest,
    actionDigest: params.actionDigest,
    expiresAtMs: params.expiresAtMs,
  };
}

function buildCronGuardedUpdateCommandFromApprovalPayload(
  payload: CronGuardedUpdateApprovalPayload,
): GuardedCronInternalCommand {
  return {
    request: normalizeGuardedUpdateRequest({
      job_id: payload.jobId,
      patch: { enabled: payload.enabled },
      preconditions: {
        expected_enabled: payload.expectedEnabled,
        expected_definition_sha: payload.expectedDefinitionSha,
        expected_revision: payload.expectedRevision,
      },
      execution_policy: { run_immediately: false, catch_up: false },
      reason: payload.reason,
    }),
    caller: {
      sessionKey: payload.callerSessionKey,
      authenticatedIdentity: payload.callerAuthenticatedIdentity,
      isAdmin: true,
      capabilities: payload.callerCapabilities,
      connectionId: payload.callerConnectionId,
      channelKind: payload.callerChannelKind,
    },
  };
}

function assertCronApprovalResolverTrusted(params: {
  payload: CronGuardedUpdateApprovalPayload;
  client: GatewayClient | null;
}): void {
  const resolver = resolveGuardedCronCaller({ client: params.client });
  assertAuthorizedGuardedUpdateCaller(resolver);
  if (resolver.sessionKey !== params.payload.callerSessionKey) {
    throw new Error("cron.approval.resolve denied: session binding mismatch");
  }
  if (resolver.authenticatedIdentity !== params.payload.callerAuthenticatedIdentity) {
    throw new Error("cron.approval.resolve denied: owner/admin binding mismatch");
  }
  if (
    params.payload.callerConnectionId &&
    resolver.connectionId !== params.payload.callerConnectionId
  ) {
    throw new Error("cron.approval.resolve denied: surface binding mismatch");
  }
}

async function handleCronApprovalResolve(params: {
  params: unknown;
  respond: RespondFn;
  context: GatewayRequestContext;
  client: GatewayClient | null;
}): Promise<void> {
  const manager = params.context.pluginApprovalManager;
  if (!manager) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "cron approval surface unavailable"),
    );
    return;
  }
  if (!validateCronApprovalResolveParams(params.params)) {
    params.respond(
      false,
      undefined,
      errorShape(
        ErrorCodes.INVALID_REQUEST,
        `invalid cron.approval.resolve params: ${formatValidationErrors(
          validateCronApprovalResolveParams.errors,
        )}`,
      ),
    );
    return;
  }
  const p = params.params as { id: string; decision: ExecApprovalDecision };
  const resolvedId = manager.lookupApprovalId(p.id, { includeResolved: true });
  if (resolvedId.kind !== "exact" && resolvedId.kind !== "prefix") {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "unknown or expired cron approval id"),
    );
    return;
  }
  const snapshot = manager.getSnapshot(resolvedId.id);
  const request = snapshot?.request;
  if (!snapshot || !request || !isCronGuardedUpdateApprovalPayload(request)) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "approval id is not a cron.guarded_update approval"),
    );
    return;
  }
  const recordedDecision = snapshot.decision ?? snapshot.consumedDecision;
  try {
    assertCronApprovalResolverTrusted({ payload: request, client: params.client });
  } catch (err) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, formatErrorMessage(err)),
    );
    return;
  }
  if (snapshot.resolvedAtMs !== undefined) {
    if (recordedDecision === p.decision) {
      params.respond(
        true,
        { ok: true, id: resolvedId.id, terminal: "CRON_APPROVAL_DECISION_IDEMPOTENT" },
        undefined,
      );
      return;
    }
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "cron approval already resolved"),
    );
    return;
  }

  const command = buildCronGuardedUpdateCommandFromApprovalPayload(request);
  const requestDigest = computeGuardedUpdateRequestDigest(command.request);
  const actionDigest = computeGuardedUpdateActionDigest({
    request: command.request,
    caller: command.caller,
    requestDigest,
  });
  if (requestDigest !== request.requestDigest || actionDigest !== request.actionDigest) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "cron approval digest binding mismatch"),
    );
    return;
  }

  if (!manager.resolve(resolvedId.id, p.decision, params.client?.connect.client.id ?? null)) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "unknown or expired cron approval id"),
    );
    return;
  }

  const resolvedEvent = {
    id: resolvedId.id,
    decision: p.decision,
    request,
    approvalKind: "cron.guarded_update",
    ts: Date.now(),
  };
  params.context.broadcast("cron.approval.resolved", resolvedEvent, { dropIfSlow: true });
  params.context.broadcast("plugin.approval.resolved", resolvedEvent, { dropIfSlow: true });

  if (p.decision === "deny") {
    params.respond(
      true,
      { ok: true, id: resolvedId.id, terminal: "CRON_APPROVAL_DENIED_ZERO_MUTATION" },
      undefined,
    );
    return;
  }

  if (!manager.consumeAllowOnce(resolvedId.id)) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "cron approval already consumed"),
    );
    return;
  }

  try {
    const result = await params.context.cron.guardedUpdate({
      ...command,
      approval: mintVerifiedCronGuardedUpdateApproval({
        approvalId: resolvedId.id,
        command,
        requestDigest,
        actionDigest,
        expiresAtMs: snapshot.expiresAtMs,
      }),
    });
    params.respond(
      true,
      { ok: true, id: resolvedId.id, terminal: "CRON_APPROVAL_ALLOW_ONCE_APPLIED", result },
      undefined,
    );
  } catch (err) {
    params.respond(
      false,
      undefined,
      errorShape(
        ErrorCodes.INVALID_REQUEST,
        `invalid cron.guarded_update params: ${formatErrorMessage(err)}`,
      ),
    );
  }
}

async function handleCronGuardedUpdateApprovalRequest(params: {
  params: Record<string, unknown>;
  respond: RespondFn;
  context: GatewayRequestContext;
  client: GatewayClient | null;
}): Promise<void> {
  const manager = params.context.pluginApprovalManager;
  if (!manager) {
    params.respond(
      false,
      undefined,
      errorShape(ErrorCodes.INVALID_REQUEST, "cron.guarded_update approval surface unavailable"),
    );
    return;
  }

  let command: GuardedCronInternalCommand;
  let validationResult: unknown;
  try {
    command = buildGuardedCronInternalCommand({
      params: params.params,
      client: params.client,
      requireApproval: false,
    });
    validationResult = await params.context.cron.validateGuardedUpdate(command);
  } catch (err) {
    params.respond(
      false,
      undefined,
      errorShape(
        ErrorCodes.INVALID_REQUEST,
        `invalid cron.guarded_update params: ${formatErrorMessage(err)}`,
      ),
    );
    return;
  }

  const requestDigest = computeGuardedUpdateRequestDigest(command.request);
  const actionDigest = computeGuardedUpdateActionDigest({
    request: command.request,
    caller: command.caller,
    requestDigest,
  });
  let record = findPendingCronGuardedUpdateApproval({
    manager,
    requestDigest,
    caller: command.caller,
  });
  let created = false;

  if (!record) {
    const payload = buildCronGuardedUpdateApprovalPayload({
      command,
      requestDigest,
      actionDigest,
      jobName: params.context.cron.getJob(command.request.jobId)?.name,
    });
    record = manager.create(
      payload,
      CRON_GUARDED_UPDATE_APPROVAL_TIMEOUT_MS,
      `cron:${randomUUID()}`,
    );
    try {
      manager.register(record, CRON_GUARDED_UPDATE_APPROVAL_TIMEOUT_MS);
      created = true;
    } catch (err) {
      params.respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, `registration failed: ${String(err)}`),
      );
      return;
    }
  }

  const requestEvent = {
    id: record.id,
    request: record.request,
    createdAtMs: record.createdAtMs,
    expiresAtMs: record.expiresAtMs,
  };

  if (created) {
    params.context.broadcast("cron.approval.requested", requestEvent, { dropIfSlow: true });
    params.context.broadcast("plugin.approval.requested", requestEvent, { dropIfSlow: true });
  }

  const hasApprovalClients =
    params.context.hasExecApprovalClients?.(params.client?.connId) ?? false;
  if (!hasApprovalClients && created) {
    manager.expire(record.id, "no-approval-route");
  }

  params.respond(
    true,
    {
      status: "hold",
      terminal: "HOLD_APPROVAL_REQUIRED",
      id: record.id,
      approvalKind: "cron.guarded_update",
      requestDigest,
      actionDigest,
      createdAtMs: record.createdAtMs,
      expiresAtMs: record.expiresAtMs,
      eligibleSurfaces: ["control-ui"],
      validation: validationResult,
    },
    undefined,
  );
}

function listConfiguredAnnounceChannelIds(cfg: OpenClawConfig): string[] {
  return listConfiguredAnnounceChannelIdsForConfig({
    config: cfg,
    env: process.env,
  });
}

function assertConfiguredAnnounceChannel(params: {
  cfg: OpenClawConfig;
  channel?: string;
  field: "delivery.channel" | "delivery.failureDestination.channel";
}) {
  if (params.channel === "last") {
    return;
  }

  const configuredChannels = listConfiguredAnnounceChannelIds(params.cfg).toSorted();
  const normalizedChannel = normalizeMessageChannel(params.channel);
  if (!normalizedChannel) {
    if (configuredChannels.length <= 1) {
      return;
    }
    throw new Error(
      `${params.field} is required when multiple channels are configured: ${configuredChannels.join(", ")}`,
    );
  }

  if (configuredChannels.length === 0) {
    return;
  }

  if (configuredChannels.includes(normalizedChannel)) {
    return;
  }

  throw new Error(`${params.field} must be one of: ${configuredChannels.join(", ")}`);
}

function resolveAnnounceValidationChannel(params: {
  channel?: string;
  to?: string;
}): string | undefined {
  if (params.channel && params.channel !== "last") {
    return params.channel;
  }
  return resolveTargetPrefixedChannel(params.to) ?? params.channel;
}

function assertCompatibleAnnounceTarget(params: {
  channel?: string;
  to?: string;
  field: "delivery.channel" | "delivery.failureDestination.channel";
}) {
  if (!params.channel || params.channel === "last") {
    return;
  }
  const error = validateTargetProviderPrefix({
    channel: params.channel,
    to: params.to,
  });
  if (error) {
    throw new Error(`${params.field}: ${error.message}`);
  }
}

function assertValidCronAnnounceDelivery(params: { cfg: OpenClawConfig; delivery?: CronDelivery }) {
  if (params.delivery && (params.delivery.mode ?? "announce") === "announce") {
    assertCompatibleAnnounceTarget({
      channel: params.delivery.channel,
      to: params.delivery.to,
      field: "delivery.channel",
    });
    assertConfiguredAnnounceChannel({
      cfg: params.cfg,
      channel: resolveAnnounceValidationChannel({
        channel: params.delivery.channel,
        to: params.delivery.to,
      }),
      field: "delivery.channel",
    });
  }

  const failureDestination = params.delivery?.failureDestination;
  if (failureDestination && (failureDestination.mode ?? "announce") === "announce") {
    assertCompatibleAnnounceTarget({
      channel: failureDestination.channel,
      to: failureDestination.to,
      field: "delivery.failureDestination.channel",
    });
    assertConfiguredAnnounceChannel({
      cfg: params.cfg,
      channel: resolveAnnounceValidationChannel({
        channel: failureDestination.channel,
        to: failureDestination.to,
      }),
      field: "delivery.failureDestination.channel",
    });
  }
}

function assertValidCronCreateDelivery(cfg: OpenClawConfig, jobCreate: CronJobCreate) {
  assertValidCronAnnounceDelivery({
    cfg,
    delivery: jobCreate.delivery,
  });
}

function assertValidCronUpdateDelivery(params: {
  cfg: OpenClawConfig;
  defaultAgentId?: string;
  currentJob: CronJob | undefined;
  patch: CronJobPatch;
}) {
  if (!params.currentJob || !("delivery" in params.patch)) {
    return;
  }

  const nextJob = structuredClone(params.currentJob);
  applyJobPatch(nextJob, params.patch, {
    defaultAgentId: params.defaultAgentId,
  });
  assertValidCronAnnounceDelivery({
    cfg: params.cfg,
    delivery: nextJob.delivery,
  });
}

function isClientIdentitySpoofFieldPresent(value: unknown): boolean {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    record.session_key !== undefined ||
    record.sessionKey !== undefined ||
    record.admin_identity !== undefined ||
    record.adminIdentity !== undefined ||
    record.authenticated_identity !== undefined ||
    record.authenticatedIdentity !== undefined
  );
}

function resolveGuardedCronCaller(params: {
  client: GatewayClient | null;
}): GuardedCronCallerContext {
  const scopes = params.client?.connect.scopes ?? [];
  const caps = params.client?.connect.caps ?? [];
  const permissions = params.client?.connect.permissions ?? {};
  const role = params.client?.connect.role;
  const sessionKey =
    params.client?.trustedSessionKey ??
    (params.client?.connId ? `gateway-connection:${params.client.connId}` : "");
  const authenticatedIdentity =
    params.client?.trustedAuthenticatedIdentity ?? params.client?.connect.client.id ?? "";
  const adminSchedulerEnabledState =
    role === "admin" ||
    scopes.includes(ADMIN_SCOPE) ||
    scopes.includes("admin.scheduler.enabled-state") ||
    caps.includes("admin.scheduler.enabled-state") ||
    permissions[ADMIN_SCOPE] === true ||
    permissions["admin.scheduler.enabled-state"] === true;
  const capabilities = new Set<string>();
  if (adminSchedulerEnabledState) {
    capabilities.add("admin.scheduler.enabled-state");
  }
  for (const cap of caps) {
    capabilities.add(cap);
  }
  for (const scope of scopes) {
    capabilities.add(scope);
  }
  const channelKind =
    params.client?.trustedChannelKind ??
    (sessionKey.includes(":group:") ||
    sessionKey.includes(":channel:") ||
    sessionKey.includes(":thread:")
      ? "group"
      : params.client
        ? "direct"
        : "shared");
  return {
    sessionKey,
    authenticatedIdentity,
    isAdmin: Boolean(params.client) && adminSchedulerEnabledState,
    capabilities: [...capabilities].toSorted(),
    connectionId: params.client?.connId,
    channelKind,
  };
}

export function buildGuardedCronInternalCommand(params: {
  params: Record<string, unknown>;
  client: GatewayClient | null;
  requireApproval: boolean;
}): GuardedCronInternalCommand {
  if (isClientIdentitySpoofFieldPresent(params.params)) {
    throw new Error("guarded cron update rejects client-supplied session/admin identity fields");
  }
  const approvalRaw = params.params.approval;
  if (isClientIdentitySpoofFieldPresent(approvalRaw)) {
    throw new Error("guarded cron update rejects client-supplied approval identity fields");
  }
  const { approval: _approval, ...requestRaw } = params.params;
  const request = normalizeGuardedUpdateRequest(requestRaw);
  const caller = resolveGuardedCronCaller({ client: params.client });
  assertAuthorizedGuardedUpdateCaller(caller);
  const approval = params.requireApproval
    ? normalizeVerifiedGuardedCronApproval(approvalRaw, caller)
    : undefined;
  if (
    params.requireApproval &&
    approval?.requestDigest !== computeGuardedUpdateRequestDigest(request)
  ) {
    throw new Error("cron.guarded_update approval request digest mismatch");
  }
  return { request, caller, approval };
}

export const cronHandlers: GatewayRequestHandlers = {
  wake: ({ params, respond, context }) => {
    if (!validateWakeParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid wake params: ${formatValidationErrors(validateWakeParams.errors)}`,
        ),
      );
      return;
    }
    const p = params as {
      mode: "now" | "next-heartbeat";
      text: string;
    };
    const result = context.cron.wake({ mode: p.mode, text: p.text });
    respond(true, result, undefined);
  },
  "cron.list": async ({ params, respond, context }) => {
    if (!validateCronListParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.list params: ${formatValidationErrors(validateCronListParams.errors)}`,
        ),
      );
      return;
    }
    const p = params as {
      includeDisabled?: boolean;
      limit?: number;
      offset?: number;
      query?: string;
      enabled?: "all" | "enabled" | "disabled";
      sortBy?: "nextRunAtMs" | "updatedAtMs" | "name";
      sortDir?: "asc" | "desc";
    };
    const page = await context.cron.listPage({
      includeDisabled: p.includeDisabled,
      limit: p.limit,
      offset: p.offset,
      query: p.query,
      enabled: p.enabled,
      sortBy: p.sortBy,
      sortDir: p.sortDir,
    });
    const deliveryPreviews = await resolveCronDeliveryPreviews({
      cfg: context.getRuntimeConfig(),
      defaultAgentId: context.cron.getDefaultAgentId(),
      jobs: page.jobs,
    });
    respond(true, { ...page, deliveryPreviews }, undefined);
  },
  "cron.status": async ({ params, respond, context }) => {
    if (!validateCronStatusParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.status params: ${formatValidationErrors(validateCronStatusParams.errors)}`,
        ),
      );
      return;
    }
    const status = await context.cron.status();
    respond(true, status, undefined);
  },
  "cron.add": async ({ params, respond, context }) => {
    const sessionKey =
      typeof (params as { sessionKey?: unknown } | null)?.sessionKey === "string"
        ? (params as { sessionKey: string }).sessionKey
        : undefined;
    let normalized: unknown;
    try {
      normalized =
        normalizeCronJobCreate(params, {
          sessionContext: { sessionKey },
        }) ?? params;
    } catch (err) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.add params: ${formatErrorMessage(err)}`,
        ),
      );
      return;
    }
    if (!validateCronAddParams(normalized)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.add params: ${formatValidationErrors(validateCronAddParams.errors)}`,
        ),
      );
      return;
    }
    const jobCreate = normalized as unknown as CronJobCreate;
    const cfg = context.getRuntimeConfig();
    const timestampValidation = validateScheduleTimestamp(jobCreate.schedule);
    if (!timestampValidation.ok) {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, timestampValidation.message),
      );
      return;
    }
    try {
      assertValidCronCreateDelivery(cfg, jobCreate);
    } catch (err) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.add params: ${formatErrorMessage(err)}`,
        ),
      );
      return;
    }
    let job: Awaited<ReturnType<typeof context.cron.add>>;
    try {
      job = await context.cron.add(jobCreate);
    } catch (err) {
      if (!(err instanceof TypeError) && !(err instanceof RangeError)) {
        throw err;
      }
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.add params: ${formatErrorMessage(err)}`,
        ),
      );
      return;
    }
    context.logGateway.info("cron: job created", { jobId: job.id, schedule: jobCreate.schedule });
    respond(true, job, undefined);
  },
  "cron.validate_update": async ({ params, respond, context, client }) => {
    if (!validateCronValidateGuardedUpdateParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.validate_update params: ${formatValidationErrors(validateCronValidateGuardedUpdateParams.errors)}`,
        ),
      );
      return;
    }
    try {
      const p = params as Record<string, unknown>;
      const result = await context.cron.validateGuardedUpdate(
        buildGuardedCronInternalCommand({ params: p, client, requireApproval: false }),
      );
      respond(true, result, undefined);
    } catch (err) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.validate_update params: ${formatErrorMessage(err)}`,
        ),
      );
    }
  },
  "cron.guarded_update": async ({ params, respond, context, client }) => {
    const p = params as Record<string, unknown> | null;
    const approvalMissing = !p || p.approval == null;
    if (!validateCronGuardedUpdateParams(params)) {
      if (approvalMissing && validateCronValidateGuardedUpdateParams(params)) {
        await handleCronGuardedUpdateApprovalRequest({
          params: params as Record<string, unknown>,
          respond,
          context,
          client,
        });
        return;
      }
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.guarded_update params: ${formatValidationErrors(validateCronGuardedUpdateParams.errors)}`,
        ),
      );
      return;
    }
    if (approvalMissing) {
      await handleCronGuardedUpdateApprovalRequest({
        params: params as Record<string, unknown>,
        respond,
        context,
        client,
      });
      return;
    }
    const approvedParams = p as Record<string, unknown>;
    try {
      const result = await context.cron.guardedUpdate(
        buildGuardedCronInternalCommand({ params: approvedParams, client, requireApproval: true }),
      );
      const jobId = String(approvedParams.job_id ?? approvedParams.jobId ?? approvedParams.id);
      context.logGateway.info("cron: guarded enabled-state update completed", { jobId });
      respond(true, result, undefined);
    } catch (err) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.guarded_update params: ${formatErrorMessage(err)}`,
        ),
      );
    }
  },
  "cron.approval.resolve": async ({ params, respond, context, client }) => {
    await handleCronApprovalResolve({ params, respond, context, client });
  },
  "cron.update": async ({ params, respond, context }) => {
    let normalizedPatch: ReturnType<typeof normalizeCronJobPatch>;
    try {
      normalizedPatch = normalizeCronJobPatch((params as { patch?: unknown } | null)?.patch);
    } catch (err) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.update params: ${formatErrorMessage(err)}`,
        ),
      );
      return;
    }
    const candidate =
      normalizedPatch && typeof params === "object" && params !== null
        ? { ...params, patch: normalizedPatch }
        : params;
    if (!validateCronUpdateParams(candidate)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.update params: ${formatValidationErrors(validateCronUpdateParams.errors)}`,
        ),
      );
      return;
    }
    const p = candidate as {
      id?: string;
      jobId?: string;
      patch: Record<string, unknown>;
    };
    const jobId = p.id ?? p.jobId;
    if (!jobId) {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, "invalid cron.update params: missing id"),
      );
      return;
    }
    const patch = p.patch as unknown as CronJobPatch;
    const cfg = context.getRuntimeConfig();
    if (patch.schedule) {
      const timestampValidation = validateScheduleTimestamp(patch.schedule);
      if (!timestampValidation.ok) {
        respond(
          false,
          undefined,
          errorShape(ErrorCodes.INVALID_REQUEST, timestampValidation.message),
        );
        return;
      }
    }
    try {
      assertValidCronUpdateDelivery({
        cfg,
        defaultAgentId: context.cron.getDefaultAgentId(),
        currentJob: context.cron.getJob(jobId),
        patch,
      });
    } catch (err) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.update params: ${formatErrorMessage(err)}`,
        ),
      );
      return;
    }
    let job: Awaited<ReturnType<typeof context.cron.update>>;
    try {
      job = await context.cron.update(jobId, patch);
    } catch (err) {
      if (!(err instanceof TypeError) && !(err instanceof RangeError)) {
        throw err;
      }
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.update params: ${formatErrorMessage(err)}`,
        ),
      );
      return;
    }
    context.logGateway.info("cron: job updated", { jobId });
    respond(true, job, undefined);
  },
  "cron.remove": async ({ params, respond, context }) => {
    if (!validateCronRemoveParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.remove params: ${formatValidationErrors(validateCronRemoveParams.errors)}`,
        ),
      );
      return;
    }
    const p = params as { id?: string; jobId?: string };
    const jobId = p.id ?? p.jobId;
    if (!jobId) {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, "invalid cron.remove params: missing id"),
      );
      return;
    }
    const result = await context.cron.remove(jobId);
    if (result.removed) {
      context.logGateway.info("cron: job removed", { jobId });
    }
    respond(true, result, undefined);
  },
  "cron.run": async ({ params, respond, context }) => {
    if (!validateCronRunParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.run params: ${formatValidationErrors(validateCronRunParams.errors)}`,
        ),
      );
      return;
    }
    const p = params as { id?: string; jobId?: string; mode?: "due" | "force" };
    const jobId = p.id ?? p.jobId;
    if (!jobId) {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, "invalid cron.run params: missing id"),
      );
      return;
    }
    let result: Awaited<ReturnType<typeof context.cron.enqueueRun>>;
    try {
      result = await context.cron.enqueueRun(jobId, p.mode ?? "force");
    } catch (error) {
      if (isInvalidCronSessionTargetIdError(error)) {
        respond(true, { ok: true, ran: false, reason: "invalid-spec" }, undefined);
        return;
      }
      throw error;
    }
    respond(true, result, undefined);
  },
  "cron.runs": async ({ params, respond, context }) => {
    if (!validateCronRunsParams(params)) {
      respond(
        false,
        undefined,
        errorShape(
          ErrorCodes.INVALID_REQUEST,
          `invalid cron.runs params: ${formatValidationErrors(validateCronRunsParams.errors)}`,
        ),
      );
      return;
    }
    const p = params as {
      scope?: "job" | "all";
      id?: string;
      jobId?: string;
      limit?: number;
      offset?: number;
      statuses?: Array<"ok" | "error" | "skipped">;
      status?: "all" | "ok" | "error" | "skipped";
      deliveryStatuses?: Array<"delivered" | "not-delivered" | "unknown" | "not-requested">;
      deliveryStatus?: "delivered" | "not-delivered" | "unknown" | "not-requested";
      query?: string;
      sortDir?: "asc" | "desc";
    };
    const explicitScope = p.scope;
    const jobId = p.id ?? p.jobId;
    const scope: "job" | "all" = explicitScope ?? (jobId ? "job" : "all");
    if (scope === "job" && !jobId) {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, "invalid cron.runs params: missing id"),
      );
      return;
    }
    if (scope === "all") {
      const jobs = await context.cron.list({ includeDisabled: true });
      const jobNameById = Object.fromEntries(
        jobs
          .filter((job) => typeof job.id === "string" && typeof job.name === "string")
          .map((job) => [job.id, job.name]),
      );
      const page = await readCronRunLogEntriesPageAll({
        storePath: context.cronStorePath,
        limit: p.limit,
        offset: p.offset,
        statuses: p.statuses,
        status: p.status,
        deliveryStatuses: p.deliveryStatuses,
        deliveryStatus: p.deliveryStatus,
        query: p.query,
        sortDir: p.sortDir,
        jobNameById,
      });
      respond(true, page, undefined);
      return;
    }
    let logPath: string;
    try {
      logPath = resolveCronRunLogPath({
        storePath: context.cronStorePath,
        jobId: jobId as string,
      });
    } catch {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, "invalid cron.runs params: invalid id"),
      );
      return;
    }
    const page = await readCronRunLogEntriesPage(logPath, {
      limit: p.limit,
      offset: p.offset,
      jobId: jobId as string,
      statuses: p.statuses,
      status: p.status,
      deliveryStatuses: p.deliveryStatuses,
      deliveryStatus: p.deliveryStatus,
      query: p.query,
      sortDir: p.sortDir,
    });
    respond(true, page, undefined);
  },
};
