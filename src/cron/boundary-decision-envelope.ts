import { createHash } from "node:crypto";

const SHA256_RE = /^[a-f0-9]{64}$/;
const LOCAL_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const MAX_DIAGNOSTIC_CHARS = 160;

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

export const BOUNDARY_ALLOW_REASON_CODES = [
  "BOUNDARY_MATCH_ALLOW",
  "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED",
] as const;

export const BOUNDARY_HOLD_REASON_CODES = [
  "BOUNDARY_UNARMED_HOLD",
  "BOUNDARY_EXPIRED_HOLD",
  "BOUNDARY_JOB_MISMATCH_HOLD",
  "BOUNDARY_AGENT_MISMATCH_HOLD",
  "BOUNDARY_SESSION_MISMATCH_HOLD",
  "BOUNDARY_CALLER_HASH_MISMATCH_HOLD",
  "BOUNDARY_SOURCE_HASH_MISMATCH_HOLD",
  "BOUNDARY_EVENTS_HASH_MISMATCH_HOLD",
  "BOUNDARY_ACTIONS_HASH_MISMATCH_HOLD",
  "BOUNDARY_LEDGER_HASH_MISMATCH_HOLD",
  "BOUNDARY_LOCAL_DATE_MISMATCH_HOLD",
  "BOUNDARY_ANCHOR_MISSING_HOLD",
  "BOUNDARY_PAYLOAD_MISSING_HOLD",
  "BOUNDARY_TARGET_GRANT_MISSING_HOLD",
] as const;

export const BOUNDARY_REJECT_REASON_CODES = [
  "BOUNDARY_SCHEMA_INVALID_REJECT",
  "BOUNDARY_CONTRACT_HASH_INVALID_REJECT",
  "BOUNDARY_PRIVACY_SCAN_FAILED_REJECT",
  "BOUNDARY_RAW_IDENTIFIER_PRESENT_REJECT",
  "BOUNDARY_DUPLICATE_REPLAY_REJECT",
  "BOUNDARY_UNAUTHORIZED_SURFACE_REJECT",
  "BOUNDARY_POLICY_EPOCH_MISMATCH_REJECT",
] as const;

export const BOUNDARY_DECISION_REASON_CODES = [
  ...BOUNDARY_ALLOW_REASON_CODES,
  ...BOUNDARY_HOLD_REASON_CODES,
  ...BOUNDARY_REJECT_REASON_CODES,
] as const;

export type BoundaryDecisionReasonCode = (typeof BOUNDARY_DECISION_REASON_CODES)[number];

export type BoundaryDecisionValue = "allow" | "hold" | "reject";

export type BoundaryDecisionEnvelope = {
  schema: "stickbot.boundary_decision.v1";
  schemaVersion: "1.0.0";
  decision: BoundaryDecisionValue;
  reasonCode: BoundaryDecisionReasonCode;
  jobId: string;
  agentId: string;
  sessionKey: string;
  callerPromptSha256: string;
  candidateSourceSha256: string;
  eventsSha256: string;
  actionsSha256: string;
  ledgerSha256: string;
  localDate: string;
  decisionSha256: string;
  sanitizedDiagnostic: string;
  deliveryAllowed: boolean;
  contractHash: string;
};

export type BoundaryDecisionEnvelopeDraft = Omit<
  BoundaryDecisionEnvelope,
  "decisionSha256" | "contractHash"
>;

export type BoundaryDecisionValidationContext = {
  jobId: string;
  agentId: string;
  sessionKey: string;
  callerPromptSha256: string;
  candidateSourceSha256: string;
  eventsSha256: string;
  actionsSha256: string;
  ledgerSha256: string;
  localDate: string;
  seenDecisionSha256?: ReadonlySet<string>;
};

export type BoundaryDecisionValidationTerminal =
  | "BOUNDARY_DECISION_VALID"
  | "BOUNDARY_DECISION_MISSING"
  | "BOUNDARY_DECISION_INVALID";

export type BoundaryDecisionValidation = {
  terminal: BoundaryDecisionValidationTerminal;
  valid: boolean;
  envelope?: BoundaryDecisionEnvelope;
  decision?: BoundaryDecisionValue;
  reasonCode?: BoundaryDecisionReasonCode;
  deliveryAllowed: boolean;
  sanitizedDiagnostic?: string;
  errors: string[];
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

function sha256Stable(value: unknown): string {
  return createHash("sha256").update(stableJson(value)).digest("hex");
}

function omitKeys<T extends Record<string, unknown>>(
  value: T,
  keys: string[],
): Record<string, unknown> {
  return Object.fromEntries(Object.entries(value).filter(([key]) => !keys.includes(key)));
}

export function computeBoundaryDecisionSha256(
  envelope: BoundaryDecisionEnvelopeDraft | BoundaryDecisionEnvelope,
): string {
  return sha256Stable(omitKeys(envelope, ["decisionSha256", "contractHash"]));
}

export function computeBoundaryContractHash(envelope: BoundaryDecisionEnvelope): string {
  return sha256Stable(omitKeys(envelope, ["contractHash"]));
}

export function completeBoundaryDecisionEnvelope(
  draft: BoundaryDecisionEnvelopeDraft,
): BoundaryDecisionEnvelope {
  const decisionSha256 = computeBoundaryDecisionSha256(draft);
  const withDecisionSha = {
    ...draft,
    decisionSha256,
    contractHash: "",
  } satisfies BoundaryDecisionEnvelope;
  return { ...withDecisionSha, contractHash: computeBoundaryContractHash(withDecisionSha) };
}

function hasRawOrPrivateText(value: string): boolean {
  return RAW_OR_PRIVATE_PATTERNS.some((pattern) => pattern.test(value));
}

function hasOnlyKnownKeys(value: Record<string, unknown>): boolean {
  const required = new Set([
    "schema",
    "schemaVersion",
    "decision",
    "reasonCode",
    "jobId",
    "agentId",
    "sessionKey",
    "callerPromptSha256",
    "candidateSourceSha256",
    "eventsSha256",
    "actionsSha256",
    "ledgerSha256",
    "localDate",
    "decisionSha256",
    "sanitizedDiagnostic",
    "deliveryAllowed",
    "contractHash",
  ]);
  return (
    Object.keys(value).every((key) => required.has(key)) &&
    [...required].every((key) => key in value)
  );
}

function isBoundaryDecisionReasonCode(value: unknown): value is BoundaryDecisionReasonCode {
  return (
    typeof value === "string" &&
    BOUNDARY_DECISION_REASON_CODES.includes(value as BoundaryDecisionReasonCode)
  );
}

function reasonMatchesDecision(decision: unknown, reasonCode: unknown): boolean {
  if (decision === "allow") {
    return BOUNDARY_ALLOW_REASON_CODES.includes(
      reasonCode as (typeof BOUNDARY_ALLOW_REASON_CODES)[number],
    );
  }
  if (decision === "hold") {
    return BOUNDARY_HOLD_REASON_CODES.includes(
      reasonCode as (typeof BOUNDARY_HOLD_REASON_CODES)[number],
    );
  }
  if (decision === "reject") {
    return BOUNDARY_REJECT_REASON_CODES.includes(
      reasonCode as (typeof BOUNDARY_REJECT_REASON_CODES)[number],
    );
  }
  return false;
}

function bindingErrors(
  envelope: BoundaryDecisionEnvelope,
  context: BoundaryDecisionValidationContext,
): string[] {
  const errors: string[] = [];
  for (const key of [
    "jobId",
    "agentId",
    "sessionKey",
    "callerPromptSha256",
    "candidateSourceSha256",
    "eventsSha256",
    "actionsSha256",
    "ledgerSha256",
    "localDate",
  ] as const) {
    if (envelope[key] !== context[key]) errors.push(`BINDING_${key}_MISMATCH`);
  }
  return errors;
}

export function validateBoundaryDecisionEnvelope(
  value: unknown,
  context: BoundaryDecisionValidationContext,
): BoundaryDecisionValidation {
  if (value === undefined || value === null) {
    return {
      terminal: "BOUNDARY_DECISION_MISSING",
      valid: false,
      deliveryAllowed: false,
      errors: ["MISSING"],
    };
  }
  const errors: string[] = [];
  if (typeof value !== "object" || Array.isArray(value)) {
    return {
      terminal: "BOUNDARY_DECISION_INVALID",
      valid: false,
      deliveryAllowed: false,
      errors: ["NOT_OBJECT"],
    };
  }
  const record = value as Record<string, unknown>;
  if (!hasOnlyKnownKeys(record)) errors.push("SCHEMA_REQUIRED_OR_EXTRA_FIELD_INVALID");
  if (record.schema !== "stickbot.boundary_decision.v1") errors.push("SCHEMA_INVALID");
  if (record.schemaVersion !== "1.0.0") errors.push("SCHEMA_VERSION_INVALID");
  if (!["allow", "hold", "reject"].includes(String(record.decision)))
    errors.push("DECISION_INVALID");
  if (!isBoundaryDecisionReasonCode(record.reasonCode)) errors.push("REASON_CODE_INVALID");
  if (!reasonMatchesDecision(record.decision, record.reasonCode))
    errors.push("REASON_CODE_DECISION_MISMATCH");
  if (record.decision === "allow" && record.deliveryAllowed !== true)
    errors.push("ALLOW_DELIVERY_NOT_ALLOWED");
  if (
    (record.decision === "hold" || record.decision === "reject") &&
    record.deliveryAllowed !== false
  ) {
    errors.push("NO_DELIVERY_DECISION_DELIVERY_ALLOWED");
  }
  for (const key of [
    "callerPromptSha256",
    "candidateSourceSha256",
    "eventsSha256",
    "actionsSha256",
    "ledgerSha256",
    "decisionSha256",
    "contractHash",
  ]) {
    if (typeof record[key] !== "string" || !SHA256_RE.test(record[key] as string))
      errors.push(`${key}_INVALID_SHA256`);
  }
  if (typeof record.localDate !== "string" || !LOCAL_DATE_RE.test(record.localDate))
    errors.push("LOCAL_DATE_INVALID");
  for (const key of ["jobId", "agentId", "sessionKey"] as const) {
    if (typeof record[key] !== "string" || !record[key]) errors.push(`${key}_INVALID`);
    if (typeof record[key] === "string" && hasRawOrPrivateText(record[key]))
      errors.push(`${key}_RAW_OR_PRIVATE`);
  }
  if (typeof record.sanitizedDiagnostic !== "string" || !record.sanitizedDiagnostic) {
    errors.push("SANITIZED_DIAGNOSTIC_INVALID");
  } else {
    if (record.sanitizedDiagnostic.length > MAX_DIAGNOSTIC_CHARS)
      errors.push("SANITIZED_DIAGNOSTIC_OVERSIZED");
    if (hasRawOrPrivateText(record.sanitizedDiagnostic))
      errors.push("SANITIZED_DIAGNOSTIC_RAW_OR_PRIVATE");
  }

  const envelope = record as BoundaryDecisionEnvelope;
  if (errors.length === 0) {
    if (envelope.decisionSha256 !== computeBoundaryDecisionSha256(envelope))
      errors.push("DECISION_HASH_MISMATCH");
    if (envelope.contractHash !== computeBoundaryContractHash(envelope))
      errors.push("CONTRACT_HASH_MISMATCH");
    errors.push(...bindingErrors(envelope, context));
    if (context.seenDecisionSha256?.has(envelope.decisionSha256)) errors.push("DUPLICATE_REPLAY");
  }
  if (errors.length > 0) {
    return { terminal: "BOUNDARY_DECISION_INVALID", valid: false, deliveryAllowed: false, errors };
  }
  return {
    terminal: "BOUNDARY_DECISION_VALID",
    valid: true,
    envelope,
    decision: envelope.decision,
    reasonCode: envelope.reasonCode,
    deliveryAllowed: envelope.deliveryAllowed,
    sanitizedDiagnostic: envelope.sanitizedDiagnostic,
    errors: [],
  };
}

export function boundaryDecisionEnvelopeToRuntimePatch(
  value: unknown,
  context: BoundaryDecisionValidationContext,
) {
  const validation = validateBoundaryDecisionEnvelope(value, context);
  if (validation.terminal === "BOUNDARY_DECISION_MISSING") {
    return { boundaryDecisionPresent: false };
  }
  if (!validation.valid || !validation.decision || !validation.reasonCode) {
    return { boundaryDecisionPresent: true, contractValid: false, contractHashMatches: false };
  }
  return {
    boundaryDecisionPresent: true,
    boundaryDecision: validation.decision,
    boundaryReasonCode: validation.reasonCode,
    contractValid: true,
    contractHashMatches: true,
  };
}

export type BoundaryDecisionEvidence = {
  envelopeSchema: "stickbot.boundary_decision.v1";
  schemaVersion: "1.0.0";
  decision: BoundaryDecisionValue;
  reasonCode: BoundaryDecisionReasonCode;
  jobAlias: string;
  bindingMatches: Record<string, boolean>;
  decisionSha256: string;
  contractHash: string;
  sanitizedDiagnostic: string;
  deliveryAllowed: boolean;
  validationTerminal: BoundaryDecisionValidationTerminal;
  timestamp: string;
  privateRawScan: "PASS" | "FAIL";
};

export function createBoundaryDecisionEvidence(
  envelope: BoundaryDecisionEnvelope,
  context: BoundaryDecisionValidationContext,
  timestamp: string,
): BoundaryDecisionEvidence {
  const validation = validateBoundaryDecisionEnvelope(envelope, context);
  const bindingMatches = Object.fromEntries(
    (
      [
        "jobId",
        "agentId",
        "sessionKey",
        "callerPromptSha256",
        "candidateSourceSha256",
        "eventsSha256",
        "actionsSha256",
        "ledgerSha256",
        "localDate",
      ] as const
    ).map((key) => [key, envelope[key] === context[key]]),
  );
  return {
    envelopeSchema: envelope.schema,
    schemaVersion: envelope.schemaVersion,
    decision: envelope.decision,
    reasonCode: envelope.reasonCode,
    jobAlias: envelope.jobId,
    bindingMatches,
    decisionSha256: envelope.decisionSha256,
    contractHash: envelope.contractHash,
    sanitizedDiagnostic: envelope.sanitizedDiagnostic,
    deliveryAllowed: envelope.deliveryAllowed,
    validationTerminal: validation.terminal,
    timestamp,
    privateRawScan: validation.valid ? "PASS" : "FAIL",
  };
}
