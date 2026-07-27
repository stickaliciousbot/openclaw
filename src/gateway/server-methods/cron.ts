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
import {
  resolveTargetPrefixedChannel,
  validateTargetProviderPrefix,
} from "../../infra/outbound/channel-target-prefix.js";
import { listConfiguredAnnounceChannelIdsForConfig } from "../../plugins/channel-plugin-ids.js";
import { normalizeMessageChannel } from "../../utils/message-channel.js";
import { ADMIN_SCOPE } from "../method-scopes.js";
import {
  ErrorCodes,
  errorShape,
  formatValidationErrors,
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
import type { GatewayClient, GatewayRequestHandlers } from "./types.js";

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
    if (!validateCronGuardedUpdateParams(params)) {
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
    try {
      const p = params as Record<string, unknown>;
      const result = await context.cron.guardedUpdate(
        buildGuardedCronInternalCommand({ params: p, client, requireApproval: true }),
      );
      const jobId = String(p.job_id ?? p.jobId ?? p.id);
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
