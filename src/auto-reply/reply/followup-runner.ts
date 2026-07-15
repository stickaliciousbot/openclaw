import crypto from "node:crypto";
import {
  hasOutboundReplyContent,
  resolveSendableOutboundReplyParts,
} from "openclaw/plugin-sdk/reply-payload";
import { resolveBootstrapWarningSignaturesSeen } from "../../agents/bootstrap-budget.js";
import { resolveContextTokensForModel } from "../../agents/context.js";
import { DEFAULT_CONTEXT_TOKENS } from "../../agents/defaults.js";
import { runWithModelFallback } from "../../agents/model-fallback.js";
import { runEmbeddedPiAgent } from "../../agents/pi-embedded.js";
import {
  buildAgentRuntimeDeliveryPlan,
  buildAgentRuntimeOutcomePlan,
} from "../../agents/runtime-plan/build.js";
import { normalizeChatType } from "../../channels/chat-type.js";
import type { SessionEntry } from "../../config/sessions.js";
import { updateSessionStoreEntry } from "../../config/sessions/store.js";
import type { TypingMode } from "../../config/types.js";
import { logVerbose } from "../../globals.js";
import { registerAgentRunContext } from "../../infra/agent-events.js";
import { formatErrorMessage } from "../../infra/errors.js";
import { enqueueSystemEvent } from "../../infra/system-events.js";
import { defaultRuntime } from "../../runtime.js";
import {
  normalizeOptionalLowercaseString,
  normalizeOptionalString,
} from "../../shared/string-coerce.js";
import { isInternalMessageChannel } from "../../utils/message-channel.js";
import { stripHeartbeatToken } from "../heartbeat.js";
import type { GetReplyOptions, ReplyPayload } from "../types.js";
import { runPreflightCompactionIfNeeded } from "./agent-runner-memory.js";
import {
  resolveQueuedReplyExecutionConfig,
  resolveQueuedReplyRuntimeConfig,
  resolveModelFallbackOptions,
  resolveRunAuthProfile,
} from "./agent-runner-utils.js";
import { resolveFollowupDeliveryPayloads } from "./followup-delivery.js";
import { resolveOriginMessageProvider } from "./origin-routing.js";
import { refreshQueuedFollowupSession, type FollowupRun } from "./queue.js";
import { createReplyOperation } from "./reply-run-registry.js";
import { isRoutableChannel, routeReply } from "./route-reply.js";
import { incrementRunCompactionCount, persistRunSessionUsage } from "./session-run-accounting.js";
import { createTypingSignaler } from "./typing-mode.js";
import type { TypingController } from "./typing.js";
import {
  runM3EnvelopeSupervisor,
  type ContractEnvelope,
  type DeliveryReceipt,
  type ShadowObservationReceipt,
  type TerminalContractCloseout,
  type ToolSupervisionReceipt,
  type UniversalContractReceipt,
} from "./umc-m3-envelope-supervision.js";

type EmbeddedAgentRunResult = Awaited<ReturnType<typeof runEmbeddedPiAgent>>;

type UmcV1QueuedRouteIntent = {
  contractVersion: "umc.v1";
  milestone: "M2Q_QUEUE_RESUME_ROUTE_ADMISSION";
  source: "queued_followup";
  hardPreference: false;
  requested: { provider: string; model: string };
  executable: { provider: string; model: string };
  directBypass: false;
  status: "INTERCEPTED_RAW_SELECTION_TO_DEFAULT_BROKER" | "DEFAULT_BROKER_ROUTE";
  updatedAt: string;
};

type SessionEntryWithUmcV1Intent = SessionEntry & {
  umcV1QueuedRouteIntent?: UmcV1QueuedRouteIntent;
};

type UmcV1QueuedRouteAdmissionResult = {
  provider?: string;
  model?: string;
  scoped: boolean;
  intercepted: boolean;
  intent?: UmcV1QueuedRouteIntent;
  hold?: boolean;
  reply?: ReplyPayload;
};

type UmcV1ShadowObserveReceipt = {
  contractVersion: "umc.v1";
  milestone: "M3G_EDITABLE_SOURCE_OBSERVE_ONLY_HOOK_NO_SEND_IMPLEMENTATION";
  mode: "observe_no_send";
  source: "queued_followup_source_hook";
  admittedTurn: {
    sessionKey?: string;
    provider?: string;
    model?: string;
    messageProvider?: string;
    originatingChannel?: string;
    originatingChatType?: string;
    senderIsOwner: boolean;
  };
  deliveryReceipt: {
    channel: "shadow";
    mode: "no_send";
    sent: false;
    providerExecutionCount: 0;
    telegramSendCount: 0;
    externalSendCount: 0;
    realWriteToolCount: 0;
  };
  universalContractReceipt: {
    status: "WOULD_PASS" | "WOULD_HOLD" | "SHADOW_FAILED";
    productionDecisionReturned: false;
    routeProviderFallbackChanged: false;
  };
  terminalCloseout: {
    status:
      | "PASS_SHADOW_OBSERVE_NO_SEND"
      | "HOLD_SHADOW_OBSERVE_NO_SEND"
      | "FAIL_SHADOW_OBSERVE_NO_SEND";
    productionPathContinues: true;
  };
  contractEnvelope?: ContractEnvelope;
  shadowObservationReceipt?: ShadowObservationReceipt;
  toolSupervisionReceipt?: ToolSupervisionReceipt;
  m3DeliveryReceipt?: DeliveryReceipt;
  universalContractReceiptV2?: UniversalContractReceipt;
  terminalContractCloseout?: TerminalContractCloseout;
  createdAt: string;
};

type UmcV1ShadowObserveResult = {
  enabled: boolean;
  receipt?: UmcV1ShadowObserveReceipt;
  error?: string;
};

const UMC_V1_SHADOW_FIXTURE_ENV = {
  mode: "UMC_SHADOW_MODE",
  ownerScope: "UMC_SHADOW_OWNER_SCOPE",
  delivery: "UMC_SHADOW_DELIVERY",
  provider: "UMC_SHADOW_PROVIDER",
  mutation: "UMC_SHADOW_MUTATION",
} as const;

function resolveUmcV1DefaultRouteFromConfig(
  config: unknown,
): { provider: string; model: string } | null {
  const cfg = config as { agents?: { defaults?: { model?: { primary?: unknown } } } } | undefined;
  const raw = normalizeOptionalString(cfg?.agents?.defaults?.model?.primary);
  if (!raw) {
    return null;
  }
  const slash = raw.indexOf("/");
  if (slash <= 0 || slash >= raw.length - 1) {
    return null;
  }
  const provider = normalizeOptionalString(raw.slice(0, slash));
  const model = normalizeOptionalString(raw.slice(slash + 1));
  if (!provider || !model) {
    return null;
  }
  return { provider, model };
}

function isUmcV1QueuedOwnerScope(params: {
  run?: FollowupRun["run"];
  queued?: FollowupRun;
}): boolean {
  const run = params.run;
  if (!run || run.senderIsOwner !== true) {
    return false;
  }
  const chatType = normalizeChatType(params.queued?.originatingChatType);
  if (chatType && chatType !== "direct") {
    return false;
  }
  if (run.groupId || run.groupChannel || run.groupSpace) {
    return false;
  }
  const provider = normalizeOptionalLowercaseString(
    params.queued?.originatingChannel ?? run.messageProvider,
  );
  if (!provider) {
    return false;
  }
  if (["cron", "heartbeat", "system", "memory-flush"].includes(provider)) {
    return false;
  }
  return true;
}

export async function applyUmcV1QueuedRouteAdmission(params: {
  config?: unknown;
  run?: FollowupRun["run"];
  queued?: FollowupRun;
  sessionEntry?: SessionEntry;
  sessionStore?: Record<string, SessionEntry>;
  sessionKey?: string;
  storePath?: string;
  provider?: string;
  model?: string;
}): Promise<UmcV1QueuedRouteAdmissionResult> {
  const selectedProvider = normalizeOptionalString(params.provider ?? params.run?.provider);
  const selectedModel = normalizeOptionalString(params.model ?? params.run?.model);
  if (!selectedProvider || !selectedModel) {
    return { provider: selectedProvider, model: selectedModel, scoped: false, intercepted: false };
  }
  if (!isUmcV1QueuedOwnerScope(params)) {
    return { provider: selectedProvider, model: selectedModel, scoped: false, intercepted: false };
  }
  const defaultRoute = resolveUmcV1DefaultRouteFromConfig(params.config ?? params.run?.config);
  if (!defaultRoute) {
    return {
      provider: selectedProvider,
      model: selectedModel,
      scoped: true,
      intercepted: false,
      hold: true,
      reply: {
        text: "HOLD_UMC_QUEUE_ROUTE_UNAVAILABLE: queued owner execution requires a configured default route.",
        isError: true,
      },
    };
  }

  const selectedRef = `${selectedProvider}/${selectedModel}`;
  const defaultRef = `${defaultRoute.provider}/${defaultRoute.model}`;
  const intercepted = selectedRef !== defaultRef;
  const intent: UmcV1QueuedRouteIntent = {
    contractVersion: "umc.v1",
    milestone: "M2Q_QUEUE_RESUME_ROUTE_ADMISSION",
    source: "queued_followup",
    hardPreference: false,
    requested: { provider: selectedProvider, model: selectedModel },
    executable: { provider: defaultRoute.provider, model: defaultRoute.model },
    directBypass: false,
    status: intercepted ? "INTERCEPTED_RAW_SELECTION_TO_DEFAULT_BROKER" : "DEFAULT_BROKER_ROUTE",
    updatedAt: new Date().toISOString(),
  };
  const updatedAt = Date.now();
  if (params.sessionEntry) {
    const entry = params.sessionEntry as SessionEntryWithUmcV1Intent;
    entry.umcV1QueuedRouteIntent = intent;
    entry.updatedAt = updatedAt;
  }
  if (params.sessionKey && params.sessionStore && params.sessionEntry) {
    params.sessionStore[params.sessionKey] = params.sessionEntry;
  }
  if (params.sessionKey && params.storePath) {
    await updateSessionStoreEntry({
      storePath: params.storePath,
      sessionKey: params.sessionKey,
      update: async () =>
        ({
          umcV1QueuedRouteIntent: intent,
          updatedAt,
        }) as Partial<SessionEntry>,
    });
  }
  const eventSessionKey = normalizeOptionalString(params.sessionKey ?? params.run?.sessionKey);
  if (intercepted && eventSessionKey) {
    enqueueSystemEvent(
      `UMC v1 queued route intent captured; execution forced through ${defaultRef} instead of raw ${selectedRef}.`,
      {
        sessionKey: eventSessionKey,
        contextKey: `umc-v1-queued-route-intent:${selectedRef}->${defaultRef}`,
      },
    );
  }
  return {
    provider: defaultRoute.provider,
    model: defaultRoute.model,
    scoped: true,
    intercepted,
    intent,
  };
}

function isUmcV1ShadowObserveOnlyEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  return (
    env[UMC_V1_SHADOW_FIXTURE_ENV.mode] === "observe_no_send" &&
    env[UMC_V1_SHADOW_FIXTURE_ENV.ownerScope] === "fixture_only" &&
    env[UMC_V1_SHADOW_FIXTURE_ENV.delivery] === "no_send" &&
    env[UMC_V1_SHADOW_FIXTURE_ENV.provider] === "mock_only" &&
    env[UMC_V1_SHADOW_FIXTURE_ENV.mutation] === "forbidden"
  );
}

function runM3EnvelopeSupervisorForFollowup(params: {
  admittedTurn: FollowupRun["run"];
  queued?: FollowupRun;
  routeObservation?: UmcV1QueuedRouteAdmissionResult;
}) {
  return runM3EnvelopeSupervisor({
    turn_id: params.admittedTurn.sessionKey,
    session_id: params.admittedTurn.sessionKey,
    channel: params.queued?.originatingChannel ?? params.admittedTurn.messageProvider,
    owner_scope: "owner_turn",
    route_intent:
      params.routeObservation?.intent ??
      ({
        contractVersion: "umc.v1",
        milestone: "M2Q_QUEUE_RESUME_ROUTE_ADMISSION",
        source: "queued_followup",
        status:
          params.routeObservation?.hold === true
            ? "HOLD_ROUTE_OBSERVATION"
            : "DEFAULT_BROKER_ROUTE",
      } as const),
    ambient_owner_chat_delivery_count: 0,
    evidence_refs: ["M3_SOURCE_BUILD_PATH_DISCOVERY_AND_INSTALL_CARD_PREPARATION"],
  });
}

export async function maybeRunUmcV1ShadowObserveOnly(params: {
  admittedTurn: FollowupRun["run"];
  queued?: FollowupRun;
  routeObservation?: UmcV1QueuedRouteAdmissionResult;
  noSend: true;
  mockProviderOnly: true;
  mutationForbidden: true;
  simulateFailure?: boolean;
  simulateHold?: boolean;
  onReceipt?: (receipt: UmcV1ShadowObserveReceipt) => void | Promise<void>;
  env?: NodeJS.ProcessEnv;
}): Promise<UmcV1ShadowObserveResult> {
  if (!isUmcV1ShadowObserveOnlyEnabled(params.env)) {
    return { enabled: false };
  }
  try {
    if (params.simulateFailure) {
      throw new Error("simulated M3G shadow fixture failure");
    }
    const wouldHold = params.simulateHold === true || params.routeObservation?.hold === true;
    const m3 = runM3EnvelopeSupervisorForFollowup(params);
    const receipt: UmcV1ShadowObserveReceipt = {
      contractVersion: "umc.v1",
      milestone: "M3G_EDITABLE_SOURCE_OBSERVE_ONLY_HOOK_NO_SEND_IMPLEMENTATION",
      mode: "observe_no_send",
      source: "queued_followup_source_hook",
      admittedTurn: {
        sessionKey: params.admittedTurn.sessionKey,
        provider: params.admittedTurn.provider,
        model: params.admittedTurn.model,
        messageProvider: params.admittedTurn.messageProvider,
        originatingChannel: params.queued?.originatingChannel,
        originatingChatType: params.queued?.originatingChatType,
        senderIsOwner: params.admittedTurn.senderIsOwner === true,
      },
      deliveryReceipt: {
        channel: "shadow",
        mode: "no_send",
        sent: false,
        providerExecutionCount: 0,
        telegramSendCount: 0,
        externalSendCount: 0,
        realWriteToolCount: 0,
      },
      universalContractReceipt: {
        status: wouldHold ? "WOULD_HOLD" : "WOULD_PASS",
        productionDecisionReturned: false,
        routeProviderFallbackChanged: false,
      },
      terminalCloseout: {
        status: wouldHold ? "HOLD_SHADOW_OBSERVE_NO_SEND" : "PASS_SHADOW_OBSERVE_NO_SEND",
        productionPathContinues: true,
      },
      contractEnvelope: m3.receipts.envelope,
      shadowObservationReceipt: m3.receipts.shadowObservationReceipt,
      toolSupervisionReceipt: m3.receipts.toolSupervisionReceipt,
      m3DeliveryReceipt: m3.receipts.deliveryReceipt,
      universalContractReceiptV2: m3.receipts.universalContractReceipt,
      terminalContractCloseout: m3.receipts.terminalCloseout,
      createdAt: new Date().toISOString(),
    };
    await params.onReceipt?.(receipt);
    return { enabled: true, receipt };
  } catch (err) {
    const m3 = runM3EnvelopeSupervisorForFollowup(params);
    const receipt: UmcV1ShadowObserveReceipt = {
      contractVersion: "umc.v1",
      milestone: "M3G_EDITABLE_SOURCE_OBSERVE_ONLY_HOOK_NO_SEND_IMPLEMENTATION",
      mode: "observe_no_send",
      source: "queued_followup_source_hook",
      admittedTurn: {
        sessionKey: params.admittedTurn.sessionKey,
        provider: params.admittedTurn.provider,
        model: params.admittedTurn.model,
        messageProvider: params.admittedTurn.messageProvider,
        originatingChannel: params.queued?.originatingChannel,
        originatingChatType: params.queued?.originatingChatType,
        senderIsOwner: params.admittedTurn.senderIsOwner === true,
      },
      deliveryReceipt: {
        channel: "shadow",
        mode: "no_send",
        sent: false,
        providerExecutionCount: 0,
        telegramSendCount: 0,
        externalSendCount: 0,
        realWriteToolCount: 0,
      },
      universalContractReceipt: {
        status: "SHADOW_FAILED",
        productionDecisionReturned: false,
        routeProviderFallbackChanged: false,
      },
      terminalCloseout: {
        status: "FAIL_SHADOW_OBSERVE_NO_SEND",
        productionPathContinues: true,
      },
      contractEnvelope: m3.receipts.envelope,
      shadowObservationReceipt: m3.receipts.shadowObservationReceipt,
      toolSupervisionReceipt: m3.receipts.toolSupervisionReceipt,
      m3DeliveryReceipt: m3.receipts.deliveryReceipt,
      universalContractReceiptV2: m3.receipts.universalContractReceipt,
      terminalContractCloseout: m3.receipts.terminalCloseout,
      createdAt: new Date().toISOString(),
    };
    await Promise.resolve(params.onReceipt?.(receipt)).catch(() => undefined);
    return { enabled: true, receipt, error: formatErrorMessage(err) };
  }
}

export function createFollowupRunner(params: {
  opts?: GetReplyOptions;
  typing: TypingController;
  typingMode: TypingMode;
  sessionEntry?: SessionEntry;
  sessionStore?: Record<string, SessionEntry>;
  sessionKey?: string;
  storePath?: string;
  defaultModel: string;
  agentCfgContextTokens?: number;
}): (queued: FollowupRun) => Promise<void> {
  const {
    opts,
    typing,
    typingMode,
    sessionEntry,
    sessionStore,
    sessionKey,
    storePath,
    defaultModel,
    agentCfgContextTokens,
  } = params;
  const typingSignals = createTypingSignaler({
    typing,
    mode: typingMode,
    isHeartbeat: opts?.isHeartbeat === true,
  });

  /**
   * Sends followup payloads, routing to the originating channel if set.
   *
   * When originatingChannel/originatingTo are set on the queued run,
   * replies are routed directly to that provider instead of using the
   * session's current dispatcher. This ensures replies go back to
   * where the message originated.
   */
  const sendFollowupPayloads = async (
    payloads: ReplyPayload[],
    queued: FollowupRun,
    resolvedRun: { provider: string; modelId: string },
  ) => {
    // Check if we should route to originating channel.
    const { originatingChannel, originatingTo } = queued;
    const runtimeConfig = resolveQueuedReplyRuntimeConfig(queued.run.config);
    const shouldRouteToOriginating = isRoutableChannel(originatingChannel) && originatingTo;
    const deliveryPlan = buildAgentRuntimeDeliveryPlan({
      provider: resolvedRun.provider,
      modelId: resolvedRun.modelId,
      config: runtimeConfig,
      workspaceDir: queued.run.workspaceDir,
      agentDir: queued.run.agentDir,
    });

    const sendablePayloads = payloads.filter(
      (payload): payload is ReplyPayload =>
        hasOutboundReplyContent(payload) && !deliveryPlan.isSilentPayload(payload),
    );

    if (sendablePayloads.length === 0) {
      return;
    }

    if (!shouldRouteToOriginating && !opts?.onBlockReply) {
      defaultRuntime.error?.(
        "followup queue: completed with payloads but no origin route or visible dispatcher is available",
      );
      return;
    }

    let crossChannelRouteFailureNeedsNotice = false;
    let routedAnyCrossChannelPayloadToOrigin = false;
    for (const payload of sendablePayloads) {
      const providerRoute = deliveryPlan.resolveFollowupRoute({
        payload,
        originatingChannel,
        originatingTo,
        originRoutable: Boolean(shouldRouteToOriginating),
        dispatcherAvailable: Boolean(opts?.onBlockReply),
      });
      if (providerRoute?.route === "drop") {
        logVerbose(
          `followup queue: provider hook dropped payload route reason=${providerRoute.reason ?? "unspecified"}`,
        );
        continue;
      }
      const deliveryRoute =
        providerRoute?.route === "origin" && shouldRouteToOriginating
          ? "origin"
          : providerRoute?.route === "dispatcher" && opts?.onBlockReply
            ? "dispatcher"
            : shouldRouteToOriginating
              ? "origin"
              : opts?.onBlockReply
                ? "dispatcher"
                : undefined;
      await typingSignals.signalTextDelta(payload.text);

      // Route to originating channel if set, otherwise fall back to dispatcher.
      if (deliveryRoute === "origin" && isRoutableChannel(originatingChannel) && originatingTo) {
        const result = await routeReply({
          payload,
          channel: originatingChannel,
          to: originatingTo,
          sessionKey: queued.run.sessionKey,
          accountId: queued.originatingAccountId,
          requesterSenderId: queued.run.senderId,
          requesterSenderName: queued.run.senderName,
          requesterSenderUsername: queued.run.senderUsername,
          requesterSenderE164: queued.run.senderE164,
          threadId: queued.originatingThreadId,
          cfg: runtimeConfig,
        });
        if (!result.ok) {
          const errorMsg = result.error ?? "unknown error";
          logVerbose(`followup queue: route-reply failed: ${errorMsg}`);
          const provider = resolveOriginMessageProvider({
            provider: queued.run.messageProvider,
          });
          const origin = resolveOriginMessageProvider({
            originatingChannel,
          });
          if (opts?.onBlockReply) {
            if (origin && origin === provider) {
              await opts.onBlockReply(payload);
            } else {
              crossChannelRouteFailureNeedsNotice = true;
            }
          } else {
            defaultRuntime.error?.(`followup queue: route-reply failed: ${errorMsg}`);
          }
        } else {
          const provider = resolveOriginMessageProvider({
            provider: queued.run.messageProvider,
          });
          const origin = resolveOriginMessageProvider({
            originatingChannel,
          });
          if (origin && provider && origin !== provider) {
            routedAnyCrossChannelPayloadToOrigin = true;
          }
        }
      } else if (deliveryRoute === "dispatcher" && opts?.onBlockReply) {
        await opts.onBlockReply(payload);
      }
    }
    if (
      crossChannelRouteFailureNeedsNotice &&
      !routedAnyCrossChannelPayloadToOrigin &&
      opts?.onBlockReply
    ) {
      await opts.onBlockReply({
        text:
          "Follow-up completed, but OpenClaw could not deliver it to the originating " +
          "channel. The reply content was not forwarded to this channel to avoid " +
          "cross-channel misdelivery.",
        isError: true,
      });
    }
  };

  return async (queued: FollowupRun) => {
    const queuedImages = queued.images ?? opts?.images;
    const queuedImageOrder = queued.imageOrder ?? opts?.imageOrder;
    queued.run.config = await resolveQueuedReplyExecutionConfig(queued.run.config, {
      originatingChannel: queued.originatingChannel,
      messageProvider: queued.run.messageProvider,
      originatingAccountId: queued.originatingAccountId,
      agentAccountId: queued.run.agentAccountId,
    });
    const replySessionKey = queued.run.sessionKey ?? sessionKey;
    const runtimeConfig = resolveQueuedReplyRuntimeConfig(queued.run.config);
    const effectiveQueued =
      runtimeConfig === queued.run.config
        ? queued
        : { ...queued, run: { ...queued.run, config: runtimeConfig } };
    let run = effectiveQueued.run;
    const replyOperation = createReplyOperation({
      sessionId: run.sessionId,
      sessionKey: replySessionKey ?? "",
      resetTriggered: false,
      upstreamAbortSignal: opts?.abortSignal,
    });
    try {
      const runId = crypto.randomUUID();
      const shouldSurfaceToControlUi = isInternalMessageChannel(
        resolveOriginMessageProvider({
          originatingChannel: queued.originatingChannel,
          provider: run.messageProvider,
        }),
      );
      if (run.sessionKey) {
        registerAgentRunContext(runId, {
          sessionKey: run.sessionKey,
          verboseLevel: run.verboseLevel,
          isControlUiVisible: shouldSurfaceToControlUi,
        });
      }
      let autoCompactionCount = 0;
      let runResult: Awaited<ReturnType<typeof runEmbeddedPiAgent>>;
      let activeSessionEntry =
        (sessionKey ? sessionStore?.[sessionKey] : undefined) ?? sessionEntry;
      const queueAdmission = await applyUmcV1QueuedRouteAdmission({
        config: runtimeConfig,
        run,
        queued: effectiveQueued,
        sessionEntry: activeSessionEntry,
        sessionStore,
        sessionKey: replySessionKey ?? sessionKey,
        storePath,
      });
      if (queueAdmission.reply) {
        replyOperation.fail(
          "umc_queue_route_unavailable",
          new Error(queueAdmission.reply.text ?? "UMC queued route unavailable"),
        );
        defaultRuntime.error?.(queueAdmission.reply.text ?? "HOLD_UMC_QUEUE_ROUTE_UNAVAILABLE");
        return;
      }
      if (queueAdmission.scoped) {
        run = {
          ...run,
          provider: queueAdmission.provider ?? run.provider,
          model: queueAdmission.model ?? run.model,
          modelOverrideSource: "auto",
        };
      }
      await maybeRunUmcV1ShadowObserveOnly({
        admittedTurn: run,
        queued: effectiveQueued,
        routeObservation: queueAdmission,
        noSend: true,
        mockProviderOnly: true,
        mutationForbidden: true,
      });
      let fallbackProvider = run.provider;
      let fallbackModel = run.model;
      activeSessionEntry = await runPreflightCompactionIfNeeded({
        cfg: runtimeConfig,
        followupRun: effectiveQueued,
        promptForEstimate: queued.prompt,
        defaultModel,
        agentCfgContextTokens,
        sessionEntry: activeSessionEntry,
        sessionStore,
        sessionKey,
        storePath,
        isHeartbeat: opts?.isHeartbeat === true,
        replyOperation,
      });
      let bootstrapPromptWarningSignaturesSeen = resolveBootstrapWarningSignaturesSeen(
        activeSessionEntry?.systemPromptReport,
      );
      replyOperation.setPhase("running");
      try {
        const outcomePlan = buildAgentRuntimeOutcomePlan();
        const fallbackResult = await runWithModelFallback<EmbeddedAgentRunResult>({
          ...resolveModelFallbackOptions(run, runtimeConfig),
          cfg: runtimeConfig,
          runId,
          classifyResult: ({ result, provider, model }) =>
            outcomePlan.classifyRunResult({ result, provider, model }),
          run: async (provider, model, runOptions) => {
            const authProfile = resolveRunAuthProfile(run, provider, { config: runtimeConfig });
            let attemptCompactionCount = 0;
            try {
              const result = await runEmbeddedPiAgent({
                allowGatewaySubagentBinding: true,
                replyOperation,
                sessionId: run.sessionId,
                sessionKey: run.sessionKey,
                agentId: run.agentId,
                trigger: "user",
                messageChannel: queued.originatingChannel ?? undefined,
                messageProvider: run.messageProvider,
                agentAccountId: run.agentAccountId,
                messageTo: queued.originatingTo,
                messageThreadId: queued.originatingThreadId,
                currentChannelId: queued.originatingTo,
                currentThreadTs:
                  queued.originatingThreadId != null
                    ? String(queued.originatingThreadId)
                    : undefined,
                groupId: run.groupId,
                groupChannel: run.groupChannel,
                groupSpace: run.groupSpace,
                senderId: run.senderId,
                senderName: run.senderName,
                senderUsername: run.senderUsername,
                senderE164: run.senderE164,
                senderIsOwner: run.senderIsOwner,
                sessionFile: run.sessionFile,
                agentDir: run.agentDir,
                workspaceDir: run.workspaceDir,
                config: runtimeConfig,
                skillsSnapshot: run.skillsSnapshot,
                prompt: queued.prompt,
                transcriptPrompt: queued.transcriptPrompt,
                currentTurnContext: queued.currentTurnContext,
                extraSystemPrompt: run.extraSystemPrompt,
                silentReplyPromptMode: run.silentReplyPromptMode,
                sourceReplyDeliveryMode: run.sourceReplyDeliveryMode,
                forceMessageTool: run.sourceReplyDeliveryMode === "message_tool_only",
                ownerNumbers: run.ownerNumbers,
                enforceFinalTag: run.enforceFinalTag,
                allowEmptyAssistantReplyAsSilent: run.allowEmptyAssistantReplyAsSilent,
                provider,
                model,
                ...authProfile,
                thinkLevel: run.thinkLevel,
                verboseLevel: run.verboseLevel,
                reasoningLevel: run.reasoningLevel,
                suppressToolErrorWarnings: opts?.suppressToolErrorWarnings,
                execOverrides: run.execOverrides,
                bashElevated: run.bashElevated,
                timeoutMs: run.timeoutMs,
                runId,
                images: queuedImages,
                imageOrder: queuedImageOrder,
                allowTransientCooldownProbe: runOptions?.allowTransientCooldownProbe,
                blockReplyBreak: run.blockReplyBreak,
                bootstrapPromptWarningSignaturesSeen,
                bootstrapPromptWarningSignature:
                  bootstrapPromptWarningSignaturesSeen[
                    bootstrapPromptWarningSignaturesSeen.length - 1
                  ],
                onAgentEvent: (evt) => {
                  if (evt.stream !== "compaction") {
                    return;
                  }
                  const phase = typeof evt.data.phase === "string" ? evt.data.phase : "";
                  const completed = evt.data?.completed === true;
                  if (phase === "end" && completed) {
                    attemptCompactionCount += 1;
                  }
                },
              });
              bootstrapPromptWarningSignaturesSeen = resolveBootstrapWarningSignaturesSeen(
                result.meta?.systemPromptReport,
              );
              const resultCompactionCount = Math.max(
                0,
                result.meta?.agentMeta?.compactionCount ?? 0,
              );
              attemptCompactionCount = Math.max(attemptCompactionCount, resultCompactionCount);
              return result;
            } finally {
              autoCompactionCount += attemptCompactionCount;
            }
          },
        });
        runResult = fallbackResult.result;
        fallbackProvider = fallbackResult.provider;
        fallbackModel = fallbackResult.model;
      } catch (err) {
        const message = formatErrorMessage(err);
        replyOperation.fail("run_failed", err);
        defaultRuntime.error?.(`Followup agent failed before reply: ${message}`);
        return;
      }

      const usage = runResult.meta?.agentMeta?.usage;
      const promptTokens = runResult.meta?.agentMeta?.promptTokens;
      const modelUsed = runResult.meta?.agentMeta?.model ?? fallbackModel ?? defaultModel;
      const providerUsed =
        runResult.meta?.agentMeta?.provider ?? fallbackProvider ?? queued.run.provider;
      const contextTokensUsed =
        resolveContextTokensForModel({
          cfg: queued.run.config,
          provider: providerUsed,
          model: modelUsed,
          contextTokensOverride: agentCfgContextTokens,
          fallbackContextTokens: sessionEntry?.contextTokens ?? DEFAULT_CONTEXT_TOKENS,
          allowAsyncLoad: false,
        }) ?? DEFAULT_CONTEXT_TOKENS;

      if (storePath && sessionKey) {
        await persistRunSessionUsage({
          storePath,
          sessionKey,
          cfg: runtimeConfig,
          usage,
          lastCallUsage: runResult.meta?.agentMeta?.lastCallUsage,
          promptTokens,
          modelUsed,
          providerUsed,
          contextTokensUsed,
          systemPromptReport: runResult.meta?.systemPromptReport,
          cliSessionBinding: runResult.meta?.agentMeta?.cliSessionBinding,
          logLabel: "followup",
        });
      }

      const payloadArray = runResult.payloads ?? [];
      if (payloadArray.length === 0) {
        return;
      }
      const sanitizedPayloads = payloadArray.flatMap((payload) => {
        const text = payload.text;
        if (!text || !text.includes("HEARTBEAT_OK")) {
          return [payload];
        }
        const stripped = stripHeartbeatToken(text, { mode: "message" });
        const hasMedia = resolveSendableOutboundReplyParts(payload).hasMedia;
        if (stripped.shouldSkip && !hasMedia) {
          return [];
        }
        return [{ ...payload, text: stripped.text }];
      });
      const finalPayloads = resolveFollowupDeliveryPayloads({
        cfg: runtimeConfig,
        payloads: sanitizedPayloads,
        messageProvider: run.messageProvider,
        originatingAccountId: queued.originatingAccountId ?? run.agentAccountId,
        originatingChannel: queued.originatingChannel,
        originatingChatType: queued.originatingChatType,
        originatingTo: queued.originatingTo,
        sentMediaUrls: runResult.messagingToolSentMediaUrls,
        sentTargets: runResult.messagingToolSentTargets,
        sentTexts: runResult.messagingToolSentTexts,
      });

      if (finalPayloads.length === 0) {
        return;
      }

      if (autoCompactionCount > 0) {
        const previousSessionId = run.sessionId;
        const count = await incrementRunCompactionCount({
          cfg: runtimeConfig,
          sessionEntry,
          sessionStore,
          sessionKey,
          storePath,
          amount: autoCompactionCount,
          compactionTokensAfter: runResult.meta?.agentMeta?.compactionTokensAfter,
          lastCallUsage: runResult.meta?.agentMeta?.lastCallUsage,
          contextTokensUsed,
          newSessionId: runResult.meta?.agentMeta?.sessionId,
          newSessionFile: runResult.meta?.agentMeta?.sessionFile,
        });
        const refreshedSessionEntry =
          sessionKey && sessionStore ? sessionStore[sessionKey] : undefined;
        if (refreshedSessionEntry) {
          const queueKey = run.sessionKey ?? sessionKey;
          if (queueKey) {
            refreshQueuedFollowupSession({
              key: queueKey,
              previousSessionId,
              nextSessionId: refreshedSessionEntry.sessionId,
              nextSessionFile: refreshedSessionEntry.sessionFile,
            });
          }
        }
        if (run.verboseLevel && run.verboseLevel !== "off") {
          const suffix = typeof count === "number" ? ` (count ${count})` : "";
          finalPayloads.unshift({
            text: `🧹 Auto-compaction complete${suffix}.`,
          });
        }
      }

      if (run.sourceReplyDeliveryMode === "message_tool_only") {
        logVerbose(
          "followup queue: automatic source delivery suppressed by sourceReplyDeliveryMode: message_tool_only",
        );
        return;
      }

      await sendFollowupPayloads(finalPayloads, effectiveQueued, {
        provider: providerUsed,
        modelId: modelUsed,
      });
    } finally {
      replyOperation.complete();
      // Both signals are required for the typing controller to clean up.
      // The main inbound dispatch path calls markDispatchIdle() from the
      // buffered dispatcher's finally block, but followup turns bypass the
      // dispatcher entirely — so we must fire both signals here.  Without
      // this, NO_REPLY / empty-payload followups leave the typing indicator
      // stuck (the keepalive loop keeps sending "typing" to Telegram
      // indefinitely until the TTL expires).
      typing.markRunComplete();
      typing.markDispatchIdle();
    }
  };
}
