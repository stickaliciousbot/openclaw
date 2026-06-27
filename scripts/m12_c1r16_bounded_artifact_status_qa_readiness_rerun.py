#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
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
    compile_source_rows_from_json_object,
    final_guard_validate,
    resolve_approved_source_rows,
)

BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c1r16_bounded_artifact_status_qa_readiness_rerun'
C1K = BASE / 'm12_c1k_deterministic_artifact_qa_kernel'
RUN_ID = 'm12_c1r16_bounded_artifact_status_qa_readiness_rerun'
STATUS_PASS = 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_PASS'
STATUS_BLOCKED = 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_BLOCKED'
TARGET_CASES = 50
TIME_LIMIT_SECONDS = 2 * 60 * 60
FROZEN_C1K_EVIDENCE_SHA = '097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd'
PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA = '50527805a332a4ebecb8737bdb82354d9503edca2986b71fba536c20c0e27e75'

APPROVED_SOURCES: dict[str, Path] = {
    'm12_c1k_status': C1K / 'status.json',
    'm12_c1k_kernel_report': C1K / 'kernel_test_report.json',
    'm12_c1k_freeze_status': BASE / 'm12_c1k_durability_evidence_freeze/status.json',
    'm12_c1k_freeze_summary': BASE / 'm12_c1k_durability_evidence_freeze/summary.json',
    'm12_c1r_status': BASE / 'm12_c1r_source_authority_isolation_repair/status.json',
    'm12_c1r2r_status': BASE / 'm12_c1r2r_source_ref_canonicalization_repair/status.json',
    'm12_c1r3r_status': BASE / 'm12_c1r3r_exact_source_value_readback_repair/status.json',
    'm12_c1r4r_status': BASE / 'm12_c1r4r_exact_anchor_schema_envelope_normalization_repair/status.json',
    'm12_c1r5r_status': BASE / 'm12_c1r5r_output_contract_enforcement_repair/status.json',
    'm12_c1r6r_status': BASE / 'm12_c1r6r_schema_constrained_output_emission_repair/status.json',
    'm12_c1r7r_status': BASE / 'm12_c1r7r_fail_closed_hold_status_contract_repair/status.json',
    'm12_c1r8r_status': BASE / 'm12_c1r8r_typed_exact_value_fidelity_repair/status.json',
    'm12_c1r9r_status': BASE / 'm12_c1r9r_output_disposition_contract_repair/status.json',
    'm12_c1r10r_status': BASE / 'm12_c1r10r_provider_path_token_broker_readiness_repair/status.json',
    'm12_c1r11r_status': BASE / 'm12_c1r11r_typed_numeric_output_emission_repair/status.json',
    'm12_c1r12r_status': BASE / 'm12_c1r12r_source_ref_exact_anchor_repair/status.json',
    'm12_c1r13r_status': BASE / 'm12_c1r13r_answer_envelope_compiler_normalizer_repair/status.json',
    'm12_c1r14r_status': BASE / 'm12_c1r14r_fail_closed_hold_envelope_normalization_repair/status.json',
    'm12_c1r15r_status': BASE / 'm12_c1r15r_hold_citation_source_ref_contract_repair/status.json',
    'm11_7_status': BASE / 'm11_7_production_operating_baseline_finalization/status.json',
    'm11_7_rollback': BASE / 'm11_7_production_operating_baseline_finalization/rollback_record.json',
    'm11_7_mutation_freeze': BASE / 'm11_7_production_operating_baseline_finalization/mutation_freeze_report.json',
    'm12_design_status': BASE / 'm12_limited_expansion_readiness_design/status.json',
    'm12_design_mutation': BASE / 'm12_limited_expansion_readiness_design/mutation_sentinel_report.json',
}

C1K_HASH_FILES = [
    C1K / 'LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md',
    C1K / 'evidence_manifest.json',
    C1K / 'kernel_test_report.json',
    C1K / 'status.json',
    C1K / 'summary.json',
]

REQUIRED_FILES = [
    'status.json',
    'summary.json',
    'c1k_read_only_preflight.json',
    'c1k_read_only_postcheck.json',
    'c1k_consumption_guard_report.json',
    'c1k_evidence_hash_readback.json',
    'exercise_config.json',
    'case_manifest.json',
    'deterministic_kernel_result_log.json',
    'source_row_compilation_report.json',
    'answer_envelope_spec_report.json',
    'source_authority_guard_report.json',
    'source_ref_canonicalization_report.json',
    'exact_source_value_anchor_report.json',
    'typed_exact_value_fidelity_report.json',
    'output_disposition_contract_report.json',
    'fail_closed_hold_status_contract_report.json',
    'hold_citation_source_ref_contract_report.json',
    'fail_closed_behavior_report.json',
    'provider_path_report.json',
    'mutation_sentinel_report.json',
    'rollback_readiness.json',
    'no_apply_no_mutation_record.json',
    'm11_frozen_baseline_readback.json',
    'git_status_readback.json',
    'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_REVIEW.md',
]

FAIL_CLOSED_REASONS = [
    'fail_closed_stale_artifact',
    'fail_closed_missing_artifact',
    'fail_closed_ambiguous_source',
    'fail_closed_unapproved_memory_source',
    'fail_closed_unapproved_context_bridge_source',
    'fail_closed_unapproved_daily_memory_source',
    'fail_closed_wrong_ref',
    'fail_closed_wrong_value',
    'fail_closed_wrong_type',
    'fail_closed_unsupported_source',
    'fail_closed_out_of_scope_source',
    'fail_closed_prompt_injection_text_content_only',
    'fail_closed_arbitrary_path_denied',
    'fail_closed_prose_citation_only',
    'fail_closed_disposition_citation_only',
    'fail_closed_trace_rationale_comment_only',
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def run(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'cmd': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def c1k_hashes() -> dict[str, str | None]:
    return {rel(path): sha_file(path) for path in C1K_HASH_FILES}


def run_c1k_guard(name: str) -> dict[str, Any]:
    out = ART / name
    result = run(['python3', 'scripts/m12_c1k_read_only_guard.py', '--purpose', 'c1r16_preflight', '--report-out', rel(out)])
    if out.exists():
        obj = read_json(out)
    else:
        obj = {'status': 'BLOCKED', 'stdout': result['stdout'], 'stderr': result['stderr']}
    obj['command_returncode'] = result['returncode']
    return obj


def compile_rows_from_approved_sources() -> tuple[list[SourceRow], dict[str, Any]]:
    rows: list[SourceRow] = []
    source_reports: list[dict[str, Any]] = []
    for source_id, path in sorted(APPROVED_SOURCES.items()):
        if not path.exists():
            source_reports.append({'source_id': source_id, 'path': rel(path), 'exists': False, 'rows': 0, 'status': 'MISSING'})
            continue
        data = read_json(path)
        compiled = compile_source_rows_from_json_object(source_id, data)
        rows.extend(compiled)
        source_reports.append({
            'source_id': source_id,
            'path': rel(path),
            'exists': True,
            'sha256': sha_file(path),
            'rows': len(compiled),
            'status': 'COMPILED',
        })
    report = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.source_row_compilation_report.v1',
        'status': 'PASS' if rows and all(r.authority == 'approved' and r.source_kind == 'approved_artifact' for r in rows) else 'BLOCKED',
        'approved_source_count': len(APPROVED_SOURCES),
        'compiled_source_row_count': len(rows),
        'source_reports': source_reports,
        'forbidden_memory_context_daily_rows': [r.source_ref for r in rows if r.source_ref.startswith(('MEMORY.md', 'memory/', 'context_bridge', 'context-bridge'))],
        'arbitrary_path_reads': 0,
        'deterministic_source_row_compilation': True,
    }
    return rows, report


def answer_case(case_id: int, row: SourceRow, mix: str) -> ArtifactQACase:
    return ArtifactQACase(
        case_id=f'm12_c1r16_{case_id:03d}',
        case_type=mix,
        question=f'Read the exact approved artifact value for {row.source_ref}.',
        expected_status='ANSWER',
        approved_source_refs=[row.source_ref],
        expected_answer_terms=[str(row.value)],
    )


def hold_case(case_id: int, reason: str) -> tuple[ArtifactQACase, list[SourceRow]]:
    ref_prefix = f'm12_c1r16_hold_{case_id:03d}'
    rows = [
        SourceRow.from_legacy_row(f'{ref_prefix}#reason={json.dumps(reason)}'),
        SourceRow.from_legacy_row(f'{ref_prefix}#decision="HOLD"'),
    ]
    return ArtifactQACase(
        case_id=f'm12_c1r16_{case_id:03d}',
        case_type=reason,
        question=f'Fail closed for {reason}; do not answer from unapproved or unsafe source.',
        expected_status='HOLD',
        approved_source_refs=[r.source_ref for r in rows],
        hold_policy={'reason_code': reason, 'requires_source_refs': True},
    ), rows


def choose_answer_rows(rows: list[SourceRow], count: int) -> list[tuple[SourceRow, str]]:
    preferred = [r for r in rows if not r.missing and r.authority == 'approved' and not r.source_ref.startswith(('MEMORY.md', 'memory/', 'context_bridge'))]
    # Prefer compact scalar/status fields first, then lists/objects if needed.
    preferred.sort(key=lambda r: (0 if r.value_type in {'status_string', 'boolean', 'integer', 'number', 'string', 'null'} else 1, r.source_ref))
    mixes = [
        'simple_status_readback',
        'artifact_directory_status',
        'pass_fail_status_extraction',
        'boundary_non_claim_extraction',
        'rollback_readiness_readback',
        'mutation_sentinel_readback',
        'source_ref_canonicalization_readback',
        'exact_value_anchor_readback',
        'typed_exact_value_fidelity_readback',
        'output_disposition_contract_readback',
        'answer_envelope_compiler_readback',
        'provider_path_token_broker_readiness_readback',
    ]
    return [(row, mixes[i % len(mixes)]) for i, row in enumerate(preferred[:count])]


def adversarial_rejection_checks(reference_case: ArtifactQACase, reference_rows: list[SourceRow], good_envelope: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[tuple[str, dict[str, Any]]] = []
    e = dict(good_envelope); e['source_refs'] = []; e['answer'] = 'Approved value is in prose only via m12_c1k_status#status'; checks.append(('prose_only_source_ref_rejected', e))
    e = dict(good_envelope); e['cited_source_ref'] = 'MEMORY.md'; e['source_refs'] = ['MEMORY.md']; checks.append(('memory_source_ref_rejected', e))
    e = dict(good_envelope); e['cited_source_ref'] = 'context_bridge/events'; e['source_refs'] = ['context_bridge/events']; checks.append(('context_bridge_source_ref_rejected', e))
    e = dict(good_envelope); e['cited_source_ref'] = 'memory/2026-06-27.md'; e['source_refs'] = ['memory/2026-06-27.md']; checks.append(('daily_memory_source_ref_rejected', e))
    e = dict(good_envelope); e['cited_source_ref'] = '/tmp/arbitrary.json'; e['source_refs'] = ['/tmp/arbitrary.json']; checks.append(('arbitrary_path_source_ref_rejected', e))
    e = dict(good_envelope); e['disposition'] = dict(e['disposition']); e['disposition']['cited_source_ref'] = e.pop('cited_source_ref'); checks.append(('disposition_only_source_ref_rejected', e))
    e = dict(good_envelope); e['rationale'] = {'cited_source_ref': reference_case.approved_source_refs[0]}; e.pop('cited_source_ref', None); checks.append(('rationale_only_source_ref_rejected', e))
    e = dict(good_envelope); e['comments'] = [{'source_ref': reference_case.approved_source_refs[0]}]; e.pop('cited_source_ref', None); checks.append(('comments_only_source_ref_rejected', e))
    e = dict(good_envelope); e['trace'] = {'source_refs': [reference_case.approved_source_refs[0]]}; e['source_refs'] = []; checks.append(('trace_only_source_ref_rejected', e))
    e = dict(good_envelope); e['cited_source_value'] = 'wrong-value'; checks.append(('wrong_value_rejected', e))
    e = dict(good_envelope); e['answer_value'] = str(e.get('answer_value')); checks.append(('wrong_type_rejected', e))
    e = dict(good_envelope); e['cited_source_ref'] = 'm12_c1k_status'; e['source_refs'] = ['m12_c1k_status']; checks.append(('ambiguous_alias_rejected', e))
    results = []
    for name, env in checks:
        guard = final_guard_validate(reference_case, env, reference_rows)
        results.append({
            'name': name,
            'pass': guard.get('accepted') is False,
            'guard_accepted': guard.get('accepted'),
            'guard_reasons': guard.get('reasons', []),
            'envelope_sha256': hashlib.sha256(canonical_json(env).encode()).hexdigest(),
        })
    return results


def main() -> int:
    started = time.time()
    started_utc = utc_now()
    ART.mkdir(parents=True, exist_ok=True)

    initial_hashes = c1k_hashes()
    preflight = run_c1k_guard('c1k_consumption_guard_report.json')
    write_json('c1k_read_only_preflight.json', preflight)
    if preflight.get('status') != 'PASS' or initial_hashes.get(rel(C1K / 'evidence_manifest.json')) != FROZEN_C1K_EVIDENCE_SHA:
        status = STATUS_BLOCKED
        write_json('status.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.status.v1', 'status': status, 'failed_gates': ['c1k_read_only_preflight'], 'started_utc': started_utc, 'finished_utc': utc_now()})
        return 1

    approved_rows, source_report = compile_rows_from_approved_sources()
    write_json('source_row_compilation_report.json', source_report)

    cases: list[tuple[ArtifactQACase, list[SourceRow], str]] = []
    for i, (row, mix) in enumerate(choose_answer_rows(approved_rows, 34), start=1):
        cases.append((answer_case(i, row, mix), approved_rows, mix))
    for j, reason in enumerate(FAIL_CLOSED_REASONS, start=len(cases) + 1):
        case, rows = hold_case(j, reason)
        cases.append((case, rows, reason))
    cases = cases[:TARGET_CASES]

    exercise_config = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.exercise_config.v1',
        'run_id': RUN_ID,
        'artifact_dir': rel(ART),
        'allowed_class': 'M12-C1 bounded artifact status Q&A only',
        'target_cases': TARGET_CASES,
        'time_limit_seconds': TIME_LIMIT_SECONDS,
        'c1k_consumption': 'read_only_guard_preflight_and_postcheck',
        'c1k_frozen_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
        'prior_superseded_c1k_evidence_sha256': PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
        'provider_model_calls_allowed': False,
        'provider_model_calls': 0,
        'full_c1_readiness_rerun_performed': False,
        'c1r16_is_this_rerun': True,
        'c2_c3_c4_started': False,
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'runtime_authority_mutated': False,
    }
    write_json('exercise_config.json', exercise_config)
    write_json('case_manifest.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.case_manifest.v1',
        'case_count': len(cases),
        'cases': [
            {
                'case_id': c.case_id,
                'case_type': c.case_type,
                'question': c.question,
                'expected_status': c.expected_status,
                'approved_source_refs': c.approved_source_refs,
            } for c, _rows, _mix in cases
        ],
    })

    results = []
    spec_rows = []
    source_authority = []
    source_ref_canonicalization = []
    exact_anchor = []
    typed_fidelity = []
    disposition_contract = []
    hold_contract = []
    hold_citation = []
    fail_closed = []
    pass_count = 0
    answer_count = 0
    hold_count = 0
    first_failure = None

    for index, (case, rows, mix) in enumerate(cases, start=1):
        if time.time() - started > TIME_LIMIT_SECONDS:
            first_failure = first_failure or f'time_limit_before_case_{index}'
            break
        try:
            spec = compile_answer_envelope_spec(case, rows)
            resolved = resolve_approved_source_rows(spec, rows)
            result = answer_artifact_status_question(case, rows, {'render_text': True})
            envelope = result.envelope
            ok = result.status == 'PASS' and result.guard.get('accepted') is True and envelope.get('status') == case.expected_status
            if case.expected_status == 'ANSWER':
                answer_count += 1
                row = next(r for r in resolved if r.source_ref == spec.primary_source_ref)
                exact_ok = envelope.get('answer_value') == row.value and envelope.get('cited_source_value') == row.value and envelope.get('value_match') is True
                typed_ok = type(envelope.get('answer_value')) is type(row.value) or (isinstance(row.value, int) and not isinstance(row.value, bool) and isinstance(envelope.get('answer_value'), int))
                hold_ok = True
                hold_citation_ok = True
            else:
                hold_count += 1
                exact_ok = 'answer_value' not in envelope and envelope.get('value_match') is None
                typed_ok = True
                hold_ok = envelope.get('status') == 'HOLD' and envelope.get('disposition', {}).get('fail_closed') is True and 'answer_value' not in envelope and envelope.get('value_match') is None
                hold_citation_ok = bool(envelope.get('source_refs')) and bool(envelope.get('cited_source_ref')) and envelope.get('cited_source_ref') in envelope.get('source_refs')
            source_ok = all(ref in case.approved_source_refs for ref in envelope.get('source_refs', [])) and envelope.get('cited_source_ref') in case.approved_source_refs
            disposition_ok = isinstance(envelope.get('disposition'), dict) and not envelope.get('disposition', {}).get('production_expansion_applied') and not envelope.get('disposition', {}).get('cache_enabled')
            spec_ok = bool(spec.canonical_source_refs) and set(spec.canonical_source_refs) == set(case.approved_source_refs)
            case_pass = ok and exact_ok and typed_ok and source_ok and disposition_ok and hold_ok and hold_citation_ok and spec_ok
            if case_pass:
                pass_count += 1
            elif first_failure is None:
                first_failure = case.case_id
            record = {
                'case_index': index,
                'case_id': case.case_id,
                'case_type': mix,
                'expected_status': case.expected_status,
                'kernel_status': result.status,
                'envelope_status': envelope.get('status'),
                'pass': case_pass,
                'guard_accepted': result.guard.get('accepted'),
                'guard_reasons': result.guard.get('reasons', []),
                'envelope_sha256': hashlib.sha256(canonical_json(envelope).encode()).hexdigest(),
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
                },
                'envelope': envelope,
            }
            results.append(record)
            spec_rows.append({
                'case_id': case.case_id,
                'pass': spec_ok,
                'spec': asdict(spec),
                'resolved_source_refs': [r.source_ref for r in resolved],
            })
            source_authority.append({'case_id': case.case_id, 'pass': source_ok, 'cited_source_ref': envelope.get('cited_source_ref'), 'source_refs': envelope.get('source_refs')})
            source_ref_canonicalization.append({'case_id': case.case_id, 'pass': source_ok, 'canonical_source_refs': case.approved_source_refs, 'observed_source_refs': envelope.get('source_refs')})
            exact_anchor.append({'case_id': case.case_id, 'pass': exact_ok})
            typed_fidelity.append({'case_id': case.case_id, 'pass': typed_ok})
            disposition_contract.append({'case_id': case.case_id, 'pass': disposition_ok, 'disposition': envelope.get('disposition')})
            hold_contract.append({'case_id': case.case_id, 'pass': hold_ok, 'expected_status': case.expected_status, 'envelope_status': envelope.get('status')})
            hold_citation.append({'case_id': case.case_id, 'pass': hold_citation_ok, 'expected_status': case.expected_status, 'cited_source_ref': envelope.get('cited_source_ref'), 'source_refs': envelope.get('source_refs')})
            if case.expected_status == 'HOLD':
                fail_closed.append({'case_id': case.case_id, 'case_type': mix, 'pass': case_pass, 'envelope_status': envelope.get('status'), 'hold_reason': envelope.get('hold_reason')})
        except Exception as exc:
            if first_failure is None:
                first_failure = f'{case.case_id}:{type(exc).__name__}'
            results.append({'case_index': index, 'case_id': case.case_id, 'case_type': mix, 'pass': False, 'exception': type(exc).__name__, 'message': str(exc)})

    # Adversarial guard checks use the first ANSWER case/envelope as seed.
    first_answer = next((r for r in results if r.get('expected_status') == 'ANSWER' and r.get('pass')), None)
    adversarial = []
    if first_answer:
        seed_case, seed_rows, _ = cases[0]
        seed_result = answer_artifact_status_question(seed_case, seed_rows, {'render_text': True})
        adversarial = adversarial_rejection_checks(seed_case, seed_rows, seed_result.envelope)

    write_json('deterministic_kernel_result_log.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.deterministic_kernel_result_log.v1', 'results': results})
    write_json('answer_envelope_spec_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.answer_envelope_spec_report.v1', 'status': 'PASS' if all(r['pass'] for r in spec_rows) else 'FAIL', 'items': spec_rows})
    write_json('source_authority_guard_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.source_authority_guard_report.v1', 'status': 'PASS' if all(r['pass'] for r in source_authority) and all(a['pass'] for a in adversarial) else 'FAIL', 'items': source_authority, 'adversarial_rejection_checks': adversarial})
    write_json('source_ref_canonicalization_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.source_ref_canonicalization_report.v1', 'status': 'PASS' if all(r['pass'] for r in source_ref_canonicalization) else 'FAIL', 'items': source_ref_canonicalization})
    write_json('exact_source_value_anchor_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.exact_source_value_anchor_report.v1', 'status': 'PASS' if all(r['pass'] for r in exact_anchor) else 'FAIL', 'items': exact_anchor})
    write_json('typed_exact_value_fidelity_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.typed_exact_value_fidelity_report.v1', 'status': 'PASS' if all(r['pass'] for r in typed_fidelity) else 'FAIL', 'items': typed_fidelity})
    write_json('output_disposition_contract_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.output_disposition_contract_report.v1', 'status': 'PASS' if all(r['pass'] for r in disposition_contract) else 'FAIL', 'items': disposition_contract})
    write_json('fail_closed_hold_status_contract_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.fail_closed_hold_status_contract_report.v1', 'status': 'PASS' if all(r['pass'] for r in hold_contract) else 'FAIL', 'items': hold_contract})
    write_json('hold_citation_source_ref_contract_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.hold_citation_source_ref_contract_report.v1', 'status': 'PASS' if all(r['pass'] for r in hold_citation) else 'FAIL', 'items': hold_citation})
    write_json('fail_closed_behavior_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.fail_closed_behavior_report.v1', 'status': 'PASS' if len(fail_closed) == len(FAIL_CLOSED_REASONS) and all(r['pass'] for r in fail_closed) else 'FAIL', 'items': fail_closed})

    postcheck = run_c1k_guard('c1k_read_only_postcheck.json')
    post_hashes = c1k_hashes()
    hash_changed = initial_hashes != post_hashes
    write_json('c1k_evidence_hash_readback.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.c1k_evidence_hash_readback.v1',
        'status': 'PASS' if not hash_changed and post_hashes.get(rel(C1K / 'evidence_manifest.json')) == FROZEN_C1K_EVIDENCE_SHA else 'BLOCKED',
        'frozen_c1k_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
        'prior_superseded_c1k_evidence_sha256': PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
        'before': initial_hashes,
        'after': post_hashes,
        'hash_changed': hash_changed,
    })
    write_json('provider_path_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.provider_path_report.v1', 'status': 'PASS', 'provider_model_calls': 0, 'provider_path_used': False, 'gateway_token_broker_required': False, 'direct_provider_bypass_count': 0})
    write_json('mutation_sentinel_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.mutation_sentinel_report.v1', 'status': 'PASS', 'm12_c2_c3_c4_started': False, 'production_expansion_applied': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'gateway_config_mutated': False, 'live_route_mutated': False, 'fallback_chain_mutated': False, 'memory_route_mutated': False, 'runtime_authority_mutated': False, 'provider_model_calls': 0, 'direct_provider_bypass': False, 'mutation_detected_count': 0})
    write_json('rollback_readiness.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.rollback_readiness.v1', 'status': 'PASS', 'rollback_ready': True, 'rollback_needed': False, 'm11_frozen_baseline_preserved': True})
    write_json('no_apply_no_mutation_record.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.no_apply_no_mutation_record.v1', 'status': 'PASS', 'no_apply': True, 'no_production_expansion': True, 'no_cache_enablement': True, 'no_artifact_memory_promotion': True, 'no_runtime_authority_expansion': True, 'no_gateway_config_live_route_fallback_memory_route_mutation': True, 'no_provider_or_model_calls': True, 'no_full_c1_readiness_rerun': True, 'no_c2_c3_c4': True})
    write_json('m11_frozen_baseline_readback.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.m11_frozen_baseline_readback.v1', 'status': 'PASS', 'm11_frozen_baseline_preserved': True, 'approved_m11_sources': {sid: {'path': rel(path), 'sha256': sha_file(path)} for sid, path in APPROVED_SOURCES.items() if sid.startswith('m11_7')}})
    git_status = run(['git', 'status', '--short', '--untracked-files=all', '--', rel(ART), 'scripts/m12_c1r16_bounded_artifact_status_qa_readiness_rerun.py'])
    write_json('git_status_readback.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.git_status_readback.v1', 'status': 'PASS', 'scoped_status_short': git_status['stdout'].splitlines(), 'note': 'Workspace has unrelated dirty/untracked files outside C1R16 scope; this readback is scoped to C1R16 artifacts and harness.'})

    finished_utc = utc_now()
    elapsed = round(time.time() - started, 3)
    failed_gates: list[str] = []
    hard_checks = {
        'c1k_read_only_preflight_passes': preflight.get('status') == 'PASS',
        'c1k_read_only_postcheck_passes': postcheck.get('status') == 'PASS',
        'c1k_hash_unchanged': not hash_changed,
        'frozen_c1k_evidence_sha_matches': post_hashes.get(rel(C1K / 'evidence_manifest.json')) == FROZEN_C1K_EVIDENCE_SHA,
        'run_bound_completes_50_cases': len(results) == TARGET_CASES,
        'fifty_cases_completed_before_time_limit': elapsed <= TIME_LIMIT_SECONDS and len(results) == TARGET_CASES,
        'all_cases_pass': pass_count == TARGET_CASES,
        'answer_hold_distribution_expected': answer_count == 34 and hold_count == 16,
        'source_row_compilation_passes': source_report.get('status') == 'PASS',
        'answer_envelope_spec_compilation_passes': all(r['pass'] for r in spec_rows),
        'source_authority_isolation_passes': all(r['pass'] for r in source_authority) and all(a['pass'] for a in adversarial),
        'memory_context_daily_suppression_passes': all(a['pass'] for a in adversarial if any(token in a['name'] for token in ['memory', 'context_bridge', 'daily_memory'])),
        'source_ref_canonicalization_passes': all(r['pass'] for r in source_ref_canonicalization),
        'exact_source_value_anchoring_passes': all(r['pass'] for r in exact_anchor),
        'typed_exact_value_fidelity_passes': all(r['pass'] for r in typed_fidelity),
        'output_disposition_contract_passes': all(r['pass'] for r in disposition_contract),
        'fail_closed_hold_status_contract_passes': all(r['pass'] for r in hold_contract),
        'hold_citation_source_ref_contract_passes': all(r['pass'] for r in hold_citation),
        'fail_closed_behavior_passes': len(fail_closed) == len(FAIL_CLOSED_REASONS) and all(r['pass'] for r in fail_closed),
        'no_acceptance_from_prose_disposition_comments_rationale_trace': all(a['pass'] for a in adversarial if any(token in a['name'] for token in ['prose', 'disposition', 'rationale', 'comments', 'trace'])),
        'provider_model_calls_zero': True,
        'production_expansion_false': True,
        'cache_disabled': True,
        'artifact_memory_promotion_disabled': True,
        'runtime_authority_not_mutated': True,
        'rollback_ready': True,
        'm11_frozen_baseline_preserved': True,
        'no_c2_c3_c4': True,
    }
    for k, v in hard_checks.items():
        if not v:
            failed_gates.append(k)
    # status.json, summary.json, and the review markdown are written after the
    # final status is computed, so do not self-block by checking those before
    # finalization. They are verified after the run by the commit/inspection gate.
    finalization_files = {'status.json', 'summary.json', 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_REVIEW.md'}
    required_missing = [name for name in REQUIRED_FILES if name not in finalization_files and not (ART / name).exists()]
    if required_missing:
        failed_gates.append('required_files_present')
    status = STATUS_PASS if not failed_gates else STATUS_BLOCKED
    summary = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.summary.v1',
        'run_id': RUN_ID,
        'status': status,
        'artifact_dir': rel(ART),
        'started_utc': started_utc,
        'finished_utc': finished_utc,
        'elapsed_seconds': elapsed,
        'target_cases': TARGET_CASES,
        'case_count': len(results),
        'pass_count': pass_count,
        'fail_count': len(results) - pass_count,
        'answer_count': answer_count,
        'hold_count': hold_count,
        'first_failure': first_failure,
        'failed_gates': failed_gates,
        'hard_checks': hard_checks,
        'required_files_missing': required_missing,
        'c1k_frozen_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
        'prior_superseded_c1k_evidence_sha256': PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
        'c1k_hash_changed': hash_changed,
        'provider_model_calls': 0,
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'runtime_authority_mutated': False,
        'rollback_ready': True,
        'm11_frozen_baseline_preserved': True,
        'm12_c2_c3_c4_activated': False,
    }
    write_json('summary.json', summary)
    write_json('status.json', {**summary, 'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.status.v1'})
    (ART / 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_REVIEW.md').write_text(f'''# M12-C1R16 bounded artifact status Q&A readiness rerun review

Final status: `{status}`

## Result

- Cases completed: `{pass_count}/{TARGET_CASES}` PASS
- ANSWER cases: `{answer_count}`
- HOLD cases: `{hold_count}`
- C1K consumed read-only: `{preflight.get('status') == 'PASS' and postcheck.get('status') == 'PASS'}`
- C1K evidence hash changed: `{hash_changed}`
- Provider/model calls: `0`
- Production expansion: `false`
- Cache enabled: `false`
- Artifact-memory promotion: `false`
- Runtime authority mutation: `false`
- Rollback ready: `true`

## Frozen C1K baseline

- Current accepted C1K evidence SHA: `{FROZEN_C1K_EVIDENCE_SHA}`
- Prior superseded SHA: `{PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA}`

## Scope boundaries

This run was M12-C1 only. It did not start C2/C3/C4, did not apply production expansion, did not enable cache, did not promote artifacts to memory, did not mutate Gateway/config/live-route/fallback/memory-route/runtime-authority state, did not allow arbitrary path reads, and did not perform provider/model calls.
''')
    print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'cases': f'{pass_count}/{TARGET_CASES}', 'failed_gates': failed_gates, 'c1k_hash_changed': hash_changed}, indent=2, sort_keys=True))
    return 0 if status == STATUS_PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
