import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SessionEntry } from "../../config/sessions.js";
import type { TemplateContext } from "../templating.js";
import type { GetReplyOptions, ReplyPayload } from "../types.js";
import { createMockTypingController } from "./test-helpers.js";

const state = vi.hoisted(() => ({
  closeoutPayload: undefined as unknown,
  finalPayload: { text: "normal final report" } as ReplyPayload,
  runAgentTurnWithFallbackMock: vi.fn(),
}));

vi.mock("./agent-runner-execution.js", () => ({
  buildKnownAgentRunFailureReplyPayload: (error: unknown) => ({ text: String(error) }),
  runAgentTurnWithFallback: async (params: {
    onAgentCloseoutPayload?: (payload: unknown) => void;
  }) => {
    state.runAgentTurnWithFallbackMock(params);
    if (state.closeoutPayload) {
      params.onAgentCloseoutPayload?.(state.closeoutPayload);
    }
    return {
      kind: "final",
      payload: state.finalPayload,
    };
  },
}));

vi.mock("./queue.js", () => ({
  enqueueFollowupRun: vi.fn(),
  refreshQueuedFollowupSession: vi.fn(),
  scheduleFollowupDrain: vi.fn(),
  resolvePiSteeringModeForQueueMode: () => "off",
}));

async function createSessionStoreFile(entry: SessionEntry) {
  const dir = await mkdtemp(join(tmpdir(), "openclaw-agent-runner-final-closeout-"));
  const storePath = join(dir, "sessions.json");
  await writeFile(storePath, JSON.stringify({ main: entry }), "utf8");
  return storePath;
}

async function readStoredMainSession(storePath: string): Promise<SessionEntry> {
  const raw = await readFile(storePath, "utf8");
  return JSON.parse(raw).main as SessionEntry;
}

async function runFinalOutcomeCase(params?: {
  opts?: GetReplyOptions;
  sessionEntry?: SessionEntry;
  sessionCtx?: Partial<TemplateContext>;
}) {
  const sessionEntry: SessionEntry = params?.sessionEntry ?? {
    sessionId: "session",
    updatedAt: Date.now(),
    chatType: "direct",
    channel: "telegram",
  };
  const sessionStore = { main: sessionEntry };
  const storePath = await createSessionStoreFile(sessionEntry);
  const typing = createMockTypingController();
  const { runReplyAgent } = await import("./agent-runner.js");
  const result = await runReplyAgent({
    commandBody: "hello",
    followupRun: {
      prompt: "hello",
      summaryLine: "hello",
      enqueuedAt: Date.now(),
      run: {
        sessionId: "session",
        sessionKey: "main",
        messageProvider: "telegram",
        sessionFile: join(tmpdir(), "openclaw-agent-runner-final-closeout-session.jsonl"),
        workspaceDir: tmpdir(),
        config: {},
        skillsSnapshot: {},
        provider: "anthropic",
        model: "claude",
        thinkLevel: "low",
        verboseLevel: "off",
        elevatedLevel: "off",
        bashElevated: {
          enabled: false,
          allowed: false,
          defaultLevel: "off",
        },
        timeoutMs: 1_000,
        blockReplyBreak: "message_end",
        skipProviderRuntimeHints: true,
      },
    } as never,
    queueKey: "main",
    resolvedQueue: { mode: "interrupt" } as never,
    shouldSteer: false,
    shouldFollowup: false,
    isActive: false,
    isStreaming: false,
    opts: params?.opts,
    typing,
    sessionEntry,
    sessionStore,
    sessionKey: "main",
    storePath,
    sessionCtx: {
      Provider: "telegram",
      Surface: "telegram",
      ChatType: "direct",
      OriginatingChannel: "telegram",
      ...params?.sessionCtx,
    } as unknown as TemplateContext,
    defaultModel: "anthropic/claude-opus-4-6",
    resolvedVerboseLevel: "off",
    isNewSession: false,
    blockStreamingEnabled: false,
    resolvedBlockStreamingBreak: "message_end",
    shouldInjectGroupIntro: false,
    typingMode: "instant",
  });
  return { result, storePath };
}

function finalOutcomeCloseoutPayload() {
  return {
    title: "FINAL_OUTCOME_CLOSEOUT_APPEND_REGRESSION",
    status: "PASS",
    failedGates: [],
    requiredFilesMissing: [],
    productionMutation: false,
    evidenceFiles: [
      { path: "status.json" },
      { path: "summary.json" },
      { path: "evidence_manifest.json" },
    ],
    closeoutDelivered: false,
    closeoutPending: true,
  };
}

describe("runReplyAgent final outcome closeout delivery", () => {
  beforeEach(() => {
    state.runAgentTurnWithFallbackMock.mockClear();
    state.closeoutPayload = finalOutcomeCloseoutPayload();
    state.finalPayload = { text: "normal final report" };
    vi.stubEnv("OPENCLAW_TEST_FAST", "1");
  });

  it("does not let runOutcome.kind final bypass closeout append or pending debt", async () => {
    const { result, storePath } = await runFinalOutcomeCase();
    const payloads = Array.isArray(result) ? result : result ? [result] : [];
    const text = payloads.map((payload) => payload.text ?? "").join("\n");

    expect(payloads).toHaveLength(2);
    expect(payloads[0]?.text).toBe("normal final report");
    expect(payloads[1]?.text).toBe(
      "Closeout: PASS. No production mutation occurred. Evidence: status.json, summary.json, evidence_manifest.json.",
    );
    expect(text.match(/Closeout: PASS/g) ?? []).toHaveLength(1);
    expect(text).not.toContain("Closeout: FAIL");
    expect(text).not.toContain("Failed: FAIL");
    expect(text).not.toContain("Failed gates: none");
    expect(payloads[1]?.channelData).toMatchObject({
      openclawCloseoutDelivered: true,
      openclawCloseoutPending: false,
    });

    const stored = await readStoredMainSession(storePath);
    expect(stored.pendingFinalDelivery).toBe(true);
    expect(stored.pendingFinalDeliveryText).toContain("normal final report");
    expect(stored.pendingFinalDeliveryText).toContain("Closeout: PASS.");
    expect(stored.pendingCloseoutDelivery).toBe(true);
    expect(stored.pendingCloseoutDeliveryText).toBe(
      "Closeout: PASS. No production mutation occurred. Evidence: status.json, summary.json, evidence_manifest.json.",
    );
  });

  it("suppresses final outcome closeout append and debt when source delivery is message_tool_only", async () => {
    const { result, storePath } = await runFinalOutcomeCase({
      opts: { sourceReplyDeliveryMode: "message_tool_only" },
    });
    const payloads = Array.isArray(result) ? result : result ? [result] : [];

    expect(payloads).toHaveLength(1);
    expect(payloads[0]?.text).toBe("normal final report");
    const stored = await readStoredMainSession(storePath);
    expect(stored.pendingFinalDelivery).toBeUndefined();
    expect(stored.pendingCloseoutDelivery).toBeUndefined();
  });

  it("suppresses final outcome closeout append and debt when sendPolicy denies source delivery", async () => {
    const { result, storePath } = await runFinalOutcomeCase({
      sessionEntry: {
        sessionId: "session",
        updatedAt: Date.now(),
        chatType: "direct",
        channel: "telegram",
        sendPolicy: "deny",
      },
    });
    const payloads = Array.isArray(result) ? result : result ? [result] : [];

    expect(payloads).toHaveLength(1);
    expect(payloads[0]?.text).toBe("normal final report");
    const stored = await readStoredMainSession(storePath);
    expect(stored.pendingFinalDelivery).toBeUndefined();
    expect(stored.pendingCloseoutDelivery).toBeUndefined();
  });
});
