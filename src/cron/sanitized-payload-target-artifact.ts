import { createHash } from "node:crypto";
import type { BoundaryDecisionEnvelope } from "./boundary-decision-envelope.js";
import type { RuntimeReplyClassification } from "./runtime-delivery-classification.js";

const SHA256_RE = /^[a-f0-9]{64}$/;
const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/;
const MAX_BODY_CHARS = 1800;
const MAX_TITLE_CHARS = 120;
const TEST_ONLY_HANDLE_PREFIX = "runtime-private-ref:test-only:";

const RAW_OR_PRIVATE_PATTERNS = [
  /telegram:[^\s"']+/i,
  /message[_-]?id\s*[:=]/i,
  /chat[_-]?id\s*[:=]/i,
  /account[_-]?id\s*[:=]/i,
  /\b\d{6,}\b/,
  /bot\d+:/i,
  /BEGIN (?:RSA|OPENSSH|PRIVATE)/i,
  /\bsk-[A-Za-z0-9_-]{8,}\b/,
  /authorization\s*:/i,
  /bearer\s+[A-Za-z0-9._-]+/i,
  /<RAW_[A-Z0-9_]+_FORBIDDEN>/,
  /<SECRET_LIKE_[A-Z0-9_]+_FORBIDDEN>/,
];

export const M25M_OUTCOMES = [
  "PAYLOAD_SANITIZATION_FAILED_NO_DELIVERY",
  "TARGET_RESOLUTION_HOLD_NO_DELIVERY",
  "TARGET_RESOLUTION_DENIED_NO_DELIVERY",
  "TARGET_GRANT_EXPIRED_NO_DELIVERY",
  "TARGET_BINDING_INVALID_NO_DELIVERY",
  "NO_SEND_ARTIFACT_CANARY",
  "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND",
] as const;

export type M25MOutcome = (typeof M25M_OUTCOMES)[number];

export type DeliveryRequiredJobEnvelope = {
  schema: "stickbot.delivery_required_job.v1";
  schemaVersion: "1.0.0";
  jobId: string;
  deliveryRequired: true;
  deliverySurface: string;
  deliveryIntent: string;
  idempotencyKey: string;
  closeoutAnchor: string;
  terminalPayloadAnchor: string;
  ledgerCompletionAnchor: string;
  sanitizationPolicy: string;
  boundaryHandlerRequired: true;
  maxDeliveries: 1;
  expiresAt: string;
  evidenceRoot: string;
  contractHash: string;
  targetResolutionRequired: true;
  targetAlias: string;
};

export type SurfacePolicy = {
  schema: "stickbot.surface_policy.v1";
  schemaVersion: "1.0.0";
  surfaceId: string;
  deliverySurface: string;
  deliveryIntent: string;
  allowedTargetAliases: string[];
  allowedCapabilities: ["send_text"];
  maxDeliveries: 1;
  policyEpoch: string;
  identityScope: string;
  sessionScopeHash: string;
  expiresAt: string;
  contractHash: string;
};

export type SanitizedPayloadEnvelope = {
  schema: "stickbot.sanitized_payload.v1";
  schemaVersion: "1.0.0";
  payloadType: "milestone_closeout";
  title: string;
  body: string;
  anchors: {
    closeoutAnchor: string;
    terminalPayloadAnchor: string;
    ledgerCompletionAnchor: string;
  };
  completionStatus: "PASS" | "HOLD" | "REJECT";
  sanitized: true;
  rawIdentifiersPresent: false;
  privateScanPass: true;
  deliverySurface: string;
  targetAlias: string;
  idempotencyKey: string;
  policyEpoch: string;
  createdAt: string;
  payloadSha256: string;
  contractHash: string;
};

export type SurfaceResponseTargetRequest = {
  schema: "stickbot.surface_response_target.request.v1";
  schemaVersion: "1.0.0";
  requestId: string;
  surfaceId: string;
  targetAlias: string;
  identityScope: string;
  sessionScopeHash: string;
  deliveryIntent: string;
  requiredCapabilities: ["send_text"];
  approvalContext: string;
  idempotencyKey: string;
  policyEpoch: string;
  expiresAt: string;
  contractHash: string;
};

export type SurfaceResponseTargetGrant = {
  schema: "stickbot.surface_response_target.grant.v1";
  schemaVersion: "1.0.0";
  grantId: string;
  requestId: string;
  surfaceId: string;
  targetAlias: string;
  targetHandleRef: string;
  targetScopeAlias: string;
  identityVerified: boolean;
  sessionVerified: boolean;
  deliveryAllowed: boolean;
  allowedCapabilities: ["send_text"];
  maxDeliveries: 1;
  policyEpoch: string;
  issuedAt: string;
  expiresAt: string;
  grantSha256: string;
  contractHash: string;
};

export type SurfaceResponseTargetReceipt = {
  schema: "stickbot.surface_response_target.receipt.v1";
  schemaVersion: "1.0.0";
  receiptId: string;
  requestId: string;
  grantId: string;
  surfaceId: string;
  targetAlias: string;
  resolutionStatus: "RESOLVED" | "HOLD" | "DENIED" | "EXPIRED";
  identityVerified: boolean;
  sessionVerified: boolean;
  rawTargetExposed: false;
  policyEpoch: string;
  durationMs: number;
  receiptSha256: string;
  contractHash: string;
};

export type DeliveryResultEnvelope = {
  schema: "stickbot.delivery_result.v1";
  schemaVersion: "1.0.0";
  jobId: string;
  deliveryAttempted: false;
  delivered: false;
  deliverySurface: string;
  targetGrantId: string;
  targetScopeAlias: string;
  deliveryStatus: "suppressed" | "not-delivered";
  idempotencyKey: string;
  policyEpoch: string;
  duplicateSuppressed: false;
  errorClass: "NO_SEND_ARTIFACT_CANARY";
  sanitizedEvidencePath: string;
  timestamp: string;
  resultSha256: string;
  contractHash: string;
};

export type DeliveryArtifactChain = {
  job: DeliveryRequiredJobEnvelope;
  boundaryDecision: BoundaryDecisionEnvelope;
  runtimeClassification: RuntimeReplyClassification;
  sanitizedPayload: SanitizedPayloadEnvelope;
  surfacePolicy: SurfacePolicy;
  targetRequest: SurfaceResponseTargetRequest;
  targetGrant: SurfaceResponseTargetGrant;
  targetReceipt: SurfaceResponseTargetReceipt;
  deliveryResult: DeliveryResultEnvelope;
};

export type ChainValidationReceipt = {
  schema: "stickbot.delivery_artifact_chain.validation_receipt.v1";
  schemaVersion: "1.0.0";
  terminal: "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND" | M25MOutcome;
  valid: boolean;
  jobId: string;
  payloadSha256?: string;
  targetReceiptSha256?: string;
  resultSha256?: string;
  idempotencyKey: string;
  policyEpoch: string;
  errors: string[];
  chainSha256: string;
  contractHash: string;
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

function omit(value: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  return Object.fromEntries(Object.entries(value).filter(([key]) => !keys.includes(key)));
}

function completeContract<T extends Record<string, unknown>>(value: T): T {
  return { ...value, contractHash: hash(omit(value, ["contractHash"])) };
}

function hasRawOrPrivate(value: string): boolean {
  return RAW_OR_PRIVATE_PATTERNS.some((pattern) => pattern.test(value));
}

function symbolicAlias(value: string): boolean {
  return /^[a-z][a-z0-9-]{2,60}$/.test(value) && !hasRawOrPrivate(value);
}

function validSha(value: string | undefined): boolean {
  return typeof value === "string" && SHA256_RE.test(value);
}

export function completeDeliveryRequiredJobEnvelope(
  draft: Omit<DeliveryRequiredJobEnvelope, "contractHash">,
): DeliveryRequiredJobEnvelope {
  return completeContract({ ...draft, contractHash: "" }) as DeliveryRequiredJobEnvelope;
}

export function completeSurfacePolicy(draft: Omit<SurfacePolicy, "contractHash">): SurfacePolicy {
  return completeContract({ ...draft, contractHash: "" }) as SurfacePolicy;
}

export type PayloadBuildResult =
  | { terminal: "PAYLOAD_READY"; payload: SanitizedPayloadEnvelope }
  | { terminal: M25MOutcome | RuntimeReplyClassification["terminal"]; errors: string[] };

export function buildSanitizedPayload(input: {
  job: DeliveryRequiredJobEnvelope;
  boundaryDecision: BoundaryDecisionEnvelope;
  runtimeClassification: RuntimeReplyClassification;
  candidateTitle: string;
  candidateBody: string;
  surfacePolicy: SurfacePolicy;
  targetAlias: string;
  createdAt: string;
}): PayloadBuildResult {
  const errors: string[] = [];
  if (input.boundaryDecision.decision === "hold")
    return { terminal: "BOUNDARY_HOLD_NO_DELIVERY", errors: [] };
  if (input.boundaryDecision.decision === "reject")
    return { terminal: "BOUNDARY_REJECT_NO_DELIVERY", errors: [] };
  if (
    input.boundaryDecision.decision !== "allow" ||
    input.boundaryDecision.deliveryAllowed !== true
  ) {
    return { terminal: "TARGET_BINDING_INVALID_NO_DELIVERY", errors: ["BOUNDARY_ALLOW_REQUIRED"] };
  }
  if (
    input.runtimeClassification.terminal !== "BOUNDARY_ALLOWED_PAYLOAD_READY" &&
    input.runtimeClassification.terminal !== "DELIVERY_REQUIRED_PAYLOAD_READY"
  ) {
    return {
      terminal: input.runtimeClassification.terminal,
      errors: ["RUNTIME_NOT_PAYLOAD_READY"],
    };
  }
  if (input.job.deliveryRequired !== true || input.job.boundaryHandlerRequired !== true)
    errors.push("JOB_DELIVERY_REQUIRED_INVALID");
  if (input.job.maxDeliveries !== 1) errors.push("JOB_MAX_DELIVERIES_INVALID");
  if (input.job.jobId !== input.boundaryDecision.jobId) errors.push("JOB_BOUNDARY_JOB_ID_MISMATCH");
  if (input.job.targetAlias !== input.targetAlias) errors.push("TARGET_ALIAS_JOB_MISMATCH");
  if (input.job.idempotencyKey !== input.runtimeClassification.idempotencyKey)
    errors.push("IDEMPOTENCY_RUNTIME_MISMATCH");
  if (input.job.deliverySurface !== input.surfacePolicy.deliverySurface)
    errors.push("SURFACE_POLICY_MISMATCH");
  if (input.job.deliveryIntent !== input.surfacePolicy.deliveryIntent)
    errors.push("DELIVERY_INTENT_POLICY_MISMATCH");
  if (!input.surfacePolicy.allowedTargetAliases.includes(input.targetAlias))
    errors.push("TARGET_ALIAS_NOT_ALLOWED");
  if (!symbolicAlias(input.targetAlias)) errors.push("TARGET_ALIAS_NOT_SYMBOLIC");
  if (!ISO_RE.test(input.createdAt)) errors.push("CREATED_AT_INVALID");
  if (!input.candidateBody || input.candidateBody.length > MAX_BODY_CHARS)
    errors.push("PAYLOAD_BODY_INVALID");
  if (!input.candidateTitle || input.candidateTitle.length > MAX_TITLE_CHARS)
    errors.push("PAYLOAD_TITLE_INVALID");
  if (hasRawOrPrivate(input.candidateTitle) || hasRawOrPrivate(input.candidateBody))
    errors.push("PAYLOAD_PRIVATE_SCAN_FAILED");
  if (errors.length > 0) {
    return {
      terminal: errors.includes("PAYLOAD_PRIVATE_SCAN_FAILED")
        ? "PAYLOAD_SANITIZATION_FAILED_NO_DELIVERY"
        : "TARGET_BINDING_INVALID_NO_DELIVERY",
      errors,
    };
  }
  const payloadWithoutHashes = {
    schema: "stickbot.sanitized_payload.v1",
    schemaVersion: "1.0.0",
    payloadType: "milestone_closeout",
    title: input.candidateTitle,
    body: input.candidateBody,
    anchors: {
      closeoutAnchor: input.job.closeoutAnchor,
      terminalPayloadAnchor: input.job.terminalPayloadAnchor,
      ledgerCompletionAnchor: input.job.ledgerCompletionAnchor,
    },
    completionStatus: "PASS",
    sanitized: true,
    rawIdentifiersPresent: false,
    privateScanPass: true,
    deliverySurface: input.job.deliverySurface,
    targetAlias: input.targetAlias,
    idempotencyKey: input.job.idempotencyKey,
    policyEpoch: input.surfacePolicy.policyEpoch,
    createdAt: input.createdAt,
    payloadSha256: "",
    contractHash: "",
  } satisfies SanitizedPayloadEnvelope;
  const payloadSha256 = hash(omit(payloadWithoutHashes, ["payloadSha256", "contractHash"]));
  const payload = completeContract({
    ...payloadWithoutHashes,
    payloadSha256,
  }) as SanitizedPayloadEnvelope;
  return { terminal: "PAYLOAD_READY", payload };
}

export function buildSurfaceResponseTargetRequest(input: {
  payload: SanitizedPayloadEnvelope;
  policy: SurfacePolicy;
  requestId: string;
  approvalContext: string;
}): SurfaceResponseTargetRequest | { terminal: M25MOutcome; errors: string[] } {
  const errors: string[] = [];
  if (!symbolicAlias(input.payload.targetAlias)) errors.push("TARGET_ALIAS_NOT_SYMBOLIC");
  if (!input.policy.allowedTargetAliases.includes(input.payload.targetAlias))
    errors.push("TARGET_ALIAS_NOT_ALLOWED");
  if (input.policy.deliverySurface !== input.payload.deliverySurface)
    errors.push("SURFACE_MISMATCH");
  if (input.policy.allowedCapabilities[0] !== "send_text") errors.push("CAPABILITY_INVALID");
  if (input.policy.maxDeliveries !== 1) errors.push("MAX_DELIVERIES_INVALID");
  if (errors.length) return { terminal: "TARGET_RESOLUTION_HOLD_NO_DELIVERY", errors };
  return completeContract({
    schema: "stickbot.surface_response_target.request.v1",
    schemaVersion: "1.0.0",
    requestId: input.requestId,
    surfaceId: input.policy.surfaceId,
    targetAlias: input.payload.targetAlias,
    identityScope: input.policy.identityScope,
    sessionScopeHash: input.policy.sessionScopeHash,
    deliveryIntent: input.policy.deliveryIntent,
    requiredCapabilities: ["send_text"],
    approvalContext: input.approvalContext,
    idempotencyKey: input.payload.idempotencyKey,
    policyEpoch: input.payload.policyEpoch,
    expiresAt: input.policy.expiresAt,
    contractHash: "",
  }) as SurfaceResponseTargetRequest;
}

export function resolveSyntheticSurfaceTarget(input: {
  request: SurfaceResponseTargetRequest;
  policy: SurfacePolicy;
  now: string;
  identityVerified?: boolean;
  sessionVerified?: boolean;
}): SurfaceResponseTargetGrant | { terminal: M25MOutcome; errors: string[] } {
  const errors: string[] = [];
  if (!symbolicAlias(input.request.targetAlias)) errors.push("TARGET_ALIAS_INVALID");
  if (!input.policy.allowedTargetAliases.includes(input.request.targetAlias))
    errors.push("TARGET_ALIAS_DENIED");
  if (input.request.surfaceId !== input.policy.surfaceId) errors.push("SURFACE_DENIED");
  if (input.request.policyEpoch !== input.policy.policyEpoch) errors.push("POLICY_EPOCH_DENIED");
  if (input.request.requiredCapabilities[0] !== "send_text") errors.push("CAPABILITY_DENIED");
  if (input.request.expiresAt <= input.now) errors.push("REQUEST_EXPIRED");
  if (input.identityVerified === false) errors.push("IDENTITY_DENIED");
  if (input.sessionVerified === false) errors.push("SESSION_DENIED");
  if (errors.length) {
    return {
      terminal: errors.includes("REQUEST_EXPIRED")
        ? "TARGET_GRANT_EXPIRED_NO_DELIVERY"
        : "TARGET_RESOLUTION_DENIED_NO_DELIVERY",
      errors,
    };
  }
  const grantBase = {
    schema: "stickbot.surface_response_target.grant.v1",
    schemaVersion: "1.0.0",
    grantId: `grant-${hash([input.request.requestId, input.request.targetAlias]).slice(0, 16)}`,
    requestId: input.request.requestId,
    surfaceId: input.request.surfaceId,
    targetAlias: input.request.targetAlias,
    targetHandleRef: `${TEST_ONLY_HANDLE_PREFIX}${hash(input.request).slice(0, 24)}`,
    targetScopeAlias: `ksa:${hash([input.request.targetAlias, input.request.policyEpoch]).slice(0, 16)}`,
    identityVerified: true,
    sessionVerified: true,
    deliveryAllowed: true,
    allowedCapabilities: ["send_text"],
    maxDeliveries: 1,
    policyEpoch: input.request.policyEpoch,
    issuedAt: input.now,
    expiresAt: input.request.expiresAt,
    grantSha256: "",
    contractHash: "",
  } satisfies SurfaceResponseTargetGrant;
  const grantSha256 = hash(omit(grantBase, ["grantSha256", "contractHash"]));
  return completeContract({ ...grantBase, grantSha256 }) as SurfaceResponseTargetGrant;
}

export function createSurfaceResponseTargetReceipt(input: {
  request: SurfaceResponseTargetRequest;
  grant: SurfaceResponseTargetGrant;
  durationMs: number;
}): SurfaceResponseTargetReceipt | { terminal: M25MOutcome; errors: string[] } {
  const errors: string[] = [];
  if (input.grant.requestId !== input.request.requestId) errors.push("REQUEST_GRANT_MISMATCH");
  if (!input.grant.identityVerified || !input.grant.sessionVerified)
    errors.push("IDENTITY_SESSION_UNVERIFIED");
  if (!input.grant.targetHandleRef.startsWith(TEST_ONLY_HANDLE_PREFIX))
    errors.push("TARGET_HANDLE_NOT_TEST_ONLY");
  if (hasRawOrPrivate(input.grant.targetHandleRef)) errors.push("TARGET_HANDLE_RAW_OR_PRIVATE");
  if (input.grant.maxDeliveries !== 1) errors.push("MAX_DELIVERIES_INVALID");
  if (errors.length) return { terminal: "TARGET_BINDING_INVALID_NO_DELIVERY", errors };
  const receiptBase = {
    schema: "stickbot.surface_response_target.receipt.v1",
    schemaVersion: "1.0.0",
    receiptId: `receipt-${hash([input.grant.grantId, input.request.requestId]).slice(0, 16)}`,
    requestId: input.request.requestId,
    grantId: input.grant.grantId,
    surfaceId: input.grant.surfaceId,
    targetAlias: input.grant.targetAlias,
    resolutionStatus: "RESOLVED",
    identityVerified: true,
    sessionVerified: true,
    rawTargetExposed: false,
    policyEpoch: input.grant.policyEpoch,
    durationMs: input.durationMs,
    receiptSha256: "",
    contractHash: "",
  } satisfies SurfaceResponseTargetReceipt;
  const receiptSha256 = hash(omit(receiptBase, ["receiptSha256", "contractHash"]));
  return completeContract({ ...receiptBase, receiptSha256 }) as SurfaceResponseTargetReceipt;
}

export function createNoSendDeliveryResult(input: {
  job: DeliveryRequiredJobEnvelope;
  payload: SanitizedPayloadEnvelope;
  grant: SurfaceResponseTargetGrant;
  receipt: SurfaceResponseTargetReceipt;
  sanitizedEvidencePath: string;
  timestamp: string;
}): DeliveryResultEnvelope | { terminal: M25MOutcome; errors: string[] } {
  const errors: string[] = [];
  if (input.receipt.resolutionStatus !== "RESOLVED") errors.push("TARGET_NOT_RESOLVED");
  if (input.payload.idempotencyKey !== input.job.idempotencyKey)
    errors.push("PAYLOAD_JOB_IDEMPOTENCY_MISMATCH");
  if (
    input.grant.policyEpoch !== input.payload.policyEpoch ||
    input.receipt.policyEpoch !== input.payload.policyEpoch
  )
    errors.push("POLICY_EPOCH_MISMATCH");
  if (
    input.grant.targetAlias !== input.payload.targetAlias ||
    input.receipt.targetAlias !== input.payload.targetAlias
  )
    errors.push("TARGET_ALIAS_MISMATCH");
  if (errors.length) return { terminal: "TARGET_BINDING_INVALID_NO_DELIVERY", errors };
  const resultBase = {
    schema: "stickbot.delivery_result.v1",
    schemaVersion: "1.0.0",
    jobId: input.job.jobId,
    deliveryAttempted: false,
    delivered: false,
    deliverySurface: input.payload.deliverySurface,
    targetGrantId: input.grant.grantId,
    targetScopeAlias: input.grant.targetScopeAlias,
    deliveryStatus: "suppressed",
    idempotencyKey: input.job.idempotencyKey,
    policyEpoch: input.payload.policyEpoch,
    duplicateSuppressed: false,
    errorClass: "NO_SEND_ARTIFACT_CANARY",
    sanitizedEvidencePath: input.sanitizedEvidencePath,
    timestamp: input.timestamp,
    resultSha256: "",
    contractHash: "",
  } satisfies DeliveryResultEnvelope;
  const resultSha256 = hash(omit(resultBase, ["resultSha256", "contractHash"]));
  return completeContract({ ...resultBase, resultSha256 }) as DeliveryResultEnvelope;
}

function contractValid(value: Record<string, unknown>): boolean {
  return (
    typeof value.contractHash === "string" &&
    value.contractHash === hash(omit(value, ["contractHash"]))
  );
}

export function validateDeliveryArtifactChain(
  chain: DeliveryArtifactChain,
): ChainValidationReceipt {
  const errors: string[] = [];
  const {
    job,
    boundaryDecision,
    runtimeClassification,
    sanitizedPayload,
    surfacePolicy,
    targetRequest,
    targetGrant,
    targetReceipt,
    deliveryResult,
  } = chain;
  for (const [label, value] of Object.entries({
    job,
    sanitizedPayload,
    surfacePolicy,
    targetRequest,
    targetGrant,
    targetReceipt,
    deliveryResult,
  })) {
    if (!contractValid(value as Record<string, unknown>))
      errors.push(`${label}_CONTRACT_HASH_INVALID`);
  }
  if (boundaryDecision.decision !== "allow" || boundaryDecision.deliveryAllowed !== true)
    errors.push("BOUNDARY_ALLOW_REQUIRED");
  if (
    runtimeClassification.terminal !== "BOUNDARY_ALLOWED_PAYLOAD_READY" &&
    runtimeClassification.terminal !== "DELIVERY_REQUIRED_PAYLOAD_READY"
  )
    errors.push("RUNTIME_PAYLOAD_READY_REQUIRED");
  if (
    job.jobId !== boundaryDecision.jobId ||
    job.jobId !== runtimeClassification.jobId ||
    job.jobId !== deliveryResult.jobId
  )
    errors.push("JOB_ID_MISMATCH");
  if (
    job.idempotencyKey !== sanitizedPayload.idempotencyKey ||
    job.idempotencyKey !== targetRequest.idempotencyKey ||
    job.idempotencyKey !== deliveryResult.idempotencyKey
  )
    errors.push("IDEMPOTENCY_MISMATCH");
  if (
    job.deliverySurface !== sanitizedPayload.deliverySurface ||
    job.deliverySurface !== surfacePolicy.deliverySurface ||
    job.deliverySurface !== deliveryResult.deliverySurface
  )
    errors.push("DELIVERY_SURFACE_MISMATCH");
  if (
    job.targetAlias !== sanitizedPayload.targetAlias ||
    job.targetAlias !== targetRequest.targetAlias ||
    job.targetAlias !== targetGrant.targetAlias ||
    job.targetAlias !== targetReceipt.targetAlias
  )
    errors.push("TARGET_ALIAS_MISMATCH");
  if (
    surfacePolicy.policyEpoch !== sanitizedPayload.policyEpoch ||
    surfacePolicy.policyEpoch !== targetRequest.policyEpoch ||
    surfacePolicy.policyEpoch !== targetGrant.policyEpoch ||
    surfacePolicy.policyEpoch !== targetReceipt.policyEpoch ||
    surfacePolicy.policyEpoch !== deliveryResult.policyEpoch
  )
    errors.push("POLICY_EPOCH_MISMATCH");
  if (
    job.closeoutAnchor !== sanitizedPayload.anchors.closeoutAnchor ||
    job.terminalPayloadAnchor !== sanitizedPayload.anchors.terminalPayloadAnchor ||
    job.ledgerCompletionAnchor !== sanitizedPayload.anchors.ledgerCompletionAnchor
  )
    errors.push("ANCHOR_MISMATCH");
  if (
    surfacePolicy.allowedCapabilities[0] !== targetRequest.requiredCapabilities[0] ||
    surfacePolicy.allowedCapabilities[0] !== targetGrant.allowedCapabilities[0]
  )
    errors.push("CAPABILITY_MISMATCH");
  if (
    job.maxDeliveries !== 1 ||
    surfacePolicy.maxDeliveries !== 1 ||
    targetGrant.maxDeliveries !== 1
  )
    errors.push("MAX_DELIVERIES_INVALID");
  if (
    targetRequest.requestId !== targetGrant.requestId ||
    targetRequest.requestId !== targetReceipt.requestId ||
    targetGrant.grantId !== targetReceipt.grantId ||
    targetGrant.grantId !== deliveryResult.targetGrantId
  )
    errors.push("GRANT_RECEIPT_RESULT_MISMATCH");
  if (
    targetReceipt.rawTargetExposed !== false ||
    !targetGrant.targetHandleRef.startsWith(TEST_ONLY_HANDLE_PREFIX)
  )
    errors.push("RAW_TARGET_EXPOSURE_INVALID");
  if (
    deliveryResult.deliveryAttempted !== false ||
    deliveryResult.delivered !== false ||
    deliveryResult.errorClass !== "NO_SEND_ARTIFACT_CANARY"
  )
    errors.push("NO_SEND_RESULT_INVALID");
  if (
    !validSha(sanitizedPayload.payloadSha256) ||
    !validSha(targetReceipt.receiptSha256) ||
    !validSha(deliveryResult.resultSha256)
  )
    errors.push("ARTIFACT_HASH_INVALID");
  const valid = errors.length === 0;
  const receiptBase = {
    schema: "stickbot.delivery_artifact_chain.validation_receipt.v1",
    schemaVersion: "1.0.0",
    terminal: valid
      ? "PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND"
      : "TARGET_BINDING_INVALID_NO_DELIVERY",
    valid,
    jobId: job.jobId,
    payloadSha256: sanitizedPayload.payloadSha256,
    targetReceiptSha256: targetReceipt.receiptSha256,
    resultSha256: deliveryResult.resultSha256,
    idempotencyKey: job.idempotencyKey,
    policyEpoch: surfacePolicy.policyEpoch,
    errors,
    chainSha256: "",
    contractHash: "",
  } satisfies ChainValidationReceipt;
  const chainSha256 = hash(omit(receiptBase, ["chainSha256", "contractHash"]));
  return completeContract({ ...receiptBase, chainSha256 }) as ChainValidationReceipt;
}
