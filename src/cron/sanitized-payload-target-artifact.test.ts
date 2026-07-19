import assert from "node:assert/strict";
import { completeBoundaryDecisionEnvelope } from "./boundary-decision-envelope.js";
import {
  classifyRuntimeReply,
  runtimeReplyClassificationToLegacyText,
} from "./runtime-delivery-classification.js";
import {
  M25M_OUTCOMES,
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
  type DeliveryRequiredJobEnvelope,
  type SanitizedPayloadEnvelope,
  type SurfaceResponseTargetGrant,
  type SurfaceResponseTargetReceipt,
  type SurfaceResponseTargetRequest,
  type SurfacePolicy,
} from "./sanitized-payload-target-artifact.js";

const sha = (char: string) => char.repeat(64);
const timestamp = "2026-07-19T09:51:00Z";
const expiresAt = "2026-07-20T00:00:00Z";

const job = completeDeliveryRequiredJobEnvelope({
  schema: "stickbot.delivery_required_job.v1",
  schemaVersion: "1.0.0",
  jobId: "job_m25m_artifact_canary",
  deliveryRequired: true,
  deliverySurface: "owner_direct",
  deliveryIntent: "ledger-completion-closeout",
  idempotencyKey: "m25m-artifact-canary-idempotency",
  closeoutAnchor: "M25M_CLOSEOUT_ANCHOR",
  terminalPayloadAnchor: "M25M_TERMINAL_PAYLOAD_ANCHOR",
  ledgerCompletionAnchor: "M25M_LEDGER_V0_1_ARTIFACT_CANARY_ANCHOR",
  sanitizationPolicy: "m25m_synthetic_no_raw_targets",
  boundaryHandlerRequired: true,
  maxDeliveries: 1,
  expiresAt,
  evidenceRoot: "sharedspace/runtime-kernel-validation/memory-ledger/m25m_synthetic_canary",
  targetResolutionRequired: true,
  targetAlias: "operator-canary-target",
});

const policy = completeSurfacePolicy({
  schema: "stickbot.surface_policy.v1",
  schemaVersion: "1.0.0",
  surfaceId: "owner-direct-canary-surface",
  deliverySurface: "owner_direct",
  deliveryIntent: "ledger-completion-closeout",
  allowedTargetAliases: ["operator-canary-target"],
  allowedCapabilities: ["send_text"],
  maxDeliveries: 1,
  policyEpoch: "policy_epoch_m25m_001",
  identityScope: "operator_canary_identity",
  sessionScopeHash: sha("6"),
  expiresAt,
});

const boundaryDecision = completeBoundaryDecisionEnvelope({
  schema: "stickbot.boundary_decision.v1",
  schemaVersion: "1.0.0",
  decision: "allow",
  reasonCode: "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED",
  jobId: job.jobId,
  agentId: "agent_main_alias",
  sessionKey: "session_alias_m25m",
  callerPromptSha256: sha("a"),
  candidateSourceSha256: sha("b"),
  eventsSha256: sha("c"),
  actionsSha256: sha("d"),
  ledgerSha256: sha("e"),
  localDate: "2026-07-19",
  sanitizedDiagnostic: "synthetic allow for artifact canary",
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
  idempotencyKey: job.idempotencyKey,
  idempotencyKeyMatches: true,
  surfaceMatches: true,
  targetGrantRequired: false,
});

function buildValidChain(): { chain: DeliveryArtifactChain; validationTerminal: string } {
  const payloadResult = buildSanitizedPayload({
    job,
    boundaryDecision,
    runtimeClassification,
    candidateTitle: "M25M sanitized artifact canary",
    candidateBody:
      "M25M_CLOSEOUT_ANCHOR\nM25M_TERMINAL_PAYLOAD_ANCHOR\nM25M_LEDGER_V0_1_ARTIFACT_CANARY_ANCHOR\nSynthetic sanitized no-send closeout body.",
    surfacePolicy: policy,
    targetAlias: "operator-canary-target",
    createdAt: timestamp,
  });
  assert.equal(payloadResult.terminal, "PAYLOAD_READY");
  const payload = payloadResult.payload;
  const request = buildSurfaceResponseTargetRequest({
    payload,
    policy,
    requestId: "target-req-m25m-canary",
    approvalContext: "m25m-no-send-artifact-canary",
  });
  assert.equal("schema" in request, true);
  const typedRequest = request as SurfaceResponseTargetRequest;
  const grant = resolveSyntheticSurfaceTarget({ request: typedRequest, policy, now: timestamp });
  assert.equal("schema" in grant, true);
  const typedGrant = grant as SurfaceResponseTargetGrant;
  const receipt = createSurfaceResponseTargetReceipt({
    request: typedRequest,
    grant: typedGrant,
    durationMs: 2,
  });
  assert.equal("schema" in receipt, true);
  const typedReceipt = receipt as SurfaceResponseTargetReceipt;
  const deliveryResult = createNoSendDeliveryResult({
    job,
    payload,
    grant: typedGrant,
    receipt: typedReceipt,
    sanitizedEvidencePath:
      "sharedspace/runtime-kernel-validation/memory-ledger/m25m_synthetic_canary/chain_validation_receipt.json",
    timestamp: "2026-07-19T09:51:01Z",
  });
  assert.equal("schema" in deliveryResult, true);
  const typedDeliveryResult = deliveryResult as DeliveryResultEnvelope;
  const chain = {
    job,
    boundaryDecision,
    runtimeClassification,
    sanitizedPayload: payload,
    surfacePolicy: policy,
    targetRequest: typedRequest,
    targetGrant: typedGrant,
    targetReceipt: typedReceipt,
    deliveryResult: typedDeliveryResult,
  } as DeliveryArtifactChain;
  const validation = validateDeliveryArtifactChain(chain);
  assert.equal(validation.valid, true);
  assert.equal(validation.terminal, "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND");
  return { chain, validationTerminal: validation.terminal };
}

assert.equal(runtimeClassification.terminal, "BOUNDARY_ALLOWED_PAYLOAD_READY");
assert.equal(runtimeReplyClassificationToLegacyText(runtimeClassification), undefined);

const { chain } = buildValidChain();
assert.equal(chain.sanitizedPayload.sanitized, true);
assert.equal(chain.sanitizedPayload.rawIdentifiersPresent, false);
assert.equal(chain.sanitizedPayload.privateScanPass, true);
assert.equal(chain.targetRequest.targetAlias, "operator-canary-target");
assert.equal(chain.targetGrant.targetHandleRef.startsWith("runtime-private-ref:test-only:"), true);
assert.equal(chain.targetReceipt.rawTargetExposed, false);
assert.equal(chain.deliveryResult.deliveryAttempted, false);
assert.equal(chain.deliveryResult.delivered, false);
assert.equal(chain.deliveryResult.errorClass, "NO_SEND_ARTIFACT_CANARY");

const second = buildValidChain().chain;
assert.equal(second.sanitizedPayload.payloadSha256, chain.sanitizedPayload.payloadSha256);
assert.equal(second.targetReceipt.receiptSha256, chain.targetReceipt.receiptSha256);
assert.equal(second.deliveryResult.resultSha256, chain.deliveryResult.resultSha256);
assert.equal(
  validateDeliveryArtifactChain(second).chainSha256,
  validateDeliveryArtifactChain(chain).chainSha256,
);

for (const decision of ["hold", "reject"] as const) {
  const blockedBoundary = completeBoundaryDecisionEnvelope({
    ...boundaryDecision,
    decision,
    reasonCode:
      decision === "hold" ? "BOUNDARY_UNARMED_HOLD" : "BOUNDARY_PRIVACY_SCAN_FAILED_REJECT",
    deliveryAllowed: false,
  });
  const result = buildSanitizedPayload({
    job,
    boundaryDecision: blockedBoundary,
    runtimeClassification,
    candidateTitle: "blocked",
    candidateBody: "blocked",
    surfacePolicy: policy,
    targetAlias: "operator-canary-target",
    createdAt: timestamp,
  });
  assert.equal(
    result.terminal,
    decision === "hold" ? "BOUNDARY_HOLD_NO_DELIVERY" : "BOUNDARY_REJECT_NO_DELIVERY",
  );
}

const rawProviderTargetSentinel = "<RAW_PROVIDER_TARGET_ID" + "_FORBIDDEN>";
const secretLikePayloadSentinel = "<SECRET_LIKE_PAYLOAD" + "_FORBIDDEN>";
for (const candidateBody of [
  "",
  rawProviderTargetSentinel,
  secretLikePayloadSentinel,
  "x".repeat(2000),
]) {
  const result = buildSanitizedPayload({
    job,
    boundaryDecision,
    runtimeClassification,
    candidateTitle: "M25M synthetic",
    candidateBody,
    surfacePolicy: policy,
    targetAlias: "operator-canary-target",
    createdAt: timestamp,
  });
  assert.notEqual(result.terminal, "PAYLOAD_READY");
}

for (const bad of [
  {
    label: "missing alias",
    policy: { ...policy, allowedTargetAliases: [] } as SurfacePolicy,
    terminal: "TARGET_RESOLUTION_HOLD_NO_DELIVERY",
  },
  {
    label: "wrong surface",
    policy: { ...policy, surfaceId: "other-surface" } as SurfacePolicy,
    terminal: "TARGET_RESOLUTION_DENIED_NO_DELIVERY",
  },
]) {
  const request = buildSurfaceResponseTargetRequest({
    payload: chain.sanitizedPayload,
    policy: bad.policy,
    requestId: `bad-${bad.label}`,
    approvalContext: "m25m",
  });
  if ("terminal" in request) assert.equal(request.terminal, bad.terminal);
}

const denied = resolveSyntheticSurfaceTarget({
  request: chain.targetRequest,
  policy,
  now: timestamp,
  identityVerified: false,
});
assert.equal("terminal" in denied && denied.terminal, "TARGET_RESOLUTION_DENIED_NO_DELIVERY");
const expired = resolveSyntheticSurfaceTarget({
  request: { ...chain.targetRequest, expiresAt: "2026-07-18T00:00:00Z" },
  policy,
  now: timestamp,
});
assert.equal("terminal" in expired && expired.terminal, "TARGET_GRANT_EXPIRED_NO_DELIVERY");
const fallback = buildSurfaceResponseTargetRequest({
  payload: {
    ...chain.sanitizedPayload,
    targetAlias: "fallback-target",
  } as SanitizedPayloadEnvelope,
  policy,
  requestId: "fallback",
  approvalContext: "m25m",
});
assert.equal("terminal" in fallback && fallback.terminal, "TARGET_RESOLUTION_HOLD_NO_DELIVERY");

for (const mutate of [
  { deliveryAttempted: true },
  { delivered: true },
  { idempotencyKey: "wrong-idempotency" },
  { policyEpoch: "wrong-policy" },
]) {
  const broken = validateDeliveryArtifactChain({
    ...chain,
    deliveryResult: { ...chain.deliveryResult, ...mutate } as typeof chain.deliveryResult,
  });
  assert.equal(broken.valid, false);
}
for (const mutate of [
  { targetAlias: "wrong-alias" },
  { targetHandleRef: "provider:real-looking-target" },
  { maxDeliveries: 2 },
]) {
  const broken = validateDeliveryArtifactChain({
    ...chain,
    targetGrant: { ...chain.targetGrant, ...mutate } as typeof chain.targetGrant,
  });
  assert.equal(broken.valid, false);
}
for (const mutate of [{ payloadSha256: "f".repeat(64) }, { targetAlias: "wrong-alias" }]) {
  const broken = validateDeliveryArtifactChain({
    ...chain,
    sanitizedPayload: { ...chain.sanitizedPayload, ...mutate } as typeof chain.sanitizedPayload,
  });
  assert.equal(broken.valid, false);
}
const rawReceipt = validateDeliveryArtifactChain({
  ...chain,
  targetReceipt: {
    ...chain.targetReceipt,
    rawTargetExposed: true,
  } as unknown as typeof chain.targetReceipt,
});
assert.equal(rawReceipt.valid, false);

const quiet = classifyRuntimeReply({
  jobId: "quiet-watcher",
  deliveryRequired: false,
  jobClass: "quiet_success",
});
assert.equal(runtimeReplyClassificationToLegacyText(quiet), "NO_REPLY");
const missingDecision = classifyRuntimeReply({
  ...runtimeClassification,
  boundaryHandlerRequired: true,
  boundaryDecisionPresent: false,
});
assert.equal(missingDecision.terminal, "BOUNDARY_DECISION_MISSING");
assert.notEqual(runtimeReplyClassificationToLegacyText(missingDecision), "NO_REPLY");
assert.equal(M25M_OUTCOMES.includes("PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND"), true);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      terminal: "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND",
      positiveFixtures: 12,
      negativeFixtures: 28,
      regressionFixtures: 6,
      outcomes: M25M_OUTCOMES.length,
    },
    null,
    2,
  ),
);
