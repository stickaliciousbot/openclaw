import assert from "node:assert/strict";
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
} from "./telegram-delivery-adapter-canary.js";

const sha = (char: string) => char.repeat(64);
const now = "2026-07-19T11:00:00Z";
const expiresAt = "2026-07-19T11:10:00Z";
const deadline = "2026-07-19T11:05:00Z";
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
  expiresAt,
  evidenceRoot:
    "sharedspace/runtime-kernel-validation/memory-ledger/m25n_telegram_delivery_adapter_canary",
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
  expiresAt,
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
  localDate: "2026-07-19",
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

function buildPayload(
  body = "M25N canary — sanitized Telegram delivery-adapter test completed.\nThis is an authorized test message. No action is required.\nContext Bridge status: PASS marker only.\nAction counts: open 0, active 5, done 39.\nLedger marker: metadata only.\nRecall authority: none.\nPosture: operator_only_manual_readonly.\nNext safe step: inspect sanitized evidence.",
): SanitizedPayloadEnvelope {
  const result = buildSanitizedPayload({
    job,
    boundaryDecision,
    runtimeClassification,
    candidateTitle:
      "[CANARY TEST — sanitized Context Bridge summary] M25N Telegram delivery-adapter canary",
    candidateBody: body,
    surfacePolicy: policy,
    targetAlias,
    createdAt: now,
  });
  assert.equal(result.terminal, "PAYLOAD_READY");
  if (!("payload" in result)) {
    throw new Error("M25N test payload was not produced");
  }
  return result.payload;
}

function buildGrantReceipt(payload = buildPayload()): {
  grant: SurfaceResponseTargetGrant;
  receipt: SurfaceResponseTargetReceipt;
  request: SurfaceResponseTargetRequest;
} {
  const request = buildSurfaceResponseTargetRequest({
    payload,
    policy,
    requestId: "target-req-m25n-canary",
    approvalContext: "m25n-owner-approved-one-send-canary",
  });
  assert.equal("schema" in request, true);
  const typedRequest = request as SurfaceResponseTargetRequest;
  const grant = resolveSyntheticSurfaceTarget({ request: typedRequest, policy, now });
  assert.equal("schema" in grant, true);
  const typedGrant = grant as SurfaceResponseTargetGrant;
  const receipt = createSurfaceResponseTargetReceipt({
    request: typedRequest,
    grant: typedGrant,
    durationMs: 1,
  });
  assert.equal("schema" in receipt, true);
  return {
    grant: typedGrant,
    receipt: receipt as SurfaceResponseTargetReceipt,
    request: typedRequest,
  };
}

function privateTarget(grant: SurfaceResponseTargetGrant): M25NPrivateTargetBinding {
  return {
    targetAlias,
    targetHandle: "private-test-handle",
    targetHandleRef: grant.targetHandleRef,
    registryAliasHash: hashM25NPrivateAlias(targetAlias),
    expiresAt,
    active: true,
  };
}

async function runValidSend() {
  const payload = buildPayload();
  const { grant, receipt } = buildGrantReceipt(payload);
  const store = new M25NMemoryIdempotencyStore();
  let calls = 0;
  const result = await deliverM25NTelegramCanary({
    jobId: job.jobId,
    payload,
    policy,
    grant,
    receipt,
    privateTarget: privateTarget(grant),
    now,
    deliveryDeadline: deadline,
    idempotencyStore: store,
    providerSend: async (input) => {
      calls += 1;
      assert.equal(input.targetHandle, "private-test-handle");
      assert.equal(input.retry.attempts, 1);
      assert.equal(input.retry.minDelayMs, 0);
      assert.equal(input.text.startsWith("[CANARY TEST — sanitized Context Bridge summary]"), true);
      return { delivered: true, providerAckRef: hashM25NPrivateAlias("provider-ack") };
    },
  });
  assert.equal(calls, 1);
  assert.deepEqual(validateM25NDeliveryResultEnvelope(result), []);
  assert.equal(result.terminal, "DELIVERED");
  assert.equal(result.deliveryAttempted, true);
  assert.equal(result.delivered, true);
  assert.equal(result.providerInvocationCount, 1);
  assert.equal(result.telegramDeliveredMessageCount, 1);
  return { payload, grant, receipt, store };
}

await runValidSend();

{
  const { payload, grant, receipt, store } = await runValidSend();
  let duplicateCalls = 0;
  const duplicate = await deliverM25NTelegramCanary({
    jobId: job.jobId,
    payload,
    policy,
    grant,
    receipt,
    privateTarget: privateTarget(grant),
    now,
    deliveryDeadline: deadline,
    idempotencyStore: store,
    providerSend: async () => {
      duplicateCalls += 1;
      return { delivered: true, providerAckRef: "should-not-run" };
    },
  });
  assert.equal(duplicateCalls, 0);
  assert.deepEqual(validateM25NDeliveryResultEnvelope(duplicate), []);
  assert.equal(duplicate.terminal, "DUPLICATE_DELIVERY_SUPPRESSED");
  assert.equal(duplicate.providerInvocationCount, 0);
  assert.equal(duplicate.telegramDeliveredMessageCount, 0);
}

const negativeCases = [
  {
    label: "unsanitized body",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload: { ...payload, body: "chat_id: forbidden" } as SanitizedPayloadEnvelope,
      grant,
      receipt,
      target,
    }),
    terminal: "PAYLOAD_SANITIZATION_FAILED_NO_DELIVERY",
  },
  {
    label: "missing target grant",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload,
      grant: { ...grant, deliveryAllowed: false } as SurfaceResponseTargetGrant,
      receipt,
      target,
    }),
    terminal: "TARGET_BINDING_INVALID_NO_DELIVERY",
  },
  {
    label: "expired grant",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload,
      grant: { ...grant, expiresAt: "2026-07-19T10:00:00Z" } as SurfaceResponseTargetGrant,
      receipt,
      target: { ...target, expiresAt: "2026-07-19T10:00:00Z" },
    }),
    terminal: "TARGET_GRANT_EXPIRED_NO_DELIVERY",
  },
  {
    label: "wrong alias",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload: { ...payload, targetAlias: "wrong-target" } as SanitizedPayloadEnvelope,
      grant,
      receipt,
      target,
    }),
    terminal: "TARGET_BINDING_INVALID_NO_DELIVERY",
  },
  {
    label: "wrong identity",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload,
      grant: { ...grant, identityVerified: false } as SurfaceResponseTargetGrant,
      receipt,
      target,
    }),
    terminal: "TARGET_BINDING_INVALID_NO_DELIVERY",
  },
  {
    label: "wrong capability",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload,
      grant: {
        ...grant,
        allowedCapabilities: ["send_text_but_wrong"],
      } as unknown as SurfaceResponseTargetGrant,
      receipt,
      target,
    }),
    terminal: "TARGET_BINDING_INVALID_NO_DELIVERY",
  },
  {
    label: "max deliveries too high",
    mutate: (
      payload: SanitizedPayloadEnvelope,
      grant: SurfaceResponseTargetGrant,
      receipt: SurfaceResponseTargetReceipt,
      target: M25NPrivateTargetBinding,
    ) => ({
      payload,
      grant: { ...grant, maxDeliveries: 2 } as unknown as SurfaceResponseTargetGrant,
      receipt,
      target,
    }),
    terminal: "TARGET_BINDING_INVALID_NO_DELIVERY",
  },
];

for (const item of negativeCases) {
  const payload = buildPayload();
  const { grant, receipt } = buildGrantReceipt(payload);
  const mutated = item.mutate(payload, grant, receipt, privateTarget(grant));
  let calls = 0;
  const result = await deliverM25NTelegramCanary({
    jobId: job.jobId,
    payload: mutated.payload,
    policy,
    grant: mutated.grant,
    receipt: mutated.receipt,
    privateTarget: mutated.target,
    now,
    deliveryDeadline: deadline,
    idempotencyStore: new M25NMemoryIdempotencyStore(),
    providerSend: async () => {
      calls += 1;
      return { delivered: true, providerAckRef: "should-not-run" };
    },
  });
  assert.equal(calls, 0, item.label);
  assert.equal(result.terminal, item.terminal, item.label);
}

{
  const payload = buildPayload();
  const { grant, receipt } = buildGrantReceipt(payload);
  const result = await deliverM25NTelegramCanary({
    jobId: job.jobId,
    payload,
    policy,
    grant,
    receipt,
    privateTarget: privateTarget(grant),
    now,
    deliveryDeadline: deadline,
    idempotencyStore: new M25NMemoryIdempotencyStore(),
    providerSend: async () => ({ delivered: false, providerAckRef: "" }),
  });
  assert.equal(result.terminal, "PROVIDER_DELIVERY_AMBIGUOUS_NO_RETRY");
  assert.equal(result.providerInvocationCount, 1);
  assert.equal(result.telegramDeliveredMessageCount, 0);
}
