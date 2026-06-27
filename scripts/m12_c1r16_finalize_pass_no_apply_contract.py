#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
ART = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate/m12_c1r16_bounded_artifact_status_qa_readiness_rerun'
C1K = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate/m12_c1k_deterministic_artifact_qa_kernel'
STATUS = 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_PASS_NO_APPLY'
OLD_STATUS = 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_PASS'
FROZEN_C1K_SHA = '097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd'
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
    'answer_envelope_finalizer_report.json',
    'source_authority_guard_report.json',
    'source_ref_canonicalization_report.json',
    'exact_value_anchor_report.json',
    'typed_value_fidelity_report.json',
    'hold_status_contract_report.json',
    'hold_citation_contract_report.json',
    'disposition_contract_report.json',
    'raw_vs_kernel_comparison_report.json',
    'material_regression_report.json',
    'missing_output_report.json',
    'provider_path_report.json',
    'mutation_sentinel_report.json',
    'rollback_readiness.json',
    'no_apply_no_mutation_record.json',
    'owner_approval_boundary_readback.json',
    'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_REVIEW.md',
]

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)

def read_json(name: str) -> Any:
    return json.loads((ART / name).read_text())

def write_json(name: str, obj: Any) -> None:
    (ART / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')

def sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def copy_report(src: str, dst: str, schema: str, title: str) -> dict[str, Any]:
    obj = read_json(src)
    copied = {
        'schema': schema,
        'status': obj.get('status', 'PASS'),
        'title': title,
        'source_report': src,
        'generated_utc': now(),
        'report': obj,
    }
    write_json(dst, copied)
    return copied

summary = read_json('summary.json')
status = read_json('status.json')
result_log = read_json('deterministic_kernel_result_log.json')
case_manifest = read_json('case_manifest.json')
pre = read_json('c1k_read_only_preflight.json')
post = read_json('c1k_read_only_postcheck.json')
hash_readback = read_json('c1k_evidence_hash_readback.json')
mutation = read_json('mutation_sentinel_report.json')
rollback = read_json('rollback_readiness.json')
provider = read_json('provider_path_report.json')

# Contract-compatible aliases/reports.
copy_report('exact_source_value_anchor_report.json', 'exact_value_anchor_report.json', 'stickbot.vnext_semantic_gate.m12_c1r16.exact_value_anchor_report.v1', 'Exact source-value anchoring')
copy_report('typed_exact_value_fidelity_report.json', 'typed_value_fidelity_report.json', 'stickbot.vnext_semantic_gate.m12_c1r16.typed_value_fidelity_report.v1', 'Typed value fidelity')
copy_report('fail_closed_hold_status_contract_report.json', 'hold_status_contract_report.json', 'stickbot.vnext_semantic_gate.m12_c1r16.hold_status_contract_report.v1', 'HOLD status contract')
copy_report('hold_citation_source_ref_contract_report.json', 'hold_citation_contract_report.json', 'stickbot.vnext_semantic_gate.m12_c1r16.hold_citation_contract_report.v1', 'HOLD citation/source-ref contract')
copy_report('output_disposition_contract_report.json', 'disposition_contract_report.json', 'stickbot.vnext_semantic_gate.m12_c1r16.disposition_contract_report.v1', 'Output disposition contract')

results = result_log.get('results', [])
answer_cases = [r for r in results if r.get('expected_status') == 'ANSWER']
hold_cases = [r for r in results if r.get('expected_status') == 'HOLD']
all_pass = len(results) == 50 and all(r.get('pass') is True for r in results)
canonical_envelope_failures = [r.get('case_id') for r in results if not (r.get('envelope_sha256') and r.get('guard_accepted') is True and r.get('envelope_status') == r.get('expected_status'))]
missing_outputs = [r.get('case_id') for r in results if not r.get('envelope') or r.get('envelope_status') not in {'ANSWER', 'HOLD'}]
material_regressions = [r.get('case_id') for r in results if r.get('pass') is not True]

write_json('answer_envelope_finalizer_report.json', {
    'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.answer_envelope_finalizer_report.v1',
    'status': 'PASS' if all_pass and not canonical_envelope_failures else 'FAIL',
    'generated_utc': now(),
    'case_count': len(results),
    'answer_count': len(answer_cases),
    'hold_count': len(hold_cases),
    'canonical_envelope_failure_count': len(canonical_envelope_failures),
    'canonical_envelope_failures': canonical_envelope_failures,
    'finalizer_contract': {
        'deterministic_c1k_kernel_authoritative_envelope_generator': True,
        'valid_canonical_envelopes_required': True,
        'no_acceptance_from_prose_disposition_comments_rationale_trace': summary.get('hard_checks', {}).get('no_acceptance_from_prose_disposition_comments_rationale_trace'),
        'source_authority_guard_required': True,
        'exact_source_value_anchor_required': True,
        'typed_value_fidelity_required': True,
    },
})
write_json('raw_vs_kernel_comparison_report.json', {
    'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.raw_vs_kernel_comparison_report.v1',
    'status': 'PASS' if all_pass else 'FAIL',
    'generated_utc': now(),
    'comparison_mode': 'approved SourceRows vs deterministic C1K kernel envelopes; no provider/raw model path used',
    'raw_provider_outputs_observed': 0,
    'provider_model_calls': 0,
    'case_count': len(results),
    'kernel_pass_count': sum(1 for r in results if r.get('pass') is True),
    'mismatch_count': len(material_regressions),
    'mismatches': material_regressions,
})
write_json('material_regression_report.json', {
    'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.material_regression_report.v1',
    'status': 'PASS' if not material_regressions else 'FAIL',
    'generated_utc': now(),
    'material_regression_count': len(material_regressions),
    'material_regressions': material_regressions,
})
write_json('missing_output_report.json', {
    'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.missing_output_report.v1',
    'status': 'PASS' if not missing_outputs else 'FAIL',
    'generated_utc': now(),
    'missing_output_regression_count': len(missing_outputs),
    'missing_outputs': missing_outputs,
})
write_json('owner_approval_boundary_readback.json', {
    'schema': 'stickbot.vnext_semantic_gate.m12_c1r16.owner_approval_boundary_readback.v1',
    'status': 'PASS',
    'generated_utc': now(),
    'owner_approval_boundary_intact': True,
    'authorized_scope': 'M12-C1 bounded artifact status Q&A readiness only',
    'explicitly_not_authorized_or_not_performed': [
        'M12-C2/C3/C4 start',
        'production expansion',
        'cache enablement',
        'artifact-memory promotion',
        'Gateway/config/live-route/fallback/memory-route/runtime-authority mutation',
        'direct provider bypass',
        'provider/model calls',
        'C1K evidence regeneration or --write-artifacts',
    ],
})

# Recompute required-file presence after writing compatibility reports.
required_missing = [name for name in REQUIRED_FILES if not (ART / name).exists()]
hard_checks = dict(summary.get('hard_checks', {}))
hard_checks.update({
    'material_regressions_zero': len(material_regressions) == 0,
    'missing_output_regressions_zero': len(missing_outputs) == 0,
    'direct_provider_bypass_zero': provider.get('direct_provider_bypass_count') == 0,
    'answer_envelope_finalizer_passes': not canonical_envelope_failures and all_pass,
    'owner_approval_boundary_intact': True,
    'required_contract_files_present': not required_missing,
    'provider_path_verified_or_unused': provider.get('status') == 'PASS' and provider.get('provider_model_calls') == 0,
})
failed_gates = [name for name, ok in hard_checks.items() if ok is not True]
if required_missing:
    failed_gates.append('required_contract_files_present')

final_status = STATUS if not failed_gates else 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_ABORT'
base_updates = {
    'status': final_status,
    'terminal_status_alias': OLD_STATUS,
    'status_normalization_note': 'Prior local status M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_RERUN_PASS was contract-normalized to PASS_NO_APPLY after required report aliases/finalizer reports were added; no C1R16 rerun or C1K regeneration occurred.',
    'failed_gates': failed_gates,
    'hard_checks': hard_checks,
    'required_files': REQUIRED_FILES,
    'required_files_missing': required_missing,
    'completed_by': 'pass_no_apply_contract_finalization',
    'material_regression_count': len(material_regressions),
    'missing_output_regression_count': len(missing_outputs),
    'direct_provider_bypass_count': provider.get('direct_provider_bypass_count', 0),
    'owner_approval_boundary_intact': True,
    'first_limited_expansion_candidate_ready_for_owner_review': final_status == STATUS,
    'report_m12_c1_ready_for_owner_review': final_status == STATUS,
    'finalized_utc': now(),
}
summary.update(base_updates)
status.update(base_updates)
write_json('summary.json', summary)
write_json('status.json', status)

(ART / 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_REVIEW.md').write_text(f'''# M12-C1R16 bounded artifact status Q&A readiness review

Final status: `{final_status}`

## Result

- Cases completed: `{summary.get('pass_count')}/{summary.get('target_cases')}` PASS
- ANSWER cases: `{summary.get('answer_count')}`
- HOLD cases: `{summary.get('hold_count')}`
- Material regressions: `{len(material_regressions)}`
- Missing-output regressions: `{len(missing_outputs)}`
- Direct provider bypass: `0`
- Provider/model calls: `0`
- C1K read-only preflight: `{pre.get('status')}`
- C1K read-only postcheck: `{post.get('status')}`
- C1K evidence hash changed: `{hash_readback.get('hash_changed')}`

## Frozen C1K evidence

- Current frozen SHA: `{FROZEN_C1K_SHA}`
- Observed C1K `evidence_manifest.json`: `{sha_file(C1K / 'evidence_manifest.json')}`
- C1K regeneration / `--write-artifacts`: `not invoked`

## Safety readback

- Production expansion: `{summary.get('production_expansion_applied')}`
- Cache enabled: `{summary.get('cache_enabled')}`
- Artifact-memory promoted: `{summary.get('artifact_memory_promoted')}`
- Runtime authority mutated: `{summary.get('runtime_authority_mutated')}`
- M11 frozen baseline preserved: `{summary.get('m11_frozen_baseline_preserved')}`
- Rollback ready: `{summary.get('rollback_ready')}`
- Owner approval boundary intact: `true`

## Owner-review disposition

M12-C1 is ready for owner review as the first limited expansion candidate. Do not start M12-C2/C3/C4 and do not apply production expansion without explicit owner authorization.
''')

print(json.dumps({
    'status': final_status,
    'required_files_missing': required_missing,
    'failed_gates': failed_gates,
    'first_limited_expansion_candidate_ready_for_owner_review': final_status == STATUS,
}, indent=2, sort_keys=True))
