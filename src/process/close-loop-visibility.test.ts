// Close-loop visibility tests cover terminal notices, evidence, stale async, and silent success.
import { describe, expect, it } from "vitest";
import {
  classifyCommandCloseLoop,
  finalizeGeneratorRequiredFiles,
  formatCloseLoopNotice,
  extractCloseoutDeliveryPayloadFromToolResult,
  formatCloseoutDeliverySummary,
  normalizeCloseoutDeliveryPayload,
  reconcileEvidenceManifest,
  reconcileGeneratorPreWriteRequiredFiles,
  reconcileRequiredFiles,
  reconcileStaleAsyncCompletion,
  resolveCloseoutDeliveryDecision,
  sha256Text,
  textContainsCloseoutSummary,
  validateCloseLoopNotice,
  type CloseLoopNoticeInput,
} from "./close-loop-visibility.js";

function createNotice(overrides: Partial<CloseLoopNoticeInput> = {}): CloseLoopNoticeInput {
  return {
    status: "PASS",
    artifactDir:
      "sharedspace/runtime-kernel-validation/vnext-semantic-gate/m13r1a_controlled_apply",
    requiredFilesMissing: [],
    failedGates: [],
    firstFailure: null,
    completedCountOrBound: "11/11 fixtures",
    mutationBoundaryReadback: {
      cacheEnabled: false,
      artifactMemoryPromoted: false,
      runtimeGatewayRouteMutation: false,
      externalSchedulingExecution: false,
      providerModelAuthoritativeCalls: 0,
      directProviderBypass: 0,
      newExpansionStarted: false,
    },
    rollbackReady: true,
    mutationSentinelsClean: true,
    artifactHashes: { "status.json": sha256Text("status") },
    recommendedNextAction: "No semantic expansion; preserve M12 C1-C4 boundaries.",
    ...overrides,
  };
}

describe("close-loop visibility", () => {
  it("accepts a terminal PASS notice with required fields and hashes", () => {
    const notice = createNotice();

    expect(validateCloseLoopNotice(notice)).toEqual({
      ok: true,
      missingFields: [],
      invalidFields: [],
      terminalState: "PASS",
    });
    expect(formatCloseLoopNotice(notice).startsWith("PASS ")).toBe(true);
  });

  it("accepts a terminal FAIL notice with failed gates and first failure", () => {
    const notice = createNotice({
      status: "FAIL",
      failedGates: ["fixture_evidence_manifest_hash_mismatch"],
      firstFailure: "fixture_evidence_manifest_hash_mismatch",
    });

    expect(validateCloseLoopNotice(notice).terminalState).toBe("FAIL");
    expect(formatCloseLoopNotice(notice)).toContain("fixture_evidence_manifest_hash_mismatch");
  });

  it("blocks when required files are missing", () => {
    const result = reconcileRequiredFiles({
      requiredFiles: ["status.json", "summary.json", "evidence_manifest.json"],
      presentFiles: ["status.json", "summary.json"],
    });

    expect(result).toEqual({
      ok: false,
      terminalState: "BLOCKED",
      missing: ["evidence_manifest.json"],
    });
  });

  it("passes required-file ordering after terminal files exist", () => {
    const result = reconcileRequiredFiles({
      requiredFiles: ["status.json", "summary.json", "evidence_manifest.json"],
      presentFiles: ["status.json", "summary.json", "evidence_manifest.json"],
    });

    expect(result.ok).toBe(true);
    expect(result.terminalState).toBe("PASS");
  });

  it("does not pre-fail generator required files on terminal files before writing them", () => {
    const result = reconcileGeneratorPreWriteRequiredFiles({
      requiredFiles: ["status.json", "summary.json", "evidence_manifest.json"],
      presentFiles: ["evidence_manifest.json"],
    });

    expect(result).toEqual({
      ok: true,
      terminalState: "PASS",
      missing: [],
      deferredTerminalFiles: ["status.json", "summary.json"],
    });
  });

  it("performs post-write required-file verification for generators", () => {
    const result = finalizeGeneratorRequiredFiles({
      terminalStatus: "M12_FINAL_ACCEPTED_PRODUCTION_STACK_CLOSEOUT_PASS",
      requiredFiles: ["status.json", "summary.json", "evidence_manifest.json"],
      presentFiles: ["status.json", "summary.json"],
    });

    expect(result).toEqual({
      ok: false,
      terminalState: "BLOCKED",
      missing: ["evidence_manifest.json"],
    });
  });

  it("does not report PASS unless terminal status itself says PASS", () => {
    const result = finalizeGeneratorRequiredFiles({
      terminalStatus: "M12_FINAL_ACCEPTED_PRODUCTION_STACK_CLOSEOUT_FAIL",
      requiredFiles: ["status.json", "summary.json"],
      presentFiles: ["status.json", "summary.json"],
    });

    expect(result.ok).toBe(false);
    expect(result.terminalState).toBe("FAIL");
  });

  it("blocks evidence manifests with hash mismatches", () => {
    const result = reconcileEvidenceManifest({
      manifest: [{ path: "status.json", sha256: "expected", required: true }],
      actualHashes: { "status.json": "actual" },
    });

    expect(result.ok).toBe(false);
    expect(result.terminalState).toBe("BLOCKED");
    expect(result.mismatchedHashes).toEqual([
      { path: "status.json", expected: "expected", actual: "actual" },
    ]);
  });

  it("preserves explicit evidence self-hash entries without self-failing", () => {
    const result = reconcileEvidenceManifest({
      manifest: [{ path: "evidence_manifest.json", sha256: "ignored", selfHash: true }],
      actualHashes: {},
    });

    expect(result.ok).toBe(true);
    expect(result.selfHashEntries).toEqual(["evidence_manifest.json"]);
  });

  it("classifies successful commands with output as PASS without independent evidence requirement", () => {
    expect(
      classifyCommandCloseLoop({
        code: 0,
        signal: null,
        termination: "exit",
        stdout: "done\n",
      }),
    ).toEqual({
      terminalState: "PASS",
      classification: "success",
      requiresIndependentArtifactState: false,
      firstFailure: null,
    });
  });

  it("classifies exit 0 with no output as silent success requiring independent artifact state", () => {
    expect(
      classifyCommandCloseLoop({ code: 0, signal: null, termination: "exit", stdout: "" }),
    ).toEqual({
      terminalState: "PASS",
      classification: "silent-success",
      requiresIndependentArtifactState: true,
      firstFailure: null,
    });
  });

  it("classifies missing independent evidence as BLOCKED", () => {
    expect(
      classifyCommandCloseLoop({
        code: 0,
        signal: null,
        termination: "exit",
        requiredEvidenceOk: false,
      }),
    ).toMatchObject({
      terminalState: "BLOCKED",
      classification: "blocked",
      firstFailure: "required_evidence_missing_or_invalid",
    });
  });

  it("classifies stale async completion as SUPERSEDED", () => {
    expect(reconcileStaleAsyncCompletion({ taskGeneration: 1, currentGeneration: 2 })).toEqual({
      terminalState: "SUPERSEDED",
      stale: true,
      reason: "generation-superseded",
    });
  });

  it("rejects completion notices missing required terminal fields", () => {
    const validation = validateCloseLoopNotice({
      ...createNotice(),
      artifactHashes: undefined,
      rollbackReady: undefined,
    });

    expect(validation.ok).toBe(false);
    expect(validation.missingFields).toEqual(
      expect.arrayContaining(["artifactHashes", "rollbackReady"]),
    );
  });

  it("emits a direct-chat terminal PASS closeout summary when final answer is only an ack", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "M12 final accepted production stack closeout",
      status: "M12_FINAL_ACCEPTED_PRODUCTION_STACK_CLOSEOUT_PASS",
      artifact_dir:
        "sharedspace/runtime-kernel-validation/vnext-semantic-gate/m12_final_accepted_production_stack_closeout",
      failed_gates: [],
      required_files_missing: [],
      production_mutation: false,
      operator_summary: "No next action required.",
    });

    const decision = resolveCloseoutDeliveryDecision({
      payload,
      directChat: true,
      existingFinalText: "Completed — M12 closeout: PASS.",
    });

    expect(decision.action).toBe("deliver");
    if (decision.action !== "deliver") {
      throw new Error("expected delivery");
    }
    expect(decision.text).toContain("Closeout: PASS.");
    expect(decision.text).toContain("No production mutation occurred");
    expect(decision.text).toContain("status.json");
    expect(decision.text).not.toContain("Failed gates: none");
    expect(decision.payload.closeoutDelivered).toBe(true);
    expect(decision.payload.closeoutPending).toBe(false);
  });

  it("keeps explicit PASS status dominant over delivery flags, empty failed arrays, and isError false", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "FINALMILE_CLOSEOUT_APPEND_PRODUCTION_SMOKE_20260628T0915Z",
      status: "PASS",
      failedGates: [],
      requiredFilesMissing: [],
      closeoutDelivered: false,
      closeoutPending: true,
      isError: false,
      productionMutation: false,
    });

    expect(payload?.status).toBe("PASS");
    const text = formatCloseoutDeliverySummary(payload!);
    expect(text).toBe(
      "Closeout: PASS. No production mutation occurred. Evidence: status.json, summary.json, evidence_manifest.json.",
    );
    expect(text).not.toContain("FAIL");
    expect(text).not.toContain("Failed");
  });

  it("does not derive FAIL from empty failed fields, delivery flags, or isError false when status is absent", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "delivery-state-only closeout",
      failedGates: [],
      requiredFilesMissing: [],
      closeoutDelivered: false,
      closeoutPending: true,
      isError: false,
      productionMutation: false,
    });

    expect(payload?.status).toBe("UNKNOWN");
    expect(formatCloseoutDeliverySummary(payload!)).toContain("Closeout: UNKNOWN.");
  });

  it("derives FAIL from non-empty failed gates only when explicit status is absent", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "derived closeout",
      failedGates: ["health_gate_failed"],
      requiredFilesMissing: [],
      productionMutation: false,
    });

    expect(payload?.status).toBe("FAIL");
    expect(formatCloseoutDeliverySummary(payload!)).toContain("Closeout: FAIL.");
    expect(formatCloseoutDeliverySummary(payload!)).toContain("Failed gates: health_gate_failed.");
  });

  it("rejects generic operational failed status details as a closeout payload", () => {
    const payload = normalizeCloseoutDeliveryPayload({ status: "failed" });

    expect(payload).toBeUndefined();
  });

  it("extracts closeout JSON from persisted toolResult message wrappers after generic failed metadata", () => {
    const closeoutPayload = {
      title: "OBSERVER_ATTACHMENT_PRODUCTION_SMOKE_20260628T1248Z",
      status: "PASS",
      failedGates: [],
      requiredFilesMissing: [],
      productionMutation: false,
      evidenceFiles: [
        { path: "status.json" },
        { path: "summary.json" },
        { path: "evidence_manifest.json" },
      ],
      closeoutDelivered: false,
      closeoutPending: true,
    };

    const payload = extractCloseoutDeliveryPayloadFromToolResult({
      type: "message",
      message: {
        role: "toolResult",
        content: [
          {
            type: "text",
            text: `${JSON.stringify({ details: { status: "failed" }, isError: false })}\n${JSON.stringify(closeoutPayload)}\ncompleted`,
          },
        ],
        isError: false,
      },
    });

    expect(payload).toMatchObject({
      title: "OBSERVER_ATTACHMENT_PRODUCTION_SMOKE_20260628T1248Z",
      status: "PASS",
      productionMutation: false,
      evidenceFiles: [
        { path: "status.json" },
        { path: "summary.json" },
        { path: "evidence_manifest.json" },
      ],
    });
    expect(formatCloseoutDeliverySummary(payload!)).toBe(
      "Closeout: PASS. No production mutation occurred. Evidence: status.json, summary.json, evidence_manifest.json.",
    );
  });

  it("selects the strongest closeout candidate instead of first weak title-only failed metadata", () => {
    const weakOperationalMetadata = {
      title: "approval-card state",
      status: "failed",
      failedGates: [],
      requiredFilesMissing: [],
      isError: false,
    };
    const explicitCloseout = {
      title: "FINALMILE_CLOSEOUT_APPEND_PRODUCTION_SMOKE_20260628T0915Z",
      status: "PASS",
      failedGates: [],
      requiredFilesMissing: [],
      productionMutation: false,
      evidenceFiles: [
        { path: "status.json" },
        { path: "summary.json" },
        { path: "evidence_manifest.json" },
      ],
      closeoutDelivered: false,
      closeoutPending: true,
    };

    const payload = extractCloseoutDeliveryPayloadFromToolResult(
      `${JSON.stringify(weakOperationalMetadata)}\n${JSON.stringify(explicitCloseout)}`,
    );

    expect(payload).toMatchObject({
      title: "FINALMILE_CLOSEOUT_APPEND_PRODUCTION_SMOKE_20260628T0915Z",
      status: "PASS",
    });
    expect(formatCloseoutDeliverySummary(payload!)).toBe(
      "Closeout: PASS. No production mutation occurred. Evidence: status.json, summary.json, evidence_manifest.json.",
    );
  });

  it("emits a bounded direct-chat terminal FAIL closeout summary", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "M12 final accepted production stack closeout",
      status: "FAIL",
      artifact_dir: "artifact/dir",
      failed_gates: ["required_files_missing"],
      required_files_missing: ["summary.json"],
      production_mutation: false,
      operator_summary: "Blocked before trustworthy terminal PASS existed.",
    });

    const decision = resolveCloseoutDeliveryDecision({ payload, directChat: true });

    expect(decision.action).toBe("deliver");
    if (decision.action !== "deliver") {
      throw new Error("expected delivery");
    }
    expect(decision.text).toContain("Closeout: FAIL.");
    expect(decision.text).toContain("required_files_missing");
    expect(decision.text).toContain("summary.json");
    expect(decision.text.match(/Closeout: FAIL/g) ?? []).toHaveLength(1);
    expect(decision.text).not.toContain("Failed: FAIL");
  });

  it("does not count completion acknowledgement alone as closeoutDelivered", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "M12 final accepted production stack closeout",
      status: "PASS",
      artifact_dir: "artifact/dir",
    });

    expect(textContainsCloseoutSummary("Completed — M12 closeout: PASS.", payload!)).toBe(false);
  });

  it("recognizes an evidence-backed final closeout summary as delivered", () => {
    const payload = normalizeCloseoutDeliveryPayload({
      title: "M12 final accepted production stack closeout",
      status: "PASS",
      artifact_dir: "artifact/dir",
    });
    const text = formatCloseoutDeliverySummary(payload!);

    expect(textContainsCloseoutSummary(text, payload!)).toBe(true);
    expect(
      resolveCloseoutDeliveryDecision({ payload, directChat: true, existingFinalText: text }),
    ).toEqual({ action: "none", reason: "closeout_already_visible" });
  });
});
