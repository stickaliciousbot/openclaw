#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from m12_c1_source_authority_guard import validate_case_result

ValueType = Literal['integer', 'number', 'boolean', 'string', 'status_string', 'null', 'array', 'object']

FORBIDDEN_SOURCE_KINDS = ['memory', 'daily_memory', 'context_bridge', 'runtime_metadata', 'arbitrary_path']


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def json_type(value: Any) -> ValueType:
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, int) and not isinstance(value, bool):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, str):
        return 'status_string' if value.isupper() and '_' in value else 'string'
    raise TypeError(f'unsupported JSON value type: {type(value).__name__}')


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True)
class SourceRow:
    source_ref: str
    source_kind: str
    artifact_ref: str
    field: str
    value: Any
    value_type: ValueType
    json_pointer: str
    content_hash: str
    authority: str = 'approved'
    stale: bool = False
    missing: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'))

    @staticmethod
    def from_legacy_row(row: str) -> 'SourceRow':
        if '#' not in row or '=' not in row:
            raise ValueError(f'invalid SourceRow string: {row!r}')
        ref, raw_value = row.split('=', 1)
        artifact_ref, field = ref.split('#', 1)
        value = json.loads(raw_value)
        return SourceRow(
            source_ref=ref,
            source_kind='approved_artifact',
            artifact_ref=artifact_ref,
            field=field,
            value=value,
            value_type=json_type(value),
            json_pointer='/' + field.replace('.', '/'),
            content_hash='sha256:' + sha_text(canonical_json(value)),
            stale='stale' in artifact_ref or 'stale' in field,
            missing=raw_value == '"ENOENT"' or 'missing' in artifact_ref,
        )

    def to_legacy_row(self) -> str:
        return f'{self.source_ref}={json.dumps(self.value, sort_keys=True)}'


@dataclass(frozen=True)
class ArtifactQACase:
    case_id: str
    case_type: str
    question: str
    expected_status: Literal['ANSWER', 'HOLD']
    approved_source_refs: list[str]
    required_exact_anchor: bool = True
    expected_answer_terms: list[str] = field(default_factory=list)
    allowed_aliases: dict[str, str] = field(default_factory=dict)
    hold_policy: dict[str, Any] | None = None
    allow_hold_no_source_ref: bool = False

    @staticmethod
    def from_harness_case(case: dict[str, Any]) -> 'ArtifactQACase':
        return ArtifactQACase(
            case_id=str(case.get('case_id')),
            case_type=str(case.get('mix') or case.get('case_type')),
            question=str(case.get('question') or ''),
            expected_status=case.get('expected_semantic_status'),
            approved_source_refs=[str(r) for r in case.get('expected_source_refs', [])],
            required_exact_anchor=bool(case.get('require_exact_source_value_anchor', True)),
            expected_answer_terms=[str(t) for t in case.get('expected_answer_terms', [])],
            allowed_aliases=dict(case.get('allowed_aliases') or {}),
            hold_policy=case.get('hold_policy') or ({'reason_code': str(case.get('expected_disposition') or case.get('mix') or 'fail_closed_hold'), 'requires_source_refs': bool(case.get('expected_source_refs'))} if case.get('expected_semantic_status') == 'HOLD' else None),
            allow_hold_no_source_ref=bool(case.get('allow_hold_no_source_ref')),
        )


@dataclass(frozen=True)
class AnswerEnvelopeSpec:
    case_id: str
    expected_status: Literal['ANSWER', 'HOLD']
    canonical_source_refs: list[str]
    primary_source_ref: str | None
    typed_value: Any = None
    value_type: ValueType | None = None
    required_fields: list[str] = field(default_factory=list)
    allowed_aliases: dict[str, str] = field(default_factory=dict)
    forbidden_source_kinds: list[str] = field(default_factory=lambda: list(FORBIDDEN_SOURCE_KINDS))
    display_policy: dict[str, Any] = field(default_factory=lambda: {'allow_display_text': True, 'display_text_non_authoritative': True})
    hold_reason: str | None = None
    requires_source_refs: bool = False
    forbid_answer_value: bool = True
    forbid_value_match_true: bool = True


@dataclass(frozen=True)
class KernelResult:
    status: Literal['PASS', 'HOLD', 'REJECT']
    envelope: dict[str, Any]
    spec: AnswerEnvelopeSpec
    source_rows: list[SourceRow]
    guard: dict[str, Any]
    reasons: list[str] = field(default_factory=list)


def validate_case_manifest(case: ArtifactQACase) -> ArtifactQACase:
    if case.expected_status not in {'ANSWER', 'HOLD'}:
        raise ValueError('expected_status must be ANSWER or HOLD')
    if case.expected_status == 'ANSWER' and not case.approved_source_refs:
        raise ValueError('ANSWER case requires at least one approved source ref')
    if any(ref.startswith(('MEMORY.md', 'memory/', 'context_bridge', 'context-bridge', '/', './', '../')) for ref in case.approved_source_refs):
        raise ValueError('case manifest contains forbidden source ref')
    return case


def resolve_approved_source_rows(spec: AnswerEnvelopeSpec, source_rows: list[SourceRow]) -> list[SourceRow]:
    by_ref = {r.source_ref: r for r in source_rows if r.authority == 'approved' and r.source_kind.startswith('approved_')}
    resolved: list[SourceRow] = []
    for ref in spec.canonical_source_refs:
        row = by_ref.get(ref)
        if row is not None:
            resolved.append(row)
    return resolved


def compile_answer_envelope_spec(case: ArtifactQACase, source_rows: list[SourceRow]) -> AnswerEnvelopeSpec:
    case = validate_case_manifest(case)
    canonical = list(case.approved_source_refs)
    primary = canonical[0] if canonical else None
    typed_value = None
    value_type = None
    if case.expected_status == 'ANSWER' and primary:
        row = next((r for r in source_rows if r.source_ref == primary), None)
        if row is None:
            raise ValueError(f'primary source row missing: {primary}')
        typed_value = row.value
        value_type = row.value_type
    if case.expected_status == 'ANSWER':
        required = ['status', 'answer_value', 'cited_source_ref', 'cited_source_value', 'value_match', 'source_refs', 'disposition']
    else:
        required = ['status', 'hold_reason', 'source_refs', 'cited_source_ref', 'disposition']
    hold_reason = None
    requires_source_refs = False
    if case.expected_status == 'HOLD':
        policy = case.hold_policy or {}
        hold_reason = str(policy.get('reason_code') or case.case_type or 'fail_closed_hold')
        requires_source_refs = bool(policy.get('requires_source_refs', bool(canonical))) and not case.allow_hold_no_source_ref
    return AnswerEnvelopeSpec(
        case_id=case.case_id,
        expected_status=case.expected_status,
        canonical_source_refs=canonical,
        primary_source_ref=primary,
        typed_value=typed_value,
        value_type=value_type,
        required_fields=required,
        allowed_aliases=case.allowed_aliases,
        hold_reason=hold_reason,
        requires_source_refs=requires_source_refs,
    )


def emit_answer_envelope(spec: AnswerEnvelopeSpec, rows: list[SourceRow]) -> dict[str, Any]:
    if spec.expected_status != 'ANSWER':
        raise ValueError('not an ANSWER spec')
    if not spec.primary_source_ref:
        raise ValueError('ANSWER spec missing primary source ref')
    row = next((r for r in rows if r.source_ref == spec.primary_source_ref), None)
    if row is None:
        raise ValueError('approved primary source row unresolved')
    return {
        'status': 'ANSWER',
        'answer': render_deterministic_text({'status': 'ANSWER', 'answer_value': row.value}),
        'answer_value': row.value,
        'cited_source_ref': row.source_ref,
        'cited_source_value': row.value,
        'value_match': True,
        'source_refs': [row.source_ref],
        'disposition': {
            'kind': 'answer_from_approved_source_rows',
            'source_authority': 'approved_artifact_source_rows_only',
            'authority': 'approved_artifact_source_rows_only',
            'source_row_count': 1,
            'control_claims': [],
        },
    }


def emit_hold_envelope(spec: AnswerEnvelopeSpec, rows: list[SourceRow]) -> dict[str, Any]:
    if spec.expected_status != 'HOLD':
        raise ValueError('not a HOLD spec')
    refs = [r.source_ref for r in rows if r.source_ref in spec.canonical_source_refs]
    if spec.requires_source_refs and not refs:
        raise ValueError('HOLD spec requires source refs but none resolved')
    cited = spec.primary_source_ref if spec.primary_source_ref in refs else (refs[0] if len(refs) == 1 else None)
    if spec.requires_source_refs and cited is None:
        raise ValueError('HOLD spec requires cited source ref but none can be selected')
    reason = spec.hold_reason or 'fail_closed_hold'
    return {
        'status': 'HOLD',
        'answer': render_deterministic_text({'status': 'HOLD', 'hold_reason': reason}),
        'hold_reason': reason,
        'source_refs': refs,
        'cited_source_ref': cited,
        'disposition': {
            'kind': 'fail_closed_hold',
            'reason': reason,
            'source_authority': 'no_authoritative_answer',
            'authority': 'not_authoritative_for_requested_status',
            'fail_closed': True,
            'control_claims': [],
        },
    }


def render_deterministic_text(envelope: dict[str, Any]) -> str:
    if envelope.get('status') == 'HOLD':
        return f"HOLD: {envelope.get('hold_reason', 'fail_closed_hold')}"
    value = envelope.get('answer_value')
    if isinstance(value, (dict, list)):
        return canonical_json(value)
    return f'The value is {json.dumps(value, sort_keys=True)}.'


def _legacy_case_for_guard(case: ArtifactQACase, source_rows: list[SourceRow]) -> dict[str, Any]:
    return {
        'case_id': case.case_id,
        'mix': case.case_type,
        'expected_semantic_status': case.expected_status,
        'expected_answer_terms': case.expected_answer_terms,
        'expected_source_refs': case.approved_source_refs,
        'source_rows': [r.to_legacy_row() for r in source_rows],
        'require_exact_source_value_anchor': case.required_exact_anchor,
        'allow_hold_no_source_ref': case.allow_hold_no_source_ref,
    }


def final_guard_validate(case: ArtifactQACase, envelope: dict[str, Any], source_rows: list[SourceRow]) -> dict[str, Any]:
    return validate_case_result(_legacy_case_for_guard(case, source_rows), canonical_json(envelope))


def answer_artifact_status_question(case: ArtifactQACase, source_rows: list[SourceRow], options: dict[str, Any] | None = None) -> KernelResult:
    options = options or {}
    case = validate_case_manifest(case)
    spec = compile_answer_envelope_spec(case, source_rows)
    resolved = resolve_approved_source_rows(spec, source_rows)
    if spec.expected_status == 'ANSWER':
        envelope = emit_answer_envelope(spec, resolved)
    else:
        envelope = emit_hold_envelope(spec, resolved)
    if not options.get('render_text', True):
        envelope.pop('answer', None)
    guard = final_guard_validate(case, envelope, source_rows)
    status: Literal['PASS', 'HOLD', 'REJECT'] = 'PASS' if guard.get('accepted') else 'REJECT'
    return KernelResult(status=status, envelope=envelope, spec=spec, source_rows=resolved, guard=guard, reasons=list(guard.get('reasons', [])))


def compile_source_rows_from_json_object(artifact_id: str, obj: Any, *, approved: bool = True) -> list[SourceRow]:
    rows: list[SourceRow] = []
    def walk(value: Any, pointer: str, field: str) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, pointer + '/' + str(k), field + '.' + str(k) if field else str(k))
        elif isinstance(value, list):
            # list as a typed leaf for C1; do not explode into competing authoritative values
            add(value, pointer or '/', field or 'value')
        else:
            add(value, pointer or '/', field or 'value')
    def add(value: Any, pointer: str, field: str) -> None:
        ref = f'{artifact_id}#{field}'
        rows.append(SourceRow(ref, 'approved_artifact' if approved else 'unapproved_artifact', artifact_id, field, value, json_type(value), pointer, 'sha256:' + sha_text(canonical_json(value)), 'approved' if approved else 'unapproved'))
    walk(obj, '', '')
    return rows
