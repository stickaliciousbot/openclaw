import { createHash } from "node:crypto";
import type {
  SanitizedPayloadEnvelope,
  SurfacePolicy,
  SurfaceResponseTargetGrant,
  SurfaceResponseTargetReceipt,
} from "./sanitized-payload-target-artifact.js";

const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/;
const TELEGRAM_CANARY_PREFIX = "[CANARY TEST — sanitized Context Bridge summary]";

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

export type M25NTelegramDeliveryTerminal =
  | "DELIVERED"
  | "DUPLICATE_DELIVERY_SUPPRESSED"
  | "TARGET_BINDING_INVALID_NO_DELIVERY"
  | "PAYLOAD_SANITIZATION_FAILED_NO_DELIVERY"
  | "TARGET_GRANT_EXPIRED_NO_DELIVERY"
  | "PROVIDER_DELIVERY_AMBIGUOUS_NO_RETRY"
  | "PROVIDER_DELIVERY_FAILED_NO_RETRY";

export type M25NPrivateTargetBinding = {
  targetAlias: string;
  targetHandle: string;
  targetHandleRef: string;
  registryAliasHash: string;
  expiresAt: string;
  active: boolean;
};

export type M25NProviderSendInput = {
  targetHandle: string;
  text: string;
  retry: { attempts: 1; minDelayMs: 0; maxDelayMs: 0; jitter: 0 };
};

export type M25NProviderSendResult = {
  delivered: boolean;
  providerAckRef: string;
};

export type M25NDeliveryResultEnvelope = {
  schema: "stickbot.delivery_result.v1";
  schemaVersion: "1.0.0";
  terminal: M25NTelegramDeliveryTerminal;
  jobId: string;
  deliveryAttempted: boolean;
  delivered: boolean;
  deliverySurface: "telegram";
  targetAlias: string;
  targetGrantId: string;
  targetScopeAlias: string;
  deliveryStatus: "delivered" | "duplicate-suppressed" | "not-delivered";
  idempotencyKey: string;
  idempotencyKeyAliasHash: string;
  policyEpoch: string;
  duplicateSuppressed: boolean;
  providerInvocationCount: number;
  telegramDeliveredMessageCount: number;
  providerAckRef?: string;
  rawTargetExposed: false;
  privateScanPass: boolean;
  pendingDeliveryCount: 0;
  timestamp: string;
  errors: string[];
  resultSha256: string;
  contractHash: string;
};

export type M25NIdempotencyStore = {
  isConsumed(key: string): boolean;
  consume(key: string, value: { providerAckRef: string; consumedAt: string }): void;
};

export class M25NMemoryIdempotencyStore implements M25NIdempotencyStore {
  private readonly consumed = new Map<string, { providerAckRef: string; consumedAt: string }>();

  isConsumed(key: string): boolean {
    return this.consumed.has(key);
  }

  consume(key: string, value: { providerAckRef: string; consumedAt: string }): void {
    if (this.consumed.has(key)) {
      throw new Error("M25N idempotency key already consumed");
    }
    this.consumed.set(key, value);
  }
}

export type M25NTelegramDeliveryAdapterInput = {
  jobId: string;
  payload: SanitizedPayloadEnvelope;
  policy: SurfacePolicy;
  grant: SurfaceResponseTargetGrant;
  receipt: SurfaceResponseTargetReceipt;
  privateTarget: M25NPrivateTargetBinding;
  now: string;
  deliveryDeadline: string;
  idempotencyStore: M25NIdempotencyStore;
  providerSend: (input: M25NProviderSendInput) => Promise<M25NProviderSendResult>;
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

function hasRawOrPrivate(value: string): boolean {
  return RAW_OR_PRIVATE_PATTERNS.some((pattern) => pattern.test(value));
}

function validIso(value: string): boolean {
  return ISO_RE.test(value);
}

export function hashM25NPrivateAlias(value: string): string {
  return hash(["m25n-private-alias", value]);
}

export function renderM25NTelegramCanaryText(payload: SanitizedPayloadEnvelope): string {
  return `${payload.title}\n\n${payload.body}`;
}

function completeResult(
  draft: Omit<M25NDeliveryResultEnvelope, "resultSha256" | "contractHash">,
): M25NDeliveryResultEnvelope {
  const withResult = {
    ...draft,
    resultSha256: "",
    contractHash: "",
  } satisfies M25NDeliveryResultEnvelope;
  const resultSha256 = hash(omit(withResult, ["resultSha256", "contractHash"]));
  const withContract = { ...withResult, resultSha256 };
  const contractHash = hash(omit(withContract, ["contractHash"]));
  return { ...withContract, contractHash };
}

function resultFor(params: {
  input: M25NTelegramDeliveryAdapterInput;
  terminal: M25NTelegramDeliveryTerminal;
  attempted: boolean;
  delivered: boolean;
  duplicate: boolean;
  providerInvocationCount: number;
  telegramDeliveredMessageCount: number;
  providerAckRef?: string;
  errors: string[];
}): M25NDeliveryResultEnvelope {
  return completeResult({
    schema: "stickbot.delivery_result.v1",
    schemaVersion: "1.0.0",
    terminal: params.terminal,
    jobId: params.input.jobId,
    deliveryAttempted: params.attempted,
    delivered: params.delivered,
    deliverySurface: "telegram",
    targetAlias: params.input.payload.targetAlias,
    targetGrantId: params.input.grant.grantId,
    targetScopeAlias: params.input.grant.targetScopeAlias,
    deliveryStatus: params.delivered
      ? "delivered"
      : params.duplicate
        ? "duplicate-suppressed"
        : "not-delivered",
    idempotencyKey: params.input.payload.idempotencyKey,
    idempotencyKeyAliasHash: hashM25NPrivateAlias(params.input.payload.idempotencyKey),
    policyEpoch: params.input.payload.policyEpoch,
    duplicateSuppressed: params.duplicate,
    providerInvocationCount: params.providerInvocationCount,
    telegramDeliveredMessageCount: params.telegramDeliveredMessageCount,
    ...(params.providerAckRef ? { providerAckRef: params.providerAckRef } : {}),
    rawTargetExposed: false,
    privateScanPass: params.errors.every((error) => error !== "RAW_OR_PRIVATE_CONTENT_DETECTED"),
    pendingDeliveryCount: 0,
    timestamp: params.input.now,
    errors: params.errors,
  });
}

function validatePreSend(input: M25NTelegramDeliveryAdapterInput): string[] {
  const errors: string[] = [];
  const text = renderM25NTelegramCanaryText(input.payload);
  if (input.payload.deliverySurface !== "telegram") errors.push("PAYLOAD_SURFACE_NOT_TELEGRAM");
  if (input.policy.deliverySurface !== "telegram") errors.push("POLICY_SURFACE_NOT_TELEGRAM");
  if (input.payload.sanitized !== true) errors.push("PAYLOAD_NOT_SANITIZED");
  if (input.payload.rawIdentifiersPresent !== false) errors.push("PAYLOAD_RAW_IDENTIFIER_FLAGGED");
  if (input.payload.privateScanPass !== true) errors.push("PAYLOAD_PRIVATE_SCAN_NOT_PASS");
  if (!text.startsWith(TELEGRAM_CANARY_PREFIX)) errors.push("CANARY_PREFIX_MISSING");
  if (
    hasRawOrPrivate(input.payload.title) ||
    hasRawOrPrivate(input.payload.body) ||
    hasRawOrPrivate(text)
  ) {
    errors.push("RAW_OR_PRIVATE_CONTENT_DETECTED");
  }
  if (input.payload.targetAlias !== "operator-canary-target")
    errors.push("TARGET_ALIAS_NOT_APPROVED");
  if (!input.policy.allowedTargetAliases.includes(input.payload.targetAlias))
    errors.push("TARGET_ALIAS_NOT_ALLOWED_BY_POLICY");
  if (
    input.grant.targetAlias !== input.payload.targetAlias ||
    input.receipt.targetAlias !== input.payload.targetAlias
  )
    errors.push("TARGET_ALIAS_MISMATCH");
  if (input.privateTarget.targetAlias !== input.payload.targetAlias)
    errors.push("PRIVATE_TARGET_ALIAS_MISMATCH");
  if (input.privateTarget.targetHandleRef !== input.grant.targetHandleRef)
    errors.push("PRIVATE_TARGET_REF_MISMATCH");
  if (!input.privateTarget.active) errors.push("PRIVATE_TARGET_INACTIVE");
  if (input.grant.deliveryAllowed !== true) errors.push("GRANT_DELIVERY_NOT_ALLOWED");
  if (input.grant.identityVerified !== true || input.grant.sessionVerified !== true)
    errors.push("IDENTITY_SESSION_NOT_VERIFIED");
  if (input.receipt.identityVerified !== true || input.receipt.sessionVerified !== true)
    errors.push("RECEIPT_IDENTITY_SESSION_NOT_VERIFIED");
  if (input.receipt.rawTargetExposed !== false) errors.push("RAW_TARGET_EXPOSED");
  if (
    input.grant.allowedCapabilities[0] !== "send_text" ||
    input.policy.allowedCapabilities[0] !== "send_text"
  )
    errors.push("CAPABILITY_NOT_SEND_TEXT");
  if (input.grant.maxDeliveries !== 1 || input.policy.maxDeliveries !== 1)
    errors.push("MAX_DELIVERIES_NOT_ONE");
  if (input.payload.idempotencyKey !== input.grant.policyEpoch && false) errors.push("UNREACHABLE");
  if (
    input.policy.policyEpoch !== input.payload.policyEpoch ||
    input.grant.policyEpoch !== input.payload.policyEpoch ||
    input.receipt.policyEpoch !== input.payload.policyEpoch
  )
    errors.push("POLICY_EPOCH_MISMATCH");
  if (input.receipt.grantId !== input.grant.grantId) errors.push("RECEIPT_GRANT_MISMATCH");
  if (!validIso(input.now) || !validIso(input.deliveryDeadline) || !validIso(input.grant.expiresAt))
    errors.push("TIMESTAMP_INVALID");
  if (input.now >= input.deliveryDeadline) errors.push("DELIVERY_DEADLINE_EXPIRED");
  if (input.now >= input.grant.expiresAt || input.now >= input.privateTarget.expiresAt)
    errors.push("TARGET_GRANT_EXPIRED");
  if (input.idempotencyStore.isConsumed(input.payload.idempotencyKey))
    errors.push("IDEMPOTENCY_CONSUMED");
  if (!input.privateTarget.targetHandle.trim()) errors.push("PRIVATE_TARGET_HANDLE_EMPTY");
  return errors;
}

export async function deliverM25NTelegramCanary(
  input: M25NTelegramDeliveryAdapterInput,
): Promise<M25NDeliveryResultEnvelope> {
  if (input.idempotencyStore.isConsumed(input.payload.idempotencyKey)) {
    return resultFor({
      input,
      terminal: "DUPLICATE_DELIVERY_SUPPRESSED",
      attempted: false,
      delivered: false,
      duplicate: true,
      providerInvocationCount: 0,
      telegramDeliveredMessageCount: 0,
      errors: [],
    });
  }

  const errors = validatePreSend(input);
  if (errors.length > 0) {
    const terminal = errors.includes("RAW_OR_PRIVATE_CONTENT_DETECTED")
      ? "PAYLOAD_SANITIZATION_FAILED_NO_DELIVERY"
      : errors.includes("TARGET_GRANT_EXPIRED")
        ? "TARGET_GRANT_EXPIRED_NO_DELIVERY"
        : "TARGET_BINDING_INVALID_NO_DELIVERY";
    return resultFor({
      input,
      terminal,
      attempted: false,
      delivered: false,
      duplicate: false,
      providerInvocationCount: 0,
      telegramDeliveredMessageCount: 0,
      errors,
    });
  }

  let providerInvocationCount = 0;
  try {
    providerInvocationCount += 1;
    const providerResult = await input.providerSend({
      targetHandle: input.privateTarget.targetHandle,
      text: renderM25NTelegramCanaryText(input.payload),
      retry: { attempts: 1, minDelayMs: 0, maxDelayMs: 0, jitter: 0 },
    });
    if (!providerResult.delivered || !providerResult.providerAckRef) {
      return resultFor({
        input,
        terminal: "PROVIDER_DELIVERY_AMBIGUOUS_NO_RETRY",
        attempted: true,
        delivered: false,
        duplicate: false,
        providerInvocationCount,
        telegramDeliveredMessageCount: 0,
        errors: ["PROVIDER_ACK_AMBIGUOUS"],
      });
    }
    input.idempotencyStore.consume(input.payload.idempotencyKey, {
      providerAckRef: providerResult.providerAckRef,
      consumedAt: input.now,
    });
    return resultFor({
      input,
      terminal: "DELIVERED",
      attempted: true,
      delivered: true,
      duplicate: false,
      providerInvocationCount,
      telegramDeliveredMessageCount: 1,
      providerAckRef: providerResult.providerAckRef,
      errors: [],
    });
  } catch {
    return resultFor({
      input,
      terminal: "PROVIDER_DELIVERY_FAILED_NO_RETRY",
      attempted: true,
      delivered: false,
      duplicate: false,
      providerInvocationCount,
      telegramDeliveredMessageCount: 0,
      errors: ["PROVIDER_SEND_FAILED_NO_RETRY"],
    });
  }
}

export function validateM25NDeliveryResultEnvelope(result: M25NDeliveryResultEnvelope): string[] {
  const errors: string[] = [];
  const resultHash = hash(
    omit(result as unknown as Record<string, unknown>, ["resultSha256", "contractHash"]),
  );
  const contractHash = hash(
    omit({ ...result, resultSha256: resultHash } as unknown as Record<string, unknown>, [
      "contractHash",
    ]),
  );
  if (result.resultSha256 !== resultHash) errors.push("RESULT_HASH_INVALID");
  if (result.contractHash !== contractHash) errors.push("CONTRACT_HASH_INVALID");
  if (result.rawTargetExposed !== false) errors.push("RAW_TARGET_EXPOSED");
  if (result.pendingDeliveryCount !== 0) errors.push("PENDING_DELIVERY_NONZERO");
  if (result.terminal === "DELIVERED") {
    if (!result.deliveryAttempted || !result.delivered) errors.push("DELIVERED_FLAGS_INVALID");
    if (result.providerInvocationCount !== 1 || result.telegramDeliveredMessageCount !== 1)
      errors.push("DELIVERED_COUNTS_INVALID");
    if (result.duplicateSuppressed !== false) errors.push("DELIVERED_DUPLICATE_FLAG_INVALID");
  }
  if (result.terminal === "DUPLICATE_DELIVERY_SUPPRESSED") {
    if (result.deliveryAttempted || result.delivered) errors.push("DUPLICATE_FLAGS_INVALID");
    if (result.providerInvocationCount !== 0 || result.telegramDeliveredMessageCount !== 0)
      errors.push("DUPLICATE_COUNTS_INVALID");
    if (result.duplicateSuppressed !== true) errors.push("DUPLICATE_FLAG_INVALID");
  }
  return errors;
}
