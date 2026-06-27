#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from m12_c2_source_authority_guard import (
    has_prompt_injection_like_text,
    text_reasons,
    validate_guidance_envelope,
)

GuidanceStatus = Literal['GUIDANCE', 'HOLD']
FORBIDDEN_SOURCE_KINDS = {'memory', 'daily_memory', 'context_bridge', 'runtime_metadata', 'arbitrary_path'}
EXTERNAL_ACTION_RE = re.compile(r'\b(send|email|post|publish|tweet|message|call|delete|deploy|apply|restart|stop|start|install|upload|write to production)\b', re.I)
FORBIDDEN_AUTHORITY_RE = re.compile(r'\b(exact code|edit code|change config|routing|fallback|safety authority|runtime authority|gateway config)\b', re.I)
CROSS_ARTIFACT_RE = re.compile(r'\b(compare|consistent|consistency|across artifacts|between artifacts|multi[- ]source|second artifact|two artifacts)\b', re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True)
class ApprovedArtifactHandle:
    artifact_id: str
    path: str
    sha256: str
    text: str | None = None
    approved: bool = True
    source_kind: str = 'approved_artifact'
    stale: bool = False
    missing: bool = False
    ambiguous: bool = False
    artifact_class: str = 'runbook'
    approval_record: str = 'owner_approved_fixture'


@dataclass(frozen=True)
class RunbookSection:
    section_id: str
    heading: str
    line_start: int
    line_end: int
    text: str
    section_hash: str
    source_ref_id: str
    artifact_id: str

    def as_source_ref(self, handle: ApprovedArtifactHandle) -> dict[str, Any]:
        return {
            'source_ref_id': self.source_ref_id,
            'artifact_id': handle.artifact_id,
            'path': handle.path,
            'sha256': handle.sha256,
            'section_id': self.section_id,
            'quote_hash': self.section_hash,
        }

    def as_section_ref(self) -> dict[str, Any]:
        return {
            'section_id': self.section_id,
            'heading': self.heading,
            'line_range': f'{self.line_start}-{self.line_end}',
            'section_hash': self.section_hash,
        }


@dataclass(frozen=True)
class C2GuidanceCase:
    case_id: str
    question: str
    expected_status: GuidanceStatus
    handles: list[ApprovedArtifactHandle]
    requested_section: str | None = None
    allow_hold_no_source_refs: bool = False
    expected_hold_reason: str | None = None


@dataclass(frozen=True)
class GuidanceEnvelopeSpec:
    case_id: str
    expected_status: GuidanceStatus
    artifact_id: str | None
    approved_source_refs: list[str]
    approved_section_ids: list[str]
    hold_reason: str | None = None
    allow_hold_no_source_refs: bool = False


@dataclass(frozen=True)
class KernelResult:
    status: Literal['PASS', 'HOLD', 'REJECT']
    envelope: dict[str, Any]
    spec: GuidanceEnvelopeSpec
    sections: list[RunbookSection]
    guard: dict[str, Any]
    reasons: list[str] = field(default_factory=list)


def validate_case_manifest(case: C2GuidanceCase) -> None:
    if case.expected_status not in {'GUIDANCE', 'HOLD'}:
        raise ValueError('expected_status must be GUIDANCE or HOLD')
    if not case.case_id:
        raise ValueError('case_id required')
    if not isinstance(case.handles, list):
        raise ValueError('handles must be a list')


def _is_arbitrary_path(path: str) -> bool:
    return str(path).startswith(('/', './', '../')) or '/memory/' in str(path)


def _hold_reason_for_case(case: C2GuidanceCase) -> str | None:
    handles = case.handles
    q = case.question or ''
    if len(handles) == 0:
        return 'missing_artifact'
    if len(handles) > 1:
        return 'multiple_artifacts'
    h = handles[0]
    if h.missing or h.text is None:
        return 'missing_artifact'
    if h.stale or (h.text is not None and sha_text(h.text) != h.sha256):
        return 'stale_artifact'
    if h.ambiguous:
        return 'ambiguous_artifact'
    if not h.approved or h.source_kind in FORBIDDEN_SOURCE_KINDS:
        return 'unapproved_source'
    if _is_arbitrary_path(h.path) or h.source_kind == 'arbitrary_path':
        return 'unapproved_source'
    if any(reason in {'memory_source_forbidden', 'daily_memory_source_forbidden', 'context_bridge_source_forbidden', 'arbitrary_path_forbidden'} for reason in text_reasons(h.path + '\n' + q)):
        return 'unapproved_source'
    if CROSS_ARTIFACT_RE.search(q):
        return 'cross_artifact_synthesis_forbidden'
    if EXTERNAL_ACTION_RE.search(q):
        return 'external_action_required'
    if FORBIDDEN_AUTHORITY_RE.search(q):
        return 'requires_forbidden_authority'
    if has_prompt_injection_like_text(h.text):
        return 'prompt_injection_risk'
    return None


def _normalize_heading(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.strip().lower()).strip('_') or 'section'


def compile_runbook_sections(handle: ApprovedArtifactHandle) -> list[RunbookSection]:
    if handle.text is None:
        return []
    lines = handle.text.splitlines()
    sections: list[tuple[str, int, int]] = []
    current_heading = 'preamble'
    current_start = 1
    for idx, line in enumerate(lines, start=1):
        m = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*$', line)
        if m:
            if idx > current_start:
                sections.append((current_heading, current_start, idx - 1))
            current_heading = m.group(1).strip()
            current_start = idx
    if lines:
        sections.append((current_heading, current_start, len(lines)))
    if not sections:
        sections.append(('preamble', 1, 1))
    out: list[RunbookSection] = []
    for n, (heading, start, end) in enumerate(sections, start=1):
        text = '\n'.join(lines[start - 1:end]).strip()
        sid = f'{handle.artifact_id}:{n:02d}:{_normalize_heading(heading)}'
        section_hash = sha_text(text)
        out.append(RunbookSection(
            section_id=sid,
            heading=heading,
            line_start=start,
            line_end=end,
            text=text,
            section_hash=section_hash,
            source_ref_id=f'{handle.artifact_id}#{sid}',
            artifact_id=handle.artifact_id,
        ))
    return out


def _section_matches(section: RunbookSection, keywords: list[str]) -> bool:
    hay = (section.heading + '\n' + section.text).lower()
    return any(k in hay for k in keywords)


def _extract_bullets(section: RunbookSection) -> list[str]:
    items: list[str] = []
    for line in section.text.splitlines():
        s = line.strip()
        m = re.match(r'^(?:[-*]\s+|\d+[.)]\s+)(.+)$', s)
        if m:
            val = m.group(1).strip()
            if val and not val.startswith('#'):
                items.append(val)
    return items


def _select_sections(case: C2GuidanceCase, sections: list[RunbookSection]) -> dict[str, list[RunbookSection]]:
    q = (case.question or '').lower()
    steps = [s for s in sections if _section_matches(s, ['step', 'next', 'procedure', 'runbook'])]
    prereq = [s for s in sections if _section_matches(s, ['prerequisite', 'requirement', 'before you begin'])]
    warnings = [s for s in sections if _section_matches(s, ['warning', 'caution', 'abort', 'do not'])]
    support = sections
    if 'prerequisite' in q:
        support = prereq or sections
    elif 'warning' in q or 'caution' in q:
        support = warnings or sections
    elif 'section' in q or 'support' in q:
        support = sections
    else:
        support = steps or sections
    return {'steps': steps, 'prerequisites': prereq, 'warnings': warnings, 'support': support}


def compile_guidance_envelope_spec(case: C2GuidanceCase, sections: list[RunbookSection], hold_reason: str | None) -> GuidanceEnvelopeSpec:
    artifact_id = case.handles[0].artifact_id if len(case.handles) == 1 else None
    return GuidanceEnvelopeSpec(
        case_id=case.case_id,
        expected_status='HOLD' if hold_reason else case.expected_status,
        artifact_id=artifact_id,
        approved_source_refs=[s.source_ref_id for s in sections],
        approved_section_ids=[s.section_id for s in sections],
        hold_reason=hold_reason or case.expected_hold_reason,
        allow_hold_no_source_refs=case.allow_hold_no_source_refs or len(sections) == 0 or hold_reason in {'missing_artifact', 'multiple_artifacts', 'unapproved_source', 'stale_artifact', 'ambiguous_artifact'},
    )


def emit_guidance_envelope(case: C2GuidanceCase, handle: ApprovedArtifactHandle, sections: list[RunbookSection]) -> dict[str, Any]:
    groups = _select_sections(case, sections)
    support = groups['support'] or sections
    if not support:
        raise ValueError('no sections available for guidance')

    guidance_steps: list[dict[str, Any]] = []
    step_sections = groups['steps'] or support
    step_items: list[tuple[str, RunbookSection]] = []
    for section in step_sections:
        for item in _extract_bullets(section):
            step_items.append((item, section))
    if not step_items:
        # Section-support questions can cite the section itself as informational guidance.
        for section in support[:1]:
            step_items.append((f'Read section "{section.heading}" for the requested guidance.', section))
    for idx, (text, section) in enumerate(step_items, start=1):
        guidance_steps.append({
            'step_id': f'{case.case_id}_step_{idx:02d}',
            'text': text,
            'source_ref_ids': [section.source_ref_id],
            'source_section_ids': [section.section_id],
            'applicability': 'required' if idx == 1 else 'conditional',
            'confidence': 'high',
        })

    def list_from_sections(selected: list[RunbookSection]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for section in selected:
            for item in _extract_bullets(section):
                out.append({'text': item, 'source_ref_ids': [section.source_ref_id], 'source_section_ids': [section.section_id]})
        return out

    cited_sections = {sid for step in guidance_steps for sid in step.get('source_section_ids', [])}
    cited_source_refs = {ref for step in guidance_steps for ref in step.get('source_ref_ids', [])}
    # Include prerequisite/warning refs as citations too when present.
    prerequisites = list_from_sections(groups['prerequisites'])
    warnings = list_from_sections(groups['warnings'])
    for item in prerequisites + warnings:
        cited_sections.update(item['source_section_ids'])
        cited_source_refs.update(item['source_ref_ids'])

    cited_section_objs = [s for s in sections if s.section_id in cited_sections]
    source_ref_objs = [s.as_source_ref(handle) for s in sections if s.source_ref_id in cited_source_refs]

    return {
        'status': 'GUIDANCE',
        'guidance_steps': guidance_steps,
        'cited_source_refs': source_ref_objs,
        'source_sections': [s.as_section_ref() for s in cited_section_objs],
        'prerequisites': prerequisites,
        'warnings': warnings,
        'applicability': 'bounded to one approved artifact and cited sections only',
        'confidence': 'high',
        'disposition': {
            'kind': 'single_artifact_guidance',
            'source_authority': 'approved_single_artifact_only',
            'artifact_id': handle.artifact_id,
            'deterministic': True,
            'model_prose_used': False,
            'external_action_executed': False,
            'mutation_applied': False,
            'production_expansion_applied': False,
        },
        'hold_reason': None,
        'authority': 'approved_single_artifact_only',
    }


def emit_hold_envelope(spec: GuidanceEnvelopeSpec, sections: list[RunbookSection], handle: ApprovedArtifactHandle | None) -> dict[str, Any]:
    can_cite = bool(handle is not None and handle.approved and handle.source_kind == 'approved_artifact' and not handle.stale and not handle.ambiguous and not _is_arbitrary_path(handle.path))
    refs = [s.as_source_ref(handle) for s in sections] if can_cite else []
    source_sections = [s.as_section_ref() for s in sections] if can_cite and sections else []
    if not refs and not spec.allow_hold_no_source_refs:
        # If no safe approved source can be cited, HOLD remains valid only when
        # the case/spec allows a no-ref fail-closed envelope.
        refs = []
    return {
        'status': 'HOLD',
        'hold_reason': spec.hold_reason or 'fail_closed_hold',
        'guidance_steps': [],
        'cited_source_refs': refs,
        'source_sections': source_sections,
        'prerequisites': [],
        'warnings': [],
        'applicability': 'insufficient',
        'confidence': 'high',
        'disposition': {
            'kind': 'fail_closed_hold',
            'reason': spec.hold_reason or 'fail_closed_hold',
            'source_authority': 'no_authoritative_guidance',
            'fail_closed': True,
            'deterministic': True,
            'model_prose_used': False,
            'external_action_executed': False,
            'mutation_applied': False,
            'production_expansion_applied': False,
        },
        'authority': 'approved_single_artifact_only' if handle is not None and handle.approved else 'no_authority',
    }


def answer_single_artifact_guidance(case: C2GuidanceCase, options: dict[str, Any] | None = None) -> KernelResult:
    validate_case_manifest(case)
    options = options or {}
    hold_reason = _hold_reason_for_case(case)
    handle = case.handles[0] if len(case.handles) == 1 else None
    sections = compile_runbook_sections(handle) if handle and handle.text else []
    spec = compile_guidance_envelope_spec(case, sections, hold_reason)

    if hold_reason:
        envelope = emit_hold_envelope(spec, sections, handle)
    else:
        if handle is None:
            raise ValueError('GUIDANCE requires exactly one handle')
        envelope = emit_guidance_envelope(case, handle, sections)

    guard_result = validate_guidance_envelope(
        envelope,
        allowed_source_refs=set(spec.approved_source_refs),
        allowed_section_ids=set(spec.approved_section_ids),
        expected_artifact_id=spec.artifact_id,
        allow_hold_without_refs=spec.allow_hold_no_source_refs or hold_reason in {'missing_artifact', 'multiple_artifacts'},
    )
    status: Literal['PASS', 'HOLD', 'REJECT']
    reasons = list(guard_result.reasons)
    if guard_result.accepted and envelope.get('status') == case.expected_status:
        status = 'PASS'
    elif guard_result.accepted and envelope.get('status') == 'HOLD':
        status = 'HOLD'
    else:
        status = 'REJECT'
        if envelope.get('status') != case.expected_status:
            reasons.append(f'unexpected_status:{envelope.get("status")}!=expected:{case.expected_status}')
    return KernelResult(status, envelope, spec, sections, guard_result.as_dict(), sorted(set(reasons)))


def artifact_handle_from_text(artifact_id: str, text: str, **kwargs: Any) -> ApprovedArtifactHandle:
    return ApprovedArtifactHandle(
        artifact_id=artifact_id,
        path=kwargs.pop('path', f'approved://{artifact_id}.md'),
        sha256=kwargs.pop('sha256', sha_text(text)),
        text=text,
        **kwargs,
    )


def result_digest(result: KernelResult) -> str:
    return sha_text(canonical_json({
        'status': result.status,
        'envelope': result.envelope,
        'guard': result.guard,
        'reasons': result.reasons,
    }))
