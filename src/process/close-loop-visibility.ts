// Close-loop visibility helpers classify terminal outcomes without expanding runtime authority.
import crypto from "node:crypto";

export type CloseLoopTerminalState =
  | "PASS"
  | "FAIL"
  | "BLOCKED"
  | "ABORTED"
  | "HOLD"
  | "SUPERSEDED";

export type CloseoutDeliveryStatus = CloseLoopTerminalState | "SKIPPED" | "UNKNOWN";

export const CLOSE_LOOP_TERMINAL_STATES: readonly CloseLoopTerminalState[] = [
  "PASS",
  "FAIL",
  "BLOCKED",
  "ABORTED",
  "HOLD",
  "SUPERSEDED",
] as const;

const CLOSEOUT_DELIVERY_STATUSES: readonly CloseoutDeliveryStatus[] = [
  "PASS",
  "FAIL",
  "BLOCKED",
  "ABORTED",
  "HOLD",
  "SUPERSEDED",
  "SKIPPED",
  "UNKNOWN",
] as const;

export type MutationBoundaryReadback = {
  cacheEnabled: boolean;
  artifactMemoryPromoted: boolean;
  runtimeGatewayRouteMutation: boolean;
  externalSchedulingExecution: boolean;
  providerModelAuthoritativeCalls: number;
  directProviderBypass: number;
  newExpansionStarted: boolean;
};

export type TerminalArtifactState = {
  status: CloseLoopTerminalState | string;
  artifactDir: string;
  requiredFilesMissing?: string[];
  failedGates?: string[];
  firstFailure?: string | null;
  rollbackReady?: boolean;
  mutationSentinelsClean?: boolean;
  artifactHashes?: Record<string, string>;
};

export type CloseLoopNoticeInput = TerminalArtifactState & {
  completedCountOrBound: string | number;
  mutationBoundaryReadback: MutationBoundaryReadback;
  recommendedNextAction: string;
};

export type CloseLoopNoticeValidation = {
  ok: boolean;
  missingFields: string[];
  invalidFields: string[];
  terminalState: CloseLoopTerminalState | null;
};

export type RequiredFileReconciliation = {
  ok: boolean;
  terminalState: CloseLoopTerminalState;
  missing: string[];
};

export type GeneratorRequiredFileReconciliation = RequiredFileReconciliation & {
  deferredTerminalFiles: string[];
};

export type EvidenceManifestEntry = {
  path: string;
  sha256?: string;
  required?: boolean;
  selfHash?: boolean;
};

export type EvidenceManifestReconciliation = {
  ok: boolean;
  terminalState: CloseLoopTerminalState;
  missingEntries: string[];
  mismatchedHashes: Array<{ path: string; expected: string; actual: string | null }>;
  selfHashEntries: string[];
};

export type CommandCloseLoopClassification = {
  terminalState: CloseLoopTerminalState;
  classification: "success" | "silent-success" | "failure" | "timeout" | "signal" | "blocked";
  requiresIndependentArtifactState: boolean;
  firstFailure: string | null;
};

export type StaleAsyncReconciliation = {
  terminalState: CloseLoopTerminalState;
  stale: boolean;
  reason: "current-generation" | "generation-superseded" | "artifact-superseded";
};

export type CloseoutBoundaryReadback = {
  changed?: string[];
  notChanged?: string[];
};

export type CloseoutEvidenceFile = {
  path: string;
  sha256?: string;
};

export type CloseoutDeliveryPayload = {
  title: string;
  status: CloseoutDeliveryStatus;
  artifactDir?: string;
  failedGates: string[];
  requiredFilesMissing: string[];
  evidenceFiles: CloseoutEvidenceFile[];
  productionMutation: boolean;
  boundary: CloseoutBoundaryReadback;
  operatorSummary: string;
  closeoutDelivered: boolean;
  closeoutPending: boolean;
};

export type CloseoutDeliveryDecision =
  | { action: "deliver"; payload: CloseoutDeliveryPayload; text: string }
  | { action: "suppress"; reason: string; payload?: CloseoutDeliveryPayload }
  | { action: "none"; reason: string };

export function isCloseLoopTerminalState(value: unknown): value is CloseLoopTerminalState {
  return (
    typeof value === "string" &&
    CLOSE_LOOP_TERMINAL_STATES.includes(value as CloseLoopTerminalState)
  );
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function readStringField(record: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return undefined;
}

function readBooleanField(record: Record<string, unknown>, ...keys: string[]): boolean | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "boolean") {
      return value;
    }
  }
  return undefined;
}

function readStringArrayField(record: Record<string, unknown>, ...keys: string[]): string[] {
  for (const key of keys) {
    const value = record[key];
    if (Array.isArray(value)) {
      return value
        .filter((entry): entry is string => typeof entry === "string" && Boolean(entry.trim()))
        .map((entry) => entry.trim());
    }
  }
  return [];
}

function normalizeStatusToken(raw: unknown): CloseLoopTerminalState | undefined {
  if (isCloseLoopTerminalState(raw)) {
    return raw;
  }
  if (typeof raw !== "string") {
    return undefined;
  }
  const upper = raw.toUpperCase();
  if (upper.includes("BLOCKED")) {
    return "BLOCKED";
  }
  if (upper.includes("ABORT")) {
    return "ABORTED";
  }
  if (upper.includes("FAIL")) {
    return "FAIL";
  }
  if (upper.includes("HOLD")) {
    return "HOLD";
  }
  if (upper.includes("SUPERSEDED")) {
    return "SUPERSEDED";
  }
  if (upper.includes("PASS")) {
    return "PASS";
  }
  return undefined;
}

function normalizeExplicitCloseoutStatus(raw: unknown): CloseoutDeliveryStatus | undefined {
  if (typeof raw !== "string") {
    return undefined;
  }
  const normalized = raw
    .trim()
    .toUpperCase()
    .replace(/[\s-]+/g, "_");
  const exact = CLOSEOUT_DELIVERY_STATUSES.find((status) => normalized === status);
  if (exact) {
    return exact;
  }
  for (const status of CLOSEOUT_DELIVERY_STATUSES) {
    if (normalized.endsWith(`_${status}`)) {
      return status;
    }
  }
  return undefined;
}

function deriveCloseoutStatus(
  candidate: Record<string, unknown>,
): CloseoutDeliveryStatus | undefined {
  const explicitStatus = normalizeExplicitCloseoutStatus(
    readStringField(candidate, "status", "terminalState", "terminal_state"),
  );
  if (explicitStatus) {
    return explicitStatus;
  }
  if (readStringArrayField(candidate, "failedGates", "failed_gates").length > 0) {
    return "FAIL";
  }
  if (
    readStringArrayField(candidate, "requiredFilesMissing", "required_files_missing").length > 0
  ) {
    return "FAIL";
  }
  if (candidate.isError === true || candidate.is_error === true) {
    return "FAIL";
  }
  const terminalError = readStringField(candidate, "terminalError", "terminal_error", "error");
  if (terminalError) {
    return "FAIL";
  }
  if (hasCloseoutShape(candidate)) {
    return "UNKNOWN";
  }
  return undefined;
}

function titleFromStatus(status: string): string {
  return status
    .replace(/_PASS$|_FAIL$|_BLOCKED$|_ABORTED$|_HOLD$|_SUPERSEDED$|_SKIPPED$|_UNKNOWN$/i, "")
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1).toLowerCase()}`)
    .join(" ");
}

function normalizeEvidenceFiles(
  record: Record<string, unknown>,
  artifactDir?: string,
): CloseoutEvidenceFile[] {
  const rawEvidence = record.evidenceFiles ?? record.evidence_files;
  if (Array.isArray(rawEvidence)) {
    return rawEvidence.flatMap((entry): CloseoutEvidenceFile[] => {
      if (typeof entry === "string" && entry.trim()) {
        return [{ path: entry.trim() }];
      }
      const rec = asRecord(entry);
      if (!rec) {
        return [];
      }
      const path = readStringField(rec, "path", "file");
      if (!path) {
        return [];
      }
      const sha256 = readStringField(rec, "sha256", "hash");
      return [{ path, ...(sha256 ? { sha256 } : {}) }];
    });
  }
  const inferred = ["status.json", "summary.json", "evidence_manifest.json"].map((file) => ({
    path: artifactDir ? `${artifactDir.replace(/\/$/, "")}/${file}` : file,
  }));
  return inferred;
}

function normalizeBoundary(record: Record<string, unknown>): CloseoutBoundaryReadback {
  let boundary = asRecord(record.boundary);
  if (!boundary) {
    boundary = asRecord(record.boundary_readback);
  }
  const boundaryRecord: Record<string, unknown> = boundary ?? {};
  return {
    changed: readStringArrayField(boundaryRecord, "changed"),
    notChanged: readStringArrayField(boundaryRecord, "notChanged", "not_changed"),
  };
}

function hasCloseoutShape(record: Record<string, unknown>): boolean {
  return Boolean(
    readStringField(record, "title") ||
    readStringField(record, "artifactDir", "artifact_dir") ||
    Array.isArray(record.evidenceFiles) ||
    Array.isArray(record.evidence_files) ||
    Array.isArray(record.failedGates) ||
    Array.isArray(record.failed_gates) ||
    Array.isArray(record.requiredFilesMissing) ||
    Array.isArray(record.required_files_missing) ||
    Object.prototype.hasOwnProperty.call(record, "productionMutation") ||
    Object.prototype.hasOwnProperty.call(record, "production_mutation") ||
    Object.prototype.hasOwnProperty.call(record, "operatorSummary") ||
    Object.prototype.hasOwnProperty.call(record, "operator_summary"),
  );
}

export function normalizeCloseoutDeliveryPayload(
  raw: unknown,
): CloseoutDeliveryPayload | undefined {
  const root = asRecord(raw);
  if (!root) {
    return undefined;
  }
  const candidate: Record<string, unknown> =
    asRecord(root.closeoutPayload) ??
    asRecord(root.closeout_payload) ??
    asRecord(root.closeout) ??
    root;
  if (!hasCloseoutShape(candidate)) {
    return undefined;
  }
  const rawStatus = readStringField(candidate, "status", "terminalState", "terminal_state");
  const status = deriveCloseoutStatus(candidate);
  if (!status) {
    return undefined;
  }
  const artifactDir = readStringField(candidate, "artifactDir", "artifact_dir");
  const title =
    readStringField(candidate, "title") ??
    (rawStatus ? titleFromStatus(rawStatus) : "Run closeout");
  const failedGates = readStringArrayField(candidate, "failedGates", "failed_gates");
  const requiredFilesMissing = readStringArrayField(
    candidate,
    "requiredFilesMissing",
    "required_files_missing",
  );
  const productionMutation =
    readBooleanField(candidate, "productionMutation", "production_mutation") ?? false;
  const evidenceFiles = normalizeEvidenceFiles(candidate, artifactDir);
  const boundary = normalizeBoundary(candidate);
  const explicitOperatorSummary = readStringField(
    candidate,
    "operatorSummary",
    "operator_summary",
    "summary",
  );
  const operatorSummary =
    explicitOperatorSummary && explicitOperatorSummary !== `${title}: ${status}.`
      ? explicitOperatorSummary
      : "";
  const closeoutDelivered =
    readBooleanField(candidate, "closeoutDelivered", "closeout_delivered") ?? false;
  const closeoutPending =
    readBooleanField(candidate, "closeoutPending", "closeout_pending") ?? !closeoutDelivered;

  return {
    title,
    status,
    ...(artifactDir ? { artifactDir } : {}),
    failedGates,
    requiredFilesMissing,
    evidenceFiles,
    productionMutation,
    boundary,
    operatorSummary,
    closeoutDelivered,
    closeoutPending,
  };
}

function parseJsonObject(text: string): Record<string, unknown> | undefined {
  try {
    const parsed = JSON.parse(text);
    return asRecord(parsed);
  } catch {
    return undefined;
  }
}

export function* parseCloseoutJsonObjectsFromText(
  text: string,
): Generator<Record<string, unknown>> {
  const trimmed = text.trim();
  const direct = parseJsonObject(trimmed);
  if (direct) {
    yield direct;
  }

  for (let start = trimmed.indexOf("{"); start >= 0; start = trimmed.indexOf("{", start + 1)) {
    let depth = 0;
    let inString = false;
    let escaped = false;
    for (let i = start; i < trimmed.length; i += 1) {
      const ch = trimmed[i];
      if (inString) {
        if (escaped) {
          escaped = false;
        } else if (ch === "\\") {
          escaped = true;
        } else if (ch === '"') {
          inString = false;
        }
        continue;
      }
      if (ch === '"') {
        inString = true;
        continue;
      }
      if (ch === "{") {
        depth += 1;
        continue;
      }
      if (ch !== "}") {
        continue;
      }
      depth -= 1;
      if (depth !== 0) {
        continue;
      }
      const parsed = parseJsonObject(trimmed.slice(start, i + 1));
      if (parsed) {
        yield parsed;
      }
      break;
    }
  }
}

function closeoutCandidateRecord(raw: unknown): Record<string, unknown> | undefined {
  const root = asRecord(raw);
  if (!root) {
    return undefined;
  }
  return (
    asRecord(root.closeoutPayload) ??
    asRecord(root.closeout_payload) ??
    asRecord(root.closeout) ??
    root
  );
}

function hasStrongCloseoutFields(record: Record<string, unknown>): boolean {
  return Boolean(
    readStringField(record, "artifactDir", "artifact_dir") ||
    Array.isArray(record.evidenceFiles) ||
    Array.isArray(record.evidence_files) ||
    readStringArrayField(record, "failedGates", "failed_gates").length > 0 ||
    readStringArrayField(record, "requiredFilesMissing", "required_files_missing").length > 0 ||
    Object.prototype.hasOwnProperty.call(record, "productionMutation") ||
    Object.prototype.hasOwnProperty.call(record, "production_mutation") ||
    Object.prototype.hasOwnProperty.call(record, "operatorSummary") ||
    Object.prototype.hasOwnProperty.call(record, "operator_summary") ||
    Object.prototype.hasOwnProperty.call(record, "closeoutDelivered") ||
    Object.prototype.hasOwnProperty.call(record, "closeout_delivered") ||
    Object.prototype.hasOwnProperty.call(record, "closeoutPending") ||
    Object.prototype.hasOwnProperty.call(record, "closeout_pending") ||
    asRecord(record.boundary) ||
    asRecord(record.boundary_readback),
  );
}

function hasDerivedCloseoutFailure(record: Record<string, unknown>): boolean {
  return Boolean(
    readStringArrayField(record, "failedGates", "failed_gates").length > 0 ||
    readStringArrayField(record, "requiredFilesMissing", "required_files_missing").length > 0 ||
    record.isError === true ||
    record.is_error === true ||
    readStringField(record, "terminalError", "terminal_error", "error"),
  );
}

function closeoutCandidateStrength(raw: unknown, payload: CloseoutDeliveryPayload): number {
  const candidate = closeoutCandidateRecord(raw);
  if (!candidate) {
    return 0;
  }
  const explicitStatus = normalizeExplicitCloseoutStatus(
    readStringField(candidate, "status", "terminalState", "terminal_state"),
  );
  const strongFields = hasStrongCloseoutFields(candidate);
  if (explicitStatus && explicitStatus !== "UNKNOWN") {
    return 400;
  }
  if (explicitStatus === "UNKNOWN" && strongFields) {
    return 300;
  }
  if (!explicitStatus && payload.status === "FAIL" && hasDerivedCloseoutFailure(candidate)) {
    return 200;
  }
  if (payload.status === "UNKNOWN" && strongFields) {
    return 150;
  }
  return 10;
}

function selectStrongestCloseoutDeliveryPayload(
  candidates: Array<{ payload: CloseoutDeliveryPayload; strength: number }>,
): CloseoutDeliveryPayload | undefined {
  let selected: { payload: CloseoutDeliveryPayload; strength: number } | undefined;
  for (const candidate of candidates) {
    if (!selected || candidate.strength > selected.strength) {
      selected = candidate;
    }
  }
  return selected?.payload;
}

function collectCloseoutDeliveryPayloadCandidate(
  candidates: Array<{ payload: CloseoutDeliveryPayload; strength: number }>,
  raw: unknown,
): void {
  const payload = normalizeCloseoutDeliveryPayload(raw);
  if (!payload) {
    return;
  }
  candidates.push({ payload, strength: closeoutCandidateStrength(raw, payload) });
}

export function extractCloseoutDeliveryPayloadFromText(
  text: string,
): CloseoutDeliveryPayload | undefined {
  const candidates: Array<{ payload: CloseoutDeliveryPayload; strength: number }> = [];
  for (const parsed of parseCloseoutJsonObjectsFromText(text)) {
    collectCloseoutDeliveryPayloadCandidate(candidates, parsed);
  }
  return selectStrongestCloseoutDeliveryPayload(candidates);
}

function collectCloseoutDeliveryPayloadCandidatesFromToolResult(
  result: unknown,
  candidates: Array<{ payload: CloseoutDeliveryPayload; strength: number }>,
  seen = new Set<Record<string, unknown>>(),
): void {
  if (typeof result === "string") {
    for (const parsed of parseCloseoutJsonObjectsFromText(result)) {
      collectCloseoutDeliveryPayloadCandidate(candidates, parsed);
    }
    return;
  }
  const root = asRecord(result);
  if (!root || seen.has(root)) {
    return;
  }
  seen.add(root);
  collectCloseoutDeliveryPayloadCandidate(candidates, root);
  if (root.details) {
    collectCloseoutDeliveryPayloadCandidate(candidates, root.details);
  }
  if (root.result !== result) {
    collectCloseoutDeliveryPayloadCandidatesFromToolResult(root.result, candidates, seen);
  }
  if (root.message !== result) {
    collectCloseoutDeliveryPayloadCandidatesFromToolResult(root.message, candidates, seen);
  }
  const content = root.content;
  if (!Array.isArray(content)) {
    return;
  }
  for (const entry of content) {
    const record = asRecord(entry);
    const entryText = typeof record?.text === "string" ? record.text.trim() : "";
    if (entryText) {
      collectCloseoutDeliveryPayloadCandidatesFromToolResult(entryText, candidates, seen);
    }
  }
}

export function extractCloseoutDeliveryPayloadFromToolResult(
  result: unknown,
): CloseoutDeliveryPayload | undefined {
  const candidates: Array<{ payload: CloseoutDeliveryPayload; strength: number }> = [];
  collectCloseoutDeliveryPayloadCandidatesFromToolResult(result, candidates);
  return selectStrongestCloseoutDeliveryPayload(candidates);
}

export function formatCloseoutDeliverySummary(payload: CloseoutDeliveryPayload): string {
  const mutationText = payload.productionMutation
    ? "Production mutation occurred."
    : "No production mutation occurred.";
  const evidence = payload.evidenceFiles
    .map((entry) => entry.path)
    .filter(Boolean)
    .join(", ");
  const evidenceText = evidence ? ` Evidence: ${evidence}.` : "";
  const failureText =
    payload.status === "FAIL"
      ? ` Failed gates: ${payload.failedGates.length ? payload.failedGates.join(", ") : "none"}. Required files missing: ${payload.requiredFilesMissing.length ? payload.requiredFilesMissing.join(", ") : "none"}.`
      : "";
  const operatorSummary =
    payload.operatorSummary && !payload.operatorSummary.includes(`Closeout: ${payload.status}.`)
      ? ` ${payload.operatorSummary}`
      : "";
  return `Closeout: ${payload.status}. ${mutationText}${failureText}${evidenceText}${operatorSummary}`
    .replace(/\s+/g, " ")
    .trim();
}

export function textContainsCloseoutSummary(
  text: string | undefined,
  payload: CloseoutDeliveryPayload,
): boolean {
  const normalized = (text ?? "").toLowerCase();
  if (!normalized.trim()) {
    return false;
  }
  const title = payload.title.toLowerCase();
  const artifact = payload.artifactDir?.toLowerCase();
  const hasStatus = normalized.includes(payload.status.toLowerCase());
  const hasCloseoutPrefix = normalized.includes(`closeout: ${payload.status.toLowerCase()}`);
  const hasTitle = title ? normalized.includes(title) : false;
  const hasArtifact = artifact ? normalized.includes(artifact) : false;
  const hasEvidence = payload.evidenceFiles.some((entry) =>
    normalized.includes(entry.path.toLowerCase()),
  );
  return (
    hasStatus &&
    (hasCloseoutPrefix || hasTitle || hasArtifact) &&
    (hasEvidence || normalized.includes("evidence"))
  );
}

export function resolveCloseoutDeliveryDecision(params: {
  payload?: CloseoutDeliveryPayload;
  directChat: boolean;
  inboundEventKind?: string;
  sendPolicyDenied?: boolean;
  messageToolOnly?: boolean;
  existingFinalText?: string;
}): CloseoutDeliveryDecision {
  if (!params.payload) {
    return { action: "none", reason: "no_terminal_closeout_payload" };
  }
  if (!params.directChat) {
    return { action: "suppress", reason: "not_direct_chat", payload: params.payload };
  }
  if (params.inboundEventKind === "room_event") {
    return { action: "suppress", reason: "room_event", payload: params.payload };
  }
  if (params.sendPolicyDenied) {
    return { action: "suppress", reason: "sendPolicy: deny", payload: params.payload };
  }
  if (params.messageToolOnly) {
    return {
      action: "suppress",
      reason: "sourceReplyDeliveryMode: message_tool_only",
      payload: params.payload,
    };
  }
  if (textContainsCloseoutSummary(params.existingFinalText, params.payload)) {
    return {
      action: "none",
      reason: "closeout_already_visible",
    };
  }
  return {
    action: "deliver",
    payload: {
      ...params.payload,
      closeoutDelivered: true,
      closeoutPending: false,
    },
    text: formatCloseoutDeliverySummary({
      ...params.payload,
      closeoutDelivered: true,
      closeoutPending: false,
    }),
  };
}

function hasOwnValue(record: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(record, key) && record[key] !== undefined;
}

export function validateCloseLoopNotice(
  input: Partial<CloseLoopNoticeInput>,
): CloseLoopNoticeValidation {
  const record = input as Record<string, unknown>;
  const requiredFields = [
    "status",
    "artifactDir",
    "failedGates",
    "firstFailure",
    "completedCountOrBound",
    "mutationBoundaryReadback",
    "rollbackReady",
    "artifactHashes",
    "recommendedNextAction",
  ];
  const missingFields = requiredFields.filter((field) => !hasOwnValue(record, field));
  const invalidFields: string[] = [];
  const terminalState = isCloseLoopTerminalState(input.status) ? input.status : null;

  if (!terminalState && hasOwnValue(record, "status")) {
    invalidFields.push("status");
  }
  if (typeof input.artifactDir !== "string" || input.artifactDir.trim() === "") {
    invalidFields.push("artifactDir");
  }
  if (input.failedGates !== undefined && !Array.isArray(input.failedGates)) {
    invalidFields.push("failedGates");
  }
  if (
    input.artifactHashes !== undefined &&
    (typeof input.artifactHashes !== "object" ||
      input.artifactHashes === null ||
      Array.isArray(input.artifactHashes))
  ) {
    invalidFields.push("artifactHashes");
  }
  if (input.rollbackReady !== undefined && typeof input.rollbackReady !== "boolean") {
    invalidFields.push("rollbackReady");
  }
  if (input.mutationBoundaryReadback !== undefined) {
    const readback = input.mutationBoundaryReadback as Partial<MutationBoundaryReadback>;
    const booleanFields: Array<keyof MutationBoundaryReadback> = [
      "cacheEnabled",
      "artifactMemoryPromoted",
      "runtimeGatewayRouteMutation",
      "externalSchedulingExecution",
      "newExpansionStarted",
    ];
    for (const field of booleanFields) {
      if (typeof readback[field] !== "boolean") {
        invalidFields.push(`mutationBoundaryReadback.${field}`);
      }
    }
    for (const field of ["providerModelAuthoritativeCalls", "directProviderBypass"] as const) {
      if (typeof readback[field] !== "number" || !Number.isFinite(readback[field] ?? Number.NaN)) {
        invalidFields.push(`mutationBoundaryReadback.${field}`);
      }
    }
  }

  return {
    ok: missingFields.length === 0 && invalidFields.length === 0,
    missingFields,
    invalidFields,
    terminalState,
  };
}

export function formatCloseLoopNotice(input: CloseLoopNoticeInput): string {
  const validation = validateCloseLoopNotice(input);
  if (!validation.ok || !validation.terminalState) {
    const fields = [...validation.missingFields, ...validation.invalidFields].join(", ");
    throw new Error(`Invalid close-loop notice: ${fields}`);
  }
  return `${validation.terminalState} ${JSON.stringify({
    status: input.status,
    artifact_dir: input.artifactDir,
    failed_gates: input.failedGates ?? [],
    first_failure: input.firstFailure ?? null,
    completed_count_or_bound: input.completedCountOrBound,
    mutation_boundary_readback: input.mutationBoundaryReadback,
    rollback_readiness: input.rollbackReady,
    artifact_hashes: input.artifactHashes ?? {},
    recommended_next_action: input.recommendedNextAction,
  })}`;
}

export function reconcileRequiredFiles(params: {
  requiredFiles: string[];
  presentFiles: Iterable<string>;
}): RequiredFileReconciliation {
  const present = new Set(params.presentFiles);
  const missing = params.requiredFiles.filter((file) => !present.has(file));
  return {
    ok: missing.length === 0,
    terminalState: missing.length === 0 ? "PASS" : "BLOCKED",
    missing,
  };
}

export function reconcileGeneratorPreWriteRequiredFiles(params: {
  requiredFiles: string[];
  presentFiles: Iterable<string>;
  terminalFiles?: string[];
}): GeneratorRequiredFileReconciliation {
  const terminalFiles = params.terminalFiles ?? ["status.json", "summary.json"];
  const terminal = new Set(terminalFiles);
  const present = new Set(params.presentFiles);
  const missing = params.requiredFiles.filter((file) => !terminal.has(file) && !present.has(file));
  return {
    ok: missing.length === 0,
    terminalState: missing.length === 0 ? "PASS" : "BLOCKED",
    missing,
    deferredTerminalFiles: params.requiredFiles.filter((file) => terminal.has(file)),
  };
}

export function finalizeGeneratorRequiredFiles(params: {
  terminalStatus: unknown;
  requiredFiles: string[];
  presentFiles: Iterable<string>;
}): RequiredFileReconciliation {
  const status = normalizeStatusToken(params.terminalStatus);
  if (status !== "PASS") {
    return {
      ok: false,
      terminalState: status ?? "BLOCKED",
      missing: [],
    };
  }
  return reconcileRequiredFiles({
    requiredFiles: params.requiredFiles,
    presentFiles: params.presentFiles,
  });
}

export function reconcileEvidenceManifest(params: {
  manifest: EvidenceManifestEntry[];
  actualHashes: Record<string, string | undefined>;
}): EvidenceManifestReconciliation {
  const missingEntries: string[] = [];
  const mismatchedHashes: EvidenceManifestReconciliation["mismatchedHashes"] = [];
  const selfHashEntries: string[] = [];

  for (const entry of params.manifest) {
    if (entry.selfHash) {
      selfHashEntries.push(entry.path);
      continue;
    }
    const actual = params.actualHashes[entry.path] ?? null;
    if (entry.required !== false && actual === null) {
      missingEntries.push(entry.path);
      continue;
    }
    if (entry.sha256 && actual !== null && entry.sha256 !== actual) {
      mismatchedHashes.push({ path: entry.path, expected: entry.sha256, actual });
    }
  }

  const ok = missingEntries.length === 0 && mismatchedHashes.length === 0;
  return {
    ok,
    terminalState: ok ? "PASS" : "BLOCKED",
    missingEntries,
    mismatchedHashes,
    selfHashEntries,
  };
}

export function sha256Text(value: string): string {
  return crypto.createHash("sha256").update(value).digest("hex");
}

export function classifyCommandCloseLoop(params: {
  code: number | null;
  signal: NodeJS.Signals | number | null;
  termination: "exit" | "timeout" | "no-output-timeout" | "signal" | string;
  stdout?: string;
  stderr?: string;
  requiredEvidenceOk?: boolean;
}): CommandCloseLoopClassification {
  if (params.requiredEvidenceOk === false) {
    return {
      terminalState: "BLOCKED",
      classification: "blocked",
      requiresIndependentArtifactState: true,
      firstFailure: "required_evidence_missing_or_invalid",
    };
  }
  if (params.termination === "timeout" || params.termination === "no-output-timeout") {
    return {
      terminalState: "FAIL",
      classification: "timeout",
      requiresIndependentArtifactState: false,
      firstFailure: params.termination,
    };
  }
  if (params.signal != null || params.termination === "signal") {
    return {
      terminalState: "ABORTED",
      classification: "signal",
      requiresIndependentArtifactState: false,
      firstFailure: `signal:${String(params.signal ?? "unknown")}`,
    };
  }
  if (params.code === 0) {
    const hasOutput = Boolean((params.stdout ?? "").trim() || (params.stderr ?? "").trim());
    return {
      terminalState: "PASS",
      classification: hasOutput ? "success" : "silent-success",
      requiresIndependentArtifactState: !hasOutput,
      firstFailure: null,
    };
  }
  return {
    terminalState: "FAIL",
    classification: "failure",
    requiresIndependentArtifactState: false,
    firstFailure: `exit_code:${String(params.code)}`,
  };
}

export function reconcileStaleAsyncCompletion(params: {
  taskGeneration: number;
  currentGeneration: number;
  artifactUpdatedAfterTaskStarted?: boolean;
}): StaleAsyncReconciliation {
  if (params.taskGeneration !== params.currentGeneration) {
    return { terminalState: "SUPERSEDED", stale: true, reason: "generation-superseded" };
  }
  if (params.artifactUpdatedAfterTaskStarted) {
    return { terminalState: "SUPERSEDED", stale: true, reason: "artifact-superseded" };
  }
  return { terminalState: "PASS", stale: false, reason: "current-generation" };
}
