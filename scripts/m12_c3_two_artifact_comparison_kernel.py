#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from m12_c3_source_authority_guard import (
    has_prompt_injection_like_text,
    text_reasons,
    validate_comparison_envelope,
)

C3Status = Literal['CONSISTENT', 'CONFLICT', 'HOLD', 'REJECT']
KernelStatus = Literal['PASS', 'HOLD', 'REJECT']
FORBIDDEN_SOURCE_KINDS = {'memory', 'daily_memory', 'context_bridge', 'runtime_metadata', 'arbitrary_path'}
EXTERNAL_ACTION_RE = re.compile(r'\b(send|email|post|publish|tweet|message|call|delete|deploy|apply|restart|stop|start|install|upload|write to production)\b', re.I)
FORBIDDEN_AUTHORITY_RE = re.compile(r'\b(exact code|edit code|change config|routing|fallback|safety authority|runtime authority|gateway config|runtime config|configuration mutation)\b', re.I)
C4_PROPOSAL_RE = re.compile(r'\b(proposal|draft a plan|recommend next steps|remediation plan|merge plan|reconcile|resolution plan|C4)\b', re.I)
ALLOWED_VALUE_TYPES = {'string', 'status', 'number', 'boolean', 'null'}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def _stable_id(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.strip().lower()).strip('_') or 'field'


@dataclass(frozen=True)
class SourceRow:
    field_id: str
    value: Any
    value_type: str
    section_id: str
    section_title: str
    source_ref_id: str
    quote: str
    artifact_id: str = ''
    path: str = ''
    sha256: str = ''

    def canonical_value(self) -> Any:
        if self.value_type == 'number':
            return float(self.value)
        if self.value_type == 'boolean':
            return bool(self.value)
        if self.value_type == 'null':
            return None
        if self.value_type in {'string', 'status'}:
            return str(self.value).strip()
        raise ValueError(f'incomparable value_type: {self.value_type}')

    def source_ref(self) -> dict[str, Any]:
        return {
            'source_ref_id': self.source_ref_id,
            'artifact_id': self.artifact_id,
            'path': self.path,
            'sha256': self.sha256,
            'section_id': self.section_id,
            'section_title': self.section_title,
            'field_id': self.field_id,
            'quote_hash': sha_text(self.quote),
        }


@dataclass(frozen=True)
class ApprovedArtifactHandle:
    artifact_id: str
    path: str
    sha256: str
    source_rows: list[SourceRow] = field(default_factory=list)
    text: str | None = None
    approved: bool = True
    source_kind: str = 'approved_artifact'
    stale: bool = False
    missing: bool = False
    ambiguous: bool = False
    approval_record: str = 'owner_approved_fixture'
    alias: str | None = None


@dataclass(frozen=True)
class C3ComparisonCase:
    case_id: str
    question: str
    expected_status: C3Status
    handles: list[ApprovedArtifactHandle]
    compared_fields: list[str]
    allow_hold_no_source_refs: bool = False
    expected_reason: str | None = None


@dataclass(frozen=True)
class ComparisonEnvelopeSpec:
    case_id: str
    expected_status: C3Status
    artifact_ids: set[str]
    approved_source_refs: set[str]
    approved_section_ids: set[str]
    compared_fields: list[str]
    hold_reason: str | None = None
    reject_reason: str | None = None
    allow_hold_no_source_refs: bool = False


@dataclass(frozen=True)
class KernelResult:
    status: KernelStatus
    envelope: dict[str, Any]
    spec: ComparisonEnvelopeSpec
    rows: list[SourceRow]
    guard: dict[str, Any]
    reasons: list[str] = field(default_factory=list)


def source_row(field_id: str, value: Any, value_type: str, *, section: str = 'status', quote: str | None = None) -> SourceRow:
    section_id = f'section:{_stable_id(section)}'
    source_ref_id = f'pending#{section_id}#{_stable_id(field_id)}'
    return SourceRow(
        field_id=field_id,
        value=value,
        value_type=value_type,
        section_id=section_id,
        section_title=section,
        source_ref_id=source_ref_id,
        quote=quote or f'{field_id}: {value}',
    )


def artifact_handle_from_rows(
    artifact_id: str,
    rows: list[SourceRow],
    *,
    path: str | None = None,
    approved: bool = True,
    source_kind: str = 'approved_artifact',
    stale: bool = False,
    missing: bool = False,
    ambiguous: bool = False,
    text: str | None = None,
    alias: str | None = None,
) -> ApprovedArtifactHandle:
    path = path or f'approved://{artifact_id}.json'
    row_payload = [{'field_id': r.field_id, 'value': r.value, 'value_type': r.value_type, 'section_id': r.section_id, 'section_title': r.section_title, 'quote': r.quote} for r in rows]
    body = text if text is not None else canonical_json(row_payload)
    sha = sha_text(body)
    enriched: list[SourceRow] = []
    for r in rows:
        sid = r.section_id
        ref = f'{artifact_id}#{sid}#{_stable_id(r.field_id)}'
        enriched.append(SourceRow(r.field_id, r.value, r.value_type, sid, r.section_title, ref, r.quote, artifact_id, path, sha))
    return ApprovedArtifactHandle(
        artifact_id=artifact_id,
        path=path,
        sha256=sha,
        source_rows=enriched,
        text=body,
        approved=approved,
        source_kind=source_kind,
        stale=stale,
        missing=missing,
        ambiguous=ambiguous,
        alias=alias,
    )


def _is_arbitrary_path(path: str) -> bool:
    return str(path).startswith(('/', './', '../')) or '/memory/' in str(path) or str(path).startswith('memory/')


def validate_case_manifest(case: C3ComparisonCase) -> None:
    if case.expected_status not in {'CONSISTENT', 'CONFLICT', 'HOLD', 'REJECT'}:
        raise ValueError('expected_status must be CONSISTENT, CONFLICT, HOLD, or REJECT')
    if not case.case_id:
        raise ValueError('case_id required')
    if not isinstance(case.handles, list):
        raise ValueError('handles must be a list')
    if not isinstance(case.compared_fields, list):
        raise ValueError('compared_fields must be a list')


def _reason_for_case(case: C3ComparisonCase) -> tuple[C3Status | None, str | None]:
    handles = case.handles
    q = case.question or ''
    if len(handles) > 2:
        return 'REJECT', 'more_than_two_artifacts'
    if len(handles) < 2:
        return 'REJECT', 'artifact_count_not_two'
    q_flags = text_reasons(q)
    if 'arbitrary_path_forbidden' in q_flags:
        return 'REJECT', 'arbitrary_path_forbidden'
    if any(f in q_flags for f in {'memory_source_forbidden', 'daily_memory_source_forbidden', 'context_bridge_source_forbidden'}):
        return 'HOLD', 'unapproved_source_authority'
    if C4_PROPOSAL_RE.search(q):
        return 'REJECT', 'c4_or_proposal_drafting_forbidden'
    if EXTERNAL_ACTION_RE.search(q):
        return 'HOLD', 'external_action_required'
    if FORBIDDEN_AUTHORITY_RE.search(q):
        return 'HOLD', 'requires_runtime_config_or_safety_authority'
    if not case.compared_fields:
        return 'HOLD', 'incomparable_fields'
    if len(set(h.artifact_id for h in handles)) != 2:
        return 'HOLD', 'ambiguous_artifact'
    for h in handles:
        hay = (h.path or '') + '\n' + (h.text or '') + '\n' + q
        if h.missing or h.text is None:
            return 'HOLD', 'missing_artifact'
        if h.stale:
            return 'HOLD', 'stale_artifact'
        if h.ambiguous:
            return 'HOLD', 'ambiguous_artifact'
        if not h.approved or h.source_kind in FORBIDDEN_SOURCE_KINDS:
            return 'HOLD', 'unapproved_artifact'
        if _is_arbitrary_path(h.path) or h.source_kind == 'arbitrary_path':
            return 'REJECT', 'arbitrary_path_forbidden'
        flags = text_reasons(h.path + '\n' + q)
        if any(f in flags for f in {'memory_source_forbidden', 'daily_memory_source_forbidden', 'context_bridge_source_forbidden', 'arbitrary_path_forbidden'}):
            return 'HOLD', 'unapproved_source_authority'
        if has_prompt_injection_like_text(h.text or ''):
            return 'HOLD', 'prompt_injection_risk'
    return None, None


def compile_source_rows(handles: list[ApprovedArtifactHandle]) -> list[SourceRow]:
    out: list[SourceRow] = []
    for h in handles:
        for r in h.source_rows:
            out.append(r)
    return sorted(out, key=lambda r: (r.artifact_id, r.field_id, r.section_id, r.source_ref_id))


def compile_comparison_envelope_spec(case: C3ComparisonCase, rows: list[SourceRow], forced_status: C3Status | None, reason: str | None) -> ComparisonEnvelopeSpec:
    artifact_ids = {h.artifact_id for h in case.handles if h.artifact_id}
    return ComparisonEnvelopeSpec(
        case_id=case.case_id,
        expected_status=forced_status or case.expected_status,
        artifact_ids=artifact_ids,
        approved_source_refs={r.source_ref_id for r in rows},
        approved_section_ids={r.section_id for r in rows},
        compared_fields=sorted(set(case.compared_fields)),
        hold_reason=reason if forced_status == 'HOLD' else None,
        reject_reason=reason if forced_status == 'REJECT' else None,
        allow_hold_no_source_refs=case.allow_hold_no_source_refs or reason in {'missing_artifact', 'artifact_count_not_two', 'more_than_two_artifacts', 'unapproved_artifact', 'arbitrary_path_forbidden'},
    )


def _base_disposition(status: C3Status) -> dict[str, Any]:
    return {
        'status': status.lower(),
        'production_expansion_applied': False,
        'mutation_applied': False,
        'external_action_executed': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'c4_started': False,
        'model_owned_authority': False,
    }


def _failure_envelope(status: C3Status, reason: str | None, rows: list[SourceRow]) -> dict[str, Any]:
    cited = [r.source_ref() for r in rows[:2]]
    env: dict[str, Any] = {
        'status': status,
        'artifact_a_ref': None,
        'artifact_b_ref': None,
        'compared_fields': [],
        'agreement_points': [],
        'conflict_points': [],
        'cited_source_refs': cited,
        'disposition': _base_disposition(status),
        'authority': 'no_authority',
        'authoritative_comparison_result': False,
    }
    if status == 'HOLD':
        env['hold_reason'] = reason or 'fail_closed'
    else:
        env['reject_reason'] = reason or 'guard_reject'
    return env


def _artifact_ref(handle: ApprovedArtifactHandle) -> dict[str, Any]:
    return {
        'artifact_id': handle.artifact_id,
        'path': handle.path,
        'sha256': handle.sha256,
        'approval_record': handle.approval_record,
    }


def _row_map(handle: ApprovedArtifactHandle) -> dict[str, SourceRow]:
    return {r.field_id: r for r in handle.source_rows}


def _values_equal(a: SourceRow, b: SourceRow) -> bool:
    if a.value_type != b.value_type:
        return False
    return a.canonical_value() == b.canonical_value()


def _value_payload(row: SourceRow) -> dict[str, Any]:
    return {'value': row.value, 'value_type': row.value_type, 'section_id': row.section_id, 'source_ref_id': row.source_ref_id}


def emit_comparison_envelope(case: C3ComparisonCase, handles: list[ApprovedArtifactHandle]) -> dict[str, Any]:
    a, b = handles[0], handles[1]
    rows_a = _row_map(a)
    rows_b = _row_map(b)
    agreement_points: list[dict[str, Any]] = []
    conflict_points: list[dict[str, Any]] = []
    cited: dict[str, dict[str, Any]] = {}
    compared_fields = sorted(set(case.compared_fields))
    for field in compared_fields:
        ra = rows_a.get(field)
        rb = rows_b.get(field)
        if ra is None or rb is None:
            conflict_type = 'missing_in_a' if ra is None else 'missing_in_b'
            refs = [r.source_ref() for r in [ra, rb] if r is not None]
            # Missing-side conflict still needs source provenance from the present side; envelope guard accepts both refs for non-missing conflicts only.
            if len(refs) < 2:
                # Use available refs; this case is still a deterministic CONFLICT point by source absence.
                pass
            for ref in refs:
                cited[ref['source_ref_id']] = ref
            conflict_points.append({
                'field': field,
                'artifact_a_value': _value_payload(ra) if ra else None,
                'artifact_b_value': _value_payload(rb) if rb else None,
                'source_refs': refs,
                'conflict_type': conflict_type,
            })
            continue
        if ra.value_type not in ALLOWED_VALUE_TYPES or rb.value_type not in ALLOWED_VALUE_TYPES:
            raise ValueError(f'incomparable field type: {field}')
        refs = [ra.source_ref(), rb.source_ref()]
        for ref in refs:
            cited[ref['source_ref_id']] = ref
        if _values_equal(ra, rb):
            agreement_points.append({
                'field': field,
                'artifact_a_value': _value_payload(ra),
                'artifact_b_value': _value_payload(rb),
                'source_refs': refs,
            })
        else:
            conflict_points.append({
                'field': field,
                'artifact_a_value': _value_payload(ra),
                'artifact_b_value': _value_payload(rb),
                'source_refs': refs,
                'conflict_type': 'value_mismatch' if ra.value_type == rb.value_type else 'semantic_incompatibility',
            })
    status: C3Status = 'CONFLICT' if conflict_points else 'CONSISTENT'
    envelope: dict[str, Any] = {
        'status': status,
        'artifact_a_ref': _artifact_ref(a),
        'artifact_b_ref': _artifact_ref(b),
        'compared_fields': compared_fields,
        'agreement_points': agreement_points,
        'conflict_points': conflict_points,
        'cited_source_refs': [cited[k] for k in sorted(cited)],
        'disposition': _base_disposition(status) | {'comparison_result': status.lower()},
        'authority': 'approved_two_artifacts_only',
        'authoritative_comparison_result': True,
    }
    return envelope


def compare_two_artifacts(case: C3ComparisonCase) -> KernelResult:
    validate_case_manifest(case)
    forced_status, reason = _reason_for_case(case)
    rows = compile_source_rows(case.handles)
    spec = compile_comparison_envelope_spec(case, rows, forced_status, reason)
    if forced_status in {'HOLD', 'REJECT'}:
        envelope = _failure_envelope(forced_status, reason, rows)
        kernel_status: KernelStatus = 'HOLD' if forced_status == 'HOLD' else 'REJECT'
    else:
        try:
            envelope = emit_comparison_envelope(case, case.handles)
            kernel_status = 'PASS'
        except ValueError as exc:
            reason = 'incomparable_fields'
            spec = compile_comparison_envelope_spec(case, rows, 'HOLD', reason)
            envelope = _failure_envelope('HOLD', reason, rows)
            kernel_status = 'HOLD'
    guard = validate_comparison_envelope(
        envelope,
        allowed_source_refs=spec.approved_source_refs,
        allowed_section_ids=spec.approved_section_ids,
        expected_artifact_ids=spec.artifact_ids,
        allow_hold_without_refs=spec.allow_hold_no_source_refs,
    )
    status = kernel_status if guard.accepted else 'REJECT'
    reasons = ([reason] if reason else []) + guard.reasons
    return KernelResult(status, envelope, spec, rows, guard.as_dict(), sorted(set(r for r in reasons if r)))


def result_digest(result: KernelResult) -> str:
    return sha_text(canonical_json({
        'status': result.status,
        'envelope': result.envelope,
        'spec': {
            'case_id': result.spec.case_id,
            'expected_status': result.spec.expected_status,
            'artifact_ids': sorted(result.spec.artifact_ids),
            'approved_source_refs': sorted(result.spec.approved_source_refs),
            'approved_section_ids': sorted(result.spec.approved_section_ids),
            'compared_fields': result.spec.compared_fields,
            'hold_reason': result.spec.hold_reason,
            'reject_reason': result.spec.reject_reason,
        },
        'guard': result.guard,
    }))
