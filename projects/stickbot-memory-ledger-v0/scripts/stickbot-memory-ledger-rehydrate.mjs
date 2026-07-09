#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(scriptDir, '..');
const repoRoot = join(projectRoot, '..', '..');
const artifactRoot = join(projectRoot, 'artifacts', 'rehydration', 'stickbot-memory-ledger');

const sourceFiles = [
  'README.md',
  'pyproject.toml',
  'docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md',
  'docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md',
  'docs/PROJECT_REHYDRATOR.md',
  'docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md',
  'docs/MILESTONES.md',
  'docs/CLEAN_ROOM_NOTES.md',
  'docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md',
  'docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md',
  'docs/M12_TINY_PRODUCTION_READONLY_CANARY.md',
  'docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md',
  'docs/M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL.md',
  'docs/M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL.md',
  'docs/M16_OPERATOR_RECALL_HARDENING_AND_REPEATABILITY.md',
  'docs/M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL.md',
  'docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md',
  'docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md',
  'docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md',
  'docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_L1_READONLY_AUDIT.md',
  'docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX.md',
  'docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION.md',
  'docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY.md',
  'docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md',
  'scripts/stickbot-memory-ledger-rehydrate.mjs',
  'scripts/stickbot-memory-ledger-cli.py',
  'scripts/stickbot-memory-ledger-m12-canary.py',
  'scripts/stickbot-memory-ledger-operator-recall.py',
  'scripts/stickbot-memory-ledger-m16-repeatability.py',
  'scripts/context_bridge_ledger_l0_l1_readonly_audit.py',
  'scripts/context_bridge_ledger_l2_authority_matrix.py',
  'scripts/context_bridge_ledger_l3_shadow_projection.py',
  'scripts/context_bridge_ledger_l4_sanitizer_canary.py',
  'scripts/context_bridge_actions_l5r_redact_provenance.py',
  'src/stickbot_memory_ledger/__init__.py',
  'src/stickbot_memory_ledger/constants.py',
  'src/stickbot_memory_ledger/util.py',
  'src/stickbot_memory_ledger/redaction.py',
  'src/stickbot_memory_ledger/store.py',
  'src/stickbot_memory_ledger/cli.py',
  'src/stickbot_memory_ledger/openclaw_readonly_adapter.py',
  'test/test_first_slice.py',
];

function sha256(data) {
  return createHash('sha256').update(data).digest('hex');
}

function readProjectFile(relPath) {
  const abs = join(projectRoot, relPath);
  if (!existsSync(abs)) return null;
  const bytes = readFileSync(abs);
  return {
    relPath,
    bytes: bytes.length,
    sha256: sha256(bytes),
    text: bytes.toString('utf8'),
  };
}

function headingSummary(text) {
  return text
    .split(/\r?\n/)
    .filter((line) => /^#{1,3}\s+/.test(line))
    .slice(0, 40);
}

function buildPacket() {
  const generatedAt = new Date().toISOString();
  const sources = sourceFiles.map(readProjectFile);
  const present = sources.filter(Boolean);
  const missing = sourceFiles.filter((_, i) => !sources[i]);
  const lld = readProjectFile('docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md');
  const milestones = readProjectFile('docs/MILESTONES.md');
  const guide = readProjectFile('docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md');

  const manifest = {
    schema: 'stickbot.memory_ledger.rehydrator.v1',
    generatedAt,
    project: 'stickbot-memory-ledger-v0.1',
    projectRoot: relative(repoRoot, projectRoot),
    branch: 'feature/stickbot-memory-ledger-v0-1',
    preferredWorktree: '/tmp/stickbot-memory-ledger-v0-worktree',
    status: missing.length === 0 ? 'PASS' : 'WARN_MISSING_SOURCES',
    implementationAuthority: 'docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md',
    noApplyBoundaries: [
      'No Gateway config mutation',
      'No model/provider route mutation',
      'No production memory-route mutation',
      'No MEMORY.md writes in v0.1',
      'No Nuzo code/package/schema/test/plugin reuse',
      'No hidden inferred writes',
    ],
    currentMilestone: 'CB-L5R actions ledger redaction/provenance repair PASS with closeout metadata repaired to explicit PASS; terminal CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND; repair terminal CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_CLOSEOUT_REPAIRED_PASS_NO_MARKER_APPEND; CB-L5 marker append blocked and not performed; no authority promotion; CB-L6/M21/M22 not started',
    previousMilestone: 'CB-L4 sanitizer canary PASS and pushed; CB-L3 shadow projection PASS and pushed; CB-L2 authority matrix PASS and pushed; CB-L1 read-only audit PASS and pushed; M20R deterministic observer recovery PASS; M20 detached observer HOLD; M19 controlled production enablement PASS',
    nextImplementationSlice: 'Finish CB-L5R actions ledger redaction/provenance repair only; do not append CB-L5 marker or start CB-L6/M21/M22 without separate owner approval',
    activeObservation: {
      milestone: 'M20R',
      status: 'MEMORY_LEDGER_V0_1_M20R_DETERMINISTIC_OBSERVER_RECOVERY_PASS_NO_AUTHORITY_PROMOTION',
      startedAt: '2026-07-06T17:49:33+10:00',
      finalEligibilityAt: '2026-07-07T17:49:33+10:00',
      sessionTarget: 'session:m20-post-production-observation',
      currentGate: 'CB-L5R',
      detachedObserver: true,
      detachedObserverNote: 'Original M20 detached observer did not execute required checks; M20R used deterministic harness and child observer artifacts instead.',
      checkpointJobs: {
        tPlus2h: '8980885e-fc62-44e7-897f-ccc84e2f673c',
        tPlus8h: '4334fb16-e319-4ef2-a804-bb83c1eef22b',
        tPlus24hFinal: '72b92d09-602f-4649-9bd8-df7b91d3d4ce',
      },
      guards: [
        'No runtime mutation',
        'No recall memory write',
        'No recall authority leak',
        'Operator surface must remain inert',
        'Do not start M21/M22 without separate owner approval',
      ],
    },
    branchRecovery: {
      currentCheckoutMayBeDifferent: true,
      preferredWorktree: '/tmp/stickbot-memory-ledger-v0-worktree',
      branch: 'feature/stickbot-memory-ledger-v0-1',
      latestPacketGitShow: 'git show feature/stickbot-memory-ledger-v0-1:projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md',
      boundedDiscovery: [
        'git worktree list',
        "git branch --all --list '*memory-ledger*'",
        'git ls-tree -r --name-only feature/stickbot-memory-ledger-v0-1 projects/stickbot-memory-ledger-v0',
      ],
    },
    sources: present.map(({ relPath, bytes, sha256: hash }) => ({ relPath, bytes, sha256: hash })),
    missingSources: missing,
  };

  const markdown = `# Stickbot Memory Ledger v0.1 — Rehydration Packet\n\n` +
`Generated: ${generatedAt}\n\n` +
`Status: ${manifest.status}\n\n` +
`Project root: \`${manifest.projectRoot}\`\n\n` +
`Branch: \`${manifest.branch}\`\n\n` +
`## Immediate Resume\n\n` +
`1. Read \`docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md\`.\n` +
`2. Read \`docs/MILESTONES.md\`, \`docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md\`, \`docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md\`, \`docs/M12_TINY_PRODUCTION_READONLY_CANARY.md\`, \`docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md\`, \`docs/M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL.md\`, \`docs/M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL.md\`, \`docs/M16_OPERATOR_RECALL_HARDENING_AND_REPEATABILITY.md\`, \`docs/M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL.md\`, \`docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md\`, \`docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md\`, \`docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md\`, \`docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_L1_READONLY_AUDIT.md\`, \`docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX.md\`, \`docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION.md\`, \`docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY.md\`, and \`docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md\`.\n` +
`3. Preserve hard boundaries: no Gateway/model/provider/runtime memory-route mutation and no \`MEMORY.md\` writes in v0.1.\n` +
`4. Treat the production recall path as operator-only and explicit-flag/confirmation/scope gated for exactly \`system:memory-ledger\`, \`project:openclaw-runtime\`, and \`project:stickbot-tars\`.\n` +
`5. Current live state: CB-L5 marker append is blocked/not performed; CB-L5R actions ledger redaction/provenance repair PASS with closeout metadata repaired to explicit PASS; terminal CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND; repair terminal CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_CLOSEOUT_REPAIRED_PASS_NO_MARKER_APPEND; CB-L4 PASS/repaired/pushed, CB-L3 PASS/repaired/pushed, CB-L2 PASS/repaired/pushed, CB-L1 PASS/pushed, M20R PASS, no authority promotion; CB-L6/M21/M22 not started. Original M20 remains HOLD because detached observer sessions did not execute required checks.\n` +
`6. If the current checkout is not the Ledger branch, use the branch/worktree recovery section below before broad filesystem searches.\n` +
`7. Update this rehydrator and docs before every milestone closeout.\n` +
`8. For M20R details, read \`docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md\`.\n\n` +
`## Current Milestone\n\n${manifest.currentMilestone}\n\n` +
`Previous milestone: ${manifest.previousMilestone}\n\n` +
`Next implementation slice: ${manifest.nextImplementationSlice}\n\n` +
`## Active Observation / Detached Observer\n\n` +
`- Milestone: ${manifest.activeObservation.milestone}\n` +
`- Status: ${manifest.activeObservation.status}\n` +
`- Started: ${manifest.activeObservation.startedAt}\n` +
`- Final eligibility: ${manifest.activeObservation.finalEligibilityAt}\n` +
`- Session target: ${manifest.activeObservation.sessionTarget}\n` +
`- Current gate: ${manifest.activeObservation.currentGate}\n` +
`- Detached observer: ${manifest.activeObservation.detachedObserver ? 'yes' : 'no'} — ${manifest.activeObservation.detachedObserverNote}\n` +
`- Checkpoints: T+2h ${manifest.activeObservation.checkpointJobs.tPlus2h}; T+8h ${manifest.activeObservation.checkpointJobs.tPlus8h}; T+24h final ${manifest.activeObservation.checkpointJobs.tPlus24hFinal}\n` +
`${manifest.activeObservation.guards.map((g) => `- Guard: ${g}`).join('\n')}\n\n` +
`## Branch / Worktree Recovery\n\n` +
`If this packet is needed while the active checkout is a different project branch, do **not** infer that Ledger files are missing. Use the Ledger branch/worktree directly.\n\n` +
`Preferred worktree: \`${manifest.branchRecovery.preferredWorktree}\`\n\n` +
`Branch: \`${manifest.branchRecovery.branch}\`\n\n` +
`Read latest packet without switching branches:\n\n` +
'```bash\n' +
`${manifest.branchRecovery.latestPacketGitShow}\n` +
'```\n\n' +
`Bounded discovery order:\n\n${manifest.branchRecovery.boundedDiscovery.map((cmd) => `- \`${cmd}\``).join('\n')}\n\n` +
`## No-Apply Boundaries\n\n${manifest.noApplyBoundaries.map((b) => `- ${b}`).join('\n')}\n\n` +
`## Source Inventory\n\n${manifest.sources.map((s) => `- \`${s.relPath}\` — ${s.bytes} bytes — sha256:${s.sha256}`).join('\n')}\n` +
`${missing.length ? `\nMissing sources:\n${missing.map((m) => `- \`${m}\``).join('\n')}\n` : ''}\n` +
`## LLD Headings\n\n${lld ? headingSummary(lld.text).map((h) => `- ${h}`).join('\n') : '- Missing LLD'}\n\n` +
`## Milestone Headings\n\n${milestones ? headingSummary(milestones.text).map((h) => `- ${h}`).join('\n') : '- Missing milestones'}\n\n` +
`## Troubleshooting Guide Headings\n\n${guide ? headingSummary(guide.text).map((h) => `- ${h}`).join('\n') : '- Missing guide'}\n\n` +
`## Validation Commands\n\n` +
'```bash\n' +
'node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status\n' +
'node --check projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs\n' +
'git diff --check -- projects/stickbot-memory-ledger-v0\n' +
'```\n';

  return { manifest, markdown };
}

function main() {
  const { manifest, markdown } = buildPacket();
  mkdirSync(artifactRoot, { recursive: true });
  const stamp = manifest.generatedAt.replace(/[:.]/g, '-');
  const runDir = join(artifactRoot, stamp);
  mkdirSync(runDir, { recursive: true });

  const latestMd = join(artifactRoot, 'latest.md');
  const latestJson = join(artifactRoot, 'latest.json');
  const runMd = join(runDir, 'rehydration.md');
  const runJson = join(runDir, 'rehydration.json');

  writeFileSync(latestMd, markdown);
  writeFileSync(latestJson, JSON.stringify(manifest, null, 2) + '\n');
  writeFileSync(runMd, markdown);
  writeFileSync(runJson, JSON.stringify(manifest, null, 2) + '\n');

  const result = {
    status: manifest.status,
    generatedAt: manifest.generatedAt,
    latestMd: relative(repoRoot, latestMd),
    latestJson: relative(repoRoot, latestJson),
    runDir: relative(repoRoot, runDir),
    sourceCount: manifest.sources.length,
    missingSources: manifest.missingSources,
    latestMdSha256: sha256(readFileSync(latestMd)),
    latestJsonSha256: sha256(readFileSync(latestJson)),
  };

  if (process.argv.includes('--status') || process.argv.includes('--json')) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`Rehydration packet written: ${result.latestMd}`);
  }

  if (manifest.status !== 'PASS') process.exitCode = 1;
}

main();
