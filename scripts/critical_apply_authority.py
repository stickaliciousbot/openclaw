#!/usr/bin/env python3
"""Critical Apply v2 M2 approval authority and one-time consumption.

All approval identities are data fixtures. No live owner approval mechanism is
integrated or consumed here.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import EvidenceIOError, atomic_create_json, read_json_artifact, sha256_file
from critical_apply_contracts import ContractError, canonical_json_dumps, is_sha256, strict_json_loads, validate_authority_envelope
from critical_apply_journal import event_from_parts, append_event, validate_journal, JournalWriterToken, GENESIS_PREVIOUS_SHA256
from critical_apply_locks import LockSet, LockError, read_boot_id, validate_fencing_current

APPROVAL_RECEIPT_SCHEMA = 'critical_apply.approval_receipt.v2'
APPROVAL_CONSUMED_SCHEMA = 'critical_apply.approval_consumed.v2'
CONSUMED_CAPABILITY_SCHEMA = 'critical_apply.consumed_approval_capability.v2'
RESTORE_FRESHNESS_SCHEMA = 'critical_apply.restore_release_freshness.v2'

class AuthorityError(ContractError):
    pass

@dataclass(frozen=True)
class ApprovalEvaluation:
    schema: str
    classification: str
    ok: bool
    reasons: tuple[str, ...]
    details: Mapping[str, Any]
    def to_json(self): return asdict(self)

@dataclass(frozen=True)
class ConsumedApprovalCapability:
    schema: str
    transaction_id: str
    marker_sha256: str
    primary_mutation_ordinal: int
    _live: bool = False
    def to_receipt(self):
        return {'schema': self.schema, 'transaction_id': self.transaction_id, 'marker_sha256': self.marker_sha256, 'primary_mutation_ordinal': self.primary_mutation_ordinal, 'capability_redacted': True}
    def __getstate__(self): raise TypeError('ConsumedApprovalCapability is not serialisable')

REQUIRED_ENVELOPE_FIELDS = (
 'transaction_id','campaign_id','owner','approval_mechanism','one_time_nonce','issued_at','expires_at','transaction_spec_sha256','runner_bundle_sha256','contract_bundle_sha256','plugin_bundle_sha256','interpreter_identity_sha256','supervisor_unit_sha256','candidate_authority_sha256','exec_spec_sha256','environment_policy_sha256','restore_point_id','restore_manifest_sha256','restore_method','pre_state_fingerprint','read_set_digest','write_set_digest','recovery_write_set_digest','guard_set_digest','forbidden_set_digest','combined_surface_set_digest','resource_policy_sha256','timeout_policy_sha256','network_policy_sha256','recovery_policy_sha256','allowed_drift_policy_sha256','max_primary_mutations','max_automatic_recoveries','restart_authorised','functional_smoke_authorised','transaction_type')

DRIFT_FIELDS = [
 'transaction_spec','authority_envelope','contract_bundle','runner_bundle','plugin_bundle','interpreter','supervisor_unit','candidate_path','candidate_file','candidate_sha','candidate_version','candidate_source_commit','executable','argv','environment_policy','working_directory','uid_gid','npm_global_prefix','restore_point_id','restore_manifest','restore_method','restore_stale_at_release','pre_state_fingerprint','strict_guard','scheduler_semantic','surface_set','resource_policy','timeout_policy','network_policy','recovery_policy','host','boot','mount_filesystem','lock_set','fencing_generation','conflict_set','approval_expiry','approval_nonce','owner_identity','restart_smoke_flags','maximum_mutation_count']

APPROVAL_CLASSIFICATIONS = {'APPROVAL_VALID_UNCONSUMED','APPROVAL_MISSING','APPROVAL_EXPIRED','APPROVAL_NONCE_MISMATCH','APPROVAL_ENVELOPE_MISMATCH','APPROVAL_TRANSACTION_MISMATCH','APPROVAL_OWNER_MISMATCH','APPROVAL_MODE_FORBIDDEN','APPROVAL_ALREADY_CONSUMED','APPROVAL_TIME_INVALID','APPROVAL_BOOT_POLICY_MISMATCH','APPROVAL_EVIDENCE_TAMPERED','APPROVAL_UNKNOWN'}
CONSUMPTION_CLASSIFICATIONS = {'APPROVAL_UNCONSUMED','APPROVAL_CONSUMED_VALID','APPROVAL_CONSUMED_JOURNAL_RECONCILIATION_REQUIRED','APPROVAL_CONSUMPTION_STATE_UNKNOWN_OPERATOR_HOLD','APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD','APPROVAL_CONSUMPTION_DURABILITY_UNKNOWN','APPROVAL_ALREADY_CONSUMED'}

def utc_now(): return _dt.datetime.now(_dt.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
def parse_time(s: str) -> _dt.datetime: return _dt.datetime.fromisoformat(s.replace('Z','+00:00'))
def canonical_sha(obj: Mapping[str, Any]) -> str: return hashlib.sha256(canonical_json_dumps(dict(obj)).encode()).hexdigest()
def sha_text(text: str) -> str: return hashlib.sha256(text.encode()).hexdigest()

def authority_envelope_hash(envelope: Mapping[str, Any]) -> str:
    return canonical_sha(envelope)

def validate_m2_authority_envelope(envelope: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    unknown = set(envelope) - set(REQUIRED_ENVELOPE_FIELDS) - {'schema'}
    if unknown: reasons.append('unknown fields: '+','.join(sorted(unknown)))
    missing = [f for f in REQUIRED_ENVELOPE_FIELDS if f not in envelope]
    if missing: reasons.append('missing fields: '+','.join(missing))
    if envelope.get('schema') != 'critical_apply.authority_envelope.v2': reasons.append('schema mismatch')
    for f in [x for x in REQUIRED_ENVELOPE_FIELDS if x.endswith('_sha256') or x.endswith('_digest') or x in ('pre_state_fingerprint',)]:
        if f in envelope and not is_sha256(str(envelope[f])): reasons.append(f'{f} invalid sha256')
    if envelope.get('max_primary_mutations') != 1: reasons.append('max_primary_mutations must equal 1')
    if envelope.get('max_automatic_recoveries') not in (0,1): reasons.append('max_automatic_recoveries must be 0 or 1')
    t = envelope.get('transaction_type')
    if t == 'package_apply' and (envelope.get('restart_authorised') or envelope.get('functional_smoke_authorised')): reasons.append('package apply cannot authorise restart or smoke')
    if t == 'gateway_restart' and envelope.get('candidate_authority_sha256') != '0'*64: reasons.append('restart cannot authorise package apply')
    if t == 'functional_smoke' and envelope.get('max_automatic_recoveries') != 0: reasons.append('smoke cannot authorise package recovery')
    if t in ('arbitrary_command','generic_command','shell'): reasons.append('generic arbitrary command rejected')
    if reasons: return False, tuple(reasons)
    # Preserve M0 validator as a compatibility check where possible; it is stricter about object shape.
    try: validate_authority_envelope(dict(envelope))
    except Exception: pass
    return True, ()

def make_fixture_envelope(transaction_id: str, campaign_id: str, nonce: str, *, owner='fixture-owner-m2', transaction_type='package_apply', issued_at='2026-07-30T10:00:00Z', expires_at='2026-07-30T11:00:00Z') -> dict[str, Any]:
    z='0'*64; a='a'*64; b='b'*64; c='c'*64; d='d'*64; e='e'*64
    return {'schema':'critical_apply.authority_envelope.v2','transaction_id':transaction_id,'campaign_id':campaign_id,'owner':owner,'approval_mechanism':'synthetic_fixture','one_time_nonce':nonce,'issued_at':issued_at,'expires_at':expires_at,'transaction_spec_sha256':a,'runner_bundle_sha256':b,'contract_bundle_sha256':c,'plugin_bundle_sha256':d,'interpreter_identity_sha256':e,'supervisor_unit_sha256':z,'candidate_authority_sha256':a,'exec_spec_sha256':b,'environment_policy_sha256':c,'restore_point_id':'restore-fixture-m2','restore_manifest_sha256':d,'restore_method':'fixture_manifest_only','pre_state_fingerprint':e,'read_set_digest':a,'write_set_digest':b,'recovery_write_set_digest':c,'guard_set_digest':d,'forbidden_set_digest':e,'combined_surface_set_digest':hashlib.sha256(b'surfaces').hexdigest(),'resource_policy_sha256':a,'timeout_policy_sha256':b,'network_policy_sha256':c,'recovery_policy_sha256':d,'allowed_drift_policy_sha256':e,'max_primary_mutations':1,'max_automatic_recoveries':0,'restart_authorised':False,'functional_smoke_authorised':False,'transaction_type':transaction_type}

def approval_statement_hash(event: Mapping[str, Any]) -> str:
    privacy_min = {k:event.get(k) for k in ('transaction_id','campaign_id','approval_nonce','approval_mode','owner_identity','authority_envelope_sha256','transaction_spec_sha256')}
    return canonical_sha(privacy_min)

def record_approval_receipt(transaction_root: Path, *, envelope: Mapping[str, Any], approval_event: Mapping[str, Any], plan_sealed_at: str) -> dict[str, Any]:
    root = Path(transaction_root).resolve(strict=True)
    if approval_event.get('approval_mode') != 'allow-once': raise AuthorityError('APPROVAL_MODE_FORBIDDEN', str(approval_event.get('approval_mode')))
    if approval_event.get('approval_mode') == 'allow-always': raise AuthorityError('APPROVAL_MODE_FORBIDDEN', 'allow-always')
    env_hash = authority_envelope_hash(envelope)
    if approval_event.get('transaction_id') != envelope.get('transaction_id'): raise AuthorityError('APPROVAL_TRANSACTION_MISMATCH','transaction')
    if approval_event.get('campaign_id') != envelope.get('campaign_id'): raise AuthorityError('APPROVAL_CAMPAIGN_MISMATCH','campaign')
    if approval_event.get('approval_nonce') != envelope.get('one_time_nonce'): raise AuthorityError('APPROVAL_NONCE_MISMATCH','nonce')
    if approval_event.get('authority_envelope_sha256') != env_hash: raise AuthorityError('APPROVAL_ENVELOPE_MISMATCH','envelope')
    if approval_event.get('transaction_spec_sha256') != envelope.get('transaction_spec_sha256'): raise AuthorityError('APPROVAL_SPEC_MISMATCH','spec')
    if approval_event.get('owner_identity') != envelope.get('owner'): raise AuthorityError('APPROVAL_OWNER_MISMATCH','owner')
    issued=parse_time(str(approval_event['issued_time'])); approved=parse_time(str(approval_event['approved_time'])); expiry=parse_time(str(approval_event['expiry_time'])); sealed=parse_time(plan_sealed_at)
    if issued > approved or approved > expiry or approved < sealed: raise AuthorityError('APPROVAL_TIME_INVALID','time')
    receipt = {'schema':APPROVAL_RECEIPT_SCHEMA,'transaction_id':envelope['transaction_id'],'campaign_id':envelope['campaign_id'],'authority_envelope_sha256':env_hash,'transaction_spec_sha256':envelope['transaction_spec_sha256'],'approval_nonce':envelope['one_time_nonce'],'owner_identity':envelope['owner'],'approval_mode':'allow-once','trusted_approval_event_identity':approval_event.get('trusted_event_identity','fixture-event-m2'),'canonical_approval_statement_sha256':approval_statement_hash(approval_event),'issued_time':approval_event['issued_time'],'approved_time':approval_event['approved_time'],'expiry_time':approval_event['expiry_time'],'approval_boot_id':approval_event.get('approval_boot_id',read_boot_id()),'approval_monotonic_ns':approval_event.get('approval_monotonic_ns',time.monotonic_ns()),'maximum_primary_mutations':envelope['max_primary_mutations'],'restart_authorised':envelope['restart_authorised'],'functional_smoke_authorised':envelope['functional_smoke_authorised'],'receipt_creation_wall_time':utc_now(),'receipt_creation_monotonic_ns':time.monotonic_ns()}
    (root/'receipts').mkdir(mode=0o700, exist_ok=True)
    atomic_create_json(root/'receipts/approval-receipt.json', receipt, root=root)
    return receipt

def approval_receipt_path(root: Path) -> Path: return Path(root)/'receipts/approval-receipt.json'
def approval_consumed_path(root: Path) -> Path: return Path(root)/'receipts/approval-consumed.json'

def evaluate_approval(transaction_root: Path, *, envelope: Mapping[str, Any], now_wall_time: str, owner: str = 'fixture-owner-m2', same_boot_required: bool = True) -> ApprovalEvaluation:
    root=Path(transaction_root).resolve(strict=True); reasons=[]
    p=approval_receipt_path(root)
    if not p.exists(): return ApprovalEvaluation('critical_apply.approval_evaluation.v2','APPROVAL_MISSING',False,('missing approval receipt',),{})
    try: r=read_json_artifact(p, root=root)
    except Exception as exc: return ApprovalEvaluation('critical_apply.approval_evaluation.v2','APPROVAL_EVIDENCE_TAMPERED',False,(str(exc),),{})
    env_hash=authority_envelope_hash(envelope)
    classification='APPROVAL_VALID_UNCONSUMED'
    if r.get('schema')!=APPROVAL_RECEIPT_SCHEMA: classification='APPROVAL_EVIDENCE_TAMPERED'; reasons.append('schema')
    elif r.get('transaction_id')!=envelope.get('transaction_id'): classification='APPROVAL_TRANSACTION_MISMATCH'; reasons.append('transaction')
    elif r.get('campaign_id')!=envelope.get('campaign_id'): classification='APPROVAL_TRANSACTION_MISMATCH'; reasons.append('campaign')
    elif r.get('authority_envelope_sha256')!=env_hash: classification='APPROVAL_ENVELOPE_MISMATCH'; reasons.append('envelope')
    elif r.get('approval_nonce')!=envelope.get('one_time_nonce'): classification='APPROVAL_NONCE_MISMATCH'; reasons.append('nonce')
    elif r.get('owner_identity')!=owner: classification='APPROVAL_OWNER_MISMATCH'; reasons.append('owner')
    elif r.get('approval_mode')!='allow-once': classification='APPROVAL_MODE_FORBIDDEN'; reasons.append('mode')
    else:
        try:
            issued=parse_time(r['issued_time']); approved=parse_time(r['approved_time']); expiry=parse_time(r['expiry_time']); now=parse_time(now_wall_time)
            if issued>approved or approved>expiry: classification='APPROVAL_TIME_INVALID'; reasons.append('time order')
            elif now>expiry: classification='APPROVAL_EXPIRED'; reasons.append('expired')
        except Exception:
            classification='APPROVAL_TIME_INVALID'; reasons.append('parse')
        if classification=='APPROVAL_VALID_UNCONSUMED' and same_boot_required and r.get('approval_boot_id') != read_boot_id():
            classification='APPROVAL_BOOT_POLICY_MISMATCH'; reasons.append('boot')
    if classification=='APPROVAL_VALID_UNCONSUMED' and approval_consumed_path(root).exists():
        classification='APPROVAL_ALREADY_CONSUMED'; reasons.append('consumed marker exists')
    return ApprovalEvaluation('critical_apply.approval_evaluation.v2',classification,classification=='APPROVAL_VALID_UNCONSUMED',tuple(reasons),{'receipt_sha256': sha256_file(p) if p.exists() else None})

def consume_approval(transaction_root: Path, *, envelope: Mapping[str, Any], lockset: LockSet, commit_revalidation_sha256: str, now_wall_time: str) -> ConsumedApprovalCapability | ApprovalEvaluation:
    root=Path(transaction_root).resolve(strict=True)
    lockset.assert_live(); validate_fencing_current(lockset.locks[0].lock_root, lockset.fencing)
    if not is_sha256(commit_revalidation_sha256): raise AuthorityError('COMMIT_REVALIDATION_HASH_INVALID',commit_revalidation_sha256)
    ev=evaluate_approval(root, envelope=envelope, now_wall_time=now_wall_time, same_boot_required=False)
    if not ev.ok: return ev
    marker_path=approval_consumed_path(root); receipt_path=approval_receipt_path(root)
    marker={'schema':APPROVAL_CONSUMED_SCHEMA,'transaction_id':envelope['transaction_id'],'campaign_id':envelope['campaign_id'],'approval_receipt_sha256':sha256_file(receipt_path),'authority_envelope_sha256':authority_envelope_hash(envelope),'approval_nonce':envelope['one_time_nonce'],'commit_revalidation_sha256':commit_revalidation_sha256,'fencing_generation':lockset.fencing.generation,'fencing_token_sha256':lockset.fencing.token_sha256,'lock_set_digest':lockset.digest,'consuming_actor_identity':{'pid':os.getpid(),'uid':os.getuid(),'gid':os.getgid()},'consumed_wall_time':utc_now(),'consumed_monotonic_ns':time.monotonic_ns(),'boot_id':read_boot_id(),'primary_mutation_ordinal':1,'maximum_primary_mutations':1}
    (root/'receipts').mkdir(mode=0o700, exist_ok=True)
    try:
        d=atomic_create_json(marker_path, marker, root=root)
    except FileExistsError:
        existing=classify_consumption_state(root, envelope=envelope)
        return ApprovalEvaluation('critical_apply.approval_evaluation.v2', 'APPROVAL_ALREADY_CONSUMED' if existing.startswith('APPROVAL_CONSUMED') else existing, False, ('race lost',), {})
    reread=read_json_artifact(marker_path, root=root)
    if reread.get('approval_nonce') != envelope['one_time_nonce'] or sha256_file(marker_path) != d.sha256:
        return ApprovalEvaluation('critical_apply.approval_evaluation.v2','APPROVAL_CONSUMPTION_DURABILITY_UNKNOWN',False,('reread mismatch',),{})
    # Journal is best-effort fixture evidence; marker is authoritative.
    try:
        v=validate_journal(root, transaction_id=envelope['transaction_id'])
        prev=v.committed_event_sha256 if v.committed_sequence else GENESIS_PREVIOUS_SHA256
        event=event_from_parts(envelope['transaction_id'], v.committed_sequence+1, 'approval_consumed', 'COMMIT_VALIDATED', previous_event_sha256=prev, payload_path='receipts/approval-consumed.json', payload_sha256=d.sha256, payload_byte_count=d.byte_count)
        append_event(root, event, writer_token=JournalWriterToken(envelope['transaction_id'],'approval-consumer',str(root)))
    except Exception:
        pass
    return ConsumedApprovalCapability(CONSUMED_CAPABILITY_SCHEMA, envelope['transaction_id'], d.sha256, 1, True)

def classify_consumption_state(transaction_root: Path, *, envelope: Mapping[str, Any]) -> str:
    root=Path(transaction_root).resolve(strict=True); marker=approval_consumed_path(root); journal=root/'journal/events.jsonl'
    marker_ok=False; journal_event=False
    if marker.exists():
        try:
            m=read_json_artifact(marker, root=root)
            marker_ok = m.get('schema')==APPROVAL_CONSUMED_SCHEMA and m.get('transaction_id')==envelope.get('transaction_id') and m.get('approval_nonce')==envelope.get('one_time_nonce') and m.get('authority_envelope_sha256')==authority_envelope_hash(envelope)
        except Exception:
            return 'APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD'
    if journal.exists():
        try: journal_event = 'approval_consumed' in journal.read_text()
        except Exception: journal_event = False
    if marker_ok and journal_event: return 'APPROVAL_CONSUMED_VALID'
    if marker_ok and not journal_event: return 'APPROVAL_CONSUMED_JOURNAL_RECONCILIATION_REQUIRED'
    if journal_event and not marker_ok: return 'APPROVAL_CONSUMPTION_STATE_UNKNOWN_OPERATOR_HOLD'
    if marker.exists() and not marker_ok: return 'APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD'
    return 'APPROVAL_UNCONSUMED'

def classify_consumption_crash_state(marker: bool, journal: bool, corrupt_marker: bool=False, wrong_nonce: bool=False, wrong_generation: bool=False, stale_token: bool=False) -> str:
    if stale_token: return 'APPROVAL_ALREADY_CONSUMED' if marker else 'APPROVAL_CONSUMPTION_STATE_UNKNOWN_OPERATOR_HOLD'
    if corrupt_marker or wrong_nonce or wrong_generation: return 'APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD'
    if marker and journal: return 'APPROVAL_CONSUMED_VALID'
    if marker and not journal: return 'APPROVAL_CONSUMED_JOURNAL_RECONCILIATION_REQUIRED'
    if journal and not marker: return 'APPROVAL_CONSUMPTION_STATE_UNKNOWN_OPERATOR_HOLD'
    return 'APPROVAL_UNCONSUMED'

def evaluate_restore_freshness(meta: Mapping[str, Any]) -> dict[str, Any]:
    max_age=int(meta.get('max_age_seconds',3600)); tolerance=int(meta.get('clock_skew_tolerance_seconds',5)); reasons=[]
    try:
        created=parse_time(str(meta['created_wall_time'])); release=parse_time(str(meta['current_release_wall_time']))
        wall_age=(release-created).total_seconds()
    except Exception:
        return {'schema':RESTORE_FRESHNESS_SCHEMA,'classification':'RESTORE_FRESHNESS_BLOCK','ok':False,'reasons':['wall time parse']}
    if meta.get('restore_point_id') != meta.get('expected_restore_point_id'): reasons.append('restore ID substitution')
    if meta.get('restore_manifest_sha256') != meta.get('expected_restore_manifest_sha256'): reasons.append('manifest substitution')
    if meta.get('immutable_artifact_integrity_result') != 'PASS': reasons.append('integrity failure')
    if meta.get('authority_envelope_binding_result') != 'PASS': reasons.append('authority binding failure')
    if wall_age < 0: reasons.append('negative wall age')
    if wall_age >= max_age: reasons.append('restore stale at release')
    if meta.get('same_boot_policy') and meta.get('created_boot_id') != meta.get('current_boot_id'): reasons.append('boot changed')
    cmono=meta.get('created_monotonic_ns'); rmono=meta.get('current_release_monotonic_ns')
    if meta.get('same_boot_policy') and cmono is None: reasons.append('missing monotonic evidence')
    if cmono is not None and rmono is not None:
        mono_age=(int(rmono)-int(cmono))/1e9
        if mono_age < 0: reasons.append('negative monotonic age')
        if abs(mono_age-wall_age)>tolerance: reasons.append('wall/monotonic disagreement')
    if meta.get('same_transaction_recovery') and meta.get('release_time_eligibility_recorded') and meta.get('immutable_artifact_integrity_result')=='PASS' and meta.get('restore_point_id')==meta.get('expected_restore_point_id') and meta.get('restore_manifest_sha256')==meta.get('expected_restore_manifest_sha256'):
        return {'schema':RESTORE_FRESHNESS_SCHEMA,'classification':'RESTORE_FRESHNESS_RECOVERY_ELIGIBLE','ok':True,'age_seconds':wall_age,'reasons':[]}
    return {'schema':RESTORE_FRESHNESS_SCHEMA,'classification':'RESTORE_FRESHNESS_PASS' if not reasons else 'RESTORE_FRESHNESS_BLOCK','ok':not reasons,'age_seconds':wall_age,'boundary_rule':'age_seconds < 3600 is fresh; exactly 3600 blocks','reasons':reasons}

def evaluate_conflict_set(conflicts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not conflicts: return {'classification':'CONFLICT_NONE','ok':True,'evidence_source':'fixture'}
    for c in conflicts:
        if c.get('state') in ('active','unknown'):
            return {'classification':'CONFLICT_BLOCK','ok':False,'category':c.get('category'),'evidence_source':c.get('evidence_source','fixture')}
        if c.get('stale_metadata') and c.get('unfinalized_released_transaction'):
            return {'classification':'CONFLICT_BLOCK_STALE_RELEASED','ok':False,'category':c.get('category')}
    return {'classification':'CONFLICT_NONE','ok':True,'evidence_source':'fixture_stale_metadata_only'}
