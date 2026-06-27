#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from m12_c4_source_authority_guard import (
    has_prompt_injection_like_text,
    text_reasons,
    validate_proposal_envelope,
)

C4Status = Literal['PROPOSAL', 'HOLD', 'REJECT']
KernelStatus = Literal['PASS', 'HOLD', 'REJECT']
FORBIDDEN_SOURCE_KINDS = {'memory', 'daily_memory', 'context_bridge', 'runtime_metadata', 'arbitrary_path'}
ALLOWED_EVIDENCE_CLASSES = {'C1', 'C2', 'C3'}
NON_EXECUTION_NOTICE = 'This proposal is non-executing: it does not execute, authorize, schedule, deploy, mutate runtime/config, or bypass owner review.'


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
    evidence_class: str = 'C4'
    artifact_id: str = ''
    path: str = ''
    sha256: str = ''
    is_conflict: bool = False
    is_uncertainty: bool = False
    is_prerequisite: bool = False

    def source_ref(self) -> dict[str, Any]:
        return {
            'source_ref_id': self.source_ref_id,
            'artifact_id': self.artifact_id,
            'path': self.path,
            'sha256': self.sha256,
            'section_id': self.section_id,
            'section_title': self.section_title,
            'field_id': self.field_id,
            'evidence_class': self.evidence_class,
            'quote_hash': sha_text(self.quote),
        }


@dataclass(frozen=True)
class ApprovedEvidenceHandle:
    artifact_id: str
    evidence_class: str
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
class C4ProposalCase:
    case_id: str
    request: str
    expected_status: C4Status
    handles: list[ApprovedEvidenceHandle]
    proposal_kind: str = 'review'
    allow_hold_no_source_refs: bool = True
    expected_reason: str | None = None


@dataclass(frozen=True)
class ProposalEnvelopeSpec:
    case_id: str
    expected_status: C4Status
    artifact_ids: set[str]
    approved_source_refs: set[str]
    approved_section_ids: set[str]
    proposal_kind: str
    hold_reason: str | None = None
    reject_reason: str | None = None
    allow_hold_no_source_refs: bool = True


@dataclass(frozen=True)
class KernelResult:
    status: KernelStatus
    envelope: dict[str, Any]
    spec: ProposalEnvelopeSpec
    rows: list[SourceRow]
    guard: dict[str, Any]
    reasons: list[str] = field(default_factory=list)


def source_row(
    field_id: str,
    value: Any,
    value_type: str,
    *,
    section: str = 'status',
    quote: str | None = None,
    evidence_class: str = 'C4',
    is_conflict: bool = False,
    is_uncertainty: bool = False,
    is_prerequisite: bool = False,
) -> SourceRow:
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
        evidence_class=evidence_class,
        is_conflict=is_conflict,
        is_uncertainty=is_uncertainty,
        is_prerequisite=is_prerequisite,
    )


def evidence_handle_from_rows(
    artifact_id: str,
    evidence_class: str,
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
) -> ApprovedEvidenceHandle:
    path = path or f'approved://{artifact_id}.json'
    row_payload = [
        {
            'field_id': r.field_id,
            'value': r.value,
            'value_type': r.value_type,
            'section_id': r.section_id,
            'section_title': r.section_title,
            'quote': r.quote,
            'evidence_class': evidence_class,
            'is_conflict': r.is_conflict,
            'is_uncertainty': r.is_uncertainty,
            'is_prerequisite': r.is_prerequisite,
        }
        for r in rows
    ]
    body = text if text is not None else canonical_json(row_payload)
    sha = sha_text(body)
    enriched: list[SourceRow] = []
    for r in rows:
        sid = r.section_id
        ref = f'{artifact_id}#{sid}#{_stable_id(r.field_id)}'
        enriched.append(
            SourceRow(
                r.field_id,
                r.value,
                r.value_type,
                sid,
                r.section_title,
                ref,
                r.quote,
                evidence_class,
                artifact_id,
                path,
                sha,
                r.is_conflict,
                r.is_uncertainty,
                r.is_prerequisite,
            )
        )
    return ApprovedEvidenceHandle(
        artifact_id=artifact_id,
        evidence_class=evidence_class,
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


def validate_case_manifest(case: C4ProposalCase) -> None:
    if case.expected_status not in {'PROPOSAL', 'HOLD', 'REJECT'}:
        raise ValueError('expected_status must be PROPOSAL, HOLD, or REJECT')
    if not case.case_id:
        raise ValueError('case_id required')
    if not isinstance(case.handles, list):
        raise ValueError('handles must be a list')
    if case.proposal_kind not in {'review', 'verify', 'request_artifact', 'safe_validation', 'owner_question', 'non_executing_plan'}:
        raise ValueError('proposal_kind unsupported')


def _reason_for_case(case: C4ProposalCase) -> tuple[C4Status | None, str | None]:
    handles = case.handles
    request = case.request or ''
    flags = text_reasons(request)
    if 'arbitrary_path_forbidden' in flags:
        return 'REJECT', 'arbitrary_path_forbidden'
    if any(f in flags for f in {'memory_source_forbidden', 'daily_memory_source_forbidden', 'context_bridge_source_forbidden'}):
        return 'HOLD', 'unapproved_source_authority'
    if 'unsupported_reconciliation_detected' in flags:
        return 'REJECT', 'unsupported_reconciliation'
    if 'safety_critical_authority_detected' in flags:
        return 'REJECT', 'safety_critical_authority_forbidden'
    if any(f in flags for f in {
        'external_action_language_detected',
        'scheduling_language_detected',
        'forbidden_runtime_config_authority_detected',
        'production_authority_detected',
        'uncertainty_or_conflict_removal_detected',
        'prompt_injection_like_text',
    }):
        return 'HOLD', 'request_outside_non_executing_c4_scope'
    if not handles:
        return 'HOLD', 'missing_evidence'
    for h in handles:
        hay = (h.path or '') + '\n' + (h.text or '') + '\n' + request
        h_flags = text_reasons(hay)
        if h.source_kind in {'memory', 'daily_memory', 'context_bridge', 'runtime_metadata'} or any(f in h_flags for f in {'memory_source_forbidden', 'daily_memory_source_forbidden', 'context_bridge_source_forbidden'}):
            return 'HOLD', 'unapproved_source_authority'
        if _is_arbitrary_path(h.path) or h.source_kind == 'arbitrary_path' or 'arbitrary_path_forbidden' in h_flags:
            return 'REJECT', 'arbitrary_path_forbidden'
        if h.evidence_class not in ALLOWED_EVIDENCE_CLASSES:
            return 'HOLD', 'unsupported_evidence_class'
        if h.missing or h.text is None:
            return 'HOLD', 'missing_evidence'
        if h.stale:
            return 'HOLD', 'stale_evidence'
        if h.ambiguous:
            return 'HOLD', 'ambiguous_evidence'
        if not h.approved:
            return 'HOLD', 'unapproved_source_authority'
        if has_prompt_injection_like_text(h.text or ''):
            return 'HOLD', 'prompt_injection_like_artifact_text'
    if not any(h.source_rows for h in handles):
        return 'HOLD', 'missing_source_rows'
    return None, None


def _compile_spec(case: C4ProposalCase, rows: list[SourceRow], status: C4Status | None, reason: str | None) -> ProposalEnvelopeSpec:
    return ProposalEnvelopeSpec(
        case_id=case.case_id,
        expected_status=case.expected_status,
        artifact_ids={h.artifact_id for h in case.handles if h.artifact_id},
        approved_source_refs={r.source_ref_id for r in rows},
        approved_section_ids={r.section_id for r in rows},
        proposal_kind=case.proposal_kind,
        hold_reason=reason if status == 'HOLD' else None,
        reject_reason=reason if status == 'REJECT' else None,
        allow_hold_no_source_refs=case.allow_hold_no_source_refs,
    )


def _disposition() -> dict[str, Any]:
    return {
        'production_expansion_applied': False,
        'mutation_applied': False,
        'external_action_executed': False,
        'scheduled_action_created': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'c4_production_route_activated': False,
        'runtime_authority_mutated': False,
        'gateway_config_mutated': False,
        'provider_model_authoritative': False,
        'provider_model_calls': 0,
    }


def _values(rows: list[SourceRow], *, predicate) -> list[str]:
    out: list[str] = []
    for r in rows:
        if predicate(r):
            value = str(r.value).strip()
            if value and value not in out:
                out.append(value)
    return out


def _step_text(kind: str, case: C4ProposalCase) -> str:
    if kind == 'review':
        return 'Review the cited approved evidence and decide whether a bounded follow-up is warranted.'
    if kind == 'verify':
        return 'Verify the cited evidence fields against the approved artifact packet before any later action.'
    if kind == 'request_artifact':
        return 'Request a follow-up artifact or clarification for the cited gap; keep the request non-executing.'
    if kind == 'safe_validation':
        return 'Prepare a read-only validation plan using the cited evidence; do not run production changes.'
    if kind == 'owner_question':
        return 'Ask the owner a bounded question about the cited evidence before proceeding.'
    return 'Draft a non-executing next-step plan from the cited approved evidence only.'


def _proposal_envelope(case: C4ProposalCase, rows: list[SourceRow], spec: ProposalEnvelopeSpec) -> dict[str, Any]:
    refs = [r.source_ref() for r in rows]
    ref_ids = [r.source_ref_id for r in rows]
    uncertainties = _values(rows, predicate=lambda r: r.is_uncertainty or _stable_id(r.field_id).startswith('uncertainty'))
    prerequisites = _values(rows, predicate=lambda r: r.is_prerequisite or _stable_id(r.field_id).startswith('prerequisite'))
    conflicts = _values(rows, predicate=lambda r: r.is_conflict or _stable_id(r.field_id).startswith('conflict'))
    assumptions = _values(rows, predicate=lambda r: _stable_id(r.field_id).startswith('assumption'))
    if not assumptions:
        assumptions = ['Approved evidence remains unchanged after the cited artifact hashes.']
    if not uncertainties:
        uncertainties = ['No additional uncertainty beyond the cited evidence was introduced by C4K.']
    if not prerequisites:
        prerequisites = ['Owner review is required before any action outside this non-executing proposal.']
    steps = [
        {
            'step_id': f'{case.case_id}.step.1',
            'action_class': case.proposal_kind,
            'text': _step_text(case.proposal_kind, case),
            'cited_source_refs': ref_ids,
            'non_executing': True,
        }
    ]
    if conflicts:
        steps.append({
            'step_id': f'{case.case_id}.step.2',
            'action_class': 'review',
            'text': 'Preserve the cited conflict in the next owner review; do not reconcile it without new approved evidence.',
            'cited_source_refs': ref_ids,
            'non_executing': True,
        })
    return {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4k.proposal_envelope.v1',
        'case_id': case.case_id,
        'status': 'PROPOSAL',
        'authority': 'approved_evidence_only',
        'proposal_steps': steps,
        'cited_source_refs': refs,
        'rationale': f'Deterministic bounded proposal drafted from {len(rows)} approved source rows across {len(spec.artifact_ids)} approved evidence handle(s).',
        'assumptions': assumptions,
        'uncertainties': uncertainties,
        'prerequisites': prerequisites,
        'preserved_conflicts': conflicts,
        'required_owner_review': True,
        'non_execution_notice': NON_EXECUTION_NOTICE,
        'disposition': _disposition(),
    }


def _hold_envelope(case: C4ProposalCase, rows: list[SourceRow], reason: str) -> dict[str, Any]:
    refs = [r.source_ref() for r in rows]
    return {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4k.proposal_envelope.v1',
        'case_id': case.case_id,
        'status': 'HOLD',
        'authority': 'approved_evidence_only' if refs else 'no_authority',
        'hold_reason': reason,
        'cited_source_refs': refs,
        'disposition': _disposition(),
    }


def _reject_envelope(case: C4ProposalCase, reason: str) -> dict[str, Any]:
    return {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4k.proposal_envelope.v1',
        'case_id': case.case_id,
        'status': 'REJECT',
        'authority': 'no_authority',
        'reject_reason': reason,
        'disposition': _disposition(),
    }


def propose_next_steps(case: C4ProposalCase) -> KernelResult:
    validate_case_manifest(case)
    rows = [row for handle in case.handles for row in handle.source_rows]
    status, reason = _reason_for_case(case)
    if status is None:
        status = 'PROPOSAL'
        reason = None
    if status == 'HOLD' and reason in {'unapproved_source_authority', 'missing_evidence'}:
        rows = []
    spec = _compile_spec(case, rows, status, reason)
    if status == 'PROPOSAL':
        envelope = _proposal_envelope(case, rows, spec)
        kernel_status: KernelStatus = 'PASS'
    elif status == 'HOLD':
        envelope = _hold_envelope(case, rows, reason or 'hold')
        kernel_status = 'HOLD'
    else:
        envelope = _reject_envelope(case, reason or 'reject')
        kernel_status = 'REJECT'
    guard = validate_proposal_envelope(
        envelope,
        allowed_source_refs=spec.approved_source_refs,
        allowed_section_ids=spec.approved_section_ids,
        expected_artifact_ids=spec.artifact_ids,
        allow_hold_without_refs=spec.allow_hold_no_source_refs,
    ).as_dict()
    # The guard must accept the fail-closed envelope itself. If it does not,
    # convert to deterministic reject so callers never consume a malformed proposal.
    if not guard.get('accepted'):
        malformed_reasons = list(guard.get('reasons', []))
        envelope = _reject_envelope(case, 'malformed_envelope_guard_reject')
        guard = validate_proposal_envelope(
            envelope,
            allowed_source_refs=spec.approved_source_refs,
            allowed_section_ids=spec.approved_section_ids,
            expected_artifact_ids=spec.artifact_ids,
            allow_hold_without_refs=True,
        ).as_dict()
        return KernelResult('REJECT', envelope, spec, rows, guard, malformed_reasons)
    return KernelResult(kernel_status, envelope, spec, rows, guard, [reason] if reason else [])


def result_digest(result: KernelResult) -> str:
    return sha_text(canonical_json({'status': result.status, 'envelope': result.envelope, 'guard': result.guard}))
