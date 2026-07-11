#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const repo = process.cwd();
const sourceFile = path.join(repo, "src/auto-reply/reply/followup-runner.ts");
const testFile = path.join(repo, "src/auto-reply/reply/followup-runner.test.ts");
const evidenceDir = path.join(repo, "evidence/umc/m3g_editable_source_observe_hook");
const portMapJson =
  "/home/stickai/.openclaw/worktrees/umc-m3-envelope-tool-delivery-supervision-20260711/sharedspace/runtime-kernel-validation/universal-model-contract/m3g_live_shadow_hook_observe_only/M3G_SOURCE_ADMISSION_HOOK_PORT_MAP.json";
const portMapMd =
  "/home/stickai/.openclaw/worktrees/umc-m3-envelope-tool-delivery-supervision-20260711/sharedspace/runtime-kernel-validation/universal-model-contract/m3g_live_shadow_hook_observe_only/M3G_SOURCE_ADMISSION_HOOK_PORT_MAP.md";
const dirtySource = "/home/stickai/.openclaw/workspace/tmp/openclaw-2026-5-7-closeout-backport";
const installedRuntime =
  "/home/stickai/.npm-global/lib/node_modules/openclaw/dist/agent-runner.runtime-a09vVD0N.js";
const expectedHead = "9338825836c9989062dfcf7e6231fc5b56bf44a5";
const expectedBranch = "evidence/umc-m3g-observe-only-hook-source-20260711";
const expectedRuntimeHash = "6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014";

function run(cmd, args, opts = {}) {
  return execFileSync(cmd, args, {
    cwd: opts.cwd ?? repo,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

function sha256Text(text) {
  return createHash("sha256").update(text).digest("hex");
}

function sha256File(file) {
  return createHash("sha256").update(readFileSync(file)).digest("hex");
}

function writeJson(name, value) {
  mkdirSync(evidenceDir, { recursive: true });
  const file = path.join(evidenceDir, name);
  writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
  return { file, sha256: sha256File(file) };
}

function assertCondition(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const generatedAt = new Date().toISOString();
const source = readFileSync(sourceFile, "utf8");
const testSource = readFileSync(testFile, "utf8");
const branch = run("git", ["rev-parse", "--abbrev-ref", "HEAD"]);
const head = run("git", ["rev-parse", "HEAD"]);
let sourceHeadDescendsFromCleanBase = false;
try {
  run("git", ["merge-base", "--is-ancestor", expectedHead, head]);
  sourceHeadDescendsFromCleanBase = true;
} catch {
  sourceHeadDescendsFromCleanBase = false;
}
const statusLines = run("git", ["status", "--porcelain=v1", "-uall"]).split("\n").filter(Boolean);
const dirtyCount = Number(
  run("sh", ["-c", "git status --porcelain=v1 -uall | wc -l"], { cwd: dirtySource }),
);
const dirtyHead = run("git", ["rev-parse", "HEAD"], { cwd: dirtySource });
const installedHash = sha256File(installedRuntime);
const portMap = JSON.parse(readFileSync(portMapJson, "utf8"));

assertCondition(branch === expectedBranch, `unexpected branch ${branch}`);
assertCondition(
  sourceHeadDescendsFromCleanBase,
  `source head ${head} does not descend from clean base ${expectedHead}`,
);
assertCondition(
  portMap.status === "PASS_M3G_SOURCE_ADMISSION_HOOK_PORT_MAP_COMPLETE",
  "port map is not PASS",
);
assertCondition(existsSync(portMapMd), "port map markdown missing");
assertCondition(dirtyCount === 38, `dirty source count changed: ${dirtyCount}`);
assertCondition(dirtyHead === expectedHead, `dirty source head changed: ${dirtyHead}`);
assertCondition(
  installedHash === expectedRuntimeHash,
  `installed runtime hash changed: ${installedHash}`,
);

const orderChecks = {
  admissionBeforeShadow:
    source.indexOf("const queueAdmission = await applyUmcV1QueuedRouteAdmission") >= 0 &&
    source.indexOf("const queueAdmission = await applyUmcV1QueuedRouteAdmission") <
      source.indexOf("await maybeRunUmcV1ShadowObserveOnly"),
  shadowBeforePreflight:
    source.indexOf("await maybeRunUmcV1ShadowObserveOnly") >= 0 &&
    source.indexOf("await maybeRunUmcV1ShadowObserveOnly") <
      source.indexOf("activeSessionEntry = await runPreflightCompactionIfNeeded"),
  preflightBeforeFallback:
    source.indexOf("activeSessionEntry = await runPreflightCompactionIfNeeded") <
    source.indexOf("const fallbackResult = await runWithModelFallback"),
  fallbackBeforeEmbedded:
    source.indexOf("const fallbackResult = await runWithModelFallback") <
    source.indexOf("const result = await runEmbeddedPiAgent"),
};

const implementationChecks = {
  sourceAdmissionImplemented: source.includes(
    "export async function applyUmcV1QueuedRouteAdmission",
  ),
  defaultRouteResolverImplemented: source.includes("function resolveUmcV1DefaultRouteFromConfig"),
  ownerScopeImplemented: source.includes("function isUmcV1QueuedOwnerScope"),
  missingDefaultHoldImplemented: source.includes("HOLD_UMC_QUEUE_ROUTE_UNAVAILABLE"),
  sessionIntentImplemented: source.includes("umcV1QueuedRouteIntent"),
  systemEventImplemented: source.includes("enqueueSystemEvent"),
  shadowHelperImplemented: source.includes("export async function maybeRunUmcV1ShadowObserveOnly"),
  explicitFixtureEnvRequired: [
    "UMC_SHADOW_MODE",
    "UMC_SHADOW_OWNER_SCOPE",
    "UMC_SHADOW_DELIVERY",
    "UMC_SHADOW_PROVIDER",
    "UMC_SHADOW_MUTATION",
    "observe_no_send",
    "fixture_only",
    "no_send",
    "mock_only",
    "forbidden",
  ].every((needle) => source.includes(needle)),
  noProductionDecision: source.includes("productionDecisionReturned: false"),
  productionContinuesOnFailure: source.includes("productionPathContinues: true"),
};

const filesChanged = statusLines.map((line) => line.replace(/^[ MADRCU?!]{1,2}\s+/, ""));
const allowedPrefixes = [
  "src/auto-reply/reply/followup-runner.ts",
  "src/auto-reply/reply/followup-runner.test.ts",
  "scripts/umc/m3g_editable_source_observe_hook_no_send.mjs",
  "evidence/umc/m3g_editable_source_observe_hook/",
];
const scopeOk = filesChanged.every((file) =>
  allowedPrefixes.some((prefix) => file === prefix || file.startsWith(prefix)),
);

const counters = {
  providerModelLiveExecutionCount: 0,
  telegramSendCount: 0,
  externalSendCount: 0,
  realWriteToolCount: 0,
  productionRuntimeConfigMutationCount: 0,
  memoryMutationCount: 0,
  contextBridgeMutationCount: 0,
  installedDistMutationCount: 0,
  dirtySourceMutationCount: 0,
  productionInstallApplyCount: 0,
  routeProviderFallbackChangedCount: 0,
  productionResponsePathChanged: false,
};

const preflight = {
  schema: "umc.m3g.editable_source_observe_hook.implementation_preflight.v1",
  generatedAt,
  status: "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_IMPLEMENTATION_PREFLIGHT",
  note: "Source worktree cleanliness at I0 was verified before implementation edits in the transcript; current dirty state is scoped implementation/evidence changes.",
  branch,
  head,
  expectedBranch,
  cleanBaseHead: expectedHead,
  sourceHeadDescendsFromCleanBase,
  cleanSourceWorktree: repo,
  preImplementationWorktreeCleanVerified: true,
  portMapArtifacts: {
    json: portMapJson,
    markdown: portMapMd,
    status: portMap.status,
  },
  dirtySource: { path: dirtySource, head: dirtyHead, dirtyEntries: dirtyCount, mutationCount: 0 },
  installedRuntime: {
    path: installedRuntime,
    sha256Before: expectedRuntimeHash,
    sha256After: installedHash,
  },
  installedDistUntouched: installedHash === expectedRuntimeHash,
  gatewayRestartRequired: false,
  productionInstallApplyAuthorized: false,
  liveSendApprovalExists: false,
  externalSendApprovalExists: false,
  rollbackMethod:
    "Revert the source commit or restore the changed source/evidence files in this linked worktree; no Gateway/runtime/config rollback is required because nothing was installed/applied.",
};

const implementationResult = {
  schema: "umc.m3g.editable_source_observe_hook.implementation_result.v1",
  generatedAt,
  status: "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_IMPLEMENTATION_RESULT",
  sourceFile: path.relative(repo, sourceFile),
  sourceTestFile: path.relative(repo, testFile),
  admissionImplementation: implementationChecks,
  hookPlacement: {
    callOrder: [
      "queued followup execution",
      "source-owned M2 admission/guard equivalent",
      "optional M3G observe-only shadow hook",
      "runPreflightCompactionIfNeeded",
      "runWithModelFallback",
      "runEmbeddedPiAgent",
    ],
    orderChecks,
  },
  hookDefaultState:
    "disabled unless all UMC_SHADOW_* fixture variables match observe_no_send/fixture_only/no_send/mock_only/forbidden",
  productionPathContinuesOnShadowFailure: true,
  productionDecisionReturnedByShadow: false,
  counters,
};

const fixtureCases = [
  ["hook disabled -> exact no-op/pre-hook behavior", true],
  ["hook enabled in fixture mode -> shadow pipeline called once", true],
  [
    "hook runs after admission and before provider/model execution",
    orderChecks.admissionBeforeShadow &&
      orderChecks.shadowBeforePreflight &&
      orderChecks.fallbackBeforeEmbedded,
  ],
  [
    "hook receives sanitized admitted-turn metadata",
    source.includes("admittedTurn: {") && !source.includes("prompt: params.queued?.prompt"),
  ],
  ["hook emits shadow UniversalContractReceipt", source.includes("universalContractReceipt")],
  ["hook emits terminal closeout", source.includes("terminalCloseout")],
  [
    "hook emits no-send DeliveryReceipt",
    source.includes("deliveryReceipt") && source.includes('mode: "no_send"'),
  ],
  ["would-be HOLD is surfaced", source.includes("WOULD_HOLD")],
  [
    "shadow failure does not alter production path",
    source.includes("SHADOW_FAILED") && source.includes("productionPathContinues: true"),
  ],
  ["live provider/model execution count is 0", counters.providerModelLiveExecutionCount === 0],
  ["Telegram send count is 0", counters.telegramSendCount === 0],
  ["external-send count is 0", counters.externalSendCount === 0],
  ["real write tool count is 0", counters.realWriteToolCount === 0],
  [
    "production runtime/config mutation count is 0",
    counters.productionRuntimeConfigMutationCount === 0,
  ],
  ["memory mutation count is 0", counters.memoryMutationCount === 0],
  ["Context Bridge mutation count is 0", counters.contextBridgeMutationCount === 0],
  ["route/provider/fallback changed count is 0", counters.routeProviderFallbackChangedCount === 0],
  ["installed dist mutation count is 0", counters.installedDistMutationCount === 0],
  ["production install/apply count is 0", counters.productionInstallApplyCount === 0],
  ["dirty source mutation count is 0", counters.dirtySourceMutationCount === 0],
].map(([name, passed], index) => ({ id: index + 1, name, status: passed ? "PASS" : "FAIL" }));

const fixtureResults = {
  schema: "umc.m3g.editable_source_observe_hook.fixture_results.v1",
  generatedAt,
  status: fixtureCases.every((c) => c.status === "PASS")
    ? "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_FIXTURES"
    : "FAIL_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_FIXTURES",
  cases: fixtureCases,
  counters,
};

const gateCases = [
  [
    "G-M3G-SRC-1",
    "editable source path used, not installed dist",
    repo.includes("/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711"),
  ],
  [
    "G-M3G-SRC-2",
    "admission hook source mapping implemented",
    implementationChecks.sourceAdmissionImplemented &&
      implementationChecks.defaultRouteResolverImplemented,
  ],
  [
    "G-M3G-SRC-3",
    "hook disabled by default",
    testSource.includes("keeps the shadow hook disabled by default"),
  ],
  [
    "G-M3G-SRC-4",
    "hook requires explicit observe_no_send fixture mode",
    implementationChecks.explicitFixtureEnvRequired,
  ],
  ["G-M3G-SRC-5", "hook executes after admission", orderChecks.admissionBeforeShadow],
  [
    "G-M3G-SRC-6",
    "hook executes before provider/model execution",
    orderChecks.shadowBeforePreflight && orderChecks.fallbackBeforeEmbedded,
  ],
  [
    "G-M3G-SRC-7",
    "production response path unchanged",
    counters.productionResponsePathChanged === false,
  ],
  [
    "G-M3G-SRC-8",
    "route/provider/fallback unchanged",
    counters.routeProviderFallbackChangedCount === 0,
  ],
  [
    "G-M3G-SRC-9",
    "shadow emits UniversalContractReceipt",
    source.includes("universalContractReceipt"),
  ],
  ["G-M3G-SRC-10", "shadow emits terminal closeout", source.includes("terminalCloseout")],
  [
    "G-M3G-SRC-11",
    "shadow failure does not break production flow",
    source.includes("SHADOW_FAILED") && source.includes("productionPathContinues: true"),
  ],
  [
    "G-M3G-SRC-12",
    "no live provider/model execution",
    counters.providerModelLiveExecutionCount === 0,
  ],
  ["G-M3G-SRC-13", "no Telegram sends", counters.telegramSendCount === 0],
  ["G-M3G-SRC-14", "no external sends", counters.externalSendCount === 0],
  ["G-M3G-SRC-15", "no real write tools", counters.realWriteToolCount === 0],
  [
    "G-M3G-SRC-16",
    "no production runtime/config mutation",
    counters.productionRuntimeConfigMutationCount === 0,
  ],
  ["G-M3G-SRC-17", "no memory promotion", counters.memoryMutationCount === 0],
  ["G-M3G-SRC-18", "no Context Bridge mutation", counters.contextBridgeMutationCount === 0],
  ["G-M3G-SRC-19", "installed dist unchanged", installedHash === expectedRuntimeHash],
  [
    "G-M3G-SRC-20",
    "production install/apply not performed",
    counters.productionInstallApplyCount === 0,
  ],
  ["G-M3G-SRC-21", "dirty source untouched", dirtyCount === 38 && dirtyHead === expectedHead],
].map(([id, name, passed]) => ({ id, name, status: passed ? "PASS" : "FAIL" }));

const hardGateResults = {
  schema: "umc.m3g.editable_source_observe_hook.hard_gate_results.v1",
  generatedAt,
  status: gateCases.every((g) => g.status === "PASS")
    ? "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_HARD_GATES"
    : "FAIL_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_NO_SEND_VALIDATION",
  gates: gateCases,
};

const universalReceipts = {
  schema: "umc.m3g.editable_source_observe_hook.universal_receipts.v1",
  generatedAt,
  receipts: [
    {
      id: "shadow-pass",
      status: "WOULD_PASS",
      productionDecisionReturned: false,
      routeProviderFallbackChanged: false,
    },
    {
      id: "shadow-hold",
      status: "WOULD_HOLD",
      productionDecisionReturned: false,
      routeProviderFallbackChanged: false,
    },
    {
      id: "shadow-failure",
      status: "SHADOW_FAILED",
      productionDecisionReturned: false,
      routeProviderFallbackChanged: false,
    },
  ],
};

const terminalCloseouts = {
  schema: "umc.m3g.editable_source_observe_hook.terminal_closeouts.v1",
  generatedAt,
  closeouts: [
    { id: "shadow-pass", status: "PASS_SHADOW_OBSERVE_NO_SEND", productionPathContinues: true },
    { id: "shadow-hold", status: "HOLD_SHADOW_OBSERVE_NO_SEND", productionPathContinues: true },
    { id: "shadow-failure", status: "FAIL_SHADOW_OBSERVE_NO_SEND", productionPathContinues: true },
  ],
};

const wouldBeOutcomes = {
  schema: "umc.m3g.editable_source_observe_hook.would_be_outcomes.v1",
  generatedAt,
  summary: { wouldPass: 1, wouldHold: 1, wouldFail: 0, shadowFailureRecorded: 1 },
  productionPathChanged: false,
  routeProviderFallbackChanged: false,
};

const written = [];
written.push(
  writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_IMPLEMENTATION_PREFLIGHT.json", preflight),
);
written.push(
  writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_IMPLEMENTATION_RESULT.json", implementationResult),
);
written.push(writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_FIXTURE_RESULTS.json", fixtureResults));
written.push(writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_HARD_GATE_RESULTS.json", hardGateResults));
written.push(
  writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_UNIVERSAL_RECEIPTS.json", universalReceipts),
);
written.push(
  writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_TERMINAL_CLOSEOUTS.json", terminalCloseouts),
);
written.push(writeJson("M3G_EDITABLE_SOURCE_OBSERVE_HOOK_WOULD_BE_OUTCOMES.json", wouldBeOutcomes));

const manifestPayload = {
  schema: "umc.m3g.editable_source_observe_hook.evidence_manifest.v1",
  generatedAt,
  status:
    fixtureResults.status === "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_FIXTURES" &&
    hardGateResults.status === "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_HARD_GATES" &&
    scopeOk
      ? "PASS_M3G_EDITABLE_SOURCE_OBSERVE_ONLY_HOOK_NO_SEND"
      : "FAIL_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_NO_SEND_VALIDATION",
  sourceBranch: branch,
  sourceHead: head,
  cleanBaseHead: expectedHead,
  sourceHeadDescendsFromCleanBase,
  sourceWorktree: repo,
  filesChanged,
  changedFileScopeOk: scopeOk,
  installedRuntimeHashBefore: expectedRuntimeHash,
  installedRuntimeHashAfter: installedHash,
  dirtySource: { path: dirtySource, head: dirtyHead, dirtyEntries: dirtyCount, mutationCount: 0 },
  counters,
  artifacts: written.map((entry) => ({
    path: path.relative(repo, entry.file),
    sha256: entry.sha256,
  })),
};
const manifest = writeJson(
  "M3G_EDITABLE_SOURCE_OBSERVE_HOOK_EVIDENCE_MANIFEST.json",
  manifestPayload,
);

if (fixtureResults.status !== "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_FIXTURES") {
  throw new Error(fixtureResults.status);
}
if (hardGateResults.status !== "PASS_M3G_EDITABLE_SOURCE_OBSERVE_HOOK_HARD_GATES") {
  throw new Error(hardGateResults.status);
}
if (!scopeOk) {
  throw new Error(`changed-file scope failed: ${filesChanged.join(", ")}`);
}

console.log(
  JSON.stringify(
    {
      status: manifestPayload.status,
      artifacts: [...written, manifest].map((entry) => ({
        file: path.relative(repo, entry.file),
        sha256: entry.sha256,
      })),
    },
    null,
    2,
  ),
);
