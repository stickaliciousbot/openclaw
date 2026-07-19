/** Typed cron reply/delivery classification before legacy NO_REPLY compatibility. */
import { createHash } from "node:crypto";

export type RuntimeReplyJobClass = "quiet_success" | "delivery_required" | "unknown";

export type RuntimeBoundaryDecision = "allow" | "hold" | "reject";

export type RuntimeReplyTerminal =
  | "QUIET_SUCCESS_NO_DELIVERY_REQUIRED"
  | "DELIVERY_REQUIRED_PAYLOAD_READY"
  | "BOUNDARY_ALLOWED_PAYLOAD_READY"
  | "BOUNDARY_HOLD_NO_DELIVERY"
  | "BOUNDARY_REJECT_NO_DELIVERY"
  | "DELIVERY_REQUIRED_PAYLOAD_MISSING"
  | "ANCHOR_MISSING_NO_DELIVERY"
  | "BOUNDARY_DECISION_MISSING"
  | "DELIVERY_CONTRACT_INVALID"
  | "DUPLICATE_DELIVERY_SUPPRESSED"
  | "DELIVERY_FAILED";

export type RuntimeReplyReasonCode =
  | "QUIET_SUCCESS_EXPLICIT_NO_DELIVERY_REQUIRED"
  | "DELIVERY_REQUIRED_PAYLOAD_READY"
  | "BOUNDARY_ALLOWED_PAYLOAD_READY"
  | "BOUNDARY_HOLD"
  | "BOUNDARY_REJECT"
  | "DELIVERY_REQUIRED_PAYLOAD_MISSING"
  | "CLOSEOUT_ANCHOR_MISSING"
  | "TERMINAL_PAYLOAD_ANCHOR_MISSING"
  | "LEDGER_COMPLETION_ANCHOR_MISSING"
  | "BOUNDARY_DECISION_REQUIRED_MISSING"
  | "UNKNOWN_JOB_CLASS_FAIL_CLOSED"
  | "QUIET_JOB_MARKED_DELIVERY_REQUIRED"
  | "MALFORMED_DELIVERY_CONTRACT"
  | "CONTRACT_HASH_MISMATCH"
  | "DELIVERY_JOB_EXPIRED"
  | "IDEMPOTENCY_KEY_MISSING"
  | "IDEMPOTENCY_KEY_MISMATCH"
  | "SURFACE_CONTRACT_MISMATCH"
  | "TARGET_GRANT_REQUIRED_MISSING"
  | "DUPLICATE_DELIVERY_SUPPRESSED"
  | "DELIVERY_FAILED";

export type RuntimeReplyRequiredAnchors = {
  closeoutAnchorPresent?: boolean;
  terminalPayloadAnchorPresent?: boolean;
  ledgerCompletionAnchorRequired?: boolean;
  ledgerCompletionAnchorPresent?: boolean;
};

export type RuntimeReplyClassificationInput = {
  jobId: string;
  deliveryRequired: boolean;
  jobClass: RuntimeReplyJobClass;
  candidatePayloadPresent?: boolean;
  requiredAnchors?: RuntimeReplyRequiredAnchors;
  boundaryHandlerRequired?: boolean;
  boundaryDecisionPresent?: boolean;
  boundaryDecision?: RuntimeBoundaryDecision;
  contractValid?: boolean;
  contractHashMatches?: boolean;
  expired?: boolean;
  idempotencyKey?: string;
  idempotencyKeyMatches?: boolean;
  surfaceMatches?: boolean;
  targetGrantRequired?: boolean;
  targetGrantPresent?: boolean;
  duplicateDeliverySuppressed?: boolean;
  deliveryFailed?: boolean;
};

export type RuntimeReplyClassification = {
  jobId: string;
  deliveryRequired: boolean;
  jobClass: RuntimeReplyJobClass;
  candidatePayloadPresent: boolean;
  requiredAnchorsPresent: boolean;
  boundaryDecisionPresent: boolean;
  boundaryDecision?: RuntimeBoundaryDecision;
  terminal: RuntimeReplyTerminal;
  reasonCode: RuntimeReplyReasonCode;
  deliveryEligible: boolean;
  quietSuccess: boolean;
  idempotencyKey?: string;
  classificationSha256: string;
};

function stableJson(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableJson(entry)).join(",")}]`;
  }
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .sort()
    .filter((key) => record[key] !== undefined)
    .map((key) => `${JSON.stringify(key)}:${stableJson(record[key])}`)
    .join(",")}}`;
}

function sha256Stable(value: unknown): string {
  return createHash("sha256").update(stableJson(value)).digest("hex");
}

function missingAnchorReason(
  anchors: RuntimeReplyRequiredAnchors | undefined,
): RuntimeReplyReasonCode | undefined {
  if (anchors?.closeoutAnchorPresent === false) {
    return "CLOSEOUT_ANCHOR_MISSING";
  }
  if (anchors?.terminalPayloadAnchorPresent === false) {
    return "TERMINAL_PAYLOAD_ANCHOR_MISSING";
  }
  if (
    anchors?.ledgerCompletionAnchorRequired === true &&
    anchors.ledgerCompletionAnchorPresent !== true
  ) {
    return "LEDGER_COMPLETION_ANCHOR_MISSING";
  }
  return undefined;
}

function requiredAnchorsPresent(anchors: RuntimeReplyRequiredAnchors | undefined): boolean {
  return missingAnchorReason(anchors) === undefined;
}

function isInvalidContract(
  input: RuntimeReplyClassificationInput,
): RuntimeReplyReasonCode | undefined {
  if (input.contractValid === false) {
    return "MALFORMED_DELIVERY_CONTRACT";
  }
  if (input.contractHashMatches === false) {
    return "CONTRACT_HASH_MISMATCH";
  }
  if (input.expired === true) {
    return "DELIVERY_JOB_EXPIRED";
  }
  if (input.deliveryRequired && !input.idempotencyKey) {
    return "IDEMPOTENCY_KEY_MISSING";
  }
  if (input.idempotencyKeyMatches === false) {
    return "IDEMPOTENCY_KEY_MISMATCH";
  }
  if (input.surfaceMatches === false) {
    return "SURFACE_CONTRACT_MISMATCH";
  }
  if (input.targetGrantRequired === true && input.targetGrantPresent !== true) {
    return "TARGET_GRANT_REQUIRED_MISSING";
  }
  return undefined;
}

function terminalForReason(reasonCode: RuntimeReplyReasonCode): RuntimeReplyTerminal {
  switch (reasonCode) {
    case "QUIET_SUCCESS_EXPLICIT_NO_DELIVERY_REQUIRED":
      return "QUIET_SUCCESS_NO_DELIVERY_REQUIRED";
    case "DELIVERY_REQUIRED_PAYLOAD_READY":
      return "DELIVERY_REQUIRED_PAYLOAD_READY";
    case "BOUNDARY_ALLOWED_PAYLOAD_READY":
      return "BOUNDARY_ALLOWED_PAYLOAD_READY";
    case "BOUNDARY_HOLD":
      return "BOUNDARY_HOLD_NO_DELIVERY";
    case "BOUNDARY_REJECT":
      return "BOUNDARY_REJECT_NO_DELIVERY";
    case "DELIVERY_REQUIRED_PAYLOAD_MISSING":
      return "DELIVERY_REQUIRED_PAYLOAD_MISSING";
    case "CLOSEOUT_ANCHOR_MISSING":
    case "TERMINAL_PAYLOAD_ANCHOR_MISSING":
    case "LEDGER_COMPLETION_ANCHOR_MISSING":
      return "ANCHOR_MISSING_NO_DELIVERY";
    case "BOUNDARY_DECISION_REQUIRED_MISSING":
      return "BOUNDARY_DECISION_MISSING";
    case "DUPLICATE_DELIVERY_SUPPRESSED":
      return "DUPLICATE_DELIVERY_SUPPRESSED";
    case "DELIVERY_FAILED":
      return "DELIVERY_FAILED";
    default:
      return "DELIVERY_CONTRACT_INVALID";
  }
}

function classifyReason(input: RuntimeReplyClassificationInput): RuntimeReplyReasonCode {
  if (input.jobClass === "unknown") {
    return "UNKNOWN_JOB_CLASS_FAIL_CLOSED";
  }
  if (input.jobClass === "quiet_success" && input.deliveryRequired) {
    return "QUIET_JOB_MARKED_DELIVERY_REQUIRED";
  }
  const invalidContract = isInvalidContract(input);
  if (invalidContract) {
    return invalidContract;
  }
  if (!input.deliveryRequired && input.jobClass === "quiet_success") {
    return "QUIET_SUCCESS_EXPLICIT_NO_DELIVERY_REQUIRED";
  }
  const anchorReason = missingAnchorReason(input.requiredAnchors);
  if (anchorReason) {
    return anchorReason;
  }
  if (input.boundaryHandlerRequired === true && input.boundaryDecisionPresent !== true) {
    return "BOUNDARY_DECISION_REQUIRED_MISSING";
  }
  if (input.boundaryDecisionPresent === true && input.boundaryDecision === "hold") {
    return "BOUNDARY_HOLD";
  }
  if (input.boundaryDecisionPresent === true && input.boundaryDecision === "reject") {
    return "BOUNDARY_REJECT";
  }
  if (input.deliveryRequired && input.candidatePayloadPresent !== true) {
    return "DELIVERY_REQUIRED_PAYLOAD_MISSING";
  }
  if (input.duplicateDeliverySuppressed === true) {
    return "DUPLICATE_DELIVERY_SUPPRESSED";
  }
  if (input.deliveryFailed === true) {
    return "DELIVERY_FAILED";
  }
  if (input.boundaryDecisionPresent === true && input.boundaryDecision === "allow") {
    return "BOUNDARY_ALLOWED_PAYLOAD_READY";
  }
  return "DELIVERY_REQUIRED_PAYLOAD_READY";
}

export function classifyRuntimeReply(
  input: RuntimeReplyClassificationInput,
): RuntimeReplyClassification {
  const candidatePayloadPresent = input.candidatePayloadPresent === true;
  const boundaryDecisionPresent = input.boundaryDecisionPresent === true;
  const reasonCode = classifyReason(input);
  const terminal = terminalForReason(reasonCode);
  const quietSuccess = terminal === "QUIET_SUCCESS_NO_DELIVERY_REQUIRED";
  const deliveryEligible =
    terminal === "DELIVERY_REQUIRED_PAYLOAD_READY" || terminal === "BOUNDARY_ALLOWED_PAYLOAD_READY";
  const classificationWithoutSha = {
    jobId: input.jobId,
    deliveryRequired: input.deliveryRequired,
    jobClass: input.jobClass,
    candidatePayloadPresent,
    requiredAnchorsPresent: requiredAnchorsPresent(input.requiredAnchors),
    boundaryDecisionPresent,
    boundaryDecision: input.boundaryDecisionPresent ? input.boundaryDecision : undefined,
    terminal,
    reasonCode,
    deliveryEligible,
    quietSuccess,
    idempotencyKey: input.idempotencyKey,
  } satisfies Omit<RuntimeReplyClassification, "classificationSha256">;
  return {
    ...classificationWithoutSha,
    classificationSha256: sha256Stable(classificationWithoutSha),
  };
}

export function runtimeReplyClassificationToLegacyText(
  classification: RuntimeReplyClassification,
): string | undefined {
  if (classification.quietSuccess && classification.deliveryRequired === false) {
    return "NO_REPLY";
  }
  if (classification.deliveryEligible) {
    return undefined;
  }
  return `CRON_DELIVERY_CLASSIFICATION_${classification.terminal}: ${classification.reasonCode}`;
}
