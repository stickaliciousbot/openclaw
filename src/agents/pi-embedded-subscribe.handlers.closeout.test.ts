import { describe, expect, it, vi } from "vitest";
import { createInlineCodeState } from "../markdown/code-spans.js";
import { createEmbeddedPiSessionEventHandler } from "./pi-embedded-subscribe.handlers.js";
import type { EmbeddedPiSubscribeContext } from "./pi-embedded-subscribe.handlers.types.js";

function createContext(overrides?: {
  onBeforeLifecycleTerminal?: () => void | Promise<void>;
  onAgentCloseoutPayload?: (payload: unknown) => void;
  onAgentToolResult?: (event: { toolName: string; result: unknown; isError: boolean }) => void;
}): EmbeddedPiSubscribeContext {
  return {
    params: {
      runId: "run-closeout-sync",
      sessionKey: "agent:main:telegram:direct:8495203551",
      onBeforeLifecycleTerminal: overrides?.onBeforeLifecycleTerminal,
      onAgentCloseoutPayload: overrides?.onAgentCloseoutPayload,
      onAgentToolResult: overrides?.onAgentToolResult,
    },
    state: {
      assistantTexts: ["normal final report"],
      toolMetas: [],
      toolMetaById: new Map(),
      toolSummaryById: new Set(),
      itemActiveIds: new Set(),
      itemStartedCount: 0,
      itemCompletedCount: 0,
      blockReplyBreak: "message_end",
      reasoningMode: "off",
      includeReasoning: false,
      shouldEmitPartialReplies: false,
      streamReasoning: false,
      deltaBuffer: "",
      blockBuffer: "",
      blockState: { thinking: false, final: false, inlineCode: createInlineCodeState() },
      partialBlockState: { thinking: false, final: false, inlineCode: createInlineCodeState() },
      emittedAssistantUpdate: false,
      reasoningStreamOpen: false,
      assistantMessageIndex: 0,
      lastAssistantTextMessageIndex: 0,
      assistantTextBaseline: 0,
      suppressBlockChunks: false,
      assistantUsageCommitted: false,
      compactionInFlight: false,
      pendingCompactionRetry: 0,
      compactionRetryPromise: null,
      unsubscribed: false,
      replayState: { replayInvalid: false, hadPotentialSideEffects: false },
      messagingToolSentTexts: [],
      messagingToolSentTextsNormalized: [],
      messagingToolSentTargets: [],
      messagingToolSentMediaUrls: [],
      pendingMessagingTexts: new Map(),
      pendingMessagingTargets: new Map(),
      successfulCronAdds: 0,
      pendingMessagingMediaUrls: new Map(),
      pendingToolMediaUrls: [],
      pendingToolAudioAsVoice: false,
      pendingToolTrustedLocalMedia: false,
      deterministicApprovalPromptPending: false,
      deterministicApprovalPromptSent: false,
    },
    log: { debug: vi.fn(), warn: vi.fn() },
    blockChunker: null,
    noteLastAssistant: vi.fn(),
    shouldEmitToolResult: () => false,
    shouldEmitToolOutput: () => false,
    emitToolSummary: vi.fn(),
    emitToolOutput: vi.fn(),
    stripBlockTags: (text: string) => text,
    emitBlockChunk: vi.fn(),
    flushBlockReplyBuffer: vi.fn(),
    emitReasoningStream: vi.fn(),
    consumeReplyDirectives: vi.fn(),
    consumePartialReplyDirectives: vi.fn(),
    resetAssistantMessageState: vi.fn(),
    resetForCompactionRetry: vi.fn(),
    finalizeAssistantTexts: vi.fn(),
    trimMessagingToolSent: vi.fn(),
    ensureCompactionPromise: vi.fn(),
    noteCompactionRetry: vi.fn(),
    resolveCompactionRetry: vi.fn(),
    maybeResolveCompactionWait: vi.fn(),
    recordAssistantUsage: vi.fn(),
    commitAssistantUsage: vi.fn(),
    incrementCompactionCount: vi.fn(),
    noteCompactionTokensAfter: vi.fn(),
    getUsageTotals: vi.fn(),
    getCompactionCount: () => 0,
    getLastCompactionTokensAfter: () => undefined,
    emitBlockReply: vi.fn(),
  } as unknown as EmbeddedPiSubscribeContext;
}

describe("createEmbeddedPiSessionEventHandler closeout observation", () => {
  it("observes closeout-shaped tool-end payload synchronously even while normal tool-end work is detached", async () => {
    let releaseTerminal: (() => void) | undefined;
    const terminalGate = new Promise<void>((resolve) => {
      releaseTerminal = resolve;
    });
    const onAgentCloseoutPayload = vi.fn();
    const onAgentToolResult = vi.fn();
    const ctx = createContext({
      onBeforeLifecycleTerminal: () => terminalGate,
      onAgentCloseoutPayload,
      onAgentToolResult,
    });
    const handle = createEmbeddedPiSessionEventHandler(ctx);

    handle({ type: "agent_end" });

    const closeoutPayload = {
      title: "OBSERVER_ATTACHMENT_PRODUCTION_SMOKE_20260628T1248Z",
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
    handle({
      type: "tool_execution_end",
      toolName: "exec",
      toolCallId: "tool-closeout",
      isError: false,
      message: {
        role: "toolResult",
        content: [
          {
            type: "text",
            text: `${JSON.stringify({ details: { status: "failed" }, isError: false })}\n${JSON.stringify(closeoutPayload)}\ncompleted`,
          },
        ],
      },
    });

    expect(onAgentCloseoutPayload).toHaveBeenCalledTimes(1);
    expect(onAgentCloseoutPayload.mock.calls[0]?.[0]).toMatchObject({
      title: "OBSERVER_ATTACHMENT_PRODUCTION_SMOKE_20260628T1248Z",
      status: "PASS",
      productionMutation: false,
      evidenceFiles: [
        { path: "status.json" },
        { path: "summary.json" },
        { path: "evidence_manifest.json" },
      ],
    });
    expect(onAgentToolResult).not.toHaveBeenCalled();

    releaseTerminal?.();
    await terminalGate;
  });

  it("does not observe generic operational failed metadata as closeout", () => {
    const onAgentCloseoutPayload = vi.fn();
    const ctx = createContext({ onAgentCloseoutPayload });
    const handle = createEmbeddedPiSessionEventHandler(ctx);

    handle({
      type: "tool_execution_end",
      toolName: "exec",
      toolCallId: "tool-generic-failed",
      isError: false,
      result: {
        content: [{ type: "text", text: "generic operational metadata should be rejected" }],
        details: { status: "failed" },
        isError: false,
      },
    });

    expect(onAgentCloseoutPayload).not.toHaveBeenCalled();
  });
});
