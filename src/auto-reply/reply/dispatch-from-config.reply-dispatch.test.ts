import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import type { PluginHookReplyDispatchResult } from "../../plugins/hooks.js";
import { createInternalHookEventPayload } from "../../test-utils/internal-hook-event-payload.js";
import {
  acpManagerRuntimeMocks,
  acpMocks,
  agentEventMocks,
  createDispatcher,
  createHookCtx,
  diagnosticMocks,
  emptyConfig,
  hookMocks,
  internalHookMocks,
  mocks,
  resetPluginTtsAndThreadMocks,
  runtimePluginMocks,
  sessionBindingMocks,
  sessionStoreMocks,
  setDiscordTestRegistry,
} from "./dispatch-from-config.shared.test-harness.js";

let dispatchReplyFromConfig: typeof import("./dispatch-from-config.js").dispatchReplyFromConfig;
let resetInboundDedupe: typeof import("./inbound-dedupe.js").resetInboundDedupe;

describe("dispatchReplyFromConfig reply_dispatch hook", () => {
  beforeAll(async () => {
    ({ dispatchReplyFromConfig } = await import("./dispatch-from-config.js"));
    ({ resetInboundDedupe } = await import("./inbound-dedupe.js"));
  });

  beforeEach(() => {
    setDiscordTestRegistry();
    resetInboundDedupe();
    mocks.routeReply.mockReset().mockResolvedValue({ ok: true, messageId: "mock" });
    mocks.tryFastAbortFromMessage.mockReset().mockResolvedValue({
      handled: false,
      aborted: false,
    });
    hookMocks.runner.hasHooks.mockReset();
    hookMocks.runner.hasHooks.mockImplementation(
      (hookName?: string) => hookName === "reply_dispatch",
    );
    hookMocks.runner.runInboundClaim.mockReset().mockResolvedValue(undefined);
    hookMocks.runner.runInboundClaimForPlugin.mockReset().mockResolvedValue(undefined);
    hookMocks.runner.runInboundClaimForPluginOutcome.mockReset().mockResolvedValue({
      status: "no_handler",
    });
    hookMocks.runner.runMessageReceived.mockReset().mockResolvedValue(undefined);
    hookMocks.runner.runBeforeDispatch.mockReset().mockResolvedValue(undefined);
    hookMocks.runner.runReplyDispatch.mockReset().mockResolvedValue(undefined);
    internalHookMocks.createInternalHookEvent.mockReset();
    internalHookMocks.createInternalHookEvent.mockImplementation(createInternalHookEventPayload);
    internalHookMocks.triggerInternalHook.mockReset().mockResolvedValue(undefined);
    acpMocks.listAcpSessionEntries.mockReset().mockResolvedValue([]);
    acpMocks.readAcpSessionEntry.mockReset().mockReturnValue(null);
    acpMocks.upsertAcpSessionMeta.mockReset().mockResolvedValue(null);
    acpMocks.requireAcpRuntimeBackend.mockReset();
    sessionBindingMocks.listBySession.mockReset().mockReturnValue([]);
    sessionBindingMocks.resolveByConversation.mockReset().mockReturnValue(null);
    sessionBindingMocks.touch.mockReset();
    sessionStoreMocks.currentEntry = undefined;
    sessionStoreMocks.loadSessionStore.mockReset().mockReturnValue({});
    sessionStoreMocks.resolveStorePath.mockReset().mockReturnValue("/tmp/mock-sessions.json");
    sessionStoreMocks.resolveSessionStoreEntry.mockReset().mockReturnValue({ existing: undefined });
    sessionStoreMocks.updateSessionStoreEntry.mockClear();
    acpManagerRuntimeMocks.getAcpSessionManager.mockReset();
    acpManagerRuntimeMocks.getAcpSessionManager.mockImplementation(() => ({
      resolveSession: () => ({ kind: "none" as const }),
      getObservabilitySnapshot: () => ({
        runtimeCache: { activeSessions: 0, idleTtlMs: 0, evictedTotal: 0 },
        turns: {
          active: 0,
          queueDepth: 0,
          completed: 0,
          failed: 0,
          averageLatencyMs: 0,
          maxLatencyMs: 0,
        },
        errorsByCode: {},
      }),
      runTurn: vi.fn(),
    }));
    agentEventMocks.emitAgentEvent.mockReset();
    agentEventMocks.onAgentEvent.mockReset().mockImplementation(() => () => {});
    diagnosticMocks.logMessageQueued.mockReset();
    diagnosticMocks.logMessageProcessed.mockReset();
    diagnosticMocks.logSessionStateChange.mockReset();
    diagnosticMocks.markDiagnosticSessionProgress.mockReset();
    runtimePluginMocks.ensureRuntimePluginsLoaded.mockReset();
    resetPluginTtsAndThreadMocks();
  });

  it("returns handled dispatch results from plugins", async () => {
    hookMocks.runner.runReplyDispatch.mockResolvedValue({
      handled: true,
      queuedFinal: true,
      counts: { tool: 1, block: 2, final: 3 },
    });

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher: createDispatcher(),
      fastAbortResolver: async () => ({ handled: false, aborted: false }),
      formatAbortReplyTextResolver: () => "⚙️ Agent was aborted.",
      replyResolver: async () => ({ text: "model reply" }),
    });

    expect(runtimePluginMocks.ensureRuntimePluginsLoaded).toHaveBeenCalledWith({
      config: emptyConfig,
      workspaceDir: expect.any(String),
    });
    expect(hookMocks.runner.runReplyDispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        sessionKey: "agent:test:session",
        sendPolicy: "allow",
        inboundAudio: false,
      }),
      expect.objectContaining({
        cfg: emptyConfig,
      }),
    );
    expect(result).toEqual({
      queuedFinal: true,
      counts: { tool: 1, block: 2, final: 3 },
    });
  });
  it("still applies send-policy deny after an unhandled plugin dispatch", async () => {
    hookMocks.runner.runReplyDispatch.mockResolvedValue({
      handled: false,
      queuedFinal: false,
      counts: { tool: 0, block: 0, final: 0 },
    } satisfies PluginHookReplyDispatchResult);

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: {
        ...emptyConfig,
        session: {
          sendPolicy: { default: "deny" },
        },
      },
      dispatcher: createDispatcher(),
      replyResolver: async () => ({ text: "model reply" }),
    });

    expect(hookMocks.runner.runReplyDispatch).toHaveBeenCalled();
    expect(result).toEqual({
      queuedFinal: false,
      counts: { tool: 0, block: 0, final: 0 },
    });
  });

  it("clears pending final delivery after final dispatch succeeds", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
      pendingFinalDelivery: true,
      pendingFinalDeliveryText: "durable reply",
      pendingFinalDeliveryCreatedAt: 1,
      pendingFinalDeliveryLastAttemptAt: 2,
      pendingFinalDeliveryAttemptCount: 3,
      pendingFinalDeliveryLastError: "previous failure",
      pendingFinalDeliveryContext: { source: "heartbeat" },
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    mocks.routeReply.mockResolvedValue({ ok: true, messageId: "mock" });

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher: createDispatcher(),
      replyResolver: async () => ({ text: "durable reply" }),
    });

    expect(result.queuedFinal).toBe(true);
    expect(sessionStoreMocks.updateSessionStoreEntry).toHaveBeenCalledOnce();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDelivery).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryText).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryCreatedAt).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryLastAttemptAt).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryAttemptCount).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryLastError).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryContext).toBeUndefined();
  });

  it("does not clear pending closeout debt when only the normal final reply succeeds", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
      pendingFinalDelivery: true,
      pendingFinalDeliveryText: "durable reply",
      pendingCloseoutDelivery: true,
      pendingCloseoutDeliveryText: "closeout debt",
      pendingCloseoutDeliveryCreatedAt: 1,
      pendingCloseoutDeliveryLastAttemptAt: 2,
      pendingCloseoutDeliveryAttemptCount: 3,
      pendingCloseoutDeliveryLastError: "previous failure",
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    mocks.routeReply.mockResolvedValue({ ok: true, messageId: "mock" });

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher: createDispatcher(),
      replyResolver: async () => ({ text: "durable reply" }),
    });

    expect(result.queuedFinal).toBe(true);
    expect(sessionStoreMocks.updateSessionStoreEntry).toHaveBeenCalledOnce();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDelivery).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryText).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDelivery).toBe(true);
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryText).toBe("closeout debt");
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryCreatedAt).toBe(1);
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryLastAttemptAt).toBe(2);
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryAttemptCount).toBe(3);
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryLastError).toBe(
      "previous failure",
    );
  });

  it("clears pending closeout debt after the visible closeout reply succeeds", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
      pendingFinalDelivery: true,
      pendingFinalDeliveryText: "durable reply\n\ncloseout debt",
      pendingCloseoutDelivery: true,
      pendingCloseoutDeliveryText: "closeout debt",
      pendingCloseoutDeliveryCreatedAt: 1,
      pendingCloseoutDeliveryLastAttemptAt: 2,
      pendingCloseoutDeliveryAttemptCount: 3,
      pendingCloseoutDeliveryLastError: null,
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    mocks.routeReply.mockResolvedValue({ ok: true, messageId: "mock" });

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher: createDispatcher(),
      replyResolver: async () => [
        { text: "durable reply" },
        {
          text: "closeout debt",
          channelData: {
            openclawCloseoutDebtReplay: true,
            openclawCloseoutDelivered: true,
            openclawCloseoutPending: false,
          },
        },
      ],
    });

    expect(result.queuedFinal).toBe(true);
    expect(sessionStoreMocks.updateSessionStoreEntry).toHaveBeenCalledOnce();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDelivery).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryText).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDelivery).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryText).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryCreatedAt).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryLastAttemptAt).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryAttemptCount).toBeUndefined();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryLastError).toBeUndefined();
  });

  const liveReadToolResultCloseoutText = [
    JSON.stringify({
      title: "closeout finalpath source-valid package",
      details: { status: "failed" },
    }),
    JSON.stringify({
      title: "closeout finalpath source-valid package",
      status: "PASS",
      failedGates: [],
      requiredFilesMissing: [],
      productionMutation: false,
      evidenceFiles: ["status.json", "summary.json", "evidence_manifest.json"],
      closeoutDelivered: false,
      closeoutPending: true,
    }),
  ].join("\n");
  const expectedCloseoutText =
    "Closeout: PASS. No production mutation occurred. Evidence: status.json, summary.json, evidence_manifest.json.";

  it("projects a source-visible closeout from tool-result text onto direct Telegram final delivery", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    const dispatcher = createDispatcher();

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    expect(result.queuedFinal).toBe(true);
    expect(dispatcher.sendFinalReply).toHaveBeenCalledOnce();
    const sentPayload = vi.mocked(dispatcher.sendFinalReply).mock.calls[0]?.[0];
    expect(sentPayload?.text).toBe(`Normal final answer preserved.\n\n${expectedCloseoutText}`);
    expect(sentPayload?.text?.match(/Closeout: PASS/g)).toHaveLength(1);
    expect(sentPayload?.text).not.toContain("Failed: FAIL");
    expect(sentPayload?.text).not.toContain("Failed gates: none");
    expect(sentPayload?.channelData).toMatchObject({
      openclawCloseoutDelivered: true,
      openclawCloseoutPending: false,
    });
  });

  it("does not append a duplicate when the direct Telegram final text already contains the closeout", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    const dispatcher = createDispatcher();

    await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: `Normal final answer preserved.\n\n${expectedCloseoutText}` };
      },
    });

    const sentPayload = vi.mocked(dispatcher.sendFinalReply).mock.calls[0]?.[0];
    expect(sentPayload?.text?.match(/Closeout: PASS/g)).toHaveLength(1);
    expect(sentPayload?.channelData?.openclawCloseoutDelivered).toBeUndefined();
  });

  it("does not project tool-result closeout text onto group Telegram final delivery", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    const dispatcher = createDispatcher();

    await dispatchReplyFromConfig({
      ctx: { ...createHookCtx(), ChatType: "group" },
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    const sentPayload = vi.mocked(dispatcher.sendFinalReply).mock.calls[0]?.[0];
    expect(sentPayload?.text ?? "").not.toContain("Closeout: PASS");
  });

  it("does not project tool-result closeout text onto channel Telegram final delivery", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    const dispatcher = createDispatcher();

    await dispatchReplyFromConfig({
      ctx: { ...createHookCtx(), ChatType: "channel" },
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    const sentPayload = vi.mocked(dispatcher.sendFinalReply).mock.calls[0]?.[0];
    expect(sentPayload?.text ?? "").not.toContain("Closeout: PASS");
  });

  it("does not project tool-result closeout text for room_event direct Telegram delivery", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    const dispatcher = createDispatcher();
    const roomEventCtx = createHookCtx() as ReturnType<typeof createHookCtx> & {
      InboundEventKind: string;
    };
    roomEventCtx.InboundEventKind = "room_event";

    await dispatchReplyFromConfig({
      ctx: roomEventCtx,
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    const sentPayload = vi.mocked(dispatcher.sendFinalReply).mock.calls[0]?.[0];
    expect(sentPayload?.text).toBe("Normal final answer preserved.");
  });

  it("does not project or persist closeout text when direct Telegram delivery is message-tool-only", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    const dispatcher = createDispatcher();

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: {
        ...emptyConfig,
        messages: { visibleReplies: "message_tool" },
      },
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    expect(result.queuedFinal).toBe(false);
    expect(dispatcher.sendFinalReply).not.toHaveBeenCalled();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDelivery).toBeUndefined();
    expect(sessionStoreMocks.updateSessionStoreEntry).not.toHaveBeenCalled();
  });

  it("does not project or persist closeout text when direct Telegram send policy denies delivery", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    const dispatcher = createDispatcher();

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: {
        ...emptyConfig,
        session: {
          sendPolicy: { default: "deny" },
        },
      },
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    expect(result.queuedFinal).toBe(false);
    expect(dispatcher.sendFinalReply).not.toHaveBeenCalled();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDelivery).toBeUndefined();
    expect(sessionStoreMocks.updateSessionStoreEntry).not.toHaveBeenCalled();
  });

  it("matches the production smoke order: tool-result line then next assistant delivery contains one closeout", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    const dispatcher = createDispatcher();
    const observedLines: Array<{ line: number; kind: "toolResult" | "assistant"; text?: string }> =
      [];

    await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        observedLines.push({
          line: 1124,
          kind: "toolResult",
          text: liveReadToolResultCloseoutText,
        });
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    const sentPayload = vi.mocked(dispatcher.sendFinalReply).mock.calls[0]?.[0];
    observedLines.push({ line: 1125, kind: "assistant", text: sentPayload?.text });
    expect(observedLines).toEqual([
      { line: 1124, kind: "toolResult", text: liveReadToolResultCloseoutText },
      {
        line: 1125,
        kind: "assistant",
        text: `Normal final answer preserved.\n\n${expectedCloseoutText}`,
      },
    ]);
    expect(sentPayload?.text?.match(/Closeout: PASS/g)).toHaveLength(1);
  });

  it("persists pending closeout debt when projected direct Telegram final delivery is not confirmed", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    const dispatcher = createDispatcher();
    vi.mocked(dispatcher.sendFinalReply).mockReturnValue(false);

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async (_ctx, options) => {
        await options?.onToolResult?.({ text: liveReadToolResultCloseoutText });
        return { text: "Normal final answer preserved." };
      },
    });

    expect(result.queuedFinal).toBe(false);
    expect(sessionStoreMocks.updateSessionStoreEntry).toHaveBeenCalledOnce();
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDelivery).toBe(true);
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryText).toBe(expectedCloseoutText);
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryText).toBe(
      `Normal final answer preserved.\n\n${expectedCloseoutText}`,
    );
    expect(sessionStoreMocks.currentEntry?.pendingCloseoutDeliveryLastError).toBe(
      "final_delivery_not_confirmed",
    );
  });

  it("preserves pending final delivery when final dispatch fails", async () => {
    hookMocks.runner.hasHooks.mockReturnValue(false);
    sessionStoreMocks.currentEntry = {
      sessionKey: "agent:test:session",
      pendingFinalDelivery: true,
      pendingFinalDeliveryText: "durable reply",
      pendingFinalDeliveryCreatedAt: 1,
    };
    sessionStoreMocks.resolveSessionStoreEntry.mockReturnValue({
      existing: sessionStoreMocks.currentEntry,
    });
    const dispatcher = createDispatcher();
    vi.mocked(dispatcher.sendFinalReply).mockReturnValue(false);

    const result = await dispatchReplyFromConfig({
      ctx: createHookCtx(),
      cfg: emptyConfig,
      dispatcher,
      replyResolver: async () => ({ text: "durable reply" }),
    });

    expect(result.queuedFinal).toBe(false);
    expect(sessionStoreMocks.updateSessionStoreEntry).not.toHaveBeenCalled();
    expect(sessionStoreMocks.currentEntry?.pendingFinalDelivery).toBe(true);
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryText).toBe("durable reply");
    expect(sessionStoreMocks.currentEntry?.pendingFinalDeliveryCreatedAt).toBe(1);
  });
});
