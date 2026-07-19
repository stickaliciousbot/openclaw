import { describe, expect, it } from "vitest";
import {
  classifyRuntimeReply,
  runtimeReplyClassificationToLegacyText,
  type RuntimeReplyClassificationInput,
  type RuntimeReplyTerminal,
} from "./runtime-delivery-classification.js";

const requiredReady = (overrides: Partial<RuntimeReplyClassificationInput> = {}) => ({
  jobId: "synthetic-delivery-required-job",
  deliveryRequired: true,
  jobClass: "delivery_required" as const,
  candidatePayloadPresent: true,
  requiredAnchors: {
    closeoutAnchorPresent: true,
    terminalPayloadAnchorPresent: true,
    ledgerCompletionAnchorRequired: true,
    ledgerCompletionAnchorPresent: true,
  },
  contractValid: true,
  contractHashMatches: true,
  expired: false,
  idempotencyKey: "m25k-synthetic-idempotency-key",
  idempotencyKeyMatches: true,
  surfaceMatches: true,
  targetGrantRequired: false,
  ...overrides,
});

function expectTerminal(input: RuntimeReplyClassificationInput, terminal: RuntimeReplyTerminal) {
  const classification = classifyRuntimeReply(input);
  expect(classification.terminal).toBe(terminal);
  expect(classification.classificationSha256).toMatch(/^[a-f0-9]{64}$/);
  return classification;
}

describe("runtime reply delivery classification", () => {
  it("classifies an explicit quiet watcher success as the only legacy NO_REPLY path", () => {
    const classification = expectTerminal(
      {
        jobId: "synthetic-quiet-watcher",
        deliveryRequired: false,
        jobClass: "quiet_success",
        candidatePayloadPresent: false,
      },
      "QUIET_SUCCESS_NO_DELIVERY_REQUIRED",
    );

    expect(classification.quietSuccess).toBe(true);
    expect(classification.deliveryEligible).toBe(false);
    expect(runtimeReplyClassificationToLegacyText(classification)).toBe("NO_REPLY");
  });

  it("classifies delivery-required payload ready without converting to NO_REPLY", () => {
    const classification = expectTerminal(requiredReady(), "DELIVERY_REQUIRED_PAYLOAD_READY");
    expect(classification.quietSuccess).toBe(false);
    expect(classification.deliveryEligible).toBe(true);
    expect(runtimeReplyClassificationToLegacyText(classification)).toBeUndefined();
  });

  it("classifies delivery-required boundary allow as payload ready", () => {
    const classification = expectTerminal(
      requiredReady({ boundaryDecisionPresent: true, boundaryDecision: "allow" }),
      "BOUNDARY_ALLOWED_PAYLOAD_READY",
    );
    expect(classification.boundaryDecision).toBe("allow");
    expect(runtimeReplyClassificationToLegacyText(classification)).toBeUndefined();
  });

  it("classifies boundary hold and reject as explicit no-delivery terminals", () => {
    const hold = expectTerminal(
      requiredReady({ boundaryDecisionPresent: true, boundaryDecision: "hold" }),
      "BOUNDARY_HOLD_NO_DELIVERY",
    );
    const reject = expectTerminal(
      requiredReady({ boundaryDecisionPresent: true, boundaryDecision: "reject" }),
      "BOUNDARY_REJECT_NO_DELIVERY",
    );

    expect(runtimeReplyClassificationToLegacyText(hold)).toContain("BOUNDARY_HOLD_NO_DELIVERY");
    expect(runtimeReplyClassificationToLegacyText(reject)).toContain("BOUNDARY_REJECT_NO_DELIVERY");
  });

  it("classifies delivery-required missing payload explicitly and never as NO_REPLY", () => {
    const classification = expectTerminal(
      requiredReady({ candidatePayloadPresent: false }),
      "DELIVERY_REQUIRED_PAYLOAD_MISSING",
    );
    expect(classification.quietSuccess).toBe(false);
    expect(runtimeReplyClassificationToLegacyText(classification)).toContain(
      "DELIVERY_REQUIRED_PAYLOAD_MISSING",
    );
  });

  it("classifies each missing anchor as anchor-missing no-delivery", () => {
    for (const requiredAnchors of [
      { closeoutAnchorPresent: false, terminalPayloadAnchorPresent: true },
      { closeoutAnchorPresent: true, terminalPayloadAnchorPresent: false },
      {
        closeoutAnchorPresent: true,
        terminalPayloadAnchorPresent: true,
        ledgerCompletionAnchorRequired: true,
        ledgerCompletionAnchorPresent: false,
      },
    ]) {
      const classification = expectTerminal(
        requiredReady({ requiredAnchors }),
        "ANCHOR_MISSING_NO_DELIVERY",
      );
      expect(runtimeReplyClassificationToLegacyText(classification)).toContain(
        "ANCHOR_MISSING_NO_DELIVERY",
      );
    }
  });

  it("classifies missing required boundary decision explicitly", () => {
    const classification = expectTerminal(
      requiredReady({ boundaryHandlerRequired: true, boundaryDecisionPresent: false }),
      "BOUNDARY_DECISION_MISSING",
    );
    expect(runtimeReplyClassificationToLegacyText(classification)).toContain(
      "BOUNDARY_DECISION_MISSING",
    );
  });

  it("classifies malformed, mismatched, expired, idempotency, surface, and target-grant errors as invalid", () => {
    for (const overrides of [
      { contractValid: false },
      { contractHashMatches: false },
      { expired: true },
      { idempotencyKey: undefined },
      { idempotencyKeyMatches: false },
      { surfaceMatches: false },
      { targetGrantRequired: true, targetGrantPresent: false },
    ]) {
      const classification = expectTerminal(requiredReady(overrides), "DELIVERY_CONTRACT_INVALID");
      expect(classification.quietSuccess).toBe(false);
      expect(runtimeReplyClassificationToLegacyText(classification)).not.toBe("NO_REPLY");
    }
  });

  it("classifies duplicate suppression and delivery failure as observable non-quiet terminals", () => {
    const duplicate = expectTerminal(
      requiredReady({ duplicateDeliverySuppressed: true }),
      "DUPLICATE_DELIVERY_SUPPRESSED",
    );
    const failure = expectTerminal(requiredReady({ deliveryFailed: true }), "DELIVERY_FAILED");
    expect(runtimeReplyClassificationToLegacyText(duplicate)).toContain(
      "DUPLICATE_DELIVERY_SUPPRESSED",
    );
    expect(runtimeReplyClassificationToLegacyText(failure)).toContain("DELIVERY_FAILED");
  });

  it("fails closed for unknown jobs and quiet jobs marked delivery-required", () => {
    const unknown = expectTerminal(
      {
        jobId: "synthetic-unknown-job",
        deliveryRequired: false,
        jobClass: "unknown",
      },
      "DELIVERY_CONTRACT_INVALID",
    );
    const contradictoryQuiet = expectTerminal(
      {
        jobId: "synthetic-quiet-marked-required",
        deliveryRequired: true,
        jobClass: "quiet_success",
        candidatePayloadPresent: false,
      },
      "DELIVERY_CONTRACT_INVALID",
    );
    expect(runtimeReplyClassificationToLegacyText(unknown)).not.toBe("NO_REPLY");
    expect(runtimeReplyClassificationToLegacyText(contradictoryQuiet)).not.toBe("NO_REPLY");
  });

  it("maps M25E/M25G/M25H-shaped no-reply closeout regressions to explicit missing payload", () => {
    for (const jobId of [
      "synthetic-m25e-final-proof",
      "synthetic-m25g-final-proof",
      "synthetic-m25h-final-proof",
    ]) {
      const classification = expectTerminal(
        requiredReady({ jobId, candidatePayloadPresent: false }),
        "DELIVERY_REQUIRED_PAYLOAD_MISSING",
      );
      expect(runtimeReplyClassificationToLegacyText(classification)).not.toBe("NO_REPLY");
    }
  });

  it("keeps classification hashes stable and content-addressed", () => {
    const first = classifyRuntimeReply(requiredReady());
    const second = classifyRuntimeReply(requiredReady());
    const changed = classifyRuntimeReply(requiredReady({ jobId: "synthetic-other-job" }));
    expect(first.classificationSha256).toBe(second.classificationSha256);
    expect(first.classificationSha256).not.toBe(changed.classificationSha256);
  });
});
