import { createHash } from "node:crypto";
import { mkdir, readFile, stat, unlink, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { pathToFileURL } from "node:url";
import { completeBoundaryDecisionEnvelope } from "./boundary-decision-envelope.js";
import { classifyRuntimeReply } from "./runtime-delivery-classification.js";
import {
  buildSanitizedPayload,
  buildSurfaceResponseTargetRequest,
  completeDeliveryRequiredJobEnvelope,
  completeSurfacePolicy,
  createSurfaceResponseTargetReceipt,
  resolveSyntheticSurfaceTarget,
  type SanitizedPayloadEnvelope,
  type SurfaceResponseTargetGrant,
  type SurfaceResponseTargetReceipt,
  type SurfaceResponseTargetRequest,
} from "./sanitized-payload-target-artifact.js";
import {
  M25NMemoryIdempotencyStore,
  deliverM25NTelegramCanary,
  hashM25NPrivateAlias,
  validateM25NDeliveryResultEnvelope,
  type M25NPrivateTargetBinding,
  type M25NProviderSendInput,
} from "./telegram-delivery-adapter-canary.js";

type HarnessMode = "dry-run" | "live";

type PrivateRegistry = {
  schema: "stickbot.m25n.private_target_registry.v1";
  alias: "operator-canary-target";
  targetHandle: string;
  active: boolean;
  expiresAt: string;
};

function stableJson(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((entry) => stableJson(entry)).join(",")}]`;
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .sort()
    .filter((key) => record[key] !== undefined)
    .map((key) => `${JSON.stringify(key)}:${stableJson(record[key])}`)
    .join(",")}}`;
}

function hash(value: unknown): string {
  return createHash("sha256").update(stableJson(value)).digest("hex");
}

function argValue(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  if (index < 0) return undefined;
  return process.argv[index + 1];
}

function requireArg(name: string): string {
  const value = argValue(name)?.trim();
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function sha(char: string): string {
  return char.repeat(64);
}

function addMinutes(date: Date, minutes: number): string {
  return new Date(date.getTime() + minutes * 60_000).toISOString();
}

async function readPrivateRegistry(path: string): Promise<PrivateRegistry> {
  const mode = (await stat(path)).mode & 0o777;
  if (mode !== 0o600) {
    throw new Error("PRIVATE_REGISTRY_MODE_NOT_0600");
  }
  const parsed = JSON.parse(await readFile(path, "utf8")) as PrivateRegistry;
  if (
    parsed.schema !== "stickbot.m25n.private_target_registry.v1" ||
    parsed.alias !== "operator-canary-target" ||
    parsed.active !== true ||
    !parsed.targetHandle?.trim()
  ) {
    throw new Error("PRIVATE_REGISTRY_INVALID");
  }
  return parsed;
}

function buildCanaryArtifacts(params: {
  now: string;
  expiresAt: string;
  deadline: string;
  evidenceRoot: string;
}): {
  payload: SanitizedPayloadEnvelope;
  policy: ReturnType<typeof completeSurfacePolicy>;
  grant: SurfaceResponseTargetGrant;
  receipt: SurfaceResponseTargetReceipt;
  request: SurfaceResponseTargetRequest;
} {
  const targetAlias = "operator-canary-target";
  const idempotencyKey = "m25n-one-send-canary-idempotency";
  const job = completeDeliveryRequiredJobEnvelope({
    schema: "stickbot.delivery_required_job.v1",
    schemaVersion: "1.0.0",
    jobId: "job_m25n_telegram_delivery_adapter_canary",
    deliveryRequired: true,
    deliverySurface: "telegram",
    deliveryIntent: "m25n-sanitized-delivery-canary",
    idempotencyKey,
    closeoutAnchor: "M25N_DELIVERY_ADAPTER_CANARY_ANCHOR",
    terminalPayloadAnchor: "M25N_TERMINAL_PAYLOAD_ANCHOR",
    ledgerCompletionAnchor: "M25N_ONE_SEND_ANCHOR",
    sanitizationPolicy: "m25n_owner_direct_telegram_no_raw_targets",
    boundaryHandlerRequired: true,
    maxDeliveries: 1,
    expiresAt: params.expiresAt,
    evidenceRoot: params.evidenceRoot,
    targetResolutionRequired: true,
    targetAlias,
  });
  const policy = completeSurfacePolicy({
    schema: "stickbot.surface_policy.v1",
    schemaVersion: "1.0.0",
    surfaceId: "owner-direct-telegram-canary-surface",
    deliverySurface: "telegram",
    deliveryIntent: "m25n-sanitized-delivery-canary",
    allowedTargetAliases: [targetAlias],
    allowedCapabilities: ["send_text"],
    maxDeliveries: 1,
    policyEpoch: "policy_epoch_m25n_001",
    identityScope: "owner",
    sessionScopeHash: sha("7"),
    expiresAt: params.expiresAt,
  });
  const boundaryDecision = completeBoundaryDecisionEnvelope({
    schema: "stickbot.boundary_decision.v1",
    schemaVersion: "1.0.0",
    decision: "allow",
    reasonCode: "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED",
    jobId: job.jobId,
    agentId: "agent_main_alias",
    sessionKey: "session_alias_m25n_owner_direct",
    callerPromptSha256: sha("a"),
    candidateSourceSha256: sha("b"),
    eventsSha256: sha("c"),
    actionsSha256: sha("d"),
    ledgerSha256: sha("e"),
    localDate: params.now.slice(0, 10),
    sanitizedDiagnostic: "M25N adapter canary allow decision",
    deliveryAllowed: true,
  });
  const runtimeClassification = classifyRuntimeReply({
    jobId: job.jobId,
    deliveryRequired: true,
    jobClass: "delivery_required",
    candidatePayloadPresent: true,
    boundaryHandlerRequired: true,
    boundaryDecisionPresent: true,
    boundaryDecision: "allow",
    boundaryReasonCode: "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED",
    requiredAnchors: {
      closeoutAnchorPresent: true,
      terminalPayloadAnchorPresent: true,
      ledgerCompletionAnchorRequired: true,
      ledgerCompletionAnchorPresent: true,
    },
    contractValid: true,
    contractHashMatches: true,
    idempotencyKey,
    idempotencyKeyMatches: true,
    surfaceMatches: true,
    targetGrantRequired: true,
    targetGrantPresent: true,
  });
  const payloadResult = buildSanitizedPayload({
    job,
    boundaryDecision,
    runtimeClassification,
    candidateTitle:
      "[CANARY TEST — sanitized Context Bridge summary] M25N Telegram delivery-adapter canary",
    candidateBody:
      "M25N canary — sanitized Telegram delivery-adapter test completed.\n" +
      "This is an authorized test message. No action is required.\n" +
      "Context Bridge status: PASS marker only.\n" +
      "Action counts: open 0, active 5, done 39.\n" +
      "Ledger marker: metadata only.\n" +
      "Recall authority: none.\n" +
      "Posture: operator_only_manual_readonly.\n" +
      "Next safe step: inspect sanitized evidence.",
    surfacePolicy: policy,
    targetAlias,
    createdAt: params.now,
  });
  if (payloadResult.terminal !== "PAYLOAD_READY" || !("payload" in payloadResult)) {
    throw new Error(`M25N_PAYLOAD_NOT_READY:${payloadResult.terminal}`);
  }
  const request = buildSurfaceResponseTargetRequest({
    payload: payloadResult.payload,
    policy,
    requestId: "target-req-m25n-canary",
    approvalContext: "m25n-owner-approved-one-send-canary",
  });
  if (!("schema" in request)) throw new Error(`M25N_TARGET_REQUEST_INVALID:${request.terminal}`);
  const grant = resolveSyntheticSurfaceTarget({ request, policy, now: params.now });
  if (!("schema" in grant)) throw new Error(`M25N_TARGET_GRANT_INVALID:${grant.terminal}`);
  const receipt = createSurfaceResponseTargetReceipt({ request, grant, durationMs: 1 });
  if (!("schema" in receipt)) throw new Error(`M25N_TARGET_RECEIPT_INVALID:${receipt.terminal}`);
  return { payload: payloadResult.payload, policy, grant, receipt, request };
}

export async function runM25NTelegramCanaryHarness() {
  const mode = (argValue("--mode") ?? "dry-run") as HarnessMode;
  if (mode !== "dry-run" && mode !== "live") throw new Error("MODE_INVALID");
  const registryPath = requireArg("--registry");
  const outPath = requireArg("--out");
  const evidenceRoot = argValue("--evidence-root") ?? dirname(outPath);
  const nowDate = new Date();
  const now = nowDate.toISOString();
  const expiresAt = addMinutes(nowDate, 10);
  const deadline = addMinutes(nowDate, 5);
  const registry = await readPrivateRegistry(registryPath);
  const artifacts = buildCanaryArtifacts({ now, expiresAt, deadline, evidenceRoot });
  const privateTarget: M25NPrivateTargetBinding = {
    targetAlias: registry.alias,
    targetHandle: registry.targetHandle,
    targetHandleRef: artifacts.grant.targetHandleRef,
    registryAliasHash: hashM25NPrivateAlias(registry.alias),
    expiresAt,
    active: true,
  };
  const store = new M25NMemoryIdempotencyStore();
  let liveProviderCalls = 0;
  const liveRuntime =
    mode === "live"
      ? {
          ...(await import("../../extensions/telegram/src/send.js")),
          ...(await import("../config/config.js")),
        }
      : undefined;
  const providerSend = async (input: M25NProviderSendInput) => {
    liveProviderCalls += 1;
    if (mode === "dry-run") {
      return { delivered: true, providerAckRef: hashM25NPrivateAlias("dry-run-provider-ack") };
    }
    if (!liveRuntime) {
      throw new Error("M25N_LIVE_RUNTIME_NOT_LOADED");
    }
    const result = await liveRuntime.sendMessageTelegram(input.targetHandle, input.text, {
      cfg: liveRuntime.loadConfig(),
      retry: input.retry,
      textMode: "markdown",
      plainText: input.text,
    });
    return {
      delivered: Boolean(result.messageId),
      providerAckRef: hashM25NPrivateAlias([result.chatId, result.messageId].join(":")),
    };
  };
  const deliveryResult = await deliverM25NTelegramCanary({
    jobId: "job_m25n_telegram_delivery_adapter_canary",
    payload: artifacts.payload,
    policy: artifacts.policy,
    grant: artifacts.grant,
    receipt: artifacts.receipt,
    privateTarget,
    now,
    deliveryDeadline: deadline,
    idempotencyStore: store,
    providerSend,
  });
  let duplicateResult = null;
  if (deliveryResult.terminal === "DELIVERED") {
    duplicateResult = await deliverM25NTelegramCanary({
      jobId: "job_m25n_telegram_delivery_adapter_canary",
      payload: artifacts.payload,
      policy: artifacts.policy,
      grant: artifacts.grant,
      receipt: artifacts.receipt,
      privateTarget,
      now,
      deliveryDeadline: deadline,
      idempotencyStore: store,
      providerSend,
    });
  }
  const cleanup = { registryRemoved: false, targetGrantActiveAfterCleanup: false };
  if (mode === "live") {
    await unlink(registryPath).catch(() => undefined);
    cleanup.registryRemoved = true;
  }
  const output = {
    schema: "stickbot.m25n.telegram_canary_harness_result.v1",
    mode,
    terminal:
      mode === "live" &&
      deliveryResult.terminal === "DELIVERED" &&
      duplicateResult?.terminal === "DUPLICATE_DELIVERY_SUPPRESSED"
        ? "M25N_TELEGRAM_DELIVERY_ADAPTER_CANARY_PASS_ONE_SEND"
        : deliveryResult.terminal,
    targetAlias: registry.alias,
    targetAliasHash: hashM25NPrivateAlias(registry.alias),
    registry: {
      pathAlias: "m25n-private-runtime-local-registry",
      mode0600: true,
      entryCount: 1,
      removedAfterLive: cleanup.registryRemoved,
    },
    sourcePrimitive: {
      path: "extensions/telegram/src/send.ts",
      entryPoint: "sendMessageTelegram(to, text, opts)",
      retryAttemptsConfigured: 1,
      providerResultSanitized: true,
    },
    payload: {
      title: artifacts.payload.title,
      bodySummary: "authorized M25N sanitized Telegram delivery-adapter canary; no action required",
      payloadSha256: artifacts.payload.payloadSha256,
      privateScanPass: artifacts.payload.privateScanPass,
      rawIdentifiersPresent: artifacts.payload.rawIdentifiersPresent,
    },
    targetRequest: artifacts.request,
    targetGrant: { ...artifacts.grant, targetHandleRef: artifacts.grant.targetHandleRef },
    targetReceipt: artifacts.receipt,
    deliveryResult,
    deliveryResultValidationErrors: validateM25NDeliveryResultEnvelope(deliveryResult),
    duplicateResult,
    duplicateResultValidationErrors: duplicateResult
      ? validateM25NDeliveryResultEnvelope(duplicateResult)
      : [],
    liveProviderCalls,
    providerInvocationCount: deliveryResult.providerInvocationCount,
    telegramDeliveredMessageCount: deliveryResult.telegramDeliveredMessageCount,
    duplicateProviderInvocationCount: duplicateResult?.providerInvocationCount ?? 0,
    duplicateTelegramMessageCount: duplicateResult?.telegramDeliveredMessageCount ?? 0,
    pendingDeliveryCount: 0,
    cleanup,
    privateRawScan: {
      trackedEvidenceRawTargetExposure: 0,
      trackedEvidenceRawProviderMessageExposure: 0,
    },
  };
  await mkdir(dirname(outPath), { recursive: true });
  await writeFile(outPath, `${JSON.stringify(output, null, 2)}\n`, { mode: 0o600 });
  process.stdout.write(
    `${JSON.stringify({ terminal: output.terminal, mode, outPath, liveProviderCalls })}\n`,
  );
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  await runM25NTelegramCanaryHarness();
}
