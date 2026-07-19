import { completeBoundaryDecisionEnvelope } from "./boundary-decision-envelope.js";
import { classifyRuntimeReply } from "./runtime-delivery-classification.js";
import {
  buildSanitizedPayload,
  buildSurfaceResponseTargetRequest,
  completeDeliveryRequiredJobEnvelope,
  completeSurfacePolicy,
  createNoSendDeliveryResult,
  createSurfaceResponseTargetReceipt,
  resolveSyntheticSurfaceTarget,
  validateDeliveryArtifactChain,
  type DeliveryArtifactChain,
  type DeliveryResultEnvelope,
  type SurfaceResponseTargetGrant,
  type SurfaceResponseTargetReceipt,
  type SurfaceResponseTargetRequest,
} from "./sanitized-payload-target-artifact.js";
import {
  M25NMemoryIdempotencyStore,
  deliverM25NTelegramCanary,
  hashM25NPrivateAlias,
  validateM25NDeliveryResultEnvelope,
  type M25NDeliveryResultEnvelope,
  type M25NPrivateTargetBinding,
} from "./telegram-delivery-adapter-canary.js";
export { runM25NTelegramCanaryHarness } from "./m25n-telegram-canary-harness.js";

export const M25O_PACKAGED_RUNTIME_WIRING_REPAIR_TERMINAL =
  "M25O_A_R_PACKAGED_RUNTIME_WIRING_REPAIR_PASS_NO_LIVE_INSTALL" as const;

const timestamp = "2026-07-19T13:30:00.000Z";
const localDate = "2026-07-19";
const expiresAt = "2026-07-20T00:00:00.000Z";
const deadline = "2026-07-19T13:35:00.000Z";
const targetAlias = "operator-canary-target";
const idempotencyKey = "m25o-a-r-packaged-runtime-wiring-idempotency";
const sha = (char: string) => char.repeat(64);

function requireEnvelope<T extends object>(
  value: T | { terminal: string; errors: string[] },
  label: string,
): T {
  if ("terminal" in value && "errors" in value) {
    throw new Error(`${label}:${value.terminal}:${value.errors.join(",")}`);
  }
  return value;
}

function buildNoSendArtifactChain(): DeliveryArtifactChain {
  const job = completeDeliveryRequiredJobEnvelope({
    schema: "stickbot.delivery_required_job.v1",
    schemaVersion: "1.0.0",
    jobId: "job_m25o_a_r_packaged_runtime_wiring_no_send",
    deliveryRequired: true,
    deliverySurface: "telegram",
    deliveryIntent: "m25o-a-r-packaged-runtime-wiring-no-send-smoke",
    idempotencyKey,
    closeoutAnchor: "M25O_A_R_CLOSEOUT_ANCHOR",
    terminalPayloadAnchor: "M25O_A_R_TERMINAL_PAYLOAD_ANCHOR",
    ledgerCompletionAnchor: "M25O_A_R_LEDGER_COMPLETION_ANCHOR",
    sanitizationPolicy: "m25o_a_r_packaged_runtime_wiring_no_raw_targets",
    boundaryHandlerRequired: true,
    maxDeliveries: 1,
    expiresAt,
    evidenceRoot:
      "sharedspace/runtime-kernel-validation/memory-ledger/m25o_a_r_packaged_runtime_wiring",
    targetResolutionRequired: true,
    targetAlias,
  });
  const policy = completeSurfacePolicy({
    schema: "stickbot.surface_policy.v1",
    schemaVersion: "1.0.0",
    surfaceId: "owner-direct-telegram-no-send-smoke-surface",
    deliverySurface: "telegram",
    deliveryIntent: "m25o-a-r-packaged-runtime-wiring-no-send-smoke",
    allowedTargetAliases: [targetAlias],
    allowedCapabilities: ["send_text"],
    maxDeliveries: 1,
    policyEpoch: "policy_epoch_m25o_a_r_001",
    identityScope: "owner",
    sessionScopeHash: sha("7"),
    expiresAt,
  });
  const boundaryDecision = completeBoundaryDecisionEnvelope({
    schema: "stickbot.boundary_decision.v1",
    schemaVersion: "1.0.0",
    decision: "allow",
    reasonCode: "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED",
    jobId: job.jobId,
    agentId: "agent_main_alias",
    sessionKey: "session_alias_m25o_a_r_owner_direct",
    callerPromptSha256: sha("a"),
    candidateSourceSha256: sha("b"),
    eventsSha256: sha("c"),
    actionsSha256: sha("d"),
    ledgerSha256: sha("e"),
    localDate,
    sanitizedDiagnostic: "M25O-A-R packaged runtime wiring no-send smoke allow decision",
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
      "[CANARY TEST — sanitized Context Bridge summary] M25O-A-R packaged runtime wiring",
    candidateBody:
      "M25O_A_R_CLOSEOUT_ANCHOR\n" +
      "M25O_A_R_TERMINAL_PAYLOAD_ANCHOR\n" +
      "M25O_A_R_LEDGER_COMPLETION_ANCHOR\n" +
      "Packaged runtime import and no-send delivery-contract smoke completed. No provider send was attempted.",
    surfacePolicy: policy,
    targetAlias,
    createdAt: timestamp,
  });
  if (payloadResult.terminal !== "PAYLOAD_READY") {
    throw new Error(`PAYLOAD_NOT_READY:${payloadResult.terminal}`);
  }
  const request: SurfaceResponseTargetRequest = requireEnvelope<SurfaceResponseTargetRequest>(
    buildSurfaceResponseTargetRequest({
      payload: payloadResult.payload,
      policy,
      requestId: "target-req-m25o-a-r-packaged-runtime-wiring",
      approvalContext: "m25o-a-r-no-live-install-no-send-smoke",
    }),
    "TARGET_REQUEST_INVALID",
  );
  const grant: SurfaceResponseTargetGrant = requireEnvelope<SurfaceResponseTargetGrant>(
    resolveSyntheticSurfaceTarget({ request, policy, now: timestamp }),
    "TARGET_GRANT_INVALID",
  );
  const receipt: SurfaceResponseTargetReceipt = requireEnvelope<SurfaceResponseTargetReceipt>(
    createSurfaceResponseTargetReceipt({ request, grant, durationMs: 1 }),
    "TARGET_RECEIPT_INVALID",
  );
  const deliveryResult: DeliveryResultEnvelope = requireEnvelope<DeliveryResultEnvelope>(
    createNoSendDeliveryResult({
      job,
      payload: payloadResult.payload,
      grant,
      receipt,
      sanitizedEvidencePath:
        "sharedspace/runtime-kernel-validation/memory-ledger/m25o_a_r_packaged_runtime_wiring/candidate_no_send_smoke.json",
      timestamp,
    }),
    "NO_SEND_RESULT_INVALID",
  );
  return {
    job,
    boundaryDecision,
    runtimeClassification,
    sanitizedPayload: payloadResult.payload,
    surfacePolicy: policy,
    targetRequest: request,
    targetGrant: grant,
    targetReceipt: receipt,
    deliveryResult,
  };
}

async function runTelegramAdapterFailClosedNoSend(chain: DeliveryArtifactChain): Promise<{
  result: M25NDeliveryResultEnvelope;
  providerCalls: number;
  validationErrors: string[];
}> {
  let providerCalls = 0;
  const privateTarget: M25NPrivateTargetBinding = {
    targetAlias,
    targetHandle: "test-only-target-handle",
    targetHandleRef: chain.targetGrant.targetHandleRef,
    registryAliasHash: hashM25NPrivateAlias(targetAlias),
    expiresAt,
    active: false,
  };
  const result = await deliverM25NTelegramCanary({
    jobId: chain.job.jobId,
    payload: chain.sanitizedPayload,
    policy: chain.surfacePolicy,
    grant: chain.targetGrant,
    receipt: chain.targetReceipt,
    privateTarget,
    now: timestamp,
    deliveryDeadline: deadline,
    idempotencyStore: new M25NMemoryIdempotencyStore(),
    providerSend: async () => {
      providerCalls += 1;
      throw new Error("M25O_A_R_PROVIDER_SEND_FORBIDDEN_IN_NO_SEND_SMOKE");
    },
  });
  return { result, providerCalls, validationErrors: validateM25NDeliveryResultEnvelope(result) };
}

export type M25OPackagedRuntimeNoSendSmokeReceipt = {
  schema: "stickbot.m25o_a_r.packaged_runtime_wiring.no_send_smoke.v1";
  terminal: typeof M25O_PACKAGED_RUNTIME_WIRING_REPAIR_TERMINAL;
  chainTerminal: "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND";
  providerSendAttempted: false;
  providerInvocationCount: 0;
  telegramDeliveredMessageCount: 0;
  adapterTerminal: "TARGET_BINDING_INVALID_NO_DELIVERY";
  importedRuntimeModules: string[];
  payloadSha256: string;
  targetReceiptSha256: string;
  resultSha256: string;
  chainSha256: string;
  errors: string[];
};

export async function runM25OPackagedRuntimeNoSendSmoke(): Promise<M25OPackagedRuntimeNoSendSmokeReceipt> {
  const chain = buildNoSendArtifactChain();
  const validation = validateDeliveryArtifactChain(chain);
  const adapter = await runTelegramAdapterFailClosedNoSend(chain);
  const errors = [...validation.errors, ...adapter.validationErrors];
  if (validation.terminal !== "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND") {
    errors.push(`CHAIN_TERMINAL:${validation.terminal}`);
  }
  if (adapter.result.terminal !== "TARGET_BINDING_INVALID_NO_DELIVERY") {
    errors.push(`ADAPTER_TERMINAL:${adapter.result.terminal}`);
  }
  if (
    adapter.providerCalls !== 0 ||
    adapter.result.deliveryAttempted !== false ||
    adapter.result.delivered !== false ||
    adapter.result.providerInvocationCount !== 0 ||
    adapter.result.telegramDeliveredMessageCount !== 0
  ) {
    errors.push("PROVIDER_SEND_ATTEMPTED_IN_NO_SEND_SMOKE");
  }
  if (errors.length > 0) {
    throw new Error(`M25O_A_R_NO_SEND_SMOKE_FAILED:${errors.join(",")}`);
  }
  const chainTerminal: "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND" =
    "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND";
  const adapterTerminal: "TARGET_BINDING_INVALID_NO_DELIVERY" =
    "TARGET_BINDING_INVALID_NO_DELIVERY";
  return {
    schema: "stickbot.m25o_a_r.packaged_runtime_wiring.no_send_smoke.v1",
    terminal: M25O_PACKAGED_RUNTIME_WIRING_REPAIR_TERMINAL,
    chainTerminal,
    providerSendAttempted: false,
    providerInvocationCount: 0,
    telegramDeliveredMessageCount: 0,
    adapterTerminal,
    importedRuntimeModules: [
      "boundary-decision-envelope",
      "runtime-delivery-classification",
      "sanitized-payload-target-artifact",
      "telegram-delivery-adapter-canary",
      "m25n-telegram-canary-harness",
    ],
    payloadSha256: chain.sanitizedPayload.payloadSha256,
    targetReceiptSha256: chain.targetReceipt.receiptSha256,
    resultSha256: chain.deliveryResult.resultSha256,
    chainSha256: validation.chainSha256,
    errors,
  };
}
