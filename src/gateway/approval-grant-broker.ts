import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { requireNodeSqlite } from "../infra/node-sqlite.js";

export const APPROVAL_GRANT_SCHEMA_VERSION = 1 as const;
export const APPROVAL_GRANT_SIGNING_PAYLOAD_SCHEMA_VERSION = 1 as const;
export const APPROVAL_GRANT_DB_USER_VERSION = 1 as const;

const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");
const TERMINAL_GRANT_STATES = new Set(["CONSUMED", "EXPIRED", "REVOKED", "CRASH_RECOVERED"]);

export type ApprovalGrantDecision = "allow-once" | "deny";
export type ApprovalGrantState = "PENDING" | "CONSUMED" | "EXPIRED" | "REVOKED" | "CRASH_RECOVERED";
export type ApprovalGrantTerminalCode =
  | "OK_CONSUMED"
  | "CONFIG_DISABLED"
  | "SCHEMA_INVALID"
  | "SIGNATURE_INVALID"
  | "KEY_NOT_FOUND"
  | "BOUNDARY_MISMATCH"
  | "EXPIRED"
  | "REPLAY_DETECTED"
  | "STATE_NOT_PENDING"
  | "ISSUER_NOT_GATEWAY"
  | "CONSUMER_NOT_GATEWAY"
  | "EXECUTION_BOUNDARY_NOT_PRE_REGISTERED"
  | "RAW_CHANNEL_METADATA_REJECTED"
  | "ENV_APPROVAL_CLAIM_REJECTED"
  | "STORE_ERROR";

export type ApprovalGrantExecutionBoundary = {
  method: string;
  approvalId: string;
  host: "auto" | "sandbox" | "gateway" | "node";
  commandSha256: string;
  argvSha256?: string | null;
  cwdSha256?: string | null;
  nodeId?: string | null;
  agentId?: string | null;
  sessionKeySha256?: string | null;
  requestPayloadSha256: string;
};

export type ApprovalGrantPresentationBinding = {
  bindingVersion: 1;
  channelNeutralNonce: string;
  promptDigest: string;
  routeDigest?: string | null;
};

export type ApprovalGrantSigningPayload = {
  signingPayloadSchemaVersion: typeof APPROVAL_GRANT_SIGNING_PAYLOAD_SCHEMA_VERSION;
  grantSchemaVersion: typeof APPROVAL_GRANT_SCHEMA_VERSION;
  grantId: string;
  approvalId: string;
  decision: ApprovalGrantDecision;
  issuer: "gateway";
  consumer: "gateway";
  createdAtMs: number;
  expiresAtMs: number;
  keyId: string;
  executionBoundary: ApprovalGrantExecutionBoundary;
  presentationBinding: ApprovalGrantPresentationBinding;
  replayNonce: string;
};

export type ApprovalGrantEnvelope = ApprovalGrantSigningPayload & {
  schemaVersion: typeof APPROVAL_GRANT_SCHEMA_VERSION;
  signature: string;
};

export type ApprovalGrantAuditEvent = {
  atMs: number;
  event: string;
  grantId?: string;
  approvalId?: string;
  code?: ApprovalGrantTerminalCode;
  detail?: string;
};

export type ApprovalGrantIssueInput = {
  approvalId: string;
  decision: ApprovalGrantDecision;
  executionBoundary: ApprovalGrantExecutionBoundary;
  presentationBinding: ApprovalGrantPresentationBinding;
  ttlMs: number;
  nowMs?: number;
  grantId?: string;
  replayNonce?: string;
  preRegisteredApprovalIds?: ReadonlySet<string>;
  rawChannelMetadata?: unknown;
  environmentApprovalClaim?: unknown;
};

export type ApprovalGrantConsumeInput = {
  grant: ApprovalGrantEnvelope;
  executionBoundary: ApprovalGrantExecutionBoundary;
  nowMs?: number;
};

export type ApprovalGrantIssueResult =
  | { ok: true; grant: ApprovalGrantEnvelope; signingPayload: string; receipt: ApprovalGrantReceipt }
  | { ok: false; code: ApprovalGrantTerminalCode; receipt: ApprovalGrantReceipt };

export type ApprovalGrantConsumeResult =
  | { ok: true; code: "OK_CONSUMED"; grantId: string; receipt: ApprovalGrantReceipt }
  | { ok: false; code: ApprovalGrantTerminalCode; grantId?: string; receipt: ApprovalGrantReceipt };

export type ApprovalGrantReceipt = {
  receiptVersion: 1;
  broker: "openclaw.gateway.approvalGrantBroker";
  classification: ApprovalGrantTerminalCode | "ISSUED";
  grantId?: string;
  approvalId?: string;
  boundaryHash?: string;
  signingPayloadSha256?: string;
  grantEnvelopeSha256?: string;
  atMs: number;
};

export type ApprovalGrantBrokerOptions = {
  enabled?: boolean;
  storePath?: string;
  keyring?: ApprovalGrantEd25519Keyring;
  allowedIssuer?: "gateway";
  allowedConsumer?: "gateway";
  audit?: (event: ApprovalGrantAuditEvent) => void;
};

type StoredGrantRow = {
  grant_id: string;
  approval_id: string;
  state: ApprovalGrantState;
  envelope_json: string;
  signing_payload: string;
  signature: string;
  key_id: string;
  boundary_hash: string;
  replay_nonce: string;
  created_at_ms: number;
  expires_at_ms: number;
  consumed_at_ms: number | null;
  terminal_code: string | null;
  audit_json: string;
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function base64UrlEncode(buf: Buffer): string {
  return buf.toString("base64").replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/g, "");
}

function base64UrlDecode(input: string): Buffer {
  const normalized = input.replaceAll("-", "+").replaceAll("_", "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  return Buffer.from(padded, "base64");
}

function publicKeyRawFromPem(publicKeyPem: string): Buffer {
  const key = crypto.createPublicKey(publicKeyPem);
  const spki = key.export({ type: "spki", format: "der" }) as Buffer;
  if (
    spki.length === ED25519_SPKI_PREFIX.length + 32 &&
    spki.subarray(0, ED25519_SPKI_PREFIX.length).equals(ED25519_SPKI_PREFIX)
  ) {
    return spki.subarray(ED25519_SPKI_PREFIX.length);
  }
  return spki;
}

export function sha256Hex(input: string | Buffer): string {
  return crypto.createHash("sha256").update(input).digest("hex");
}

export function sha256Json(value: unknown): string {
  return sha256Hex(canonicalJson(value));
}

export function canonicalJson(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error("canonical json refuses non-finite numbers");
    return JSON.stringify(value);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) return `[${value.map((entry) => canonicalJson(entry)).join(",")}]`;
  if (isObject(value)) {
    const entries = Object.entries(value)
      .filter(([, entry]) => entry !== undefined)
      .sort(([a], [b]) => a.localeCompare(b));
    return `{${entries.map(([key, entry]) => `${JSON.stringify(key)}:${canonicalJson(entry)}`).join(",")}}`;
  }
  throw new Error(`canonical json refuses unsupported type: ${typeof value}`);
}

export function canonicalApprovalGrantSigningPayload(
  payload: ApprovalGrantSigningPayload,
): string {
  return canonicalJson(payload);
}

export function buildApprovalGrantBoundaryHash(boundary: ApprovalGrantExecutionBoundary): string {
  return sha256Json(boundary);
}

export function buildChannelNeutralPresentationBinding(params: {
  promptText: string;
  routeDescriptor?: string | null;
  nonce?: string;
}): ApprovalGrantPresentationBinding {
  return {
    bindingVersion: 1,
    channelNeutralNonce: params.nonce ?? base64UrlEncode(crypto.randomBytes(24)),
    promptDigest: sha256Hex(params.promptText),
    routeDigest: params.routeDescriptor ? sha256Hex(params.routeDescriptor) : null,
  };
}

export function buildExecutionBoundary(params: {
  method: string;
  approvalId: string;
  host?: ApprovalGrantExecutionBoundary["host"] | null;
  command: string;
  commandArgv?: string[] | null;
  cwd?: string | null;
  nodeId?: string | null;
  agentId?: string | null;
  sessionKey?: string | null;
  requestPayload: unknown;
}): ApprovalGrantExecutionBoundary {
  return {
    method: params.method,
    approvalId: params.approvalId,
    host: params.host ?? "auto",
    commandSha256: sha256Hex(params.command),
    argvSha256: params.commandArgv ? sha256Json(params.commandArgv) : null,
    cwdSha256: params.cwd ? sha256Hex(params.cwd) : null,
    nodeId: params.nodeId ?? null,
    agentId: params.agentId ?? null,
    sessionKeySha256: params.sessionKey ? sha256Hex(params.sessionKey) : null,
    requestPayloadSha256: sha256Json(params.requestPayload),
  };
}

export function assertNoRawChannelMetadata(value: unknown): boolean {
  if (!isObject(value)) return true;
  const forbidden = new Set([
    "telegram",
    "telegramChatId",
    "telegramMessageId",
    "chat_id",
    "message_id",
    "from",
    "rawUpdate",
    "turnSourceTo",
    "turnSourceThreadId",
  ]);
  const stack: unknown[] = [value];
  while (stack.length > 0) {
    const current = stack.pop();
    if (!isObject(current)) continue;
    for (const [key, entry] of Object.entries(current)) {
      if (forbidden.has(key)) return false;
      if (isObject(entry) || Array.isArray(entry)) stack.push(entry);
    }
  }
  return true;
}

export function assertNoEnvironmentApprovalClaim(value: unknown): boolean {
  if (!isObject(value)) return true;
  const stack: unknown[] = [value];
  while (stack.length > 0) {
    const current = stack.pop();
    if (!isObject(current)) continue;
    for (const [key, entry] of Object.entries(current)) {
      const normalized = key.toLowerCase();
      if (
        normalized.includes("approval") &&
        (normalized.includes("env") || normalized.includes("environment") || normalized.includes("token"))
      ) {
        return false;
      }
      if (normalized.startsWith("openclaw_approval") || normalized.startsWith("approval_")) {
        return false;
      }
      if (isObject(entry) || Array.isArray(entry)) stack.push(entry);
    }
  }
  return true;
}

export class ApprovalGrantEd25519Keyring {
  private keys = new Map<string, { publicKeyPem: string; privateKeyPem?: string }>();
  private activeKeyId: string | null = null;

  static createTestOnly(seedLabel = "test-key"): ApprovalGrantEd25519Keyring {
    const keyring = new ApprovalGrantEd25519Keyring();
    keyring.rotateTestOnly(seedLabel);
    return keyring;
  }

  rotateTestOnly(label = `test-${Date.now()}`): string {
    const { publicKey, privateKey } = crypto.generateKeyPairSync("ed25519");
    const publicKeyPem = publicKey.export({ type: "spki", format: "pem" }).toString();
    const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }).toString();
    const keyId = `test-ed25519-${sha256Hex(`${label}:${base64UrlEncode(publicKeyRawFromPem(publicKeyPem))}`).slice(0, 16)}`;
    this.keys.set(keyId, { publicKeyPem, privateKeyPem });
    this.activeKeyId = keyId;
    return keyId;
  }

  importPublicKey(keyId: string, publicKeyPem: string): void {
    this.keys.set(keyId, { publicKeyPem });
  }

  getActiveKeyId(): string {
    if (!this.activeKeyId) throw new Error("approval grant keyring has no active key");
    return this.activeKeyId;
  }

  getPublicKeyPem(keyId: string): string | null {
    return this.keys.get(keyId)?.publicKeyPem ?? null;
  }

  sign(payload: string): { keyId: string; signature: string } {
    const keyId = this.getActiveKeyId();
    const entry = this.keys.get(keyId);
    if (!entry?.privateKeyPem) throw new Error(`approval grant private key unavailable: ${keyId}`);
    const signature = crypto.sign(null, Buffer.from(payload, "utf8"), crypto.createPrivateKey(entry.privateKeyPem));
    return { keyId, signature: base64UrlEncode(signature) };
  }

  verify(keyId: string, payload: string, signatureBase64Url: string): boolean {
    const publicKeyPem = this.getPublicKeyPem(keyId);
    if (!publicKeyPem) return false;
    try {
      return crypto.verify(
        null,
        Buffer.from(payload, "utf8"),
        crypto.createPublicKey(publicKeyPem),
        base64UrlDecode(signatureBase64Url),
      );
    } catch {
      return false;
    }
  }
}

export class ApprovalGrantSqliteStore {
  private db: any;

  constructor(public readonly filePath: string) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    const { DatabaseSync } = requireNodeSqlite();
    this.db = new DatabaseSync(filePath);
    this.migrate();
  }

  close(): void {
    this.db.close();
  }

  migrate(): void {
    this.db.exec("PRAGMA journal_mode = WAL");
    this.db.exec("PRAGMA synchronous = NORMAL");
    const version = this.db.prepare("PRAGMA user_version").get()?.user_version ?? 0;
    if (version > APPROVAL_GRANT_DB_USER_VERSION) {
      throw new Error(`approval grant db version ${version} is newer than supported ${APPROVAL_GRANT_DB_USER_VERSION}`);
    }
    if (version < 1) {
      this.db.exec(`
        CREATE TABLE IF NOT EXISTS approval_grants (
          grant_id TEXT PRIMARY KEY,
          approval_id TEXT NOT NULL,
          state TEXT NOT NULL CHECK (state IN ('PENDING','CONSUMED','EXPIRED','REVOKED','CRASH_RECOVERED')),
          envelope_json TEXT NOT NULL,
          signing_payload TEXT NOT NULL,
          signature TEXT NOT NULL,
          key_id TEXT NOT NULL,
          boundary_hash TEXT NOT NULL,
          replay_nonce TEXT NOT NULL UNIQUE,
          created_at_ms INTEGER NOT NULL,
          expires_at_ms INTEGER NOT NULL,
          consumed_at_ms INTEGER,
          terminal_code TEXT,
          audit_json TEXT NOT NULL DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_approval_grants_approval_id ON approval_grants(approval_id);
        CREATE INDEX IF NOT EXISTS idx_approval_grants_state ON approval_grants(state);
        PRAGMA user_version = 1;
      `);
    }
  }

  insertPending(params: {
    envelope: ApprovalGrantEnvelope;
    signingPayload: string;
    boundaryHash: string;
    audit: ApprovalGrantAuditEvent[];
  }): void {
    this.db.prepare(`
      INSERT INTO approval_grants (
        grant_id, approval_id, state, envelope_json, signing_payload, signature, key_id,
        boundary_hash, replay_nonce, created_at_ms, expires_at_ms, audit_json
      ) VALUES (?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      params.envelope.grantId,
      params.envelope.approvalId,
      canonicalJson(params.envelope),
      params.signingPayload,
      params.envelope.signature,
      params.envelope.keyId,
      params.boundaryHash,
      params.envelope.replayNonce,
      params.envelope.createdAtMs,
      params.envelope.expiresAtMs,
      canonicalJson(params.audit),
    );
  }

  get(grantId: string): StoredGrantRow | null {
    return this.db.prepare("SELECT * FROM approval_grants WHERE grant_id = ?").get(grantId) ?? null;
  }

  atomicallyConsume(params: {
    grantId: string;
    nowMs: number;
    terminalCode: ApprovalGrantTerminalCode;
    audit: ApprovalGrantAuditEvent;
  }): { consumed: boolean; priorState?: ApprovalGrantState | null } {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const row = this.get(params.grantId);
      if (!row) {
        this.db.exec("ROLLBACK");
        return { consumed: false, priorState: null };
      }
      if (row.state !== "PENDING") {
        this.db.exec("ROLLBACK");
        return { consumed: false, priorState: row.state };
      }
      const audit = JSON.parse(row.audit_json) as ApprovalGrantAuditEvent[];
      audit.push(params.audit);
      this.db.prepare(`
        UPDATE approval_grants
        SET state = 'CONSUMED', consumed_at_ms = ?, terminal_code = ?, audit_json = ?
        WHERE grant_id = ? AND state = 'PENDING'
      `).run(params.nowMs, params.terminalCode, canonicalJson(audit), params.grantId);
      this.db.exec("COMMIT");
      return { consumed: true, priorState: "PENDING" };
    } catch (err) {
      this.db.exec("ROLLBACK");
      throw err;
    }
  }

  markTerminal(params: {
    grantId: string;
    state: Exclude<ApprovalGrantState, "PENDING" | "CONSUMED">;
    code: ApprovalGrantTerminalCode;
    nowMs: number;
  }): void {
    this.db.prepare(`
      UPDATE approval_grants SET state = ?, terminal_code = ? WHERE grant_id = ? AND state = 'PENDING'
    `).run(params.state, params.code, params.grantId);
  }

  listRows(): StoredGrantRow[] {
    return this.db.prepare("SELECT * FROM approval_grants ORDER BY created_at_ms, grant_id").all();
  }
}

function validateBoundary(boundary: unknown): boundary is ApprovalGrantExecutionBoundary {
  if (!isObject(boundary)) return false;
  return (
    typeof boundary.method === "string" &&
    typeof boundary.approvalId === "string" &&
    ["auto", "sandbox", "gateway", "node"].includes(String(boundary.host)) &&
    typeof boundary.commandSha256 === "string" &&
    typeof boundary.requestPayloadSha256 === "string"
  );
}

function validatePresentationBinding(binding: unknown): binding is ApprovalGrantPresentationBinding {
  return (
    isObject(binding) &&
    binding.bindingVersion === 1 &&
    typeof binding.channelNeutralNonce === "string" &&
    typeof binding.promptDigest === "string" &&
    !Object.prototype.hasOwnProperty.call(binding, "telegram")
  );
}

export function validateApprovalGrantEnvelope(value: unknown): value is ApprovalGrantEnvelope {
  if (!isObject(value)) return false;
  if (value.schemaVersion !== APPROVAL_GRANT_SCHEMA_VERSION) return false;
  if (value.signingPayloadSchemaVersion !== APPROVAL_GRANT_SIGNING_PAYLOAD_SCHEMA_VERSION) return false;
  if (value.grantSchemaVersion !== APPROVAL_GRANT_SCHEMA_VERSION) return false;
  if (value.issuer !== "gateway" || value.consumer !== "gateway") return false;
  if (value.decision !== "allow-once" && value.decision !== "deny") return false;
  for (const key of ["grantId", "approvalId", "keyId", "replayNonce", "signature"] as const) {
    if (typeof value[key] !== "string" || value[key].length === 0) return false;
  }
  if (typeof value.createdAtMs !== "number" || typeof value.expiresAtMs !== "number") return false;
  return validateBoundary(value.executionBoundary) && validatePresentationBinding(value.presentationBinding);
}

function signingPayloadFromEnvelope(envelope: ApprovalGrantEnvelope): ApprovalGrantSigningPayload {
  const { schemaVersion: _schemaVersion, signature: _signature, ...payload } = envelope;
  return payload;
}

function makeReceipt(params: {
  classification: ApprovalGrantReceipt["classification"];
  grant?: ApprovalGrantEnvelope;
  boundaryHash?: string;
  signingPayload?: string;
  nowMs: number;
}): ApprovalGrantReceipt {
  const envelopeJson = params.grant ? canonicalJson(params.grant) : undefined;
  return {
    receiptVersion: 1,
    broker: "openclaw.gateway.approvalGrantBroker",
    classification: params.classification,
    grantId: params.grant?.grantId,
    approvalId: params.grant?.approvalId,
    boundaryHash: params.boundaryHash,
    signingPayloadSha256: params.signingPayload ? sha256Hex(params.signingPayload) : undefined,
    grantEnvelopeSha256: envelopeJson ? sha256Hex(envelopeJson) : undefined,
    atMs: params.nowMs,
  };
}

export class ApprovalGrantBroker {
  private readonly enabled: boolean;
  private readonly store: ApprovalGrantSqliteStore | null;
  private readonly keyring: ApprovalGrantEd25519Keyring;
  private readonly audit: (event: ApprovalGrantAuditEvent) => void;

  constructor(opts: ApprovalGrantBrokerOptions = {}) {
    this.enabled = opts.enabled === true;
    this.keyring = opts.keyring ?? ApprovalGrantEd25519Keyring.createTestOnly("approval-grant-default-test-only");
    this.audit = opts.audit ?? (() => undefined);
    this.store = this.enabled
      ? new ApprovalGrantSqliteStore(opts.storePath ?? path.join(process.cwd(), ".artifacts", "approval-grants", "approval-grants.sqlite"))
      : null;
  }

  close(): void {
    this.store?.close();
  }

  issue(input: ApprovalGrantIssueInput): ApprovalGrantIssueResult {
    const nowMs = input.nowMs ?? Date.now();
    if (!this.enabled || !this.store) {
      return { ok: false, code: "CONFIG_DISABLED", receipt: makeReceipt({ classification: "CONFIG_DISABLED", nowMs }) };
    }
    if (input.rawChannelMetadata !== undefined && !assertNoRawChannelMetadata(input.rawChannelMetadata)) {
      return { ok: false, code: "RAW_CHANNEL_METADATA_REJECTED", receipt: makeReceipt({ classification: "RAW_CHANNEL_METADATA_REJECTED", nowMs }) };
    }
    if (input.environmentApprovalClaim !== undefined && !assertNoEnvironmentApprovalClaim(input.environmentApprovalClaim)) {
      return { ok: false, code: "ENV_APPROVAL_CLAIM_REJECTED", receipt: makeReceipt({ classification: "ENV_APPROVAL_CLAIM_REJECTED", nowMs }) };
    }
    if (input.preRegisteredApprovalIds && !input.preRegisteredApprovalIds.has(input.approvalId)) {
      return { ok: false, code: "EXECUTION_BOUNDARY_NOT_PRE_REGISTERED", receipt: makeReceipt({ classification: "EXECUTION_BOUNDARY_NOT_PRE_REGISTERED", nowMs }) };
    }
    if (input.decision === "deny") {
      return { ok: false, code: "EXECUTION_BOUNDARY_NOT_PRE_REGISTERED", receipt: makeReceipt({ classification: "EXECUTION_BOUNDARY_NOT_PRE_REGISTERED", nowMs }) };
    }
    const keyId = this.keyring.getActiveKeyId();
    const grantId = input.grantId ?? crypto.randomUUID();
    const replayNonce = input.replayNonce ?? base64UrlEncode(crypto.randomBytes(32));
    const signingPayload: ApprovalGrantSigningPayload = {
      signingPayloadSchemaVersion: APPROVAL_GRANT_SIGNING_PAYLOAD_SCHEMA_VERSION,
      grantSchemaVersion: APPROVAL_GRANT_SCHEMA_VERSION,
      grantId,
      approvalId: input.approvalId,
      decision: input.decision,
      issuer: "gateway",
      consumer: "gateway",
      createdAtMs: nowMs,
      expiresAtMs: nowMs + input.ttlMs,
      keyId,
      executionBoundary: input.executionBoundary,
      presentationBinding: input.presentationBinding,
      replayNonce,
    };
    const canonicalPayload = canonicalApprovalGrantSigningPayload(signingPayload);
    const { signature } = this.keyring.sign(canonicalPayload);
    const grant: ApprovalGrantEnvelope = { schemaVersion: APPROVAL_GRANT_SCHEMA_VERSION, ...signingPayload, signature };
    const boundaryHash = buildApprovalGrantBoundaryHash(input.executionBoundary);
    const audit = [{ atMs: nowMs, event: "ISSUED", grantId, approvalId: input.approvalId }];
    try {
      this.store.insertPending({ envelope: grant, signingPayload: canonicalPayload, boundaryHash, audit });
      this.audit(audit[0]);
      return {
        ok: true,
        grant,
        signingPayload: canonicalPayload,
        receipt: makeReceipt({ classification: "ISSUED", grant, boundaryHash, signingPayload: canonicalPayload, nowMs }),
      };
    } catch (err) {
      this.audit({ atMs: nowMs, event: "STORE_ERROR", grantId, approvalId: input.approvalId, detail: String(err) });
      return { ok: false, code: "STORE_ERROR", receipt: makeReceipt({ classification: "STORE_ERROR", grant, boundaryHash, signingPayload: canonicalPayload, nowMs }) };
    }
  }

  consume(input: ApprovalGrantConsumeInput): ApprovalGrantConsumeResult {
    const nowMs = input.nowMs ?? Date.now();
    const boundaryHash = buildApprovalGrantBoundaryHash(input.executionBoundary);
    if (!this.enabled || !this.store) {
      return { ok: false, code: "CONFIG_DISABLED", receipt: makeReceipt({ classification: "CONFIG_DISABLED", nowMs, boundaryHash }) };
    }
    if (!validateApprovalGrantEnvelope(input.grant)) {
      return { ok: false, code: "SCHEMA_INVALID", receipt: makeReceipt({ classification: "SCHEMA_INVALID", nowMs, boundaryHash }) };
    }
    if (input.grant.issuer !== "gateway") {
      return { ok: false, code: "ISSUER_NOT_GATEWAY", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "ISSUER_NOT_GATEWAY", grant: input.grant, nowMs, boundaryHash }) };
    }
    if (input.grant.consumer !== "gateway") {
      return { ok: false, code: "CONSUMER_NOT_GATEWAY", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "CONSUMER_NOT_GATEWAY", grant: input.grant, nowMs, boundaryHash }) };
    }
    const signingPayload = canonicalApprovalGrantSigningPayload(signingPayloadFromEnvelope(input.grant));
    if (!this.keyring.getPublicKeyPem(input.grant.keyId)) {
      return { ok: false, code: "KEY_NOT_FOUND", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "KEY_NOT_FOUND", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    if (!this.keyring.verify(input.grant.keyId, signingPayload, input.grant.signature)) {
      return { ok: false, code: "SIGNATURE_INVALID", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "SIGNATURE_INVALID", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    if (canonicalJson(input.grant.executionBoundary) !== canonicalJson(input.executionBoundary)) {
      return { ok: false, code: "BOUNDARY_MISMATCH", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "BOUNDARY_MISMATCH", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    if (nowMs > input.grant.expiresAtMs) {
      this.store.markTerminal({ grantId: input.grant.grantId, state: "EXPIRED", code: "EXPIRED", nowMs });
      return { ok: false, code: "EXPIRED", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "EXPIRED", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    const row = this.store.get(input.grant.grantId);
    if (!row) {
      return { ok: false, code: "REPLAY_DETECTED", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "REPLAY_DETECTED", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    if (row.boundary_hash !== boundaryHash) {
      return { ok: false, code: "BOUNDARY_MISMATCH", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "BOUNDARY_MISMATCH", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    if (row.state !== "PENDING") {
      const code = TERMINAL_GRANT_STATES.has(row.state) ? "REPLAY_DETECTED" : "STATE_NOT_PENDING";
      return { ok: false, code, grantId: input.grant.grantId, receipt: makeReceipt({ classification: code, grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    const consumed = this.store.atomicallyConsume({
      grantId: input.grant.grantId,
      nowMs,
      terminalCode: "OK_CONSUMED",
      audit: { atMs: nowMs, event: "CONSUMED", grantId: input.grant.grantId, approvalId: input.grant.approvalId, code: "OK_CONSUMED" },
    });
    if (!consumed.consumed) {
      const code = consumed.priorState && consumed.priorState !== "PENDING" ? "REPLAY_DETECTED" : "STATE_NOT_PENDING";
      return { ok: false, code, grantId: input.grant.grantId, receipt: makeReceipt({ classification: code, grant: input.grant, signingPayload, nowMs, boundaryHash }) };
    }
    this.audit({ atMs: nowMs, event: "CONSUMED", grantId: input.grant.grantId, approvalId: input.grant.approvalId, code: "OK_CONSUMED" });
    return { ok: true, code: "OK_CONSUMED", grantId: input.grant.grantId, receipt: makeReceipt({ classification: "OK_CONSUMED", grant: input.grant, signingPayload, nowMs, boundaryHash }) };
  }

  rowsForObserver(): StoredGrantRow[] {
    return this.store?.listRows() ?? [];
  }
}

export function verifyApprovalGrantObserverReceipt(receipt: ApprovalGrantReceipt): boolean {
  return (
    receipt.receiptVersion === 1 &&
    receipt.broker === "openclaw.gateway.approvalGrantBroker" &&
    typeof receipt.classification === "string" &&
    typeof receipt.atMs === "number"
  );
}
