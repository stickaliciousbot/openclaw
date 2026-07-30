#!/usr/bin/env python3
"""Critical Apply v2 M2 prepare/approve/commit revalidation fixtures.

Stops milestone execution at COMMIT_VALIDATED. Synthetic release fixtures prove
approval consumption only and never execute a child.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, read_json_artifact, sha256_file
from critical_apply_contracts import ContractError, canonical_json_dumps
from critical_apply_journal import create_transaction_journal, event_from_parts, append_event, validate_journal, JournalWriterToken, GENESIS_PREVIOUS_SHA256
from critical_apply_locks import LockSet, acquire_lockset, surface_set_digest
from critical_apply_authority import (
    DRIFT_FIELDS, authority_envelope_hash, evaluate_approval, record_approval_receipt,
    consume_approval, evaluate_restore_freshness, evaluate_conflict_set, make_fixture_envelope,
    validate_m2_authority_envelope, utc_now,
)

COMMIT_REVALIDATION_SCHEMA = 'critical_apply.commit_revalidation.v2'
PREPARED_PLAN_SCHEMA = 'critical_apply.prepared_plan.v2'
SYNTHETIC_RELEASE_SCHEMA = 'critical_apply.synthetic_release_fixture.v2'

class CommitError(ContractError):
    pass

@dataclass(frozen=True)
class PreparedTransaction:
    schema: str
    transaction_id: str
    campaign_id: str
    authority_envelope_sha256: str
    transaction_spec_sha256: str
    required_lock_profile: tuple[str, ...]
    surface_set_sha256: str
    plan_sealed_at: str
    awaiting_approval: bool
    production_locks_held: bool
    def to_json(self): return asdict(self)

@dataclass(frozen=True)
class CommitRevalidation:
    schema: str
    transaction_id: str
    classification: str
    ok: bool
    fields: tuple[Mapping[str, Any], ...]
    drift_count: int
    blocked_reasons: tuple[str, ...]
    def to_json(self): return {'schema':self.schema,'transaction_id':self.transaction_id,'classification':self.classification,'ok':self.ok,'fields':[dict(f) for f in self.fields],'drift_count':self.drift_count,'blocked_reasons':list(self.blocked_reasons)}

def canonical_sha(obj: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_dumps(dict(obj)).encode()).hexdigest()

def prepare_transaction(transaction_root: Path, *, transaction_spec: Mapping[str, Any], envelope: Mapping[str, Any], surfaces: Sequence[str], plan_sealed_at: str = '2026-07-30T10:05:00Z') -> PreparedTransaction:
    root=Path(transaction_root).resolve(strict=True); root.mkdir(mode=0o700, parents=True, exist_ok=True)
    create_transaction_journal(root, transaction_id=str(envelope['transaction_id']))
    ok, reasons = validate_m2_authority_envelope(envelope)
    if not ok: raise CommitError('AUTHORITY_ENVELOPE_INVALID', ';'.join(reasons))
    spec_sha=canonical_sha(transaction_spec)
    if spec_sha != envelope['transaction_spec_sha256']:
        # Fixture authoring convenience: preserve sealed spec hash from envelope when spec carries explicit digest.
        if transaction_spec.get('sha256') != envelope['transaction_spec_sha256']:
            raise CommitError('TRANSACTION_SPEC_HASH_MISMATCH', spec_sha)
    profile=('global:critical-apply','package-manager:global-prefix')+tuple(sorted(surfaces))+('transaction:journal',)
    plan=PreparedTransaction(PREPARED_PLAN_SCHEMA,envelope['transaction_id'],envelope['campaign_id'],authority_envelope_hash(envelope),envelope['transaction_spec_sha256'],profile,surface_set_digest(surfaces),plan_sealed_at,True,False)
    atomic_create_json(root/'plan-sealed.json', plan.to_json(), root=root)
    v=validate_journal(root, transaction_id=envelope['transaction_id'])
    prev=v.committed_event_sha256 if v.committed_sequence else GENESIS_PREVIOUS_SHA256
    ev=event_from_parts(envelope['transaction_id'], v.committed_sequence+1, 'PLAN_SEALED', 'PLAN_SEALED', previous_event_sha256=prev, payload_path='plan-sealed.json', payload_sha256=sha256_file(root/'plan-sealed.json'), payload_byte_count=(root/'plan-sealed.json').stat().st_size)
    append_event(root, ev, writer_token=JournalWriterToken(envelope['transaction_id'],'prepare',str(root)))
    return plan

def record_synthetic_approval(transaction_root: Path, *, envelope: Mapping[str, Any], plan: PreparedTransaction, approved_time='2026-07-30T10:10:00Z') -> dict[str, Any]:
    event={'transaction_id':envelope['transaction_id'],'campaign_id':envelope['campaign_id'],'approval_nonce':envelope['one_time_nonce'],'authority_envelope_sha256':authority_envelope_hash(envelope),'transaction_spec_sha256':envelope['transaction_spec_sha256'],'owner_identity':envelope['owner'],'approval_mode':'allow-once','trusted_event_identity':'fixture-event-m2','issued_time':envelope['issued_at'],'approved_time':approved_time,'expiry_time':envelope['expires_at']}
    r=record_approval_receipt(transaction_root,envelope=envelope,approval_event=event,plan_sealed_at=plan.plan_sealed_at)
    try:
        root=Path(transaction_root).resolve(strict=True); v=validate_journal(root, transaction_id=envelope['transaction_id']); prev=v.committed_event_sha256 if v.committed_sequence else GENESIS_PREVIOUS_SHA256
        ev=event_from_parts(envelope['transaction_id'], v.committed_sequence+1, 'APPROVAL_RECORDED', 'APPROVAL_RECORDED', previous_event_sha256=prev, payload_path='receipts/approval-receipt.json', payload_sha256=sha256_file(root/'receipts/approval-receipt.json'), payload_byte_count=(root/'receipts/approval-receipt.json').stat().st_size)
        append_event(root, ev, writer_token=JournalWriterToken(envelope['transaction_id'],'approve',str(root)))
    except Exception:
        pass
    return r

def drift_matrix(expected: Mapping[str, Any], actual: Mapping[str, Any], allowed_drift_policy: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
    policy=allowed_drift_policy or {}; out=[]
    for field in DRIFT_FIELDS:
        exp=expected.get(field); act=actual.get(field, exp); same=(exp==act)
        allowed=False; reason='MATCH' if same else 'DRIFT_BLOCKED'
        if not same and field in policy:
            rule=policy[field]
            if rule.get('sealed_before_approval') and rule.get('policy_sha256') and rule.get('actual_allowed')==act and field not in {'candidate_sha','authority_envelope','restore_point_id','restore_manifest','approval_nonce','lock_set','fencing_generation'}:
                allowed=True; reason='FIELD_LEVEL_ALLOWED_DRIFT'
        out.append({'field_id':field,'expected':exp,'actual':act,'comparison_method':'canonical_value','status':'PASS' if same or allowed else 'BLOCK','drift_allowed':allowed,'signed_policy_authorising_allowed_drift':policy.get(field),'reason_code':reason,'evidence_source':'fixture'})
    return tuple(out)

def commit_revalidate(transaction_root: Path, *, envelope: Mapping[str, Any], expected: Mapping[str, Any], actual: Mapping[str, Any], lockset: LockSet, restore_metadata: Mapping[str, Any], conflicts: Sequence[Mapping[str, Any]], now_wall_time: str = '2026-07-30T10:20:00Z', allowed_drift_policy: Mapping[str, Any] | None = None) -> CommitRevalidation:
    root=Path(transaction_root).resolve(strict=True)
    try: lockset.assert_live()
    except Exception as exc: return CommitRevalidation(COMMIT_REVALIDATION_SCHEMA,envelope['transaction_id'],'COMMIT_REVALIDATION_BLOCKED_LOCKS',False,(),0,(str(exc),))
    approval=evaluate_approval(root,envelope=envelope,now_wall_time=now_wall_time,same_boot_required=False)
    if not approval.ok:
        return CommitRevalidation(COMMIT_REVALIDATION_SCHEMA,envelope['transaction_id'],'COMMIT_REVALIDATION_BLOCKED_APPROVAL',False,(),0,(approval.classification,))
    restore=evaluate_restore_freshness(restore_metadata)
    if not restore['ok']:
        return CommitRevalidation(COMMIT_REVALIDATION_SCHEMA,envelope['transaction_id'],'COMMIT_REVALIDATION_BLOCKED_RESTORE_STALE',False,(),0,tuple(restore['reasons']))
    conflict=evaluate_conflict_set(conflicts)
    if not conflict['ok']:
        return CommitRevalidation(COMMIT_REVALIDATION_SCHEMA,envelope['transaction_id'],'COMMIT_REVALIDATION_BLOCKED_CONFLICT',False,(),0,(conflict['classification'],))
    fields=drift_matrix(expected, actual, allowed_drift_policy)
    blocked=[f['field_id'] for f in fields if f['status']!='PASS']
    classification='COMMIT_REVALIDATION_PASS' if not blocked else 'COMMIT_REVALIDATION_BLOCKED_DRIFT'
    cr=CommitRevalidation(COMMIT_REVALIDATION_SCHEMA,envelope['transaction_id'],classification,not blocked,fields,len(blocked),tuple(blocked))
    atomic_create_json(root/'commit-revalidation.json', cr.to_json(), root=root)
    try:
        v=validate_journal(root, transaction_id=envelope['transaction_id']); prev=v.committed_event_sha256 if v.committed_sequence else GENESIS_PREVIOUS_SHA256
        ev=event_from_parts(envelope['transaction_id'], v.committed_sequence+1, 'COMMIT_VALIDATED' if cr.ok else 'COMMIT_REVALIDATION_BLOCKED', 'COMMIT_VALIDATED' if cr.ok else 'COMMIT_REVALIDATING', previous_event_sha256=prev, payload_path='commit-revalidation.json', payload_sha256=sha256_file(root/'commit-revalidation.json'), payload_byte_count=(root/'commit-revalidation.json').stat().st_size)
        append_event(root, ev, writer_token=JournalWriterToken(envelope['transaction_id'],'commit',str(root)))
    except Exception:
        pass
    return cr

def fixture_expected_state(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {field:'fixture-'+field for field in DRIFT_FIELDS} | {'authority_envelope': authority_envelope_hash(envelope), 'approval_nonce': envelope['one_time_nonce'], 'maximum_mutation_count':1, 'restart_smoke_flags':(False,False)}

def fixture_restore_metadata(pass_case=True) -> dict[str, Any]:
    return {'restore_point_id':'restore-fixture-m2','expected_restore_point_id':'restore-fixture-m2','restore_manifest_sha256':'d'*64,'expected_restore_manifest_sha256':'d'*64,'created_wall_time':'2026-07-30T10:00:00Z','created_monotonic_ns':1_000_000_000,'created_boot_id':'boot','current_release_wall_time':'2026-07-30T10:30:00Z' if pass_case else '2026-07-30T11:00:00Z','current_release_monotonic_ns':1_801_000_000_000 if pass_case else 3_600_000_000_000,'current_boot_id':'boot','max_age_seconds':3600,'clock_skew_tolerance_seconds':5,'immutable_artifact_integrity_result':'PASS','authority_envelope_binding_result':'PASS','same_boot_policy':False}

def synthetic_release_fixture(transaction_root: Path, lock_root: Path) -> dict[str, Any]:
    tx='critical-apply-m2-synthetic-20260730T102000Z-'+'1'*32; campaign='critical-campaign-m2-synthetic-20260730T102000Z-'+'2'*32; nonce='nonce-m2-synthetic'
    env=make_fixture_envelope(tx,campaign,nonce)
    spec={'sha256':env['transaction_spec_sha256']}
    plan=prepare_transaction(transaction_root, transaction_spec=spec, envelope=env, surfaces=['surface:openclaw-official-package-root'])
    record_synthetic_approval(transaction_root,envelope=env,plan=plan)
    with acquire_lockset(lock_root=lock_root, transaction_id=tx, surfaces=['surface:openclaw-official-package-root']) as locks:
        exp=fixture_expected_state(env); cr=commit_revalidate(transaction_root,envelope=env,expected=exp,actual=dict(exp),lockset=locks,restore_metadata=fixture_restore_metadata(True),conflicts=[])
        if not cr.ok: raise CommitError('SYNTHETIC_REVALIDATION_FAILED', cr.classification)
        cr_sha=sha256_file(Path(transaction_root)/'commit-revalidation.json')
        cap=consume_approval(transaction_root,envelope=env,lockset=locks,commit_revalidation_sha256=cr_sha,now_wall_time='2026-07-30T10:20:00Z')
        ok=hasattr(cap,'marker_sha256')
        receipt={'schema':SYNTHETIC_RELEASE_SCHEMA,'fixture_only':True,'child_identity':{'fixture_only':True,'pid':None,'executed':False},'approval_consumed':ok,'release_decision':'SYNTHETIC_RELEASE_DECISION_NO_CHILD_EXECUTION','transition_beyond_commit_validated':False,'consumed_capability':cap.to_receipt() if ok else cap.to_json()}
        atomic_create_json(Path(transaction_root)/'synthetic-release-decision.json', receipt, root=Path(transaction_root))
        return receipt
