import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChannelPlugin } from "../../channels/plugins/types.public.js";
import type { OpenClawConfig } from "../../config/types.openclaw.js";
import {
  computeGuardedUpdateActionDigest,
  computeGuardedUpdateRequestDigest,
  normalizeGuardedUpdateRequest,
} from "../../cron/service/guarded-update.js";
import type { CronJob } from "../../cron/types.js";
import type { PluginApprovalRequestPayload } from "../../infra/plugin-approvals.js";
import { resetPluginRuntimeStateForTest, setActivePluginRegistry } from "../../plugins/runtime.js";
import {
  createChannelTestPluginBase,
  createTestRegistry,
} from "../../test-utils/channel-plugins.js";
import { ExecApprovalManager } from "../exec-approval-manager.js";

const getRuntimeConfig = vi.hoisted(() =>
  vi.fn<() => OpenClawConfig>(() => ({}) as OpenClawConfig),
);

vi.mock("../../config/config.js", async () => {
  const actual =
    await vi.importActual<typeof import("../../config/config.js")>("../../config/config.js");
  return {
    ...actual,
    getRuntimeConfig,
  };
});

import { cronHandlers } from "./cron.js";
import { createPluginApprovalHandlers } from "./plugin-approval.js";

function createPrefixOnlyChannelPlugin(
  id: string,
  targetPrefixes: readonly string[],
  aliases?: readonly string[],
): ChannelPlugin {
  const base = createChannelTestPluginBase({ id });
  return {
    ...base,
    meta: {
      ...base.meta,
      ...(aliases ? { aliases } : {}),
    },
    messaging: { targetPrefixes },
  };
}

function setCronValidationTestRegistry(): void {
  setActivePluginRegistry(
    createTestRegistry([
      {
        pluginId: "telegram",
        plugin: createPrefixOnlyChannelPlugin("telegram", ["telegram", "tg"]),
        source: "test:telegram",
      },
      {
        pluginId: "slack",
        plugin: createPrefixOnlyChannelPlugin("slack", ["slack"]),
        source: "test:slack",
      },
      {
        pluginId: "msteams",
        plugin: createPrefixOnlyChannelPlugin("msteams", ["msteams", "teams"], ["teams"]),
        source: "test:msteams",
      },
      {
        pluginId: "synology-chat",
        plugin: createPrefixOnlyChannelPlugin("synology-chat", [
          "synology-chat",
          "synology_chat",
          "synology",
        ]),
        source: "test:synology-chat",
      },
    ]),
  );
}

function createCronContext(currentJob?: CronJob) {
  const broadcasts: Array<{ event: string; payload: unknown }> = [];
  const pluginApprovalManager = new ExecApprovalManager<PluginApprovalRequestPayload>();
  return {
    cron: {
      add: vi.fn(async () => ({ id: "cron-1" })),
      update: vi.fn(async () => ({ id: "cron-1" })),
      validateGuardedUpdate: vi.fn(async () => ({ ok: true, dryRun: true })),
      guardedUpdate: vi.fn(async () => ({ ok: true, dryRun: false })),
      getDefaultAgentId: vi.fn(() => "main"),
      getJob: vi.fn(() => currentJob),
    },
    logGateway: {
      info: vi.fn(),
      error: vi.fn(),
    },
    getRuntimeConfig: () => getRuntimeConfig(),
    pluginApprovalManager,
    hasExecApprovalClients: vi.fn(() => false),
    broadcast: vi.fn((event: string, payload: unknown) => {
      broadcasts.push({ event, payload });
    }),
    broadcasts,
  };
}

function createAdminClient(
  sessionKey = "agent:main:telegram:direct:8495203551",
  opts: {
    scopes?: string[];
    trustedChannelKind?: "direct" | "group" | "shared" | "system";
    trustedAuthenticatedIdentity?: string;
    connId?: string;
  } = {},
) {
  return {
    connect: {
      minProtocol: 1,
      maxProtocol: 1,
      client: { id: "stick", version: "test", platform: "test", mode: "cli" },
      scopes: opts.scopes ?? ["operator.admin"],
    },
    connId: opts.connId ?? "conn-1",
    trustedSessionKey: sessionKey,
    trustedAuthenticatedIdentity: opts.trustedAuthenticatedIdentity ?? "stick",
    trustedChannelKind: opts.trustedChannelKind ?? "direct",
  };
}

const guardedValidationParams = {
  job_id: "cron-1",
  patch: { enabled: true },
  preconditions: {
    expected_enabled: false,
    expected_revision: "1",
    expected_definition_sha: "a".repeat(64),
  },
  execution_policy: { run_immediately: false, catch_up: false },
  reason: "protected memory writer resume",
} as const;

const guardedRequestDigest = computeGuardedUpdateRequestDigest(
  normalizeGuardedUpdateRequest(guardedValidationParams),
);
const guardedActionDigest = computeGuardedUpdateActionDigest({
  request: normalizeGuardedUpdateRequest(guardedValidationParams),
  caller: {
    sessionKey: "agent:main:telegram:direct:8495203551",
    authenticatedIdentity: "stick",
    isAdmin: true,
    capabilities: ["admin.scheduler.enabled-state", "operator.admin"],
    connectionId: "conn-1",
    channelKind: "direct",
  },
  requestDigest: guardedRequestDigest,
});

const guardedUpdateParams = {
  ...guardedValidationParams,
  approval: {
    approval_kind: "cron.guarded_update",
    approval_id: "approval-1",
    nonce: "nonce-1",
    tool_name: "cron",
    action: "update",
    gateway_method: "cron.guarded_update",
    job_id: "cron-1",
    enabled: true,
    expected_enabled: false,
    expected_definition_sha: "a".repeat(64),
    expected_revision: "1",
    run_immediately: false,
    catch_up: false,
    request_digest: guardedRequestDigest,
    action_digest: guardedActionDigest,
    expires_at_ms: 1_800_000_000_000,
  },
} as const;

async function invokeGuardedCron(
  method: "cron.validate_update" | "cron.guarded_update",
  params: Record<string, unknown>,
  client = createAdminClient(),
) {
  const context = createCronContext(createCronJob());
  const respond = vi.fn();
  await cronHandlers[method]({
    req: {} as never,
    params: params as never,
    respond: respond as never,
    context: context as never,
    client: client as never,
    isWebchatConnect: () => false,
  });
  return { context, respond };
}

async function invokeCronAdd(params: Record<string, unknown>) {
  const context = createCronContext();
  const respond = vi.fn();
  await cronHandlers["cron.add"]({
    req: {} as never,
    params: params as never,
    respond: respond as never,
    context: context as never,
    client: null,
    isWebchatConnect: () => false,
  });
  return { context, respond };
}

async function invokeCronUpdate(params: Record<string, unknown>, currentJob: CronJob) {
  const context = createCronContext(currentJob);
  const respond = vi.fn();
  await cronHandlers["cron.update"]({
    req: {} as never,
    params: params as never,
    respond: respond as never,
    context: context as never,
    client: null,
    isWebchatConnect: () => false,
  });
  return { context, respond };
}

function cronApprovalIdFromBroadcasts(
  broadcasts: Array<{ event: string; payload: unknown }>,
): string {
  const payload = broadcasts.find((entry) => entry.event === "cron.approval.requested")?.payload as
    | { id?: string }
    | undefined;
  if (!payload?.id) {
    throw new Error("cron.approval.requested broadcast missing");
  }
  return payload.id;
}

function createCronJob(overrides: Partial<CronJob> = {}): CronJob {
  return {
    id: "cron-1",
    name: "cron job",
    enabled: true,
    createdAtMs: 1,
    updatedAtMs: 1,
    schedule: { kind: "every", everyMs: 60_000 },
    sessionTarget: "isolated",
    wakeMode: "next-heartbeat",
    payload: { kind: "agentTurn", message: "hello" },
    delivery: { mode: "none" },
    state: {},
    ...overrides,
  };
}

describe("cron method validation", () => {
  beforeEach(() => {
    getRuntimeConfig.mockReset().mockReturnValue({} as OpenClawConfig);
    setCronValidationTestRegistry();
  });

  afterEach(() => {
    resetPluginRuntimeStateForTest();
  });

  it("routes cron.validate_update to guarded dry-run service without broad update", async () => {
    const { context, respond } = await invokeGuardedCron(
      "cron.validate_update",
      guardedValidationParams,
    );

    expect(context.cron.validateGuardedUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        request: expect.objectContaining({ jobId: "cron-1", patch: { enabled: true } }),
        caller: expect.objectContaining({
          isAdmin: true,
          capabilities: expect.arrayContaining(["admin.scheduler.enabled-state"]),
          sessionKey: "agent:main:telegram:direct:8495203551",
          authenticatedIdentity: "stick",
          channelKind: "direct",
        }),
      }),
    );
    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(true, { ok: true, dryRun: true }, undefined);
  });

  it("routes cron.guarded_update to guarded service and surfaces missing approval as a typed HOLD request", async () => {
    const { context, respond } = await invokeGuardedCron(
      "cron.guarded_update",
      guardedUpdateParams,
    );
    expect(context.cron.guardedUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        request: expect.objectContaining({ jobId: "cron-1", patch: { enabled: true } }),
        caller: expect.objectContaining({ isAdmin: true }),
        approval: expect.objectContaining({
          approvalKind: "cron.guarded_update",
          sessionKey: "agent:main:telegram:direct:8495203551",
          authenticatedIdentity: "stick",
          actionDigest: guardedActionDigest,
        }),
      }),
    );
    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(true, { ok: true, dryRun: false }, undefined);

    const missingApproval = await invokeGuardedCron("cron.guarded_update", guardedValidationParams);
    expect(missingApproval.context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(missingApproval.context.cron.validateGuardedUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        request: expect.objectContaining({ jobId: "cron-1", patch: { enabled: true } }),
        caller: expect.objectContaining({ isAdmin: true }),
      }),
    );
    const missingRequested = missingApproval.context.broadcasts.find(
      (entry) => entry.event === "cron.approval.requested",
    );
    expect(missingRequested).toEqual(
      expect.objectContaining({
        event: "cron.approval.requested",
        payload: expect.objectContaining({
          id: expect.stringMatching(/^cron:/),
          request: expect.objectContaining({
            approvalKind: "cron.guarded_update",
            gatewayMethod: "cron.guarded_update",
            action: "update",
            requestDigest: guardedRequestDigest,
            actionDigest: guardedActionDigest,
            jobId: "cron-1",
            enabled: true,
            eligibleSurfaces: ["control-ui"],
            allowedDecisions: ["allow-once", "deny"],
          }),
        }),
      }),
    );
    expect(missingApproval.respond).toHaveBeenCalledWith(
      true,
      expect.objectContaining({
        status: "hold",
        terminal: "HOLD_APPROVAL_REQUIRED",
        approvalKind: "cron.guarded_update",
        actionDigest: guardedActionDigest,
        eligibleSurfaces: ["control-ui"],
      }),
      undefined,
    );
  });

  it("does not mutate when a surfaced cron guarded update approval is denied", async () => {
    const context = createCronContext(createCronJob());
    context.hasExecApprovalClients.mockReturnValue(true);
    const respond = vi.fn();
    await cronHandlers["cron.guarded_update"]({
      req: {} as never,
      params: guardedValidationParams as never,
      respond: respond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    const approvalId = cronApprovalIdFromBroadcasts(context.broadcasts);
    const resolveRespond = vi.fn();
    await cronHandlers["cron.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "deny" } as never,
      respond: resolveRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    expect(context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(respond.mock.calls[0]?.[0]).toBe(true);
    expect(resolveRespond).toHaveBeenCalledWith(
      true,
      expect.objectContaining({ terminal: "CRON_APPROVAL_DENIED_ZERO_MUTATION" }),
      undefined,
    );
  });

  it("allows a surfaced cron guarded update exactly once across duplicate requests", async () => {
    const context = createCronContext(createCronJob());
    context.hasExecApprovalClients.mockReturnValue(true);
    const respondA = vi.fn();
    const respondB = vi.fn();

    await cronHandlers["cron.guarded_update"]({
      req: {} as never,
      params: guardedValidationParams as never,
      respond: respondA as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });
    await cronHandlers["cron.guarded_update"]({
      req: {} as never,
      params: guardedValidationParams as never,
      respond: respondB as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    expect(
      context.broadcasts.filter((entry) => entry.event === "cron.approval.requested"),
    ).toHaveLength(1);
    const approvalId = cronApprovalIdFromBroadcasts(context.broadcasts);
    const resolveRespond = vi.fn();
    await cronHandlers["cron.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: resolveRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    expect(context.cron.guardedUpdate).toHaveBeenCalledTimes(1);
    expect(context.cron.guardedUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        approval: expect.objectContaining({
          approvalKind: "cron.guarded_update",
          approvalId,
          nonce: expect.stringMatching(/^cron:/),
          toolName: "cron",
          action: "update",
          gatewayMethod: "cron.guarded_update",
          sessionKey: "agent:main:telegram:direct:8495203551",
          authenticatedIdentity: "stick",
          requestDigest: guardedRequestDigest,
          actionDigest: guardedActionDigest,
        }),
      }),
    );
    expect(resolveRespond.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ terminal: "CRON_APPROVAL_ALLOW_ONCE_APPLIED" }),
    );

    const replayRespond = vi.fn();
    await cronHandlers["cron.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: replayRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });
    expect(context.cron.guardedUpdate).toHaveBeenCalledTimes(1);
    expect(replayRespond.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ terminal: "CRON_APPROVAL_DECISION_IDEMPOTENT" }),
    );
  });

  it("rejects plugin resolution for cron approvals and uses cron-specific resolution", async () => {
    const context = createCronContext(createCronJob());
    context.hasExecApprovalClients.mockReturnValue(true);
    const respond = vi.fn();
    await cronHandlers["cron.guarded_update"]({
      req: {} as never,
      params: guardedValidationParams as never,
      respond: respond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    const approvalId = cronApprovalIdFromBroadcasts(context.broadcasts);
    const pluginRespond = vi.fn();
    const pluginHandlers = createPluginApprovalHandlers(context.pluginApprovalManager);
    await pluginHandlers["plugin.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: pluginRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    expect(pluginRespond.mock.calls[0]?.[0]).toBe(false);
    expect(String(pluginRespond.mock.calls[0]?.[2]?.message)).toContain(
      "cannot resolve cron.guarded_update",
    );
    expect(context.cron.guardedUpdate).not.toHaveBeenCalled();

    const cronRespond = vi.fn();
    await cronHandlers["cron.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: cronRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });
    expect(cronRespond.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ terminal: "CRON_APPROVAL_ALLOW_ONCE_APPLIED" }),
    );
    expect(context.cron.guardedUpdate).toHaveBeenCalledTimes(1);
    expect(context.broadcasts.map((entry) => entry.event)).toContain("plugin.approval.resolved");
  });

  it("rejects cross-route and wrong-owner idempotent replay after cron approval resolution", async () => {
    const context = createCronContext(createCronJob());
    context.hasExecApprovalClients.mockReturnValue(true);
    const respond = vi.fn();
    await cronHandlers["cron.guarded_update"]({
      req: {} as never,
      params: guardedValidationParams as never,
      respond: respond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });

    const approvalId = cronApprovalIdFromBroadcasts(context.broadcasts);
    const cronRespond = vi.fn();
    await cronHandlers["cron.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: cronRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });
    expect(cronRespond.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ terminal: "CRON_APPROVAL_ALLOW_ONCE_APPLIED" }),
    );
    expect(context.cron.guardedUpdate).toHaveBeenCalledTimes(1);

    const pluginRespond = vi.fn();
    const pluginHandlers = createPluginApprovalHandlers(context.pluginApprovalManager);
    await pluginHandlers["plugin.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: pluginRespond as never,
      context: context as never,
      client: createAdminClient() as never,
      isWebchatConnect: () => false,
    });
    expect(pluginRespond.mock.calls[0]?.[0]).toBe(false);
    expect(String(pluginRespond.mock.calls[0]?.[2]?.message)).toContain(
      "cannot resolve cron.guarded_update",
    );

    const wrongOwnerRespond = vi.fn();
    await cronHandlers["cron.approval.resolve"]({
      req: {} as never,
      params: { id: approvalId, decision: "allow-once" } as never,
      respond: wrongOwnerRespond as never,
      context: context as never,
      client: createAdminClient("agent:main:telegram:direct:wrong-owner", {
        trustedAuthenticatedIdentity: "wrong-owner",
        connId: "conn-2",
      }) as never,
      isWebchatConnect: () => false,
    });
    expect(wrongOwnerRespond.mock.calls[0]?.[0]).toBe(false);
    expect(context.cron.guardedUpdate).toHaveBeenCalledTimes(1);
  });

  it("rejects spoofable client identity fields before the guarded service", async () => {
    const topLevelSpoof = await invokeGuardedCron("cron.validate_update", {
      ...guardedValidationParams,
      session_key: "agent:main:telegram:direct:spoof",
    });
    expect(topLevelSpoof.context.cron.validateGuardedUpdate).not.toHaveBeenCalled();
    expect(topLevelSpoof.respond.mock.calls[0]?.[0]).toBe(false);

    const approvalSpoof = await invokeGuardedCron("cron.guarded_update", {
      ...guardedUpdateParams,
      approval: { ...guardedUpdateParams.approval, admin_identity: "spoof" },
    });
    expect(approvalSpoof.context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(approvalSpoof.respond.mock.calls[0]?.[0]).toBe(false);

    const crossAction = await invokeGuardedCron("cron.guarded_update", {
      ...guardedUpdateParams,
      approval: { ...guardedUpdateParams.approval, action: "run" },
    });
    expect(crossAction.context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(crossAction.respond.mock.calls[0]?.[0]).toBe(false);

    const wrongOwner = await invokeGuardedCron("cron.guarded_update", {
      ...guardedUpdateParams,
      approval: {
        ...guardedUpdateParams.approval,
        session_key: "agent:main:telegram:direct:wrong-owner",
      },
    });
    expect(wrongOwner.context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(wrongOwner.respond.mock.calls[0]?.[0]).toBe(false);
  });

  it("derives caller context from trusted Gateway client state and denies group/shared/non-admin callers", async () => {
    const group = await invokeGuardedCron(
      "cron.validate_update",
      guardedValidationParams,
      createAdminClient("agent:main:telegram:group:-100", { trustedChannelKind: "group" }),
    );
    expect(group.context.cron.validateGuardedUpdate).not.toHaveBeenCalled();
    expect(group.respond.mock.calls[0]?.[0]).toBe(false);

    const shared = await invokeGuardedCron(
      "cron.validate_update",
      guardedValidationParams,
      createAdminClient("gateway-shared", { trustedChannelKind: "shared" }),
    );
    expect(shared.context.cron.validateGuardedUpdate).not.toHaveBeenCalled();
    expect(shared.respond.mock.calls[0]?.[0]).toBe(false);

    const nonAdmin = await invokeGuardedCron(
      "cron.validate_update",
      guardedValidationParams,
      createAdminClient("agent:main:telegram:direct:8495203551", { scopes: [] }),
    );
    expect(nonAdmin.context.cron.validateGuardedUpdate).not.toHaveBeenCalled();
    expect(nonAdmin.respond.mock.calls[0]?.[0]).toBe(false);
  });

  it("preserves broad cron.update routing for existing administrative callers", async () => {
    const current = createCronJob();
    const { context, respond } = await invokeCronUpdate(
      {
        id: "cron-1",
        patch: {
          schedule: { kind: "every", everyMs: 120_000 },
          payload: { kind: "agentTurn", message: "updated" },
          delivery: { mode: "none" },
        },
      },
      current,
    );

    expect(context.cron.update).toHaveBeenCalled();
    expect(context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(respond.mock.calls[0]?.[0]).toBe(true);
  });

  it("accepts threadId on announce delivery add params", async () => {
    getRuntimeConfig.mockReturnValue({
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronAdd({
      name: "topic announce add",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      sessionTarget: "isolated",
      wakeMode: "next-heartbeat",
      payload: { kind: "agentTurn", message: "hello" },
      delivery: {
        mode: "announce",
        channel: "telegram",
        to: "-1001234567890",
        threadId: 123,
      },
    });

    expect(context.cron.add).toHaveBeenCalledWith(
      expect.objectContaining({
        delivery: expect.objectContaining({
          mode: "announce",
          channel: "telegram",
          to: "-1001234567890",
          threadId: 123,
        }),
      }),
    );
    expect(respond).toHaveBeenCalledWith(true, { id: "cron-1" }, undefined);
  });

  it("accepts threadId on announce delivery update params", async () => {
    getRuntimeConfig.mockReturnValue({
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronUpdate(
      {
        id: "cron-1",
        patch: {
          delivery: {
            mode: "announce",
            channel: "telegram",
            to: "-1001234567890",
            threadId: "456",
          },
        },
      },
      createCronJob({
        delivery: { mode: "announce", channel: "telegram", to: "-1001234567890" },
      }),
    );

    expect(context.cron.update).toHaveBeenCalledWith(
      "cron-1",
      expect.objectContaining({
        delivery: expect.objectContaining({
          mode: "announce",
          channel: "telegram",
          to: "-1001234567890",
          threadId: "456",
        }),
      }),
    );
    expect(respond).toHaveBeenCalledWith(true, { id: "cron-1" }, undefined);
  });

  it("rejects execution-derived diagnostics in cron.update state patches", async () => {
    const { context, respond } = await invokeCronUpdate(
      {
        id: "cron-1",
        patch: {
          state: {
            lastDiagnostics: {
              summary: "forged",
              entries: [
                {
                  ts: 1,
                  source: "agent-run",
                  severity: "error",
                  message: "forged",
                },
              ],
            },
          },
        },
      },
      createCronJob(),
    );

    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        code: "INVALID_REQUEST",
      }),
    );
  });

  it("rejects ambiguous announce delivery on add when multiple channels are configured", async () => {
    getRuntimeConfig.mockReturnValue({
      session: {
        mainKey: "main",
      },
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
          slack: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronAdd({
      name: "ambiguous announce add",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      sessionTarget: "isolated",
      wakeMode: "next-heartbeat",
      payload: { kind: "agentTurn", message: "hello" },
      delivery: { mode: "announce" },
    });

    expect(context.cron.add).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        message: expect.stringContaining("delivery.channel is required"),
      }),
    );
  });

  it("accepts provider-prefixed announce target without delivery.channel when multiple channels are configured", async () => {
    getRuntimeConfig.mockReturnValue({
      session: {
        mainKey: "main",
      },
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
          slack: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronAdd({
      name: "prefixed announce add",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      sessionTarget: "isolated",
      wakeMode: "next-heartbeat",
      payload: { kind: "agentTurn", message: "hello" },
      delivery: { mode: "announce", to: "telegram:123" },
    });

    expect(context.cron.add).toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(true, { id: "cron-1" }, undefined);
  });

  it("rejects announce targets prefixed for a different explicit delivery channel", async () => {
    getRuntimeConfig.mockReturnValue({
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
          slack: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronAdd({
      name: "mismatched announce add",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      sessionTarget: "isolated",
      wakeMode: "next-heartbeat",
      payload: { kind: "agentTurn", message: "hello" },
      delivery: { mode: "announce", channel: "slack", to: "telegram:123" },
    });

    expect(context.cron.add).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        message: expect.stringContaining("belongs to telegram, not slack"),
      }),
    );
  });

  it("accepts provider-prefixed announce targets when delivery.channel uses a channel alias", async () => {
    getRuntimeConfig.mockReturnValue({
      channels: {
        msteams: {
          botToken: "teams-token",
        },
      },
      plugins: {
        entries: {
          msteams: { enabled: true },
        },
      },
    } as OpenClawConfig);

    for (const to of ["teams:19:meeting_abc@thread.tacv2", "msteams:19:meeting_abc@thread.tacv2"]) {
      const { context, respond } = await invokeCronAdd({
        name: `aliased announce add ${to}`,
        enabled: true,
        schedule: { kind: "every", everyMs: 60_000 },
        sessionTarget: "isolated",
        wakeMode: "next-heartbeat",
        payload: { kind: "agentTurn", message: "hello" },
        delivery: {
          mode: "announce",
          channel: "teams",
          to,
        },
      });

      expect(context.cron.add).toHaveBeenCalled();
      expect(respond).toHaveBeenCalledWith(true, { id: "cron-1" }, undefined);
    }
  });

  it("validates announce delivery patches that omit mode", async () => {
    getRuntimeConfig.mockReturnValue({
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
          slack: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronUpdate(
      {
        id: "cron-1",
        patch: {
          delivery: { channel: "slack", to: "telegram:123" },
        },
      },
      createCronJob({
        delivery: { mode: "announce", channel: "telegram", to: "123" },
      }),
    );

    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        message: expect.stringContaining("belongs to telegram, not slack"),
      }),
    );
  });

  it("rejects underscored provider prefixes for a different explicit delivery channel", async () => {
    getRuntimeConfig.mockReturnValue({
      channels: {
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
        "synology-chat": {
          token: "synology-token",
        },
      },
      plugins: {
        entries: {
          slack: { enabled: true },
          "synology-chat": { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronAdd({
      name: "underscored mismatch add",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      sessionTarget: "isolated",
      wakeMode: "next-heartbeat",
      payload: { kind: "agentTurn", message: "hello" },
      delivery: { mode: "announce", channel: "slack", to: "synology_chat:123" },
    });

    expect(context.cron.add).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        message: expect.stringContaining("belongs to synology-chat, not slack"),
      }),
    );
  });

  it("rejects ambiguous announce delivery on update when multiple channels are configured", async () => {
    getRuntimeConfig.mockReturnValue({
      session: {
        mainKey: "main",
      },
      channels: {
        telegram: {
          botToken: "telegram-token",
        },
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
      },
      plugins: {
        entries: {
          telegram: { enabled: true },
          slack: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronUpdate(
      {
        id: "cron-1",
        patch: {
          delivery: { mode: "announce" },
        },
      },
      createCronJob(),
    );

    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        message: expect.stringContaining("delivery.channel is required"),
      }),
    );
  });

  it("rejects target ids mistakenly supplied as delivery.channel providers", async () => {
    getRuntimeConfig.mockReturnValue({
      session: {
        mainKey: "main",
      },
      channels: {
        slack: {
          botToken: "xoxb-slack-token",
          appToken: "xapp-slack-token",
        },
      },
      plugins: {
        entries: {
          slack: { enabled: true },
        },
      },
    } as OpenClawConfig);

    const { context, respond } = await invokeCronAdd({
      name: "invalid delivery provider",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      sessionTarget: "isolated",
      wakeMode: "next-heartbeat",
      payload: { kind: "agentTurn", message: "hello" },
      delivery: {
        mode: "announce",
        channel: "C0AT2Q238MQ",
        to: "C0AT2Q238MQ",
      },
    });

    expect(context.cron.add).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        message: expect.stringContaining("delivery.channel must be one of: slack"),
      }),
    );
  });

  it("returns INVALID_REQUEST when cron.add throws a croner parse error (#74066)", async () => {
    const context = createCronContext();
    context.cron.add.mockRejectedValueOnce(new TypeError("CronPattern: Expected 5 or 6 fields"));
    const respond = vi.fn();
    await cronHandlers["cron.add"]({
      req: {} as never,
      params: {
        name: "bad-cron",
        enabled: true,
        schedule: { kind: "cron", cron: "not-a-cron-expr" },
        sessionTarget: "isolated",
        wakeMode: "next-heartbeat",
        payload: { kind: "agentTurn", message: "ping" },
      } as never,
      respond: respond as never,
      context: context as never,
      client: null,
      isWebchatConnect: () => false,
    });

    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        code: "INVALID_REQUEST",
        message: expect.stringContaining("CronPattern"),
      }),
    );
  });

  it("returns INVALID_REQUEST when cron.update throws a croner parse error (#74066)", async () => {
    const existingJob = createCronJob();
    const context = createCronContext(existingJob);
    context.cron.update.mockRejectedValueOnce(
      new RangeError("CronPattern: Value out of range (99)"),
    );
    const respond = vi.fn();
    await cronHandlers["cron.update"]({
      req: {} as never,
      params: {
        id: existingJob.id,
        patch: {
          schedule: { kind: "cron", cron: "99 * * * *" },
        },
      } as never,
      respond: respond as never,
      context: context as never,
      client: null,
      isWebchatConnect: () => false,
    });

    expect(respond).toHaveBeenCalledWith(
      false,
      undefined,
      expect.objectContaining({
        code: "INVALID_REQUEST",
        message: expect.stringContaining("CronPattern"),
      }),
    );
  });

  it("re-throws non-parse errors from cron.add instead of masking as INVALID_REQUEST", async () => {
    const context = createCronContext();
    context.cron.add.mockRejectedValueOnce(new Error("DB write failed"));
    const respond = vi.fn();
    await expect(
      cronHandlers["cron.add"]({
        req: {} as never,
        params: {
          name: "db-fail",
          enabled: true,
          schedule: { kind: "every", everyMs: 60_000 },
          sessionTarget: "isolated",
          wakeMode: "next-heartbeat",
          payload: { kind: "agentTurn", message: "ping" },
        } as never,
        respond: respond as never,
        context: context as never,
        client: null,
        isWebchatConnect: () => false,
      }),
    ).rejects.toThrow("DB write failed");
    expect(respond).not.toHaveBeenCalled();
  });
});
