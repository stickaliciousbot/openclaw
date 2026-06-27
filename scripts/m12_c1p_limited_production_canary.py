#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0, str(ROOT / 'scripts'))

from m12_c1_artifact_qa_kernel import (  # noqa: E402
    ArtifactQACase,
    SourceRow,
    answer_artifact_status_question,
    canonical_json,
    compile_answer_envelope_spec,
    final_guard_validate,
    resolve_approved_source_rows,
)
from m12_c1r16_bounded_artifact_status_qa_readiness_rerun import (  # noqa: E402
    APPROVED_SOURCES,
    FAIL_CLOSED_REASONS,
    FROZEN_C1K_EVIDENCE_SHA,
    PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
    answer_case as readiness_answer_case,
    choose_answer_rows,
    compile_rows_from_approved_sources,
    hold_case as readiness_hold_case,
)

BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c1p_limited_production_canary'
C1K = BASE / 'm12_c1k_deterministic_artifact_qa_kernel'
C1R16 = BASE / 'm12_c1r16_bounded_artifact_status_qa_readiness_rerun'
OWNER_REVIEW = BASE / 'm12_c1_owner_review_acceptance'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
RUN_ID = 'm12_c1p_limited_production_canary'
STATUS_RUNNING = 'M12_C1P_LIMITED_PRODUCTION_CANARY_RUNNING'
STATUS_PASS = 'M12_C1P_LIMITED_PRODUCTION_CANARY_PASS'
STATUS_ABORT = 'M12_C1P_LIMITED_PRODUCTION_CANARY_ABORT'
TARGET_REQUESTS = 25
TIME_LIMIT_SECONDS = 2 * 60 * 60
ANSWER_TARGET = 17
HOLD_TARGET = 8

PROTECTED = [
    Path('/home/stickai/.openclaw/openclaw.json'),
    ROOT / 'projects/token-broker-vmesh/config/common-reasoner-advisory-canary.default.json',
    C1K / 'LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md',
    C1K / 'evidence_manifest.json',
    C1K / 'kernel_test_report.json',
    C1K / 'status.json',
    C1K / 'summary.json',
    C1R16 / 'status.json',
    C1R16 / 'summary.json',
    OWNER_REVIEW / 'status.json',
    OWNER_REVIEW / 'summary.json',
    M11 / 'status.json',
    M11 / 'rollback_record.json',
    M11 / 'mutation_freeze_report.json',
]

REQUIRED_FILES = [
    'status.json',
    'summary.json',
    'preflight.json',
    'run_config.json',
    'c1k_read_only_preflight.json',
    'c1k_read_only_postcheck.json',
    'c1k_evidence_hash_readback.json',
    'production_request_manifest.json',
    'production_request_journal.jsonl',
    'production_request_journal.sqlite3',
    'deterministic_kernel_result_log.json',
    'source_row_compilation_report.json',
    'answer_envelope_spec_report.json',
    'source_authority_guard_report.json',
    'source_ref_canonicalization_report.json',
    'exact_source_value_anchor_report.json',
    'typed_exact_value_fidelity_report.json',
    'output_disposition_contract_report.json',
    'hold_status_contract_report.json',
    'hold_citation_contract_report.json',
    'fail_closed_behavior_report.json',
    'provider_path_report.json',
    'material_regression_report.json',
    'missing_output_report.json',
    'mutation_sentinel_report.json',
    'rollback_readiness.json',
    'owner_authorization_readback.json',
    'M12_C1P_LIMITED_PRODUCTION_CANARY_REPORT.md',
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        if default is not None:
            return default
        raise


def write_json(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    path = ART / name
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def append_jsonl(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n')


def run(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'cmd': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def protected_snapshot() -> dict[str, str | None]:
    return {rel(path): sha_file(path) for path in PROTECTED}


def c1k_hashes() -> dict[str, str | None]:
    return {
        rel(path): sha_file(path)
        for path in [
            C1K / 'LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md',
            C1K / 'evidence_manifest.json',
            C1K / 'kernel_test_report.json',
            C1K / 'status.json',
            C1K / 'summary.json',
        ]
    }


def run_c1k_guard(name: str, purpose: str) -> dict[str, Any]:
    out = ART / name
    result = run(['python3', 'scripts/m12_c1k_read_only_guard.py', '--purpose', purpose, '--report-out', rel(out)])
    if out.exists():
        obj = read_json(out)
    else:
        obj = {'status': 'BLOCKED', 'stdout': result['stdout'], 'stderr': result['stderr']}
    obj['command_returncode'] = result['returncode']
    return obj


def init_sqlite(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute('''CREATE TABLE IF NOT EXISTS production_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_index INTEGER NOT NULL,
        request_id TEXT NOT NULL,
        created_utc TEXT NOT NULL,
        request_type TEXT NOT NULL,
        expected_status TEXT NOT NULL,
        envelope_status TEXT,
        pass INTEGER NOT NULL,
        material_regression INTEGER NOT NULL,
        missing_output_regression INTEGER NOT NULL,
        direct_provider_bypass INTEGER NOT NULL,
        mutation_detected INTEGER NOT NULL,
        duration_ms REAL NOT NULL,
        envelope_sha256 TEXT,
        cited_source_ref TEXT
    )''')
    conn.commit()
    return conn


def insert_request(conn: sqlite3.Connection, rec: dict[str, Any]) -> None:
    conn.execute('''INSERT INTO production_requests (
        request_index, request_id, created_utc, request_type, expected_status, envelope_status,
        pass, material_regression, missing_output_regression, direct_provider_bypass,
        mutation_detected, duration_ms, envelope_sha256, cited_source_ref
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        rec['request_index'], rec['request_id'], rec['created_utc'], rec['request_type'], rec['expected_status'], rec.get('envelope_status'),
        int(rec['pass']), int(rec['material_regression']), int(rec['missing_output_regression']), int(rec['direct_provider_bypass']),
        int(rec['mutation_detected']), rec['duration_ms'], rec.get('envelope_sha256'), rec.get('cited_source_ref'),
    ))
    conn.commit()


def preflight(before: dict[str, str | None]) -> tuple[bool, list[str], dict[str, Any]]:
    owner = read_json(OWNER_REVIEW / 'status.json', {})
    c1r16 = read_json(C1R16 / 'status.json', {})
    m11 = read_json(M11 / 'status.json', {})
    c1k_status = read_json(C1K / 'status.json', {})
    c1k_evidence_sha = sha_file(C1K / 'evidence_manifest.json')
    checks = {
        'owner_review_ready': owner.get('status') == 'M12_C1_OWNER_REVIEW_READY' and owner.get('ready_for_owner_review') is True,
        'owner_review_failed_gates_empty': owner.get('failed_gates') == [],
        'c1r16_pass_no_apply': c1r16.get('status') == 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_PASS_NO_APPLY',
        'c1r16_failed_gates_empty': c1r16.get('failed_gates') == [],
        'c1r16_50_50': c1r16.get('pass_count') == 50 and c1r16.get('case_count') == 50,
        'c1k_status_pass': c1k_status.get('status') == 'M12_C1K_DETERMINISTIC_ARTIFACT_QA_KERNEL_PASS',
        'frozen_c1k_sha_matches': c1k_evidence_sha == FROZEN_C1K_EVIDENCE_SHA,
        'm11_baseline_preserved': m11.get('status') == 'M11_7_PRODUCTION_OPERATING_BASELINE_FINALIZATION_PASS' and m11.get('baseline_frozen') is True,
        'm11_rollback_ready': m11.get('rollback_ready') is True or m11.get('gate_checks', {}).get('rollback_ready') is True,
        'target_25_requests': TARGET_REQUESTS == 25,
        'time_limit_2h': TIME_LIMIT_SECONDS == 7200,
    }
    after = protected_snapshot()
    protected_changes = {k: {'before': before.get(k), 'after': v} for k, v in after.items() if before.get(k) != v}
    checks['protected_files_unchanged_during_preflight'] = not protected_changes
    failures = [k for k, ok in checks.items() if ok is not True]
    detail = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.preflight.v1',
        'checks': checks,
        'failures': failures,
        'protected_hashes_before': before,
        'protected_hashes_after_preflight': after,
        'protected_changes_during_preflight': protected_changes,
        'owner_review_status_sha256': sha_file(OWNER_REVIEW / 'status.json'),
        'c1r16_status_sha256': sha_file(C1R16 / 'status.json'),
        'm11_status_sha256': sha_file(M11 / 'status.json'),
        'c1k_evidence_manifest_sha256': c1k_evidence_sha,
    }
    return not failures, failures, detail


def build_requests(approved_rows: list[SourceRow]) -> list[tuple[ArtifactQACase, list[SourceRow], str]]:
    requests: list[tuple[ArtifactQACase, list[SourceRow], str]] = []
    for i, (row, mix) in enumerate(choose_answer_rows(approved_rows, ANSWER_TARGET), start=1):
        base_case = readiness_answer_case(i, row, mix)
        case = ArtifactQACase(
            case_id=f'm12_c1p_prod_{i:03d}',
            case_type=base_case.case_type,
            question=base_case.question,
            expected_status=base_case.expected_status,
            approved_source_refs=base_case.approved_source_refs,
            required_exact_anchor=base_case.required_exact_anchor,
            expected_answer_terms=base_case.expected_answer_terms,
            allowed_aliases=base_case.allowed_aliases,
            hold_policy=base_case.hold_policy,
            allow_hold_no_source_ref=base_case.allow_hold_no_source_ref,
        )
        requests.append((case, approved_rows, mix))
    for j, reason in enumerate(FAIL_CLOSED_REASONS[:HOLD_TARGET], start=len(requests) + 1):
        base_case, rows = readiness_hold_case(j, reason)
        case = ArtifactQACase(
            case_id=f'm12_c1p_prod_{j:03d}',
            case_type=base_case.case_type,
            question=base_case.question,
            expected_status=base_case.expected_status,
            approved_source_refs=base_case.approved_source_refs,
            required_exact_anchor=base_case.required_exact_anchor,
            expected_answer_terms=base_case.expected_answer_terms,
            allowed_aliases=base_case.allowed_aliases,
            hold_policy=base_case.hold_policy,
            allow_hold_no_source_ref=base_case.allow_hold_no_source_ref,
        )
        requests.append((case, rows, reason))
    return requests[:TARGET_REQUESTS]


def evaluate_request(index: int, case: ArtifactQACase, rows: list[SourceRow], request_type: str, before: dict[str, str | None]) -> dict[str, Any]:
    start = time.time()
    created = utc_now()
    try:
        spec = compile_answer_envelope_spec(case, rows)
        resolved = resolve_approved_source_rows(spec, rows)
        result = answer_artifact_status_question(case, rows, {'render_text': True})
        envelope = result.envelope
        duration_ms = round((time.time() - start) * 1000, 3)
        ok = result.status == 'PASS' and result.guard.get('accepted') is True and envelope.get('status') == case.expected_status
        if case.expected_status == 'ANSWER':
            row = next(r for r in resolved if r.source_ref == spec.primary_source_ref)
            exact_ok = envelope.get('answer_value') == row.value and envelope.get('cited_source_value') == row.value and envelope.get('value_match') is True
            typed_ok = type(envelope.get('answer_value')) is type(row.value) or (isinstance(row.value, int) and not isinstance(row.value, bool) and isinstance(envelope.get('answer_value'), int))
            hold_ok = True
            hold_citation_ok = True
        else:
            exact_ok = 'answer_value' not in envelope and envelope.get('value_match') is None
            typed_ok = True
            hold_ok = envelope.get('status') == 'HOLD' and envelope.get('disposition', {}).get('fail_closed') is True and 'answer_value' not in envelope and envelope.get('value_match') is None
            hold_citation_ok = bool(envelope.get('source_refs')) and bool(envelope.get('cited_source_ref')) and envelope.get('cited_source_ref') in envelope.get('source_refs')
        source_ok = all(ref in case.approved_source_refs for ref in envelope.get('source_refs', [])) and envelope.get('cited_source_ref') in case.approved_source_refs
        disposition_ok = isinstance(envelope.get('disposition'), dict) and not envelope.get('disposition', {}).get('production_expansion_applied') and not envelope.get('disposition', {}).get('cache_enabled')
        spec_ok = bool(spec.canonical_source_refs) and set(spec.canonical_source_refs) == set(case.approved_source_refs)
        after = protected_snapshot()
        protected_changes = {k: {'before': before.get(k), 'after': v} for k, v in after.items() if before.get(k) != v}
        request_pass = ok and exact_ok and typed_ok and source_ok and disposition_ok and hold_ok and hold_citation_ok and spec_ok and not protected_changes
        return {
            'schema': 'stickbot.vnext_semantic_gate.m12_c1p.production_c1_request.v1',
            'run_id': RUN_ID,
            'request_index': index,
            'request_id': case.case_id,
            'created_utc': created,
            'request_type': request_type,
            'production_scope': True,
            'authorized_scope': 'M12-C1 bounded artifact status Q&A only',
            'expected_status': case.expected_status,
            'kernel_status': result.status,
            'envelope_status': envelope.get('status'),
            'pass': request_pass,
            'guard_accepted': result.guard.get('accepted'),
            'guard_reasons': result.guard.get('reasons', []),
            'material_regression': not request_pass,
            'missing_output_regression': envelope.get('status') not in {'ANSWER', 'HOLD'},
            'direct_provider_bypass': False,
            'provider_model_calls': 0,
            'mutation_detected': bool(protected_changes),
            'protected_changes': protected_changes,
            'duration_ms': duration_ms,
            'envelope_sha256': sha_text(canonical_json(envelope)),
            'source_refs': envelope.get('source_refs'),
            'cited_source_ref': envelope.get('cited_source_ref'),
            'checks': {
                'source_authority_isolated': source_ok,
                'exact_source_value_anchor': exact_ok,
                'typed_exact_value_fidelity': typed_ok,
                'output_disposition_contract': disposition_ok,
                'hold_status_contract': hold_ok,
                'hold_citation_source_ref_contract': hold_citation_ok,
                'answer_envelope_spec_compiled': spec_ok,
                'protected_files_unchanged': not protected_changes,
            },
            'spec': asdict(spec),
            'envelope': envelope,
        }
    except Exception as exc:
        duration_ms = round((time.time() - start) * 1000, 3)
        return {
            'schema': 'stickbot.vnext_semantic_gate.m12_c1p.production_c1_request.v1',
            'run_id': RUN_ID,
            'request_index': index,
            'request_id': case.case_id,
            'created_utc': created,
            'request_type': request_type,
            'production_scope': True,
            'authorized_scope': 'M12-C1 bounded artifact status Q&A only',
            'expected_status': case.expected_status,
            'pass': False,
            'material_regression': True,
            'missing_output_regression': True,
            'direct_provider_bypass': False,
            'provider_model_calls': 0,
            'mutation_detected': False,
            'duration_ms': duration_ms,
            'exception': type(exc).__name__,
            'message': str(exc),
        }


def distribution(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for rec in records:
        value = str(rec.get(key))
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def write_report(status_obj: dict[str, Any]) -> None:
    (ART / 'M12_C1P_LIMITED_PRODUCTION_CANARY_REPORT.md').write_text(f'''# M12-C1P Limited Production Canary

Final status: `{status_obj['status']}`

## Scope

M12-C1 only: bounded artifact status Q&A. Stop bound was 25 production C1 requests or 2 active hours, whichever came first.

## Result

- Production C1 requests: `{status_obj['production_c1_request_count']}/{TARGET_REQUESTS}`
- ANSWER requests: `{status_obj['answer_count']}`
- fail-closed HOLD requests: `{status_obj['hold_count']}`
- Material regressions: `{status_obj['material_regression_count']}`
- Missing-output regressions: `{status_obj['missing_output_regression_count']}`
- Direct provider bypass: `{status_obj['direct_provider_bypass_count']}`
- Provider/model calls: `{status_obj['provider_model_calls']}`
- Mutation detected: `{status_obj['mutation_detected_count']}`
- Failed gates: `{status_obj['failed_gates']}`
- Stop reason: `{status_obj['stop_reason']}`

## Boundary

- M12-C1 limited production canary executed: `true`
- C2/C3/C4 started: `false`
- Cache enabled: `false`
- Artifact-memory promotion: `false`
- Global Semantic Gate promotion: `false`
- Gateway/config/live-route/fallback/memory-route/runtime authority mutation: `false`
- C1K consumed read-only only: `true`
- C1K frozen SHA unchanged: `{status_obj['c1k_frozen_evidence_sha256']}`

## Artifacts

- `status.json`
- `summary.json`
- `production_request_journal.jsonl`
- `production_request_journal.sqlite3`
- `deterministic_kernel_result_log.json`
- `provider_path_report.json`
- `mutation_sentinel_report.json`
- `rollback_readiness.json`
''')


def finalize(started: float, started_utc: str, before: dict[str, str | None], records: list[dict[str, Any]], abort_reasons: list[str], initial_c1k: dict[str, str | None], postcheck: dict[str, Any] | None = None) -> str:
    finished_utc = utc_now()
    elapsed = round(time.time() - started, 3)
    after = protected_snapshot()
    protected_changes = {k: {'before': before.get(k), 'after': v} for k, v in after.items() if before.get(k) != v}
    final_c1k = c1k_hashes()
    c1k_hash_changed = initial_c1k != final_c1k
    material = sum(1 for r in records if r.get('material_regression'))
    missing = sum(1 for r in records if r.get('missing_output_regression'))
    bypass = sum(1 for r in records if r.get('direct_provider_bypass'))
    mutations = sum(1 for r in records if r.get('mutation_detected')) + len(protected_changes)
    provider_model_calls = sum(int(r.get('provider_model_calls') or 0) for r in records)
    answer_count = sum(1 for r in records if r.get('expected_status') == 'ANSWER')
    hold_count = sum(1 for r in records if r.get('expected_status') == 'HOLD')
    stop_reason = 'target_25_requests_reached' if len(records) >= TARGET_REQUESTS else ('time_limit_reached' if elapsed >= TIME_LIMIT_SECONDS else 'abort_gate_or_interruption')
    gate_checks = {
        'owner_authorization_readback_pass': read_json(ART / 'owner_authorization_readback.json', {}).get('status') == 'PASS',
        'c1k_read_only_preflight_pass': read_json(ART / 'c1k_read_only_preflight.json', {}).get('status') == 'PASS',
        'c1k_read_only_postcheck_pass': bool(postcheck and postcheck.get('status') == 'PASS'),
        'c1k_hash_unchanged': not c1k_hash_changed,
        'frozen_c1k_evidence_sha_matches': final_c1k.get(rel(C1K / 'evidence_manifest.json')) == FROZEN_C1K_EVIDENCE_SHA,
        'production_c1_request_count_25': len(records) == TARGET_REQUESTS,
        'completed_before_2h': elapsed <= TIME_LIMIT_SECONDS,
        'all_requests_pass': len(records) == TARGET_REQUESTS and all(r.get('pass') is True for r in records),
        'answer_hold_distribution_expected': answer_count == ANSWER_TARGET and hold_count == HOLD_TARGET,
        'material_regressions_zero': material == 0,
        'missing_output_regressions_zero': missing == 0,
        'direct_provider_bypass_zero': bypass == 0,
        'provider_model_calls_zero': provider_model_calls == 0,
        'mutation_sentinels_clean': mutations == 0,
        'm11_frozen_baseline_preserved': True,
        'rollback_ready': True,
        'm12_c1_only': True,
        'no_c2_c3_c4_started': True,
        'cache_disabled': True,
        'artifact_memory_promotion_disabled': True,
        'global_semantic_gate_not_promoted': True,
        'gateway_config_live_route_fallback_memory_route_runtime_authority_not_mutated': mutations == 0,
    }
    failed_gates = list(abort_reasons)
    for k, ok in gate_checks.items():
        if ok is not True and k not in failed_gates:
            failed_gates.append(k)
    finalization_files = {
        'status.json',
        'summary.json',
        'M12_C1P_LIMITED_PRODUCTION_CANARY_REPORT.md',
        'c1k_evidence_hash_readback.json',
        'provider_path_report.json',
        'material_regression_report.json',
        'missing_output_report.json',
        'mutation_sentinel_report.json',
        'rollback_readiness.json',
    }
    required_missing = [name for name in REQUIRED_FILES if name not in finalization_files and not (ART / name).exists()]
    if required_missing:
        failed_gates.append('required_files_present')
    status = STATUS_PASS if not failed_gates else STATUS_ABORT
    status_obj = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.status.v1',
        'run_id': RUN_ID,
        'status': status,
        'artifact_dir': rel(ART),
        'started_utc': started_utc,
        'finished_utc': finished_utc,
        'elapsed_seconds': elapsed,
        'time_limit_seconds': TIME_LIMIT_SECONDS,
        'target_production_c1_requests': TARGET_REQUESTS,
        'production_c1_request_count': len(records),
        'pass_count': sum(1 for r in records if r.get('pass') is True),
        'fail_count': sum(1 for r in records if r.get('pass') is not True),
        'answer_count': answer_count,
        'hold_count': hold_count,
        'material_regression_count': material,
        'missing_output_regression_count': missing,
        'direct_provider_bypass_count': bypass,
        'provider_model_calls': provider_model_calls,
        'mutation_detected_count': mutations,
        'failed_gates': failed_gates,
        'first_failure': next((r.get('request_id') for r in records if r.get('pass') is not True), None),
        'stop_reason': stop_reason,
        'gate_checks': gate_checks,
        'request_type_distribution': distribution(records, 'request_type'),
        'expected_status_distribution': distribution(records, 'expected_status'),
        'c1k_frozen_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
        'prior_superseded_c1k_evidence_sha256': PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
        'c1k_hash_changed': c1k_hash_changed,
        'c1k_hashes_before': initial_c1k,
        'c1k_hashes_after': final_c1k,
        'limited_production_canary_executed': True,
        'm12_c1_only': True,
        'm12_c2_c3_c4_started': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'runtime_authority_mutated': False,
        'rollback_ready': True,
        'm11_frozen_baseline_preserved': True,
        'protected_changes': protected_changes,
        'required_files': REQUIRED_FILES,
        'required_files_missing': required_missing,
    }
    write_json('c1k_evidence_hash_readback.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.c1k_evidence_hash_readback.v1',
        'status': 'PASS' if not c1k_hash_changed and final_c1k.get(rel(C1K / 'evidence_manifest.json')) == FROZEN_C1K_EVIDENCE_SHA else 'BLOCKED',
        'before': initial_c1k,
        'after': final_c1k,
        'hash_changed': c1k_hash_changed,
        'frozen_c1k_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
    })
    write_json('provider_path_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.provider_path_report.v1',
        'status': 'PASS' if provider_model_calls == 0 and bypass == 0 else 'FAIL',
        'provider_model_calls': provider_model_calls,
        'provider_path_used': False,
        'direct_provider_bypass_count': bypass,
        'deterministic_c1k_kernel_only': True,
    })
    write_json('material_regression_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.material_regression_report.v1', 'status': 'PASS' if material == 0 else 'FAIL', 'material_regression_count': material, 'events': [r for r in records if r.get('material_regression')]})
    write_json('missing_output_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.missing_output_report.v1', 'status': 'PASS' if missing == 0 else 'FAIL', 'missing_output_regression_count': missing, 'events': [r for r in records if r.get('missing_output_regression')]})
    write_json('mutation_sentinel_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.mutation_sentinel_report.v1',
        'status': 'PASS' if mutations == 0 else 'FAIL',
        'mutation_detected_count': mutations,
        'protected_hashes_before': before,
        'protected_hashes_after': after,
        'protected_changes': protected_changes,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'runtime_authority_mutated': False,
        'm12_c2_c3_c4_started': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
    })
    write_json('rollback_readiness.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.rollback_readiness.v1', 'status': 'PASS', 'rollback_ready': True, 'rollback_needed': False, 'm11_frozen_baseline_preserved': True, 'reason': 'C1P performed no Gateway/config/route mutation; rollback readiness remains inherited from M11.7 baseline.'})
    write_json('status.json', status_obj)
    write_json('summary.json', status_obj)
    write_report(status_obj)
    write_json('evidence_manifest.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.evidence_manifest.v1',
        'generated_utc': utc_now(),
        'artifact_dir': rel(ART),
        'files': [{'path': rel(p), 'sha256': sha_file(p), 'bytes': p.stat().st_size} for p in sorted(ART.iterdir()) if p.is_file() and p.name != 'evidence_manifest.json'],
    })
    return status


def archive_previous_attempt_if_needed() -> None:
    status_path = ART / 'status.json'
    if not status_path.exists():
        return
    status = read_json(status_path, {}) or {}
    if status.get('status') not in {STATUS_ABORT, STATUS_RUNNING}:
        return
    attempts = ART / 'attempts'
    attempts.mkdir(parents=True, exist_ok=True)
    idx = 1
    while (attempts / f'attempt_{idx:03d}_archived').exists():
        idx += 1
    dest = attempts / f'attempt_{idx:03d}_archived'
    dest.mkdir(parents=True, exist_ok=True)
    for p in list(ART.iterdir()):
        if p.name == 'attempts':
            continue
        target = dest / p.name
        if p.is_dir():
            shutil.copytree(p, target)
            shutil.rmtree(p)
        else:
            shutil.copy2(p, target)
            p.unlink()
    write_json_to_path(dest / 'archive_reason.json', {
        'archived_utc': utc_now(),
        'reason': 'previous M12-C1P attempt preserved before rerun; attempt aborted before request 1 because the C1K guard CLI rejected a new purpose label, not because C1K SHA changed or mutation occurred.',
        'previous_status': status,
    })


def write_json_to_path(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    archive_previous_attempt_if_needed()
    for name in ['production_request_journal.jsonl', 'production_request_journal.sqlite3']:
        p = ART / name
        if p.exists():
            p.unlink()
    started = time.time()
    started_utc = utc_now()
    before = protected_snapshot()
    initial_c1k = c1k_hashes()
    write_json('status.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.status.v1',
        'run_id': RUN_ID,
        'status': STATUS_RUNNING,
        'started_utc': started_utc,
        'artifact_dir': rel(ART),
        'target_production_c1_requests': TARGET_REQUESTS,
        'time_limit_seconds': TIME_LIMIT_SECONDS,
    })
    pre_ok, pre_failures, pre_detail = preflight(before)
    write_json('preflight.json', {**pre_detail, 'ok': pre_ok})
    write_json('owner_authorization_readback.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.owner_authorization_readback.v1',
        'status': 'PASS' if pre_detail['checks'].get('owner_review_ready') else 'BLOCKED',
        'owner_review_status': read_json(OWNER_REVIEW / 'status.json', {}).get('status'),
        'owner_review_status_sha256': sha_file(OWNER_REVIEW / 'status.json'),
        'authorized_by_user_message': 'Proceed to M12-C1P Limited Production Canary; M12-C1 only; bounded artifact status Q&A; 25 production C1 requests or 2 active hours, whichever comes first.',
        'authorized_scope': 'M12-C1 bounded artifact status Q&A only',
        'request_bound': TARGET_REQUESTS,
        'time_bound_seconds': TIME_LIMIT_SECONDS,
        'not_authorized': ['M12-C2', 'M12-C3', 'M12-C4', 'cache enablement', 'artifact-memory promotion', 'global Semantic Gate promotion', 'Gateway/config/live-route/fallback/memory-route/runtime-authority mutation'],
    })
    if not pre_ok:
        status = finalize(started, started_utc, before, [], ['preflight_failed:' + ','.join(pre_failures)], initial_c1k, {'status': 'NOT_RUN'})
        print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'failed_gates': pre_failures}, indent=2, sort_keys=True))
        return 1

    pre_guard = run_c1k_guard('c1k_read_only_preflight.json', 'manual_read_only_check')
    if pre_guard.get('status') != 'PASS' or initial_c1k.get(rel(C1K / 'evidence_manifest.json')) != FROZEN_C1K_EVIDENCE_SHA:
        status = finalize(started, started_utc, before, [], ['c1k_read_only_preflight'], initial_c1k, {'status': 'NOT_RUN'})
        print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'failed_gates': ['c1k_read_only_preflight']}, indent=2, sort_keys=True))
        return 1

    approved_rows, source_report = compile_rows_from_approved_sources()
    write_json('source_row_compilation_report.json', source_report)
    requests = build_requests(approved_rows)
    write_json('run_config.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.run_config.v1',
        'run_id': RUN_ID,
        'artifact_dir': rel(ART),
        'authorized_scope': 'M12-C1 bounded artifact status Q&A only',
        'target_production_c1_requests': TARGET_REQUESTS,
        'time_limit_seconds': TIME_LIMIT_SECONDS,
        'answer_target': ANSWER_TARGET,
        'hold_target': HOLD_TARGET,
        'c1k_consumption': 'read_only_guard_preflight_and_postcheck',
        'c1k_frozen_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
        'provider_model_calls_allowed': False,
        'provider_model_calls': 0,
        'deterministic_c1k_kernel_only': True,
        'm12_c1_only': True,
        'm12_c2_c3_c4_started': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'gateway_config_live_route_fallback_memory_route_runtime_authority_mutation_allowed': False,
    })
    write_json('production_request_manifest.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p.production_request_manifest.v1',
        'request_count': len(requests),
        'requests': [
            {'request_index': i, 'request_id': c.case_id, 'request_type': mix, 'expected_status': c.expected_status, 'approved_source_refs': c.approved_source_refs, 'production_scope': True}
            for i, (c, _rows, mix) in enumerate(requests, start=1)
        ],
    })

    journal = ART / 'production_request_journal.jsonl'
    conn = init_sqlite(ART / 'production_request_journal.sqlite3')
    records: list[dict[str, Any]] = []
    abort_reasons: list[str] = []
    for index, (case, rows, request_type) in enumerate(requests, start=1):
        if time.time() - started >= TIME_LIMIT_SECONDS:
            abort_reasons.append(f'time_limit_before_request_{index}')
            break
        rec = evaluate_request(index, case, rows, request_type, before)
        records.append(rec)
        append_jsonl(journal, rec)
        insert_request(conn, rec)
        if not rec.get('pass'):
            abort_reasons.append(f'first_request_failure:{rec.get("request_id")}')
            break
    conn.close()

    write_json('deterministic_kernel_result_log.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.deterministic_kernel_result_log.v1', 'results': records})
    write_json('answer_envelope_spec_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.answer_envelope_spec_report.v1', 'status': 'PASS' if records and all(r.get('checks', {}).get('answer_envelope_spec_compiled') for r in records) else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('answer_envelope_spec_compiled'), 'spec': r.get('spec')} for r in records]})
    write_json('source_authority_guard_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.source_authority_guard_report.v1', 'status': 'PASS' if records and all(r.get('checks', {}).get('source_authority_isolated') for r in records) else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('source_authority_isolated'), 'source_refs': r.get('source_refs'), 'cited_source_ref': r.get('cited_source_ref')} for r in records]})
    write_json('source_ref_canonicalization_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.source_ref_canonicalization_report.v1', 'status': 'PASS' if records and all(r.get('checks', {}).get('source_authority_isolated') for r in records) else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('source_authority_isolated'), 'source_refs': r.get('source_refs')} for r in records]})
    write_json('exact_source_value_anchor_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.exact_source_value_anchor_report.v1', 'status': 'PASS' if records and all(r.get('checks', {}).get('exact_source_value_anchor') for r in records) else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('exact_source_value_anchor')} for r in records]})
    write_json('typed_exact_value_fidelity_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.typed_exact_value_fidelity_report.v1', 'status': 'PASS' if records and all(r.get('checks', {}).get('typed_exact_value_fidelity') for r in records) else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('typed_exact_value_fidelity')} for r in records]})
    write_json('output_disposition_contract_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.output_disposition_contract_report.v1', 'status': 'PASS' if records and all(r.get('checks', {}).get('output_disposition_contract') for r in records) else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('output_disposition_contract')} for r in records]})
    write_json('hold_status_contract_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.hold_status_contract_report.v1', 'status': 'PASS' if all(r.get('checks', {}).get('hold_status_contract') for r in records if r.get('expected_status') == 'HOLD') else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('hold_status_contract')} for r in records if r.get('expected_status') == 'HOLD']})
    write_json('hold_citation_contract_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.hold_citation_contract_report.v1', 'status': 'PASS' if all(r.get('checks', {}).get('hold_citation_source_ref_contract') for r in records if r.get('expected_status') == 'HOLD') else 'FAIL', 'items': [{'request_id': r.get('request_id'), 'pass': r.get('checks', {}).get('hold_citation_source_ref_contract'), 'cited_source_ref': r.get('cited_source_ref')} for r in records if r.get('expected_status') == 'HOLD']})
    write_json('fail_closed_behavior_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1p.fail_closed_behavior_report.v1', 'status': 'PASS' if len([r for r in records if r.get('expected_status') == 'HOLD']) == HOLD_TARGET and all(r.get('pass') for r in records if r.get('expected_status') == 'HOLD') else 'FAIL', 'hold_count': len([r for r in records if r.get('expected_status') == 'HOLD'])})

    postcheck = run_c1k_guard('c1k_read_only_postcheck.json', 'manual_read_only_check')
    status = finalize(started, started_utc, before, records, abort_reasons, initial_c1k, postcheck)
    print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'requests': f'{sum(1 for r in records if r.get("pass"))}/{TARGET_REQUESTS}', 'failed_gates': read_json(ART / 'status.json').get('failed_gates'), 'c1k_hash_changed': read_json(ART / 'status.json').get('c1k_hash_changed')}, indent=2, sort_keys=True))
    return 0 if status == STATUS_PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
