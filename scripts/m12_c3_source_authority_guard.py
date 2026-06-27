#!/usr/bin/env python3
"""M12-C3 two-artifact consistency comparison source authority guard.

Validates deterministic C3 comparison envelopes. C3 authority is exactly two
approved artifacts and bounded SourceRows from both artifacts. The guard rejects
attempts to smuggle C4 proposal drafting, provider/model authority, arbitrary
paths, memory/context/daily-memory authority, external actions, or runtime
mutation through envelope text/provenance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

FORBIDDEN_SOURCE_PATTERNS = [
    (re.compile(r'\bMEMORY\.md\b', re.I), 'memory_source_forbidden'),
    (re.compile(r'\bmemory/\d{4}-\d{2}-\d{2}\.md\b', re.I), 'daily_memory_source_forbidden'),
    (re.compile(r'\bmemory/[\w./-]+\.md\b', re.I), 'memory_source_forbidden'),
    (re.compile(r'\bcontext[-_ ]bridge\b|sharedspace/context-bridge', re.I), 'context_bridge_source_forbidden'),
    (re.compile(r'(^|\s)(/|\.\.?/)[\w./-]+', re.I), 'arbitrary_path_forbidden'),
]

PROMPT_INJECTION_PATTERNS = [
    re.compile(r'ignore (all )?(previous|prior|system|developer) instructions', re.I),
    re.compile(r'bypass (safety|guard|source|authority|policy)', re.I),
    re.compile(r'(exfiltrate|leak|dump) (secret|token|key|password)', re.I),
    re.compile(r'enable (cache|artifact-memory|global semantic gate)', re.I),
    re.compile(r'mutate (gateway|runtime|config|route|fallback|memory)', re.I),
    re.compile(r'use (memory|context[-_ ]bridge|daily memory|another artifact) as authority', re.I),
]

EXTERNAL_ACTION_PATTERNS = [
    re.compile(r'\b(send|email|post|publish|tweet|message|call|delete|deploy|apply|restart|stop|start|install|upload|write to production)\b', re.I),
]

FORBIDDEN_AUTHORITY_PATTERNS = [
    re.compile(r'\b(exact code|edit code|change config|routing|fallback|safety authority|runtime authority|gateway config|runtime config|configuration mutation)\b', re.I),
]

C4_PROPOSAL_PATTERNS = [
    re.compile(r'\b(proposal|draft a plan|recommend next steps|remediation plan|merge plan|reconcile|resolution plan|C4)\b', re.I),
]

ALLOWED_STATUS = {'CONSISTENT', 'CONFLICT', 'HOLD', 'REJECT'}

@dataclass(frozen=True)
class GuardResult:
    accepted: bool
    status: str
    reasons: list[str]
    checked: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            'accepted': self.accepted,
            'status': self.status,
            'reasons': self.reasons,
            'checked': self.checked,
        }


def text_reasons(text: str) -> list[str]:
    reasons: list[str] = []
    hay = text or ''
    for pattern, reason in FORBIDDEN_SOURCE_PATTERNS:
        if pattern.search(hay):
            reasons.append(reason)
    if any(pattern.search(hay) for pattern in EXTERNAL_ACTION_PATTERNS):
        reasons.append('external_action_language_detected')
    if any(pattern.search(hay) for pattern in FORBIDDEN_AUTHORITY_PATTERNS):
        reasons.append('forbidden_runtime_config_authority_detected')
    if any(pattern.search(hay) for pattern in C4_PROPOSAL_PATTERNS):
        reasons.append('c4_or_proposal_language_detected')
    return sorted(set(reasons))


def has_prompt_injection_like_text(text: str) -> bool:
    return any(pattern.search(text or '') for pattern in PROMPT_INJECTION_PATTERNS)


def _collect_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_collect_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_collect_strings(item))
        return out
    return []


def _source_ref_id(ref_obj: Any) -> str:
    if isinstance(ref_obj, dict):
        return str(ref_obj.get('source_ref_id') or '')
    return str(ref_obj or '')


def validate_comparison_envelope(
    envelope: dict[str, Any],
    *,
    allowed_source_refs: set[str],
    allowed_section_ids: set[str],
    expected_artifact_ids: set[str],
    allow_hold_without_refs: bool = False,
) -> GuardResult:
    reasons: list[str] = []
    checked: dict[str, Any] = {
        'allowed_source_ref_count': len(allowed_source_refs),
        'allowed_section_id_count': len(allowed_section_ids),
        'expected_artifact_ids': sorted(expected_artifact_ids),
    }

    if not isinstance(envelope, dict):
        return GuardResult(False, 'REJECT', ['envelope_not_object'], checked)

    status = envelope.get('status')
    if status not in ALLOWED_STATUS:
        reasons.append('invalid_status')

    if status in {'CONSISTENT', 'CONFLICT'}:
        if envelope.get('authority') != 'approved_two_artifacts_only':
            reasons.append('comparison_requires_approved_two_artifacts_authority')
        if not envelope.get('artifact_a_ref') or not envelope.get('artifact_b_ref'):
            reasons.append('comparison_requires_both_artifact_refs')
        if not envelope.get('compared_fields'):
            reasons.append('comparison_requires_compared_fields')
        if envelope.get('hold_reason'):
            reasons.append('comparison_must_not_include_hold_reason')
        if envelope.get('reject_reason'):
            reasons.append('comparison_must_not_include_reject_reason')
    elif status == 'HOLD':
        if envelope.get('authority') not in {'approved_two_artifacts_only', 'no_authority', None}:
            reasons.append('invalid_hold_authority')
        if not envelope.get('hold_reason'):
            reasons.append('hold_requires_hold_reason')
        if envelope.get('agreement_points') or envelope.get('conflict_points'):
            reasons.append('hold_must_not_include_authoritative_points')
    elif status == 'REJECT':
        if envelope.get('authority') not in {'no_authority', None}:
            reasons.append('reject_must_not_claim_authority')
        if not envelope.get('reject_reason'):
            reasons.append('reject_requires_reject_reason')
        if envelope.get('agreement_points') or envelope.get('conflict_points'):
            reasons.append('reject_must_not_include_authoritative_points')

    disposition = envelope.get('disposition')
    if not isinstance(disposition, dict):
        reasons.append('disposition_missing_or_not_object')
    else:
        for key, reason in [
            ('production_expansion_applied', 'production_expansion_smuggled'),
            ('mutation_applied', 'mutation_smuggled'),
            ('external_action_executed', 'external_action_execution_smuggled'),
            ('cache_enabled', 'cache_enablement_smuggled'),
            ('artifact_memory_promoted', 'artifact_memory_promotion_smuggled'),
            ('c4_started', 'c4_activation_smuggled'),
        ]:
            if disposition.get(key) is True:
                reasons.append(reason)

    source_refs = envelope.get('cited_source_refs', []) or []
    if not isinstance(source_refs, list):
        reasons.append('cited_source_refs_not_list')
        source_refs = []
    normalized_refs: list[str] = []
    artifact_ids: set[str] = set()
    for ref_obj in source_refs:
        if not isinstance(ref_obj, dict):
            reasons.append('source_ref_not_object')
            continue
        ref_id = str(ref_obj.get('source_ref_id') or '')
        artifact_id = str(ref_obj.get('artifact_id') or '')
        section_id = str(ref_obj.get('section_id') or '')
        normalized_refs.append(ref_id)
        if artifact_id:
            artifact_ids.add(artifact_id)
        if ref_id not in allowed_source_refs:
            reasons.append(f'unapproved_source_ref:{ref_id}')
        if section_id not in allowed_section_ids:
            reasons.append(f'unapproved_section_id:{section_id}')
        if artifact_id not in expected_artifact_ids:
            reasons.append(f'wrong_artifact_id:{artifact_id}')
        if str(ref_obj.get('path') or '').startswith(('/', './', '../')):
            reasons.append('arbitrary_path_in_source_ref')
    if status in {'CONSISTENT', 'CONFLICT'}:
        if not normalized_refs:
            reasons.append('comparison_requires_cited_source_refs')
        if artifact_ids != expected_artifact_ids:
            reasons.append('comparison_requires_refs_from_both_artifacts')
    elif status == 'HOLD' and not normalized_refs and not allow_hold_without_refs:
        reasons.append('hold_missing_cited_source_refs_without_permission')

    compared_fields = envelope.get('compared_fields', []) or []
    if status in {'CONSISTENT', 'CONFLICT'} and not isinstance(compared_fields, list):
        reasons.append('compared_fields_not_list')

    agreement_points = envelope.get('agreement_points', []) or []
    conflict_points = envelope.get('conflict_points', []) or []
    if status == 'CONSISTENT':
        if not agreement_points:
            reasons.append('consistent_requires_agreement_points')
        if conflict_points:
            reasons.append('consistent_must_not_include_conflict_points')
    if status == 'CONFLICT':
        if not conflict_points:
            reasons.append('conflict_requires_conflict_points')

    for point_kind, points in [('agreement', agreement_points), ('conflict', conflict_points)]:
        if not isinstance(points, list):
            reasons.append(f'{point_kind}_points_not_list')
            continue
        for point in points:
            if not isinstance(point, dict):
                reasons.append(f'{point_kind}_point_not_object')
                continue
            if not point.get('field'):
                reasons.append(f'{point_kind}_point_missing_field')
            point_refs = point.get('source_refs') or []
            if not isinstance(point_refs, list) or not point_refs:
                reasons.append(f'{point_kind}_point_missing_source_refs')
                continue
            point_ref_ids = {_source_ref_id(r) for r in point_refs}
            if not point_ref_ids <= allowed_source_refs:
                reasons.append(f'{point_kind}_point_unapproved_source_ref')
            point_section_ids = {str(r.get('section_id') or '') for r in point_refs if isinstance(r, dict)}
            if not point_section_ids <= allowed_section_ids:
                reasons.append(f'{point_kind}_point_unapproved_section_id')
            point_artifacts = {str(r.get('artifact_id') or '') for r in point_refs if isinstance(r, dict)}
            if status in {'CONSISTENT', 'CONFLICT'} and point_artifacts != expected_artifact_ids:
                reasons.append(f'{point_kind}_point_requires_both_artifacts')
            if point_kind == 'conflict':
                if 'artifact_a_value' not in point or 'artifact_b_value' not in point:
                    reasons.append('conflict_point_requires_both_values')
                if not point.get('conflict_type'):
                    reasons.append('conflict_point_requires_conflict_type')

    # Model/prose/disposition-only source authority is forbidden: citations must
    # live in structured cited_source_refs and point source_refs.
    if status in {'CONSISTENT', 'CONFLICT'} and normalized_refs:
        structured_point_refs: set[str] = set()
        for point in list(agreement_points if isinstance(agreement_points, list) else []) + list(conflict_points if isinstance(conflict_points, list) else []):
            if isinstance(point, dict):
                structured_point_refs.update(_source_ref_id(r) for r in (point.get('source_refs') or []))
        if not structured_point_refs:
            reasons.append('source_refs_not_bound_to_comparison_points')

    joined = '\n'.join(_collect_strings(envelope))
    text_flags = text_reasons(joined)
    if status in {'HOLD', 'REJECT'}:
        text_flags = [r for r in text_flags if r not in {'external_action_language_detected', 'forbidden_runtime_config_authority_detected', 'c4_or_proposal_language_detected'}]
    reasons.extend(text_flags)

    checked.update({
        'status': status,
        'cited_source_refs': normalized_refs,
        'artifact_ids': sorted(artifact_ids),
        'agreement_point_count': len(agreement_points) if isinstance(agreement_points, list) else None,
        'conflict_point_count': len(conflict_points) if isinstance(conflict_points, list) else None,
    })
    reasons = sorted(set(reasons))
    return GuardResult(not reasons, 'PASS' if not reasons else 'REJECT', reasons, checked)
