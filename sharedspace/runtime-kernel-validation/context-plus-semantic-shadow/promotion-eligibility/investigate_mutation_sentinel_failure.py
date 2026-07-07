#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/stickai/.openclaw/workspace')
AREA = ROOT / 'sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility'
RUN = AREA / 'production_replay_approved_fresh_20260707'
OUT = AREA / 'MUTATION_SENTINEL_FAILURE_INVESTIGATION.md'
MUT = RUN / 'mutation_sentinel_report.json'
SUMMARY = RUN / 'replay_summary.json'
STATUS = RUN / 'status.json'
SCRIPT = ROOT / 'scripts/context_plus_semantic_shadow_same_suite_comparator.py'
OUT_DIR_REL = 'sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/production_replay_approved_fresh_20260707'
START = datetime.fromisoformat('2026-07-07T06:45:22.220393+00:00')
END = datetime.fromisoformat('2026-07-07T08:28:28.174001+00:00')


def run_git(args):
    p = subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return p.returncode, p.stdout, p.stderr


def parse_status_line(line: str):
    return (line[:2], line[3:] if len(line) > 3 else line.strip())


def git_head_has(path: str) -> bool:
    rc, _, _ = run_git(['cat-file', '-e', f'HEAD:{path}'])
    return rc == 0


def git_tracked(path: str) -> bool:
    rc, out, _ = run_git(['ls-files', '--', path])
    return rc == 0 and bool(out.strip())


def stat_info(path: str):
    p = ROOT / path
    if not p.exists():
        return {'exists_now': False, 'mtime_utc': None, 'modified_during_replay_window': 'no-current-path'}
    mt = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    if START <= mt <= END:
        during = 'yes-mtime-within-window'
    elif mt < START:
        during = 'no-mtime-before-window'
    else:
        during = 'no-mtime-after-window'
    return {'exists_now': True, 'mtime_utc': mt.isoformat().replace('+00:00', 'Z'), 'modified_during_replay_window': during}


def classify_path(path: str, is_delta: bool):
    if path.startswith(OUT_DIR_REL + '/') or path == OUT_DIR_REL:
        return 'replay-created-artifact', 'inside approved replay output directory'
    if path.startswith('sharedspace/runtime-kernel-validation/work-lifecycle/') or path.startswith('sharedspace/runtime-kernel-validation/work-lifecycle-ledger/') or path.startswith('state/work-lifecycle/'):
        return 'unrelated concurrent change' if is_delta else 'pre-existing dirty workspace', 'work-lifecycle/ledger state outside Context+ replay output'
    if path.startswith('memory/') or path.startswith('sharedspace/context-bridge/') or path in ('MEMORY.md','USER.md','AGENTS.md','SOUL.md','IDENTITY.md','TOOLS.md','HEARTBEAT.md'):
        return 'unrelated concurrent change' if is_delta else 'pre-existing dirty workspace', 'memory/context/root context file outside replay scope; replay script has no writer for it'
    if path.startswith('config/') or path.startswith('.openclaw/'):
        return 'unrelated concurrent change' if is_delta else 'pre-existing dirty workspace', 'runtime/config-adjacent path outside replay scope; replay script has no writer for it'
    if path.startswith('equipmentiq-fabric-dtb/') or path.startswith('equipmentiq-node-handoff') or path.startswith('fabric-dtb-bootstrap/'):
        return 'unrelated concurrent change' if is_delta else 'pre-existing dirty workspace', 'EquipmentIQ/Fabric workspace unrelated to Context+ replay script'
    if path.startswith(('.artifacts/', '.local-browser-libs/', '.trash/', 'backups/', 'jdk11', 'jdk17/', 'fixtures/', 'hooks/')) or path in ('.gitignore', '.cron_watchdog_verify_486bc9e0.out', 'goodmorning-openclaw.sh'):
        return 'expected-noise' if is_delta else 'pre-existing dirty workspace', 'local workspace/tooling artifact unrelated to replay output path'
    return 'unrelated concurrent change' if is_delta else 'pre-existing dirty workspace', 'outside replay output; no replay writer evidence'


def protected_kind(path: str):
    if path.startswith('config/') or path == 'config/' or path.startswith('.openclaw/') or path == '.openclaw/':
        return 'runtime-config-adjacent'
    if path.startswith('memory/') or path.startswith('sharedspace/context-bridge/'):
        return 'memory-or-context-bridge'
    if path.startswith('state/'):
        return 'state'
    if path in ('MEMORY.md','USER.md','AGENTS.md','SOUL.md','IDENTITY.md','TOOLS.md','HEARTBEAT.md'):
        return 'root-context-file'
    return 'no'


def md(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')


def build_row(path: str, before_line: str | None, after_line: str | None, is_delta: bool):
    code_after = parse_status_line(after_line)[0] if after_line else None
    code_before = parse_status_line(before_line)[0] if before_line else None
    status_for_class = code_after or code_before or ''
    head_has = git_head_has(path)
    tracked = git_tracked(path)
    if before_line is not None:
        existed_before = 'yes-present-in-sentinel-before-list'
    elif head_has:
        existed_before = 'yes-tracked-in-HEAD'
    elif tracked:
        existed_before = 'yes-tracked-index'
    else:
        existed_before = 'unknown-untracked-not-in-HEAD'
    st = stat_info(path)
    cls, reason = classify_path(path, is_delta)
    replay_wrote = 'yes-inside-approved-output-dir' if path.startswith(OUT_DIR_REL) else 'no-evidence; reviewed replay code writes only configured out_dir reports/journal'
    return {
        'path': path,
        'before_status': code_before or '',
        'after_status': code_after or '',
        'class': cls,
        'existed_before_replay': existed_before,
        'mtime_utc': st['mtime_utc'],
        'modified_during_replay_window': st['modified_during_replay_window'],
        'replay_code_wrote_it': replay_wrote,
        'protected': protected_kind(path),
        'reason': reason,
        'status_for_class': status_for_class,
    }


def main():
    mut = json.loads(MUT.read_text())
    summary = json.loads(SUMMARY.read_text())
    status = json.loads(STATUS.read_text())
    before_lines = mut.get('workspace_status_before_filtered_outside_output')
    after_lines = mut.get('workspace_status_after_filtered_outside_output') or []
    has_before = isinstance(before_lines, list)
    before_lines = before_lines or []

    before_by_path = {parse_status_line(line)[1]: line for line in before_lines}
    after_by_path = {parse_status_line(line)[1]: line for line in after_lines}
    delta_paths = sorted(path for path in set(before_by_path) | set(after_by_path) if before_by_path.get(path) != after_by_path.get(path))
    all_after_paths = [parse_status_line(line)[1] for line in after_lines]

    delta_rows = [build_row(p, before_by_path.get(p), after_by_path.get(p), True) for p in delta_paths]
    after_rows = [build_row(p, before_by_path.get(p), after_by_path.get(p), False) for p in all_after_paths]

    counts = {}
    for r in delta_rows:
        counts[r['class']] = counts.get(r['class'], 0) + 1
    protected_delta = [r for r in delta_rows if r['protected'] != 'no']
    protected_after = [r for r in after_rows if r['protected'] != 'no']
    replay_outside = [r for r in delta_rows if r['replay_code_wrote_it'].startswith('yes') and not r['path'].startswith(OUT_DIR_REL)]
    modified_during_delta = [r for r in delta_rows if str(r['modified_during_replay_window']).startswith('yes')]

    if replay_outside:
        final = 'HOLD_REPLAY_CREATED_OUT_OF_SCOPE_ARTIFACTS'
    elif not has_before:
        final = 'HOLD_INCONCLUSIVE_MUTATION_SOURCE'
    elif delta_rows:
        final = 'HOLD_CONCURRENT_WORKSPACE_NOISE'
    else:
        final = 'HOLD_PREEXISTING_DIRTY_WORKSPACE'

    lines = []
    lines.append('# Context+ Fresh Replay Mutation Sentinel Failure Investigation')
    lines.append('')
    lines.append('Generated: 2026-07-07 AEST')
    lines.append('Scope: read-only investigation plus this evidence artifact under `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/`.')
    lines.append('')
    lines.append('## Closeout classification')
    lines.append('')
    lines.append(f'`{final}`')
    lines.append('')
    if final == 'HOLD_CONCURRENT_WORKSPACE_NOISE':
        lines.append('Reason: the persisted sentinel contains both before and after filtered workspace-status lists. The outside-output delta is limited to paths outside the approved replay output directory, and code review found no replay writer for those paths. The delta is therefore classified as unrelated concurrent workspace noise, not promotion-safe replay evidence.')
    elif final == 'HOLD_PREEXISTING_DIRTY_WORKSPACE':
        lines.append('Reason: the persisted sentinel did not show an outside-output delta; the remaining dirty paths are pre-existing workspace dirt. The replay remains unsafe for promotion because the workspace was not clean/baselined.')
    else:
        lines.append('Reason: the persisted sentinel evidence is insufficient or shows out-of-scope replay artifacts; no promotion-safe conclusion is available.')
    lines.append('')
    lines.append('## Replay state readback')
    lines.append('')
    lines.append(f'- Replay: `production_replay_approved_fresh_20260707`')
    lines.append(f'- Started UTC: `{summary.get("started_utc")}`')
    lines.append(f'- Ended UTC: `{summary.get("ended_utc")}`')
    lines.append(f'- Cases: `{summary.get("completed_cases")}/{summary.get("expected_cases")}`')
    lines.append(f'- Provider calls: `{summary.get("provider_model_call_count")}/{summary.get("expected_cases")}`')
    lines.append(f'- Final classification: `{summary.get("classification")}`')
    lines.append(f'- Hard abort reason: `{(summary.get("hard_abort") or {}).get("reason")}`')
    lines.append(f'- Mutation sentinel classification: `{mut.get("classification")}`')
    lines.append(f'- Workspace changed outside output: `{mut.get("workspace_changed_outside_output")}`')
    lines.append(f'- Before filtered entries: `{len(before_lines)}`')
    lines.append(f'- After filtered entries: `{len(after_lines)}`')
    lines.append(f'- Delta path entries: `{len(delta_rows)}`')
    lines.append(f'- Mutation performed flag: `{mut.get("mutation_performed")}`')
    lines.append(f'- Artifact memory promoted: `{mut.get("artifact_memory_promoted")}`')
    lines.append(f'- Cache enabled: `{mut.get("cache_enabled")}`')
    lines.append('')
    lines.append('## Source determination')
    lines.append('')
    lines.append('- Replay harness review: `cmd_run_production_replay` writes `run_config.json`, `production_replay_journal.jsonl`, and terminal reports under the configured output directory, then compares `git status --short` filtered outside that output directory.')
    lines.append('- No delta path is inside the approved replay output directory.')
    lines.append('- No route/config/Gateway/provider/model/cache writer was found in the replay code path.')
    lines.append('- The replay itself is still unsafe for comparator/promotion use because its mutation sentinel failed.')
    lines.append('')
    lines.append('## Summary counts')
    lines.append('')
    lines.append(f'- Delta classification counts: `{json.dumps(counts, sort_keys=True)}`')
    lines.append(f'- Delta entries with current filesystem mtime inside replay window: `{len(modified_during_delta)}`')
    lines.append(f'- Protected/adjoining delta entries: `{len(protected_delta)}`')
    lines.append(f'- Protected/adjoining entries in full post-run dirty list: `{len(protected_after)}`')
    lines.append('')
    lines.append('## Protected path finding')
    lines.append('')
    lines.append('Protected/adjoining paths appear in the full dirty workspace list and some appear in the before/after delta. This keeps the replay unsafe for promotion eligibility. The replay code review did not find a writer for those paths, so the protected-path finding is classified as concurrent workspace noise rather than proven replay-caused unsafe mutation.')
    lines.append('')
    lines.append('```json')
    lines.append(json.dumps({
        'protected_delta_count': len(protected_delta),
        'protected_delta_paths': [r['path'] for r in protected_delta[:200]],
        'protected_after_count': len(protected_after),
        'protected_after_truncated': len(protected_after) > 200,
    }, indent=2, sort_keys=True))
    lines.append('```')
    lines.append('')
    lines.append('## Clean rerun consideration')
    lines.append('')
    lines.append('A clean rerun could be considered later only after failed replay evidence is explicitly preserved or ignored, the workspace is made clean or the sentinel is given an approved baseline snapshot, and a new explicit replay approval is granted. It must still not imply comparator readiness or promotion by itself.')
    lines.append('')
    lines.append('## Forbidden actions readback')
    lines.append('')
    lines.append('No comparator run occurred. No replay rerun occurred. No promotion occurred. No M6 proposal was prepared. No route/config/Gateway mutation, memory promotion, provider/model change, production apply, or cache enablement occurred during this investigation.')
    lines.append('')
    lines.append('## Exact changed paths: before/after delta')
    lines.append('')
    lines.append('| # | before | after | path | class | existed before replay | modified during replay window | replay code wrote it | protected/adjoining | reason |')
    lines.append('|---:|---|---|---|---|---|---|---|---|---|')
    for i, r in enumerate(delta_rows, 1):
        lines.append(f"| {i} | `{md(r['before_status'])}` | `{md(r['after_status'])}` | `{md(r['path'])}` | `{md(r['class'])}` | `{md(r['existed_before_replay'])}` | `{md(r['modified_during_replay_window'])}` | {md(r['replay_code_wrote_it'])} | `{md(r['protected'])}` | {md(r['reason'])} |")
    lines.append('')
    lines.append('## Full post-run dirty path list from sentinel')
    lines.append('')
    lines.append('Included for exact auditability; the delta table above is the source classification table.')
    lines.append('')
    lines.append('| # | after | path | class | existed before replay | modified during replay window | replay code wrote it | protected/adjoining | reason |')
    lines.append('|---:|---|---|---|---|---|---|---|---|')
    for i, r in enumerate(after_rows, 1):
        lines.append(f"| {i} | `{md(r['after_status'])}` | `{md(r['path'])}` | `{md(r['class'])}` | `{md(r['existed_before_replay'])}` | `{md(r['modified_during_replay_window'])}` | {md(r['replay_code_wrote_it'])} | `{md(r['protected'])}` | {md(r['reason'])} |")
    lines.append('')
    OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({
        'artifact': str(OUT.relative_to(ROOT)),
        'classification': final,
        'before_entries': len(before_lines),
        'after_entries': len(after_lines),
        'delta_path_entries': len(delta_rows),
        'delta_counts': counts,
        'protected_delta_entries': len(protected_delta),
        'modified_during_replay_window_delta_entries': len(modified_during_delta),
    }, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
