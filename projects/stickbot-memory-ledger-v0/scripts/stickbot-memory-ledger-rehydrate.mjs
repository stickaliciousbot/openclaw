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
  'docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md',
  'docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md',
  'docs/PROJECT_REHYDRATOR.md',
  'docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md',
  'docs/MILESTONES.md',
  'docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md',
  'docs/M25D_BOUNDARY_HANDLER_ARMING_PLAN_NO_APPLY.md',
  'artifacts/memory-ledger/m25d-boundary-handler-arming-plan/status.json',
  'artifacts/memory-ledger/m25d-boundary-handler-arming-plan/summary.json',
  'scripts/stickbot-memory-ledger-rehydrate.mjs',
  'scripts/context_bridge_actions_l5r_redact_provenance.py',
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
    currentMilestone: 'M25D boundary-handler arming plan READY/no-apply; installed M25B handler remains enabled, hash-proven, and unarmed; exact installed-handler arming fields and future M25E one-shot arming/disarm proof plan documented; terminal M25D_BOUNDARY_HANDLER_ARMING_PLAN_READY_NO_APPLY; no plugin arming, no retry scheduling/run, no delivery/send, no Gateway/plugin config mutation, no Ledger/Context Bridge mutation, no authority promotion; M25E/M26 not started',
    previousMilestone: 'M25C pushed blocked closeout at 3b36d0317b2b5d520be3b9c9de6e8c4eeab6d717: M25C_PUSHED_BLOCKED_SAFE_SINGLE_RETRY_SCHEDULING_NOT_ESTABLISHED because handler was enabled/hash-proven but unarmed. M25B-R hash provenance/preservation PASS at fd00fb76518d463d009b055918d88bcf75d50b27. CB-L5R actions ledger redaction/provenance repair PASS/no marker append; M20R deterministic observer recovery PASS',
    nextImplementationSlice: 'Recommended only, not started: M25E — Boundary Handler Armed One-Shot Retry Controlled Execution. Requires separate owner approval allowing bounded plugin config arming/disarming, exactly one one-shot retry schedule/run, immediate disarm/removal, and sanitized evidence. Do not start M25E/M26 automatically; do not mutate routes/model/provider/fallback/memory routes, Ledger, or Context Bridge',
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
`2. Read \`docs/MILESTONES.md\`, \`docs/PROJECT_REHYDRATOR.md\`, \`docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md\`, \`docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md\`, \`docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md\`, and \`docs/M25D_BOUNDARY_HANDLER_ARMING_PLAN_NO_APPLY.md\`. For older implementation slice docs not present in this evidence branch, use the branch/worktree recovery section instead of broad filesystem searches.\n` +
`3. Preserve hard boundaries: no Gateway/model/provider/runtime memory-route mutation and no \`MEMORY.md\` writes in v0.1.\n` +
`4. Treat the production recall path as operator-only and explicit-flag/confirmation/scope gated for exactly \`system:memory-ledger\`, \`project:openclaw-runtime\`, and \`project:stickbot-tars\`.\n` +
`5. Current live state: M25D arming plan READY/no-apply. M25B-R hash provenance and scoped preservation push PASS; installed boundary-handler runtime hash \`98a174e1767221f355d7a28364f738c2918eab320ed5373f9851d31da33b4347\` is provenance-proven. M25C pushed blocked because the handler was enabled/hash-proven but unarmed; no retry scheduled/run and no delivery/send. M25D documented exact arming fields and future M25E plan without arming, scheduling, delivery, config mutation, Ledger/Context Bridge mutation, or authority promotion. M25E/M26 not started.\n` +
`6. Scoped preservation push rule: if global tracked dirt is unrelated/pre-existing, do not treat it as clean; require explicit owner approval for scoped committed-head push, verify empty index/no rebase/no merge and committed diff scope, then push without staging/commit/amend/force.\n` +
`7. If the current checkout is not the Ledger branch, use the branch/worktree recovery section below before broad filesystem searches.\n` +
`8. Update this rehydrator and docs before every milestone closeout.\n` +
`9. For M20R details, read \`docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md\`.\n\n` +
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
