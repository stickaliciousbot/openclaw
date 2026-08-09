import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  ApprovalGrantBroker,
  ApprovalGrantEd25519Keyring,
  buildChannelNeutralPresentationBinding,
  buildExecutionBoundary,
  canonicalApprovalGrantSigningPayload,
  canonicalJson,
  sha256Hex,
  verifyApprovalGrantObserverReceipt,
  type ApprovalGrantEnvelope,
} from "./approval-grant-broker.js";

const tempDirs: string[] = [];

afterEach(() => {
  for (const dir of tempDirs.splice(0)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

function tempDb(label = "case"): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `openclaw-g1-grants-${label}-`));
  tempDirs.push(dir);
  return path.join(dir, "grants.sqlite");
}

function fixture(label = "base") {
  const approvalId = `approval-${label}`;
  const requestPayload = { method: "exec.approval.request", approvalId, command: `echo ${label}` };
  const boundary = buildExecutionBoundary({
    method: "approval.grant.consume",
    approvalId,
    host: "gateway",
    command: `echo ${label}`,
    commandArgv: ["echo", label],
    cwd: `/tmp/${label}`,
    agentId: `agent-${label}`,
    sessionKey: `session-${label}`,
    requestPayload,
  });
  const presentationBinding = buildChannelNeutralPresentationBinding({
    promptText: `Approve ${label}`,
    routeDescriptor: `channel-neutral:${label}`,
    nonce: `nonce-${label}`,
  });
  return { approvalId, requestPayload, boundary, presentationBinding };
}

function issueGrant(label = "ok", keyring = ApprovalGrantEd25519Keyring.createTestOnly(label)) {
  const broker = new ApprovalGrantBroker({ enabled: true, storePath: tempDb(label), keyring });
  const f = fixture(label);
  const issued = broker.issue({
    approvalId: f.approvalId,
    decision: "allow-once",
    executionBoundary: f.boundary,
    presentationBinding: f.presentationBinding,
    ttlMs: 60_000,
    nowMs: 1_000,
    grantId: `grant-${label}`,
    replayNonce: `replay-${label}`,
    preRegisteredApprovalIds: new Set([f.approvalId]),
  });
  expect(issued.ok).toBe(true);
  if (!issued.ok) throw new Error(issued.code);
  return { broker, keyring, ...f, grant: issued.grant, receipt: issued.receipt };
}

describe("approval grant broker source-only core", () => {
  it("defaults disabled and fails closed", () => {
    const broker = new ApprovalGrantBroker();
    const f = fixture("disabled");
    const issued = broker.issue({
      approvalId: f.approvalId,
      decision: "allow-once",
      executionBoundary: f.boundary,
      presentationBinding: f.presentationBinding,
      ttlMs: 10_000,
      preRegisteredApprovalIds: new Set([f.approvalId]),
    });
    expect(issued.ok).toBe(false);
    expect(issued.receipt.classification).toBe("CONFIG_DISABLED");
  });

  it("canonical serialization is stable and sorted", () => {
    expect(canonicalJson({ z: 1, a: { b: true, a: null } })).toBe(
      '{"a":{"a":null,"b":true},"z":1}',
    );
    const { grant } = issueGrant("canonical");
    const { schemaVersion: _schemaVersion, signature: _signature, ...payload } = grant;
    expect(sha256Hex(canonicalApprovalGrantSigningPayload(payload))).toMatch(/^[a-f0-9]{64}$/);
  });

  it("issues, verifies, consumes once, and records observer receipts", () => {
    const { broker, boundary, grant, receipt } = issueGrant("consume");
    expect(receipt.classification).toBe("ISSUED");
    expect(verifyApprovalGrantObserverReceipt(receipt)).toBe(true);
    const consumed = broker.consume({ grant, executionBoundary: boundary, nowMs: 2_000 });
    expect(consumed.ok).toBe(true);
    expect(consumed.receipt.classification).toBe("OK_CONSUMED");
    expect(broker.rowsForObserver()[0]?.state).toBe("CONSUMED");
    const replay = broker.consume({ grant, executionBoundary: boundary, nowMs: 2_001 });
    expect(replay.ok).toBe(false);
    expect(replay.code).toBe("REPLAY_DETECTED");
  });

  it("persists one-time state across broker restart", () => {
    const keyring = ApprovalGrantEd25519Keyring.createTestOnly("restart");
    const db = tempDb("restart");
    const f = fixture("restart");
    const brokerA = new ApprovalGrantBroker({ enabled: true, storePath: db, keyring });
    const issued = brokerA.issue({
      approvalId: f.approvalId,
      decision: "allow-once",
      executionBoundary: f.boundary,
      presentationBinding: f.presentationBinding,
      ttlMs: 60_000,
      nowMs: 10,
      grantId: "grant-restart",
      replayNonce: "replay-restart",
      preRegisteredApprovalIds: new Set([f.approvalId]),
    });
    expect(issued.ok).toBe(true);
    if (!issued.ok) throw new Error(issued.code);
    brokerA.close();
    const brokerB = new ApprovalGrantBroker({ enabled: true, storePath: db, keyring });
    expect(brokerB.consume({ grant: issued.grant, executionBoundary: f.boundary, nowMs: 20 }).ok).toBe(true);
    brokerB.close();
    const brokerC = new ApprovalGrantBroker({ enabled: true, storePath: db, keyring });
    const replay = brokerC.consume({ grant: issued.grant, executionBoundary: f.boundary, nowMs: 21 });
    expect(replay.ok).toBe(false);
    expect(replay.code).toBe("REPLAY_DETECTED");
  });

  it.each([2, 5, 20])("permits exactly one winner among %i concurrent consumers", async (consumerCount) => {
    const { broker, boundary, grant } = issueGrant(`concurrency-${consumerCount}`);
    const results = await Promise.all(
      Array.from({ length: consumerCount }, (_, i) =>
        Promise.resolve().then(() => broker.consume({ grant, executionBoundary: boundary, nowMs: 3_000 + i })),
      ),
    );
    expect(results.filter((result) => result.ok)).toHaveLength(1);
    expect(results.filter((result) => !result.ok).map((result) => result.code)).toEqual(
      Array.from({ length: consumerCount - 1 }, () => "REPLAY_DETECTED"),
    );
  });

  it("rotates test-only Ed25519 keys and still verifies older grants", () => {
    const keyring = ApprovalGrantEd25519Keyring.createTestOnly("rotate-a");
    const { broker, boundary, grant } = issueGrant("rotate", keyring);
    const firstKey = grant.keyId;
    const secondKey = keyring.rotateTestOnly("rotate-b");
    expect(secondKey).not.toBe(firstKey);
    const consumed = broker.consume({ grant, executionBoundary: boundary, nowMs: 4_000 });
    expect(consumed.ok).toBe(true);
  });

  it("rejects raw channel metadata and environment-variable approval claims", () => {
    const keyring = ApprovalGrantEd25519Keyring.createTestOnly("bypass");
    const broker = new ApprovalGrantBroker({ enabled: true, storePath: tempDb("bypass"), keyring });
    const f = fixture("bypass");
    const raw = broker.issue({
      approvalId: f.approvalId,
      decision: "allow-once",
      executionBoundary: f.boundary,
      presentationBinding: f.presentationBinding,
      ttlMs: 60_000,
      preRegisteredApprovalIds: new Set([f.approvalId]),
      rawChannelMetadata: { telegram: { chat_id: 123 } },
    });
    expect(raw.ok).toBe(false);
    if (raw.ok) throw new Error("raw metadata bypass unexpectedly issued grant");
    expect(raw.code).toBe("RAW_CHANNEL_METADATA_REJECTED");
    const env = broker.issue({
      approvalId: f.approvalId,
      decision: "allow-once",
      executionBoundary: f.boundary,
      presentationBinding: f.presentationBinding,
      ttlMs: 60_000,
      preRegisteredApprovalIds: new Set([f.approvalId]),
      environmentApprovalClaim: { OPENCLAW_APPROVAL_TOKEN: "nope" },
    });
    expect(env.ok).toBe(false);
    if (env.ok) throw new Error("environment approval claim unexpectedly issued grant");
    expect(env.code).toBe("ENV_APPROVAL_CLAIM_REJECTED");
  });
});

type MatrixMutation = "none" | "signature" | "boundary" | "expiry" | "unknownKey" | "schema" | "replay" | "unregistered";
const matrixCases: Array<{ id: string; mutation: MatrixMutation; expected: string }> = [];
for (const mutation of ["none", "signature", "boundary", "expiry", "unknownKey", "schema", "replay", "unregistered"] as MatrixMutation[]) {
  for (let i = 0; i < 8; i += 1) {
    matrixCases.push({
      id: `${mutation}-${i}`,
      mutation,
      expected:
        mutation === "none"
          ? "OK_CONSUMED"
          : mutation === "signature"
            ? "SIGNATURE_INVALID"
            : mutation === "boundary"
              ? "BOUNDARY_MISMATCH"
              : mutation === "expiry"
                ? "EXPIRED"
                : mutation === "unknownKey"
                  ? "KEY_NOT_FOUND"
                  : mutation === "schema"
                    ? "SCHEMA_INVALID"
                    : mutation === "replay"
                      ? "REPLAY_DETECTED"
                      : "EXECUTION_BOUNDARY_NOT_PRE_REGISTERED",
    });
  }
}

describe("approval grant deterministic 64-case matrix", () => {
  it.each(matrixCases)("matrix $id -> $expected", ({ id, mutation, expected }) => {
    const keyring = ApprovalGrantEd25519Keyring.createTestOnly(id);
    const broker = new ApprovalGrantBroker({ enabled: true, storePath: tempDb(id), keyring });
    const f = fixture(id);
    const preRegisteredApprovalIds = mutation === "unregistered" ? new Set<string>() : new Set([f.approvalId]);
    const issued = broker.issue({
      approvalId: f.approvalId,
      decision: "allow-once",
      executionBoundary: f.boundary,
      presentationBinding: f.presentationBinding,
      ttlMs: 1_000,
      nowMs: 10_000,
      grantId: `grant-${id}`,
      replayNonce: `replay-${id}`,
      preRegisteredApprovalIds,
    });
    if (mutation === "unregistered") {
      expect(issued.ok).toBe(false);
      if (!issued.ok) expect(issued.code).toBe(expected);
      return;
    }
    expect(issued.ok).toBe(true);
    if (!issued.ok) throw new Error(issued.code);
    let grant: ApprovalGrantEnvelope = issued.grant;
    let boundary = f.boundary;
    let nowMs = 10_001;
    if (mutation === "signature") grant = { ...grant, signature: `${grant.signature}x` };
    if (mutation === "unknownKey") grant = { ...grant, keyId: "test-ed25519-missing" };
    if (mutation === "schema") grant = { ...grant, schemaVersion: 99 as 1 };
    if (mutation === "boundary") boundary = { ...boundary, commandSha256: sha256Hex("other") };
    if (mutation === "expiry") nowMs = 11_002;
    if (mutation === "replay") {
      const first = broker.consume({ grant, executionBoundary: boundary, nowMs });
      expect(first.ok).toBe(true);
    }
    const consumed = broker.consume({ grant, executionBoundary: boundary, nowMs: nowMs + 1 });
    if (expected === "OK_CONSUMED") {
      expect(consumed.ok).toBe(true);
      expect(consumed.code).toBe(expected);
    } else {
      expect(consumed.ok).toBe(false);
      expect(consumed.code).toBe(expected);
    }
  });
});

describe("approval grant static bypass guard", () => {
  it("does not accept raw Telegram metadata or env approval claims in source", () => {
    const source = fs.readFileSync(new URL("./approval-grant-broker.ts", import.meta.url), "utf8");
    expect(source).not.toContain("process.env.OPENCLAW_APPROVAL");
    expect(source).toContain("RAW_CHANNEL_METADATA_REJECTED");
    expect(source).toContain("ENV_APPROVAL_CLAIM_REJECTED");
  });
});
