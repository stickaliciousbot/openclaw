#!/usr/bin/env python3
"""M12-C4 bounded proposal source authority and non-execution guard.

C4K may draft bounded next-step proposals from approved evidence only. It never
executes, authorizes, schedules, mutates runtime/config, deploys, promotes cache
or artifact-memory, or treats provider/model prose as authoritative.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

ALLOWED_STATUS = {'PROPOSAL', 'HOLD', 'REJECT'}
ALLOWED_STEP_CLASSES = {'review', 'verify', 'request_artifact', 'safe_validation', 'owner_question', 'non_executing_plan'}

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

SCHEDULING_PATTERNS = [
    re.compile(r'\b(schedule|cron|remind|timer|wake event|set an alarm)\b', re.I),
]

FORBIDDEN_AUTHORITY_PATTERNS = [
    re.compile(r'\b(exact code|edit code|change config|routing|fallback|safety authority|runtime authority|gateway config|runtime config|configuration mutation)\b', re.I),
    re.compile(r'\b(cache|artifact-memory|global semantic gate|memory-route|live-route)\b', re.I),
]

PRODUCTION_AUTHORITY_PATTERNS = [
    re.compile(r'\b(production approval|approve production|deploy to production|production deployment|activate production|production route activation)\b', re.I),
]

SAFETY_CRITICAL_PATTERNS = [
    re.compile(r'\b(legal advice|medical advice|financial advice|diagnosis|prescription|investment advice|emergency response|safety-critical)\b', re.I),
]

UNSUPPORTED_RECONCILIATION_PATTERNS = [
    re.compile(r'\b(reconcile beyond evidence|merge conflicting facts|pick the truth|resolve the conflict without evidence|unsupported reconciliation)\b', re.I),
]

UNCERTAINTY_REMOVAL_PATTERNS = [
    re.compile(r'\b(remove uncertainty|drop uncertainty|ignore uncertainty|hide uncertainty|ignore conflict|remove conflict|drop conflict)\b', re.I),
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


def has_prompt_injection_like_text(text: str) -> bool:
    return any(pattern.search(text or '') for pattern in PROMPT_INJECTION_PATTERNS)


def text_reasons(text: str) -> list[str]:
    hay = text or ''
    reasons: list[str] = []
    for pattern, reason in FORBIDDEN_SOURCE_PATTERNS:
        if pattern.search(hay):
            reasons.append(reason)
    if any(pattern.search(hay) for pattern in PROMPT_INJECTION_PATTERNS):
        reasons.append('prompt_injection_like_text')
    if any(pattern.search(hay) for pattern in EXTERNAL_ACTION_PATTERNS):
        reasons.append('external_action_language_detected')
    if any(pattern.search(hay) for pattern in SCHEDULING_PATTERNS):
        reasons.append('scheduling_language_detected')
    if any(pattern.search(hay) for pattern in FORBIDDEN_AUTHORITY_PATTERNS):
        reasons.append('forbidden_runtime_config_authority_detected')
    if any(pattern.search(hay) for pattern in PRODUCTION_AUTHORITY_PATTERNS):
        reasons.append('production_authority_detected')
    if any(pattern.search(hay) for pattern in SAFETY_CRITICAL_PATTERNS):
        reasons.append('safety_critical_authority_detected')
    if any(pattern.search(hay) for pattern in UNSUPPORTED_RECONCILIATION_PATTERNS):
        reasons.append('unsupported_reconciliation_detected')
    if any(pattern.search(hay) for pattern in UNCERTAINTY_REMOVAL_PATTERNS):
        reasons.append('uncertainty_or_conflict_removal_detected')
    return sorted(set(reasons))


def _source_ref_id(ref_obj: Any) -> str:
    if isinstance(ref_obj, dict):
        return str(ref_obj.get('source_ref_id') or '')
    return str(ref_obj or '')


def _collect_strings(value: Any, *, skip_keys: set[str] | None = None) -> list[str]:
    skip_keys = skip_keys or set()
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_collect_strings(item, skip_keys=skip_keys))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for key, item in value.items():
            if str(key) in skip_keys:
                continue
            out.extend(_collect_strings(item, skip_keys=skip_keys))
        return out
    return []


def _validate_source_refs(
    source_refs: Any,
    *,
    allowed_source_refs: set[str],
    allowed_section_ids: set[str],
    expected_artifact_ids: set[str],
    reasons: list[str],
) -> tuple[list[str], set[str]]:
    if not isinstance(source_refs, list):
        reasons.append('cited_source_refs_not_list')
        return [], set()
    normalized_refs: list[str] = []
    artifact_ids: set[str] = set()
    for ref_obj in source_refs:
        if not isinstance(ref_obj, dict):
            reasons.append('source_ref_not_object')
            continue
        ref_id = str(ref_obj.get('source_ref_id') or '')
        artifact_id = str(ref_obj.get('artifact_id') or '')
        section_id = str(ref_obj.get('section_id') or '')
        path = str(ref_obj.get('path') or '')
        normalized_refs.append(ref_id)
        if artifact_id:
            artifact_ids.add(artifact_id)
        if ref_id not in allowed_source_refs:
            reasons.append(f'unapproved_source_ref:{ref_id}')
        if section_id not in allowed_section_ids:
            reasons.append(f'unapproved_section_id:{section_id}')
        if artifact_id not in expected_artifact_ids:
            reasons.append(f'wrong_artifact_id:{artifact_id}')
        if path.startswith(('/', './', '../')) or '/memory/' in path or path.startswith('memory/'):
            reasons.append('arbitrary_or_memory_path_in_source_ref')
    return normalized_refs, artifact_ids


def validate_proposal_envelope(
    envelope: dict[str, Any],
    *,
    allowed_source_refs: set[str],
    allowed_section_ids: set[str],
    expected_artifact_ids: set[str],
    allow_hold_without_refs: bool = True,
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

    disposition = envelope.get('disposition')
    if not isinstance(disposition, dict):
        reasons.append('disposition_missing_or_not_object')
        disposition = {}
    else:
        for key, reason in [
            ('production_expansion_applied', 'production_expansion_smuggled'),
            ('mutation_applied', 'mutation_smuggled'),
            ('external_action_executed', 'external_action_execution_smuggled'),
            ('scheduled_action_created', 'scheduled_action_smuggled'),
            ('cache_enabled', 'cache_enablement_smuggled'),
            ('artifact_memory_promoted', 'artifact_memory_promotion_smuggled'),
            ('global_semantic_gate_promoted', 'global_semantic_gate_promotion_smuggled'),
            ('c4_production_route_activated', 'c4_production_route_activation_smuggled'),
            ('runtime_authority_mutated', 'runtime_authority_mutation_smuggled'),
            ('gateway_config_mutated', 'gateway_config_mutation_smuggled'),
            ('provider_model_authoritative', 'provider_model_authority_smuggled'),
        ]:
            if disposition.get(key) is True:
                reasons.append(reason)
        if disposition.get('provider_model_calls', 0) != 0:
            reasons.append('provider_model_calls_nonzero')

    cited_source_refs = envelope.get('cited_source_refs', []) or []
    normalized_refs, artifact_ids = _validate_source_refs(
        cited_source_refs,
        allowed_source_refs=allowed_source_refs,
        allowed_section_ids=allowed_section_ids,
        expected_artifact_ids=expected_artifact_ids,
        reasons=reasons,
    )

    if status == 'PROPOSAL':
        if envelope.get('authority') != 'approved_evidence_only':
            reasons.append('proposal_requires_approved_evidence_only_authority')
        if not normalized_refs:
            reasons.append('proposal_requires_cited_source_refs')
        if not artifact_ids.issubset(expected_artifact_ids) or not artifact_ids:
            reasons.append('proposal_requires_expected_artifact_refs')
        if envelope.get('required_owner_review') is not True:
            reasons.append('proposal_requires_required_owner_review_true')
        notice = str(envelope.get('non_execution_notice') or '')
        if not notice or 'does not execute' not in notice.lower() or 'owner review' not in notice.lower():
            reasons.append('proposal_requires_explicit_non_execution_notice')
        steps = envelope.get('proposal_steps')
        if not isinstance(steps, list) or not steps:
            reasons.append('proposal_requires_nonempty_steps')
            steps = []
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                reasons.append(f'proposal_step_not_object:{idx}')
                continue
            if step.get('action_class') not in ALLOWED_STEP_CLASSES:
                reasons.append(f'unsupported_step_action_class:{step.get("action_class")}')
            step_refs = step.get('cited_source_refs', []) or []
            if not isinstance(step_refs, list) or not step_refs:
                reasons.append(f'proposal_step_missing_cited_refs:{idx}')
            for ref_id in step_refs:
                if str(ref_id) not in allowed_source_refs:
                    reasons.append(f'proposal_step_unapproved_ref:{ref_id}')
            for text in _collect_strings(step):
                for reason in text_reasons(text):
                    if reason in {
                        'external_action_language_detected',
                        'scheduling_language_detected',
                        'forbidden_runtime_config_authority_detected',
                        'production_authority_detected',
                        'safety_critical_authority_detected',
                        'unsupported_reconciliation_detected',
                        'uncertainty_or_conflict_removal_detected',
                        'prompt_injection_like_text',
                    }:
                        reasons.append(f'forbidden_proposal_step_text:{reason}')
        for key in ['rationale', 'assumptions', 'uncertainties', 'prerequisites']:
            if key not in envelope:
                reasons.append(f'proposal_missing_{key}')
        if not isinstance(envelope.get('assumptions'), list):
            reasons.append('proposal_assumptions_not_list')
        if not isinstance(envelope.get('uncertainties'), list):
            reasons.append('proposal_uncertainties_not_list')
        if not isinstance(envelope.get('prerequisites'), list):
            reasons.append('proposal_prerequisites_not_list')
        if envelope.get('hold_reason'):
            reasons.append('proposal_must_not_include_hold_reason')
        if envelope.get('reject_reason'):
            reasons.append('proposal_must_not_include_reject_reason')
    elif status == 'HOLD':
        if envelope.get('authority') not in {'approved_evidence_only', 'no_authority', None}:
            reasons.append('invalid_hold_authority')
        if not envelope.get('hold_reason'):
            reasons.append('hold_requires_hold_reason')
        if envelope.get('proposal_steps'):
            reasons.append('hold_must_not_include_authoritative_proposal_steps')
        if not normalized_refs and not allow_hold_without_refs:
            reasons.append('hold_missing_cited_source_refs_without_permission')
        if envelope.get('required_owner_review') not in {None, False}:
            reasons.append('hold_must_not_claim_required_owner_review_proposal')
    elif status == 'REJECT':
        if envelope.get('authority') not in {'no_authority', None}:
            reasons.append('reject_must_not_claim_authority')
        if not envelope.get('reject_reason'):
            reasons.append('reject_requires_reject_reason')
        if envelope.get('proposal_steps'):
            reasons.append('reject_must_not_include_proposal_steps')
        if envelope.get('cited_source_refs'):
            reasons.append('reject_must_not_include_authoritative_citations')

    # Model/prose may exist later only as non-authoritative decoration. It never
    # satisfies source authority or changes control fields.
    if envelope.get('model_prose_authoritative') is True:
        reasons.append('model_prose_authority_forbidden')
    if envelope.get('model_prose') and status == 'PROPOSAL' and not normalized_refs:
        reasons.append('model_prose_cannot_satisfy_source_authority')

    # Scan bounded user-facing proposal text, but do not punish machine-readable
    # hold/reject reason codes for naming the blocked class.
    skip = {'hold_reason', 'reject_reason', 'non_execution_notice'}
    for text in _collect_strings(envelope, skip_keys=skip):
        for reason in text_reasons(text):
            if reason in {'memory_source_forbidden', 'daily_memory_source_forbidden', 'context_bridge_source_forbidden', 'arbitrary_path_forbidden'}:
                reasons.append(f'forbidden_source_text:{reason}')
            if reason == 'prompt_injection_like_text':
                reasons.append('prompt_injection_text_in_envelope')

    accepted = not reasons
    final_status = str(status if status in ALLOWED_STATUS else 'REJECT')
    return GuardResult(accepted, final_status, sorted(set(reasons)), checked)
