import assert from "node:assert/strict";
import {
  BOUNDARY_DECISION_REASON_CODES,
  BOUNDARY_HOLD_REASON_CODES,
  BOUNDARY_REJECT_REASON_CODES,
  completeBoundaryDecisionEnvelope,
  computeBoundaryContractHash,
  computeBoundaryDecisionSha256,
  createBoundaryDecisionEvidence,
  validateBoundaryDecisionEnvelope,
  type BoundaryDecisionEnvelope,
  type BoundaryDecisionEnvelopeDraft,
  type BoundaryDecisionValidationContext,
} from "./boundary-decision-envelope.js";
import {
  classifyRuntimeReply,
  classifyRuntimeReplyWithBoundaryDecisionEnvelope,
  runtimeReplyClassificationToLegacyText,
  type RuntimeReplyClassificationInput,
} from "./runtime-delivery-classification.js";

const sha = (char: string) => char.repeat(64);

const context: BoundaryDecisionValidationContext = {
  jobId: "job_delivery_m25l_fixture",
  agentId: "agent_main_alias",
  sessionKey: "session_alias_m25l",
  callerPromptSha256: sha("a"),
  candidateSourceSha256: sha("b"),
  eventsSha256: sha("c"),
  actionsSha256: sha("d"),
  ledgerSha256: sha("e"),
  localDate: "2026-07-19",
};

const requiredReady = (
  overrides: Partial<RuntimeReplyClassificationInput> = {},
): RuntimeReplyClassificationInput => ({
  jobId: context.jobId,
  deliveryRequired: true,
  jobClass: "delivery_required",
  candidatePayloadPresent: true,
  requiredAnchors: {
    closeoutAnchorPresent: true,
    terminalPayloadAnchorPresent: true,
    ledgerCompletionAnchorRequired: true,
    ledgerCompletionAnchorPresent: true,
  },
  boundaryHandlerRequired: true,
  contractValid: true,
  contractHashMatches: true,
  idempotencyKey: "m25l-synthetic-idempotency-key",
  idempotencyKeyMatches: true,
  surfaceMatches: true,
  targetGrantRequired: false,
  ...overrides,
});

function draft(
  overrides: Partial<BoundaryDecisionEnvelopeDraft> = {},
): BoundaryDecisionEnvelopeDraft {
  return {
    schema: "stickbot.boundary_decision.v1",
    schemaVersion: "1.0.0",
    decision: "allow",
    reasonCode: "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED",
    jobId: context.jobId,
    agentId: context.agentId,
    sessionKey: context.sessionKey,
    callerPromptSha256: context.callerPromptSha256,
    candidateSourceSha256: context.candidateSourceSha256,
    eventsSha256: context.eventsSha256,
    actionsSha256: context.actionsSha256,
    ledgerSha256: context.ledgerSha256,
    localDate: context.localDate,
    sanitizedDiagnostic: "synthetic boundary decision fixture",
    deliveryAllowed: true,
    ...overrides,
  };
}

function env(overrides: Partial<BoundaryDecisionEnvelopeDraft> = {}) {
  return completeBoundaryDecisionEnvelope(draft(overrides));
}

function expectValid(envelope: BoundaryDecisionEnvelope) {
  const validation = validateBoundaryDecisionEnvelope(envelope, context);
  assert.equal(validation.terminal, "BOUNDARY_DECISION_VALID");
  assert.equal(validation.valid, true);
  return validation;
}

function expectInvalid(value: unknown, label: string) {
  const validation = validateBoundaryDecisionEnvelope(value, context);
  assert.equal(validation.terminal, "BOUNDARY_DECISION_INVALID", label);
  assert.equal(validation.valid, false, label);
  return validation;
}

const allow = env();
expectValid(allow);
assert.equal(allow.decisionSha256, computeBoundaryDecisionSha256(allow));
assert.equal(allow.contractHash, computeBoundaryContractHash(allow));

const reordered = JSON.parse(
  JSON.stringify(allow, Object.keys(allow).reverse()),
) as BoundaryDecisionEnvelope;
assert.equal(
  computeBoundaryDecisionSha256(reordered),
  allow.decisionSha256,
  "key order must not change decision hash",
);
assert.equal(
  computeBoundaryContractHash(reordered),
  allow.contractHash,
  "key order must not change contract hash",
);

for (const [key, value] of [
  ["jobId", "job_other"],
  ["agentId", "agent_other"],
  ["sessionKey", "session_other"],
  ["callerPromptSha256", sha("1")],
  ["candidateSourceSha256", sha("2")],
  ["eventsSha256", sha("3")],
  ["actionsSha256", sha("4")],
  ["ledgerSha256", sha("5")],
  ["localDate", "2026-07-20"],
  ["sanitizedDiagnostic", "changed synthetic diagnostic"],
  ["decision", "hold"],
] as const) {
  const changed = completeBoundaryDecisionEnvelope(
    draft({ [key]: value } as Partial<BoundaryDecisionEnvelopeDraft>),
  );
  assert.notEqual(changed.decisionSha256, allow.decisionSha256, `${key} must change decision hash`);
}

const allowClassification = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
  ...requiredReady(),
  boundaryDecisionEnvelope: allow,
  boundaryDecisionContext: context,
});
assert.equal(allowClassification.terminal, "BOUNDARY_ALLOWED_PAYLOAD_READY");
assert.equal(allowClassification.reasonCode, "BOUNDARY_MATCH_ALLOW_DELIVERY_REQUIRED");
assert.equal(allowClassification.deliveryEligible, true);
assert.equal(runtimeReplyClassificationToLegacyText(allowClassification), undefined);

const hold = env({ decision: "hold", reasonCode: "BOUNDARY_UNARMED_HOLD", deliveryAllowed: false });
const holdClassification = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
  ...requiredReady(),
  boundaryDecisionEnvelope: hold,
  boundaryDecisionContext: context,
});
assert.equal(holdClassification.terminal, "BOUNDARY_HOLD_NO_DELIVERY");
assert.equal(holdClassification.reasonCode, "BOUNDARY_UNARMED_HOLD");
assert.equal(holdClassification.deliveryEligible, false);
assert.notEqual(runtimeReplyClassificationToLegacyText(holdClassification), "NO_REPLY");

const reject = env({
  decision: "reject",
  reasonCode: "BOUNDARY_PRIVACY_SCAN_FAILED_REJECT",
  deliveryAllowed: false,
});
const rejectClassification = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
  ...requiredReady(),
  boundaryDecisionEnvelope: reject,
  boundaryDecisionContext: context,
});
assert.equal(rejectClassification.terminal, "BOUNDARY_REJECT_NO_DELIVERY");
assert.equal(rejectClassification.reasonCode, "BOUNDARY_PRIVACY_SCAN_FAILED_REJECT");
assert.equal(rejectClassification.deliveryEligible, false);
assert.notEqual(runtimeReplyClassificationToLegacyText(rejectClassification), "NO_REPLY");

const missingEnvelope = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
  ...requiredReady(),
  boundaryDecisionContext: context,
});
assert.equal(missingEnvelope.terminal, "BOUNDARY_DECISION_MISSING");
assert.notEqual(runtimeReplyClassificationToLegacyText(missingEnvelope), "NO_REPLY");

for (const broken of [
  { ...allow, decision: "maybe" },
  { ...allow, deliveryAllowed: false },
  { ...hold, deliveryAllowed: true },
  { ...reject, deliveryAllowed: true },
  { ...allow, reasonCode: undefined },
  { ...allow, callerPromptSha256: "not-sha" },
  { ...allow, decisionSha256: sha("f") },
  { ...allow, contractHash: sha("f") },
  { ...allow, jobId: "job_other" },
  { ...allow, agentId: "agent_other" },
  { ...allow, sessionKey: "session_other" },
  { ...allow, callerPromptSha256: sha("1") },
  { ...allow, candidateSourceSha256: sha("2") },
  { ...allow, eventsSha256: sha("3") },
  { ...allow, actionsSha256: sha("4") },
  { ...allow, ledgerSha256: sha("5") },
  { ...allow, localDate: "2026-07-20" },
  { ...allow, schema: "stickbot.boundary_decision.v2" },
  { ...allow, jobId: "<RAW_TELEGRAM_TARGET_ID_FORBIDDEN>" },
  { ...allow, sanitizedDiagnostic: "<SECRET_LIKE_DIAGNOSTIC_FORBIDDEN>" },
  { ...allow, sanitizedDiagnostic: "x".repeat(180) },
  { ...allow, reasonCode: "BOUNDARY_UNARMED_HOLD" },
]) {
  expectInvalid(broken, JSON.stringify(broken).slice(0, 90));
}

const duplicateValidation = validateBoundaryDecisionEnvelope(allow, {
  ...context,
  seenDecisionSha256: new Set([allow.decisionSha256]),
});
assert.equal(duplicateValidation.terminal, "BOUNDARY_DECISION_INVALID");
assert(duplicateValidation.errors.includes("DUPLICATE_REPLAY"));

for (const reasonCode of BOUNDARY_HOLD_REASON_CODES) {
  expectValid(env({ decision: "hold", reasonCode, deliveryAllowed: false }));
}
for (const reasonCode of BOUNDARY_REJECT_REASON_CODES) {
  expectValid(env({ decision: "reject", reasonCode, deliveryAllowed: false }));
}
assert.equal(BOUNDARY_DECISION_REASON_CODES.length, 23);

const invalidEnvelopeClassification = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
  ...requiredReady(),
  boundaryDecisionEnvelope: { ...allow, contractHash: sha("f") },
  boundaryDecisionContext: context,
});
assert.equal(invalidEnvelopeClassification.terminal, "DELIVERY_CONTRACT_INVALID");
assert.notEqual(runtimeReplyClassificationToLegacyText(invalidEnvelopeClassification), "NO_REPLY");

const quiet = classifyRuntimeReply({
  jobId: "synthetic-quiet-watcher",
  deliveryRequired: false,
  jobClass: "quiet_success",
});
assert.equal(quiet.terminal, "QUIET_SUCCESS_NO_DELIVERY_REQUIRED");
assert.equal(runtimeReplyClassificationToLegacyText(quiet), "NO_REPLY");

const noPayloadWithAllow = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
  ...requiredReady({ candidatePayloadPresent: false }),
  boundaryDecisionEnvelope: allow,
  boundaryDecisionContext: context,
});
assert.equal(noPayloadWithAllow.terminal, "DELIVERY_REQUIRED_PAYLOAD_MISSING");
assert.notEqual(runtimeReplyClassificationToLegacyText(noPayloadWithAllow), "NO_REPLY");

for (const regression of [
  env({
    decision: "hold",
    reasonCode: "BOUNDARY_EVENTS_HASH_MISMATCH_HOLD",
    deliveryAllowed: false,
  }),
  env({ decision: "hold", reasonCode: "BOUNDARY_PAYLOAD_MISSING_HOLD", deliveryAllowed: false }),
  env({
    decision: "reject",
    reasonCode: "BOUNDARY_CONTRACT_HASH_INVALID_REJECT",
    deliveryAllowed: false,
  }),
]) {
  const classification = classifyRuntimeReplyWithBoundaryDecisionEnvelope({
    ...requiredReady({ candidatePayloadPresent: regression.decision === "hold" ? false : true }),
    boundaryDecisionEnvelope: regression,
    boundaryDecisionContext: context,
  });
  assert.notEqual(classification.terminal, "QUIET_SUCCESS_NO_DELIVERY_REQUIRED");
  assert.notEqual(runtimeReplyClassificationToLegacyText(classification), "NO_REPLY");
}

const evidence = createBoundaryDecisionEvidence(hold, context, "2026-07-19T19:40:00+10:00");
assert.equal(evidence.validationTerminal, "BOUNDARY_DECISION_VALID");
assert.equal(evidence.privateRawScan, "PASS");
assert.equal(evidence.deliveryAllowed, false);
assert.equal(evidence.bindingMatches.jobId, true);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      reasonCodeCount: BOUNDARY_DECISION_REASON_CODES.length,
      positiveFixtures: 11,
      negativeFixtures: 22,
      regressionFixtures: 6,
    },
    null,
    2,
  ),
);
