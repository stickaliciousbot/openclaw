#!/usr/bin/env python3
"""M12-C2 single-artifact runbook guidance source authority guard.

Deterministic final guard for C2 guidance envelopes. It validates that a
GUIDANCE/HOLD envelope is bounded to exactly one approved artifact, cites only
approved deterministic sections/source refs, and does not smuggle production
mutation, external action execution, arbitrary paths, memory/context authority,
or cross-artifact synthesis.
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
    re.compile(r'\b(exact code|edit code|change config|routing|fallback|safety authority|runtime authority|gateway config)\b', re.I),
]

CROSS_ARTIFACT_PATTERNS = [
    re.compile(r'\b(compare|consistent|consistency|across artifacts|between artifacts|multi[- ]source|second artifact|two artifacts)\b', re.I),
]

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
    for pattern, reason in FORBIDDEN_SOURCE_PATTERNS:
        if pattern.search(text or ''):
            reasons.append(reason)
    if any(pattern.search(text or '') for pattern in EXTERNAL_ACTION_PATTERNS):
        reasons.append('external_action_language_detected')
    if any(pattern.search(text or '') for pattern in FORBIDDEN_AUTHORITY_PATTERNS):
        reasons.append('forbidden_code_config_routing_safety_authority_detected')
    if any(pattern.search(text or '') for pattern in CROSS_ARTIFACT_PATTERNS):
        reasons.append('cross_artifact_or_multi_source_language_detected')
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


def validate_guidance_envelope(
    envelope: dict[str, Any],
    *,
    allowed_source_refs: set[str],
    allowed_section_ids: set[str],
    expected_artifact_id: str | None,
    allow_hold_without_refs: bool = False,
) -> GuardResult:
    reasons: list[str] = []
    checked: dict[str, Any] = {
        'allowed_source_ref_count': len(allowed_source_refs),
        'allowed_section_id_count': len(allowed_section_ids),
        'expected_artifact_id': expected_artifact_id,
    }

    if not isinstance(envelope, dict):
        return GuardResult(False, 'REJECT', ['envelope_not_object'], checked)

    status = envelope.get('status')
    if status not in {'GUIDANCE', 'HOLD'}:
        reasons.append('invalid_status')

    if status == 'GUIDANCE' and envelope.get('authority') != 'approved_single_artifact_only':
        reasons.append('guidance_requires_approved_single_artifact_authority')
    if status == 'HOLD' and envelope.get('authority') not in {'approved_single_artifact_only', 'no_authority', None}:
        reasons.append('invalid_hold_authority')

    disposition = envelope.get('disposition')
    if not isinstance(disposition, dict):
        reasons.append('disposition_missing_or_not_object')
    else:
        if disposition.get('production_expansion_applied') is True:
            reasons.append('production_expansion_smuggled')
        if disposition.get('mutation_applied') is True:
            reasons.append('mutation_smuggled')
        if disposition.get('external_action_executed') is True:
            reasons.append('external_action_execution_smuggled')

    source_refs = envelope.get('cited_source_refs', [])
    if source_refs is None:
        source_refs = []
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
        if expected_artifact_id and artifact_id != expected_artifact_id:
            reasons.append(f'wrong_artifact_id:{artifact_id}')
        if str(ref_obj.get('path') or '').startswith(('/', './', '../')):
            reasons.append('arbitrary_path_in_source_ref')
    if len(artifact_ids) > 1:
        reasons.append('multiple_artifacts_in_citations')

    source_sections = envelope.get('source_sections', [])
    if source_sections is None:
        source_sections = []
    if not isinstance(source_sections, list):
        reasons.append('source_sections_not_list')
        source_sections = []
    for section in source_sections:
        if not isinstance(section, dict):
            reasons.append('source_section_not_object')
            continue
        sid = str(section.get('section_id') or '')
        if sid not in allowed_section_ids:
            reasons.append(f'unapproved_source_section:{sid}')

    guidance_steps = envelope.get('guidance_steps', [])
    if guidance_steps is None:
        guidance_steps = []
    if not isinstance(guidance_steps, list):
        reasons.append('guidance_steps_not_list')
        guidance_steps = []

    if status == 'GUIDANCE':
        if not guidance_steps:
            reasons.append('guidance_requires_steps')
        if not normalized_refs:
            reasons.append('guidance_requires_cited_source_refs')
        for step in guidance_steps:
            if not isinstance(step, dict):
                reasons.append('guidance_step_not_object')
                continue
            step_refs = [str(r) for r in step.get('source_ref_ids') or []]
            step_sections = [str(s) for s in step.get('source_section_ids') or []]
            if not step_refs:
                reasons.append('guidance_step_missing_source_ref_ids')
            if not step_sections:
                reasons.append('guidance_step_missing_source_section_ids')
            for ref in step_refs:
                if ref not in allowed_source_refs:
                    reasons.append(f'guidance_step_unapproved_ref:{ref}')
            for sid in step_sections:
                if sid not in allowed_section_ids:
                    reasons.append(f'guidance_step_unapproved_section:{sid}')
        if envelope.get('hold_reason') not in {None, ''}:
            reasons.append('guidance_must_not_include_hold_reason')
    elif status == 'HOLD':
        if guidance_steps:
            reasons.append('hold_must_not_include_authoritative_guidance_steps')
        if not envelope.get('hold_reason'):
            reasons.append('hold_requires_hold_reason')
        if not normalized_refs and not allow_hold_without_refs:
            reasons.append('hold_missing_cited_source_refs_without_permission')

    # Scan envelope strings for forbidden authority/path/provenance claims. For HOLD,
    # the hold_reason itself may mention the category, so filter known reason tokens.
    joined = '\n'.join(_collect_strings(envelope))
    text_flags = text_reasons(joined)
    if status == 'HOLD':
        text_flags = [r for r in text_flags if r not in {'external_action_language_detected', 'forbidden_code_config_routing_safety_authority_detected', 'cross_artifact_or_multi_source_language_detected'}]
    reasons.extend(text_flags)

    checked.update({
        'status': status,
        'cited_source_refs': normalized_refs,
        'artifact_ids': sorted(artifact_ids),
        'guidance_step_count': len(guidance_steps),
        'source_section_count': len(source_sections),
    })
    accepted = not reasons
    return GuardResult(accepted, 'PASS' if accepted else 'REJECT', sorted(set(reasons)), checked)
