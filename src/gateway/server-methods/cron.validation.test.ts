import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChannelPlugin } from "../../channels/plugins/types.public.js";
import type { OpenClawConfig } from "../../config/types.openclaw.js";
import type { CronJob } from "../../cron/types.js";
import { resetPluginRuntimeStateForTest, setActivePluginRegistry } from "../../plugins/runtime.js";
import {
  createChannelTestPluginBase,
  createTestRegistry,
} from "../../test-utils/channel-plugins.js";

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
    },
    getRuntimeConfig: () => getRuntimeConfig(),
  };
}

function createAdminClient(sessionKey = "agent:main:telegram:direct:8495203551") {
  return {
    connect: {
      minProtocol: 1,
      maxProtocol: 1,
      client: { id: "stick", version: "test", platform: "test", mode: "cli" },
      scopes: ["operator.admin"],
    },
    connId: "conn-1",
    sessionKey,
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
  session_key: "agent:main:telegram:direct:8495203551",
  admin_identity: "stick",
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
    job_id: "cron-1",
    enabled: true,
    expected_definition_sha: "a".repeat(64),
    expected_revision: "1",
    request_digest: "b".repeat(64),
    expires_at_ms: 1_800_000_000_000,
  },
} as const;

async function invokeGuardedCron(method: "cron.validate_update" | "cron.guarded_update", params: Record<string, unknown>, client = createAdminClient()) {
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
      guardedValidationParams,
      expect.objectContaining({
        authenticated: true,
        adminSchedulerEnabledState: true,
        sessionKey: "agent:main:telegram:direct:8495203551",
        adminIdentity: "stick",
      }),
    );
    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(true, { ok: true, dryRun: true }, undefined);
  });

  it("routes cron.guarded_update to guarded service and rejects missing approval", async () => {
    const { context, respond } = await invokeGuardedCron("cron.guarded_update", guardedUpdateParams);
    expect(context.cron.guardedUpdate).toHaveBeenCalledWith(
      guardedUpdateParams,
      expect.objectContaining({ adminSchedulerEnabledState: true }),
    );
    expect(context.cron.update).not.toHaveBeenCalled();
    expect(respond).toHaveBeenCalledWith(true, { ok: true, dryRun: false }, undefined);

    const missingApproval = await invokeGuardedCron(
      "cron.guarded_update",
      guardedValidationParams,
    );
    expect(missingApproval.context.cron.guardedUpdate).not.toHaveBeenCalled();
    expect(missingApproval.respond.mock.calls[0]?.[0]).toBe(false);
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
