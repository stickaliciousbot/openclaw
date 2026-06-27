#!/usr/bin/env python3
"""M12-C1 Source Authority Guard.

Deterministic guard for bounded artifact status Q&A outputs.
It does not call providers and does not read arbitrary paths. It validates that a
semantic answer is valid JSON and cites only the source refs allowed by the case
manifest. Unapproved memory/context/daily-note/runtime refs fail closed.
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

UNAPPROVED_PATTERNS = [
    (re.compile(r'\bMEMORY\.md\b', re.I), 'unapproved_memory_source'),
    (re.compile(r'\bmemory/\d{4}-\d{2}-\d{2}\.md\b', re.I), 'unapproved_daily_memory_source'),
    (re.compile(r'\bmemory/[\w./-]+\.md\b', re.I), 'unapproved_memory_source'),
    (re.compile(r'\bsharedspace/context-bridge\b|\bcontext-bridge\b', re.I), 'unapproved_context_bridge_source'),
    (re.compile(r'\btool\s*call\b|\bruntime metadata\b|\bsession transcript\b', re.I), 'tool_runtime_metadata'),
]

HOLD_DISPOSITIONS = {
    'fail_closed_stale',
    'fail_closed_missing',
    'fail_closed_ambiguous',
    'fail_closed_unapproved_source',
    'hold_exact_source_required',
    'unapproved_source_hold',
    'source_authority_hold',
}

@dataclass
class GuardResult:
    accepted: bool
    status: str
    reasons: list[str]
    source_classes: dict[str, str]
    parsed: dict[str, Any] | None
    canonicalized_source_refs: list[dict[str, Any]] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            'accepted': self.accepted,
            'status': self.status,
            'reasons': self.reasons,
            'source_classes': self.source_classes,
            'parsed': self.parsed,
            'canonicalized_source_refs': self.canonicalized_source_refs or [],
        }


def parse_semantic_output(text: str) -> dict[str, Any] | None:
    s = (text or '').strip()
    if s.startswith('```'):
        s = re.sub(r'^```(?:json)?\s*', '', s)
        s = re.sub(r'\s*```$', '', s)
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        m = re.search(r'\{.*\}', s, re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None


def classify_source_ref(ref: str, allowed_refs: set[str]) -> str:
    ref = str(ref)
    if ref in allowed_refs:
        return 'approved_artifact_source'
    for pattern, cls in UNAPPROVED_PATTERNS:
        if pattern.search(ref):
            return cls
    if ref.startswith('fixture_'):
        return 'approved_fixture_source' if ref in allowed_refs else 'ambiguous_source'
    if '#' in ref and ref.split('#', 1)[0] in {r.split('#', 1)[0] for r in allowed_refs if '#' in r}:
        return 'ambiguous_source'
    return 'ambiguous_source'


def classify_text_sources(text: str, allowed_refs: set[str]) -> dict[str, str]:
    classes: dict[str, str] = {}
    for pattern, cls in UNAPPROVED_PATTERNS:
        for match in pattern.finditer(text or ''):
            # Preserve the most specific earlier classification, e.g. daily-memory
            # before the broader memory/*.md rule.
            classes.setdefault(match.group(0), cls)
    for ref in allowed_refs:
        if ref in (text or ''):
            classes[ref] = 'approved_artifact_source'
    return classes


def parse_source_row(row: str) -> tuple[str, Any] | None:
    """Parse a manifest SourceRow of the form canonical_ref=<json value>.

    The guard treats SourceRows as the only place where a value-decorated ref can
    get its approved value.  Invalid or valueless rows are ignored rather than
    guessed from arbitrary artifact paths.
    """
    if '=' not in str(row):
        return None
    base, raw_value = str(row).split('=', 1)
    base = base.strip()
    if not base:
        return None
    try:
        return base, json.loads(raw_value)
    except Exception:
        return None


def source_row_values(source_rows: list[str] | None) -> dict[str, list[Any]]:
    values: dict[str, list[Any]] = {}
    for row in source_rows or []:
        parsed = parse_source_row(str(row))
        if parsed is None:
            continue
        base, value = parsed
        values.setdefault(base, []).append(value)
    return values


def parse_value_decorated_ref(ref: str) -> tuple[str, Any, str] | None:
    """Parse source refs like m12_design_status#status="PASS".

    Returns (base_ref, parsed_value, raw_value_text).  This deliberately accepts
    only JSON literal values so escaping and quoting are deterministic.  Partial
    or fuzzy values never normalize because comparison is exact against the
    approved SourceRow value.
    """
    if '=' not in str(ref):
        return None
    base, raw_value = str(ref).split('=', 1)
    base = base.strip()
    if not base or '#' not in base:
        return None
    try:
        value = json.loads(raw_value)
    except Exception:
        return None
    return base, value, raw_value


def canonicalize_source_ref(ref: str, allowed_refs: set[str], source_rows: list[str] | None = None) -> tuple[str, str, dict[str, Any] | None, str | None]:
    """Classify and optionally normalize a cited source ref.

    Value-decorated refs are accepted only when their base ref is explicitly
    approved and exactly one approved SourceRow gives that base ref the exact
    cited value.  All unapproved memory/context/daily/runtime refs stay
    fail-closed.  The function never reads files or infers values.
    """
    ref = str(ref)
    if ref in allowed_refs:
        return ref, 'approved_artifact_source', None, None
    for pattern, cls in UNAPPROVED_PATTERNS:
        if pattern.search(ref):
            return ref, cls, None, None
    decorated = parse_value_decorated_ref(ref)
    if decorated is not None:
        base, value, raw_value = decorated
        if base not in allowed_refs:
            return ref, 'ambiguous_source', None, f'value_decorated_base_not_approved:{base}'
        rows = source_row_values(source_rows)
        values = rows.get(base, [])
        if len(values) != 1:
            return ref, 'ambiguous_source', None, f'value_decorated_base_ambiguous:{base}:match_count={len(values)}'
        approved_value = values[0]
        if value != approved_value:
            return ref, 'ambiguous_source', None, f'value_decorated_value_mismatch:{base}'
        return base, 'approved_artifact_source', {
            'original_ref': ref,
            'normalized_ref': base,
            'raw_value': raw_value,
            'value': value,
            'match': 'exact_source_row_value',
        }, None
    if ref.startswith('fixture_'):
        return ref, ('approved_fixture_source' if ref in allowed_refs else 'ambiguous_source'), None, None
    if '#' in ref and ref.split('#', 1)[0] in {r.split('#', 1)[0] for r in allowed_refs if '#' in r}:
        return ref, 'ambiguous_source', None, None
    return ref, 'ambiguous_source', None, None


def json_value_type(value: Any) -> str:
    """Return a deterministic JSON value type label.

    Python's bool is a subclass of int, so bool must be checked first.  Integers
    and floats stay distinct for M12-C1 exact anchors because `100` and `100.0`
    are different JSON lexical/type commitments for these artifacts.
    """
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, int):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, dict):
        return 'object'
    return type(value).__name__


def exact_json_typed_value_matches(cited_value: Any, approved_value: Any) -> bool:
    """Return true only when value and JSON type both match exactly.

    No string-to-number or string-to-boolean coercion is accepted.  Integer
    SourceRows require JSON integers; floats for integers are rejected.  Arrays
    and objects must match recursively with typed equality.  NaN/Infinity are
    rejected as non-portable/non-canonical JSON numbers.
    """
    if json_value_type(cited_value) != json_value_type(approved_value):
        return False
    if isinstance(approved_value, float):
        if not math.isfinite(approved_value) or not math.isfinite(cited_value):
            return False
        return cited_value == approved_value
    if isinstance(approved_value, list):
        return len(cited_value) == len(approved_value) and all(exact_json_typed_value_matches(c, a) for c, a in zip(cited_value, approved_value))
    if isinstance(approved_value, dict):
        if set(cited_value.keys()) != set(approved_value.keys()):
            return False
        return all(exact_json_typed_value_matches(cited_value[k], approved_value[k]) for k in approved_value.keys())
    return cited_value == approved_value


def exact_source_value_matches(cited_value: Any, approved_value: Any) -> bool:
    """Return true only for deterministic typed exact-value anchors."""
    return exact_json_typed_value_matches(cited_value, approved_value)


def enforce_exact_source_value_anchor(parsed: dict[str, Any], allowed_refs: set[str], source_rows: list[str] | None) -> list[str]:
    """Require structured exact source-value anchoring for ANSWER outputs.

    This is intentionally stricter than prose substring matching.  The model may
    paraphrase in `answer`, but accepted output must include:
      - answer_value
      - cited_source_ref
      - cited_source_value
      - value_match=true
    The cited ref may be value-decorated only if canonicalization normalizes it
    to an approved base ref with exact SourceRow value match.
    """
    reasons: list[str] = []
    if parsed.get('status') != 'ANSWER':
        return reasons
    for field in ['answer_value', 'cited_source_ref', 'cited_source_value', 'value_match']:
        if field not in parsed:
            reasons.append(f'exact_source_value_anchor_missing_field:{field}')
    if reasons:
        return reasons
    if parsed.get('value_match') is not True:
        reasons.append('exact_source_value_anchor_value_match_not_true')
    cited_ref_raw = str(parsed.get('cited_source_ref'))
    cited_ref, cls, _record, reason = canonicalize_source_ref(cited_ref_raw, allowed_refs, source_rows)
    if reason:
        reasons.append(f'exact_source_value_anchor_ref_canonicalization:{reason}')
    if cls not in {'approved_artifact_source', 'approved_fixture_source'} or cited_ref not in allowed_refs:
        reasons.append(f'exact_source_value_anchor_ref_not_approved:{cited_ref_raw}:{cls}')
        return reasons
    values = source_row_values(source_rows).get(cited_ref, [])
    if len(values) != 1:
        reasons.append(f'exact_source_value_anchor_ambiguous_source_value:{cited_ref}:count={len(values)}')
        return reasons
    approved_value = values[0]
    cited_value = parsed.get('cited_source_value')
    answer_value = parsed.get('answer_value')
    if not exact_source_value_matches(cited_value, approved_value):
        reasons.append(f'exact_source_value_anchor_cited_value_mismatch:{cited_ref}')
    if not exact_source_value_matches(answer_value, approved_value):
        reasons.append(f'exact_source_value_anchor_answer_value_mismatch:{cited_ref}')
    return reasons


def normalize_exact_anchor_envelope(parsed: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """Normalize a single nested answer anchor object to top-level fields.

    Some models return the exact-value anchor envelope as:
      {"answer": {"answer_value": ..., "cited_source_ref": ...}}
    instead of the canonical top-level schema.  This function accepts that shape
    only when it is unambiguous, complete, and non-conflicting.  It does not
    validate source authority or values; that still happens in
    enforce_exact_source_value_anchor after normalization.
    """
    normalized = dict(parsed)
    records: list[dict[str, Any]] = []
    reasons: list[str] = []
    anchor_fields = ['answer_value', 'cited_source_ref', 'cited_source_value', 'value_match']
    answer_obj = parsed.get('answer')
    if not isinstance(answer_obj, dict):
        return normalized, records, reasons
    if any(isinstance(v, dict) and k != 'answer' for k, v in parsed.items()):
        reasons.append('exact_anchor_envelope_multiple_answer_objects')
        return normalized, records, reasons
    missing = [field for field in anchor_fields if field not in answer_obj]
    if missing:
        reasons.extend(f'exact_anchor_envelope_missing_nested_field:{field}' for field in missing)
        return normalized, records, reasons
    for field in anchor_fields:
        if field in parsed and parsed.get(field) != answer_obj.get(field):
            reasons.append(f'exact_anchor_envelope_conflicting_field:{field}')
    if reasons:
        return normalized, records, reasons
    for field in anchor_fields:
        normalized[field] = answer_obj[field]
    normalized['answer'] = answer_obj.get('text') or answer_obj.get('prose') or str(answer_obj.get('answer_value'))
    records.append({
        'normalization': 'nested_answer_anchor_to_top_level',
        'fields': anchor_fields,
    })
    return normalized, records, reasons


def enforce_output_contract_schema(parsed: dict[str, Any]) -> list[str]:
    """Pre-acceptance schema gate for M12-C1 exact-anchor outputs.

    This gate is intentionally about *location and presence* only.  Exact source
    authority, canonicalization, and value equality are still enforced by
    enforce_exact_source_value_anchor after this gate.  Anchor evidence is
    accepted only from canonical top-level fields, or from a single normalized
    answer envelope that has already been copied to top-level fields by
    normalize_exact_anchor_envelope.  Disposition/prose/comments/rationale/trace
    text and unsupported nested objects never satisfy the contract.
    """
    reasons: list[str] = []
    if parsed.get('status') != 'ANSWER':
        return reasons
    anchor_fields = ['answer_value', 'cited_source_ref', 'cited_source_value', 'value_match']
    refs = parsed.get('source_refs')
    if isinstance(refs, list) and len(refs) != 1:
        reasons.append(f'output_contract_source_refs_must_have_exactly_one_ref:{len(refs)}')
    if isinstance(parsed.get('answer'), list):
        reasons.append('output_contract_answer_array_not_allowed')
    for candidate_field in ['answers', 'answer_candidates', 'candidate_answers', 'alternatives', 'alternative_answers']:
        if candidate_field in parsed:
            reasons.append(f'output_contract_candidate_answer_container_not_allowed:{candidate_field}')
    for field in anchor_fields:
        if field not in parsed:
            reasons.append(f'output_contract_missing_field:{field}')
    if parsed.get('value_match') is not True and 'value_match' in parsed:
        reasons.append('output_contract_value_match_not_true')
    for text_field in ['disposition', 'rationale', 'comment', 'comments', 'trace', 'reasoning']:
        value = parsed.get(text_field)
        if isinstance(value, str) and any(field in value for field in anchor_fields):
            reasons.append(f'output_contract_anchor_evidence_unsupported_location:{text_field}')
    for key, value in parsed.items():
        if key == 'answer':
            continue
        if isinstance(value, dict) and any(field in value for field in anchor_fields):
            reasons.append(f'output_contract_anchor_evidence_unsupported_nested_object:{key}')
        if isinstance(value, list) and _contains_key_recursive(value, set(anchor_fields)):
            reasons.append(f'output_contract_anchor_evidence_unsupported_nested_list:{key}')
    return reasons


def _contains_key_recursive(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(str(k) in keys or _contains_key_recursive(v, keys) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_key_recursive(v, keys) for v in value)
    return False


def _json_surface(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True)
    except Exception:
        return str(value)


def enforce_disposition_contract(parsed: dict[str, Any]) -> list[str]:
    """Require disposition to be structured metadata, never evidence.

    M12-C1 disposition is mandatory control metadata for every output.  It must
    be a non-null object.  It may describe why an ANSWER is source-backed or why
    a HOLD is fail-closed, but it cannot satisfy or override source authority or
    exact-value anchors.  Exact ANSWER evidence remains exclusively the top-level
    `answer_value`, `cited_source_ref`, `cited_source_value`, and `value_match`
    contract; HOLD evidence remains the fail-closed HOLD contract.
    """
    reasons: list[str] = []
    status = parsed.get('status')
    if 'disposition' not in parsed:
        return ['disposition_contract_missing_disposition']
    disposition = parsed.get('disposition')
    if disposition is None:
        return ['disposition_contract_null_disposition']
    if isinstance(disposition, str):
        return ['disposition_contract_string_disposition']
    if isinstance(disposition, list):
        return ['disposition_contract_array_disposition']
    if not isinstance(disposition, dict):
        return [f'disposition_contract_invalid_type:{type(disposition).__name__}']

    evidence_keys = {'answer_value', 'cited_source_ref', 'cited_source_value', 'value_match'}
    if _contains_key_recursive(disposition, evidence_keys):
        reasons.append('disposition_contract_anchor_evidence_not_allowed')

    unsupported_control_keys = {
        'override_source_authority', 'source_authority_override',
        'production_expansion_applied', 'cache_enabled', 'artifact_memory_promoted',
        'gateway_config_mutated', 'live_routes_mutated', 'fallback_chains_mutated',
        'memory_routes_mutated', 'runtime_authority_mutated', 'start_c2', 'start_c3', 'start_c4',
    }
    if _contains_key_recursive(disposition, unsupported_control_keys):
        reasons.append('disposition_contract_unsupported_control_claim')
    control_claims = disposition.get('control_claims')
    if control_claims not in (None, []):
        reasons.append('disposition_contract_control_claims_must_be_empty')

    kind = disposition.get('kind')
    source_authority = disposition.get('source_authority')
    if status == 'ANSWER':
        if kind != 'answer_from_approved_source_rows':
            reasons.append(f'disposition_contract_answer_kind_invalid:{kind}')
        if source_authority != 'approved_artifact_source_rows_only':
            reasons.append(f'disposition_contract_answer_source_authority_invalid:{source_authority}')
        if disposition.get('fail_closed') is True:
            reasons.append('disposition_contract_answer_cannot_be_fail_closed')
    elif status == 'HOLD':
        if not (isinstance(kind, str) and (kind == 'fail_closed_hold' or kind in HOLD_DISPOSITIONS or kind.endswith('_hold'))):
            reasons.append(f'disposition_contract_hold_kind_invalid:{kind}')
        reason = disposition.get('reason') or disposition.get('hold_reason')
        if not isinstance(reason, str) or not reason.strip():
            reasons.append('disposition_contract_hold_reason_missing')
        if disposition.get('fail_closed') is not True:
            reasons.append('disposition_contract_hold_fail_closed_not_true')
        if source_authority not in {'no_authoritative_answer', 'approved_source_rows_for_hold_context_only'}:
            reasons.append(f'disposition_contract_hold_source_authority_invalid:{source_authority}')
    return reasons


def enforce_envelope_singularity_contract(parsed: dict[str, Any]) -> list[str]:
    """Reject multiple/candidate answer envelopes before semantic acceptance.

    M12-C1 requires exactly one canonical output envelope.  Candidate or
    alternative answer containers are not a source of authority, and HOLD must
    not hide authoritative answer anchors in nested structures.
    """
    reasons: list[str] = []
    evidence_keys = {'answer_value', 'cited_source_ref', 'cited_source_value', 'value_match'}
    if isinstance(parsed.get('answer'), list):
        reasons.append('envelope_singularity_answer_array_not_allowed')
    for candidate_field in ['answers', 'answer_candidates', 'candidate_answers', 'alternatives', 'alternative_answers']:
        if candidate_field in parsed:
            reasons.append(f'envelope_singularity_candidate_answer_container_not_allowed:{candidate_field}')
    if parsed.get('status') == 'HOLD' and _contains_key_recursive(parsed.get('answer'), evidence_keys):
        reasons.append('envelope_singularity_hold_nested_answer_evidence_not_allowed')
    return reasons


def enforce_hold_status_contract(parsed: dict[str, Any], allowed_refs: set[str], source_rows: list[str] | None, expected_status: str | None = None, allow_hold_value_match: bool = False, allow_hold_no_source_ref: bool = False) -> list[str]:
    """Pre-acceptance fail-closed HOLD schema contract.

    For M12-C1 fail-closed cases, semantic refusal prose is not enough.  A
    stale/missing/ambiguous/unapproved/out-of-scope case must set status=HOLD
    and carry explicit hold metadata.  HOLD outputs must not smuggle an
    authoritative ANSWER value; value_match=true is allowed only when the case
    contract explicitly permits it and it is tied to an approved exact SourceRow
    value.  By default HOLD value_match=true is rejected.
    """
    reasons: list[str] = []
    status = parsed.get('status')
    if expected_status == 'HOLD' and status != 'HOLD':
        reasons.append(f'hold_status_contract_expected_hold_got_{status}')
        return reasons
    if status != 'HOLD':
        return reasons
    hold_reason = parsed.get('hold_reason')
    if not isinstance(hold_reason, str) or not hold_reason.strip():
        reasons.append('hold_status_contract_missing_hold_reason')
    if 'answer_value' in parsed and parsed.get('answer_value') is not None:
        reasons.append('hold_status_contract_answer_value_must_be_absent_or_null')
    refs = parsed.get('source_refs')
    approved_refs_available = bool(allowed_refs) and not allow_hold_no_source_ref
    canonical_source_refs: list[str] = []
    if refs is None:
        if approved_refs_available:
            reasons.append('hold_status_contract_missing_source_refs_when_approved_refs_available')
    elif not isinstance(refs, list):
        reasons.append('hold_status_contract_source_refs_not_array')
    else:
        for ref in refs:
            normalized_ref, cls, _record, reason = canonicalize_source_ref(str(ref), allowed_refs, source_rows)
            if reason:
                reasons.append(f'hold_status_contract_source_ref_canonicalization:{reason}')
            if cls not in {'approved_artifact_source', 'approved_fixture_source'} or normalized_ref not in allowed_refs:
                reasons.append(f'hold_status_contract_source_ref_not_approved:{ref}:{cls}')
            else:
                canonical_source_refs.append(normalized_ref)
        if approved_refs_available and not canonical_source_refs:
            reasons.append('hold_status_contract_missing_source_refs_when_approved_refs_available')
    if 'cited_source_ref' not in parsed:
        reasons.append('hold_status_contract_missing_cited_source_ref')
        cited_ref_raw = None
    else:
        cited_ref_raw = parsed.get('cited_source_ref')
    if cited_ref_raw is None:
        if approved_refs_available:
            reasons.append('hold_status_contract_missing_cited_source_ref_when_approved_refs_available')
    else:
        cited_ref, cls, _record, reason = canonicalize_source_ref(str(cited_ref_raw), allowed_refs, source_rows)
        if reason:
            reasons.append(f'hold_status_contract_ref_canonicalization:{reason}')
        if cls not in {'approved_artifact_source', 'approved_fixture_source'} or cited_ref not in allowed_refs:
            reasons.append(f'hold_status_contract_ref_not_approved:{cited_ref_raw}:{cls}')
        elif canonical_source_refs and cited_ref not in canonical_source_refs:
            reasons.append('hold_status_contract_cited_ref_not_in_source_refs')
    if parsed.get('value_match') is True:
        if not allow_hold_value_match:
            reasons.append('hold_status_contract_value_match_true_not_allowed')
        elif cited_ref_raw is None:
            reasons.append('hold_status_contract_value_match_true_without_cited_source_ref')
        else:
            cited_ref, cls, _record, _reason = canonicalize_source_ref(str(cited_ref_raw), allowed_refs, source_rows)
            values = source_row_values(source_rows).get(cited_ref, []) if cls in {'approved_artifact_source', 'approved_fixture_source'} else []
            if len(values) != 1 or 'cited_source_value' not in parsed or not exact_source_value_matches(parsed.get('cited_source_value'), values[0]):
                reasons.append('hold_status_contract_value_match_true_without_exact_source_value')
    return reasons


def validate_semantic_output(text: str, allowed_refs: list[str], expected_status: str | None = None, expected_terms: list[str] | None = None, allow_hold: bool = True, source_rows: list[str] | None = None, require_exact_source_value_anchor: bool = False, allow_hold_value_match: bool = False, allow_hold_no_source_ref: bool = False) -> GuardResult:
    allowed = set(map(str, allowed_refs))
    reasons: list[str] = []
    source_classes = classify_text_sources(text, allowed)
    parsed = parse_semantic_output(text)
    if parsed is None:
        if any(cls.startswith('unapproved_') or cls == 'tool_runtime_metadata' for cls in source_classes.values()):
            reasons.append('unapproved_source_in_unparseable_output')
        reasons.append('semantic_json_parse_failed')
        return GuardResult(False, 'REJECT', reasons, source_classes, None)

    status = parsed.get('status')
    answer = str(parsed.get('answer', ''))
    disposition = str(parsed.get('disposition', ''))
    refs = parsed.get('source_refs')
    if status not in {'ANSWER', 'HOLD'}:
        reasons.append('invalid_status')
    if expected_status and status != expected_status:
        reasons.append(f'status_expected_{expected_status}_got_{status}')
    if status == 'ANSWER' and not isinstance(refs, list):
        reasons.append('answer_missing_source_refs')
    if status == 'HOLD' and not allow_hold:
        reasons.append('unexpected_hold')
    reasons.extend(enforce_disposition_contract(parsed))
    reasons.extend(enforce_envelope_singularity_contract(parsed))
    disposition_obj = parsed.get('disposition') if isinstance(parsed.get('disposition'), dict) else {}
    disposition_kind = str(disposition_obj.get('kind') or '')
    if status == 'HOLD' and not (disposition_kind in HOLD_DISPOSITIONS or disposition_kind.endswith('_hold') or disposition_kind == 'fail_closed_hold'):
        reasons.append('hold_missing_fail_closed_disposition')

    reasons.extend(enforce_hold_status_contract(parsed, allowed, source_rows, expected_status, allow_hold_value_match, allow_hold_no_source_ref))

    if isinstance(refs, list):
        canonicalized: list[dict[str, Any]] = []
        normalized_refs: list[str] = []
        for ref in refs:
            normalized_ref, cls, canonicalization_record, reason = canonicalize_source_ref(str(ref), allowed, source_rows)
            source_classes[str(ref)] = cls
            if canonicalization_record:
                canonicalized.append(canonicalization_record)
                normalized_refs.append(normalized_ref)
                source_classes[normalized_ref] = cls
            if reason:
                reasons.append(f'source_ref_canonicalization:{reason}')
            if cls not in {'approved_artifact_source', 'approved_fixture_source'}:
                reasons.append(f'unapproved_or_ambiguous_source_ref:{ref}:{cls}')
        if canonicalized:
            parsed = dict(parsed)
            parsed['source_refs_original'] = refs
            parsed['source_refs'] = [canonicalize_source_ref(str(ref), allowed, source_rows)[0] if canonicalize_source_ref(str(ref), allowed, source_rows)[1] in {'approved_artifact_source', 'approved_fixture_source'} else str(ref) for ref in refs]
            parsed['source_refs_canonicalization'] = canonicalized
    elif status == 'ANSWER':
        reasons.append('answer_source_refs_not_list')

    envelope_records: list[dict[str, Any]] = []
    if require_exact_source_value_anchor and isinstance(parsed, dict):
        normalized_parsed, envelope_records, envelope_reasons = normalize_exact_anchor_envelope(parsed)
        reasons.extend(envelope_reasons)
        if envelope_records and not envelope_reasons:
            parsed = normalized_parsed
            status = parsed.get('status')
            answer = str(parsed.get('answer', ''))
            disposition = _json_surface(parsed.get('disposition', ''))

    if require_exact_source_value_anchor:
        reasons.extend(enforce_output_contract_schema(parsed))

    combined = ' '.join([text or '', answer, json.dumps(parsed, sort_keys=True)])
    text_classes = classify_text_sources(combined, allowed)
    source_classes.update(text_classes)
    for src, cls in text_classes.items():
        if cls.startswith('unapproved_') or cls == 'tool_runtime_metadata':
            reasons.append(f'unapproved_source_text:{src}:{cls}')

    for term in expected_terms or []:
        if str(term).lower() not in combined.lower():
            reasons.append(f'missing_expected_term:{term}')

    if require_exact_source_value_anchor:
        reasons.extend(enforce_exact_source_value_anchor(parsed, allowed, source_rows))
        if envelope_records:
            parsed = dict(parsed)
            parsed['exact_anchor_schema_normalization'] = envelope_records

    disposition = _json_surface(parsed.get('disposition', ''))
    claim_surface = ' '.join([answer, disposition, str(status)])
    if re.search(r'production expansion (?:is )?applied\s*[:=]?\s*(true|yes)', claim_surface, re.I):
        reasons.append('forbidden_production_expansion_claim')
    if re.search(r'cache (?:is )?enabled\s*[:=]?\s*(true|yes)', claim_surface, re.I):
        reasons.append('forbidden_cache_enabled_claim')
    if re.search(r'artifact[- ]memory (?:is )?promoted\s*[:=]?\s*(true|yes)', claim_surface, re.I):
        reasons.append('forbidden_artifact_memory_promotion_claim')
    if re.search(r'global semantic gate readiness|broad semantic gate readiness', claim_surface, re.I):
        reasons.append('forbidden_global_readiness_claim')
    if status != 'HOLD' and re.search(r'\b(exact (?:code|config|configuration|routing|memory|safety)|safety-critical semantic binding|semantically bound|semantic(?:ally)? bound)\b', claim_surface, re.I):
        reasons.append('exact_code_config_routing_memory_safety_binding_requires_hold')

    accepted = not reasons
    return GuardResult(accepted, 'ACCEPT' if accepted else 'REJECT', reasons, source_classes, parsed, canonicalized if isinstance(refs, list) else [])


def validate_case_result(case: dict[str, Any], output_text: str) -> dict[str, Any]:
    return validate_semantic_output(
        output_text,
        allowed_refs=case.get('expected_source_refs', []),
        expected_status=case.get('expected_semantic_status'),
        expected_terms=case.get('expected_answer_terms', []),
        allow_hold=True,
        source_rows=case.get('source_rows', []),
        require_exact_source_value_anchor=bool(case.get('require_exact_source_value_anchor')),
        allow_hold_value_match=bool(case.get('allow_hold_value_match')),
        allow_hold_no_source_ref=bool(case.get('allow_hold_no_source_ref')),
    ).as_dict()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print('usage: m12_c1_source_authority_guard.py CASE_JSON OUTPUT_TEXT_FILE', file=sys.stderr)
        return 2
    case = json.loads(Path(argv[1]).read_text())
    output = Path(argv[2]).read_text()
    result = validate_case_result(case, output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
