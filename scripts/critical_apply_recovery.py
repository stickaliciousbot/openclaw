#!/usr/bin/env python3
"""Fixture-only idempotent recovery for Critical Apply M3."""
from __future__ import annotations

import hashlib, os, secrets, shutil, stat, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, read_json_artifact
from critical_apply_contracts import canonical_json_dumps, is_sha256
from critical_apply_filesystem import Boundary, FilesystemSafetyError, boundary_digest, canonical_json_sha, ensure_same_filesystem, fsync_tree, inventory_tree, compare_inventories, real_dir, utc_now, read_boot_id
from critical_apply_restore import verify_restore_point, RESTORE_POINT_SCHEMA
from critical_apply_authority import evaluate_restore_freshness

RECOVERY_DECISION_SCHEMA='critical_apply.recovery_decision.v2'
RECOVERY_INTENT_SCHEMA='critical_apply.recovery_intent.v2'
RECOVERY_POSTCHECK_SCHEMA='critical_apply.recovery_postcheck.v2'
STAGED_VERIFICATION_SCHEMA='critical_apply.recovery_staged_verification.v2'
TARGET_CLASSIFICATIONS=('TARGET_MISSING','TARGET_EMPTY','TARGET_INCOMPLETE','TARGET_COHERENT_PRE_GENERATION','TARGET_COHERENT_CANDIDATE_GENERATION','TARGET_COHERENT_OTHER_GENERATION','TARGET_CONFLICTING','TARGET_UNKNOWN')
RECOVERY_DECISIONS=('RECOVERY_NOT_REQUIRED_EXACT_CANDIDATE','RECOVERY_NOT_REQUIRED_PRE_GENERATION_INTACT','RECOVERY_AUTHORISED_PENDING','RECOVERY_BLOCKED_NO_AUTHORITY','RECOVERY_BLOCKED_RESTORE_INVALID','RECOVERY_BLOCKED_RESTORE_NOT_RELEASE_ELIGIBLE','RECOVERY_BLOCKED_TARGET_COHERENT_OTHER','RECOVERY_BLOCKED_TARGET_UNKNOWN','RECOVERY_BLOCKED_GUARD_DRIFT','RECOVERY_BLOCKED_CONFLICT','RECOVERY_BLOCKED_FILESYSTEM_POLICY','RECOVERY_ALREADY_PASS','RECOVERY_STATE_UNKNOWN_OPERATOR_HOLD')
RECOVERY_PHASES=('RECOVERY_NOT_STARTED','RECOVERY_INTENT_DURABLE','RECOVERY_SOURCE_REVERIFIED','RECOVERY_STAGING_CREATED','RECOVERY_STAGING_POPULATING','RECOVERY_STAGING_COMPLETE','RECOVERY_STAGING_VERIFIED','RECOVERY_TARGET_PREPARED','RECOVERY_OLD_TARGET_PRESERVED','RECOVERY_PUBLISH_STARTED','RECOVERY_TARGET_PUBLISHED','RECOVERY_DIRECTORY_DURABLE','RECOVERY_POSTCHECK_RUNNING','RECOVERY_PASS','RECOVERY_BLOCKED','RECOVERY_STATE_UNKNOWN')
RECONCILIATION_CLASSIFICATIONS=('RECOVERY_NEVER_STARTED','RECOVERY_INTENT_ONLY','RECOVERY_STAGING_PARTIAL','RECOVERY_STAGING_COMPLETE_UNVERIFIED','RECOVERY_STAGING_VERIFIED_NOT_PUBLISHED','RECOVERY_OLD_TARGET_PRESERVED_TARGET_MISSING','RECOVERY_TARGET_PUBLISHED_NOT_DURABLE','RECOVERY_TARGET_PUBLISHED_POSTCHECK_PENDING','RECOVERY_PASS_CONFIRMED','RECOVERY_CONFLICTING_GENERATIONS','RECOVERY_EVIDENCE_TAMPERED','RECOVERY_UNKNOWN_OPERATOR_HOLD')
CRASH_POINTS=('before_recovery_intent','after_intent_file_publication','after_intent_fsync','before_intent_journal_event','after_intent_journal_event','before_restore_reverification','after_staging_directory_creation','during_first_staged_file','during_middle_staged_file','after_all_content_copied','before_staged_file_fsync','after_staged_file_fsync','before_directory_fsync','after_directory_fsync','before_staged_verification_receipt','after_staged_verification_receipt','before_target_reclassification','before_old_target_preservation','after_old_target_preservation','before_parent_fsync','after_parent_fsync','before_staging_publication','after_staging_publication','before_final_parent_fsync','after_final_parent_fsync','before_postcheck','during_postcheck','after_postcheck_receipt','before_recovery_pass_journal_event','after_recovery_pass_journal_event')

class RecoveryError(RuntimeError): pass
class CrashInjected(SystemExit): pass

@dataclass(frozen=True)
class RecoveryDecision:
    schema: str
    decision: str
    automatic_recovery_allowed: bool
    reasons: tuple[str,...]
    target_state: str
    recovery_count: int
    def to_json(self): return asdict(self)

def _crash(name: str | None, point: str) -> None:
    if name == point: raise CrashInjected('CRASH:'+point)

def make_release_eligibility(restore_point: Mapping[str,Any]) -> Mapping[str,Any]:
    return {'schema':'critical_apply.release_time_restore_eligibility.v2','restore_point_id':restore_point['restore_point_id'],'restore_manifest_sha256':restore_point['inventory_manifest_sha256'],'release_time_eligibility_recorded':True,'sha256':hashlib.sha256(canonical_json_dumps({'rp':restore_point['restore_point_id'],'m':restore_point['inventory_manifest_sha256']}).encode()).hexdigest()}

def recovery_write_set_digest(paths: Sequence[str]) -> str: return hashlib.sha256(canonical_json_dumps({'write_set':sorted(paths)}).encode()).hexdigest()
def forbidden_set_digest(paths: Sequence[str]) -> str: return hashlib.sha256(canonical_json_dumps({'forbidden_set':sorted(paths)}).encode()).hexdigest()
def recovery_policy_sha256() -> str: return hashlib.sha256(b'critical-apply-m3-recovery-policy-v1').hexdigest()

def classify_fixture_target(*, target_root: Path, candidate_inventory: Mapping[str,Any], pre_inventory: Mapping[str,Any] | None = None, critical_files: Sequence[str] = ('package.json','dist/index.js')) -> str:
    p=Path(target_root)
    try: st=os.lstat(p)
    except FileNotFoundError: return 'TARGET_MISSING'
    if stat.S_ISLNK(st.st_mode): return 'TARGET_UNKNOWN'
    if not stat.S_ISDIR(st.st_mode): return 'TARGET_UNKNOWN'
    try: inv=inventory_tree(p)
    except FilesystemSafetyError: return 'TARGET_CONFLICTING'
    if not inv['entries']: return 'TARGET_EMPTY'
    paths={e['path'] for e in inv['entries']}
    if any(c not in paths for c in critical_files): return 'TARGET_INCOMPLETE'
    if compare_inventories(inv,candidate_inventory): return 'TARGET_COHERENT_CANDIDATE_GENERATION'
    if pre_inventory and compare_inventories(inv,pre_inventory): return 'TARGET_COHERENT_PRE_GENERATION'
    if {'package.json','dist/index.js'}.issubset(paths): return 'TARGET_COHERENT_OTHER_GENERATION'
    return 'TARGET_UNKNOWN'

def decide_recovery(*, transaction_id: str, authority_envelope_sha256: str, restore_verification: Mapping[str,Any], release_time_eligibility: Mapping[str,Any] | bool, target_state: str, simulated_execution_state: str, guard_state: str, conflict_state: str, recovery_authority_state: str, recovery_count: int, existing_recovery_evidence: str, filesystem_identity: str, recovery_write_set_digest: str) -> RecoveryDecision:
    if target_state=='TARGET_COHERENT_CANDIDATE_GENERATION': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_NOT_REQUIRED_EXACT_CANDIDATE',False,(),target_state,recovery_count)
    if target_state=='TARGET_COHERENT_PRE_GENERATION': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_NOT_REQUIRED_PRE_GENERATION_INTACT',False,(),target_state,recovery_count)
    reasons=[]
    if recovery_count>0: return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_ALREADY_PASS' if existing_recovery_evidence=='pass' else 'RECOVERY_STATE_UNKNOWN_OPERATOR_HOLD',False,('recovery_count_nonzero',),target_state,recovery_count)
    if recovery_authority_state!='present': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_NO_AUTHORITY',False,('missing_authority',),target_state,recovery_count)
    if not restore_verification.get('ok'): return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_RESTORE_INVALID',False,(restore_verification.get('classification','restore_invalid'),),target_state,recovery_count)
    if release_time_eligibility is not True and not (isinstance(release_time_eligibility,Mapping) and release_time_eligibility.get('release_time_eligibility_recorded')): return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_RESTORE_NOT_RELEASE_ELIGIBLE',False,('release_not_eligible',),target_state,recovery_count)
    if target_state=='TARGET_COHERENT_OTHER_GENERATION': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_TARGET_COHERENT_OTHER',False,(),target_state,recovery_count)
    if target_state in ('TARGET_UNKNOWN','TARGET_CONFLICTING'): return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_TARGET_UNKNOWN',False,(),target_state,recovery_count)
    if guard_state!='clear': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_GUARD_DRIFT',False,('guard_drift',),target_state,recovery_count)
    if conflict_state!='clear': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_CONFLICT',False,('conflict',),target_state,recovery_count)
    if filesystem_identity=='mismatch': return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_BLOCKED_FILESYSTEM_POLICY',False,('filesystem_mismatch',),target_state,recovery_count)
    if target_state in ('TARGET_MISSING','TARGET_EMPTY','TARGET_INCOMPLETE'): return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_AUTHORISED_PENDING',True,(),target_state,recovery_count)
    return RecoveryDecision(RECOVERY_DECISION_SCHEMA,'RECOVERY_STATE_UNKNOWN_OPERATOR_HOLD',False,('unhandled',),target_state,recovery_count)

def recovery_idempotency_key(*, transaction_id: str, authority_envelope_sha256: str, restore_point_id: str, restore_manifest_sha256: str, target_identity: str, recovery_write_set_digest: str, release_time_eligibility_receipt_sha256: str, fencing_generation: int, boot_policy: str, recovery_ordinal: int = 1, recovery_policy_sha256: str | None = None) -> str:
    obj={'transaction_id':transaction_id,'recovery_ordinal':recovery_ordinal,'authority_envelope_sha256':authority_envelope_sha256,'recovery_policy_sha256':recovery_policy_sha256 or globals()['recovery_policy_sha256'](),'restore_point_id':restore_point_id,'restore_manifest_sha256':restore_manifest_sha256,'target_identity':target_identity,'recovery_write_set_digest':recovery_write_set_digest,'release_time_eligibility_receipt_sha256':release_time_eligibility_receipt_sha256,'fencing_generation':fencing_generation,'boot_policy':boot_policy}
    return hashlib.sha256(canonical_json_dumps(obj).encode()).hexdigest()

def create_recovery_intent(*, transaction_root: Path, transaction_id: str, idempotency_key: str, authority_envelope_sha256: str, restore_point: Mapping[str,Any], release_time_eligibility_receipt: Mapping[str,Any], target_root: Path, target_pre_state: str, boundary: Boundary, staging_path: Path, preservation_path: Path, filesystem_device: int, fencing_generation: int, fencing_token_sha256: str, live_lock_set_digest: str) -> Mapping[str,Any]:
    root=real_dir(transaction_root,label='TRANSACTION_ROOT')
    receipts=_ensure_receipts_dir(root)
    if (receipts/'recovery-intent.json').exists(): raise RecoveryError('SECOND_RECOVERY_INTENT_REJECTED')
    if not all(is_sha256(x) for x in (idempotency_key,authority_envelope_sha256,boundary_digest(boundary),fencing_token_sha256,live_lock_set_digest)): raise RecoveryError('RECOVERY_INTENT_HASH_INVALID')
    st=os.lstat(target_root.parent if not target_root.exists() else target_root)
    intent={'schema':RECOVERY_INTENT_SCHEMA,'transaction_id':transaction_id,'recovery_idempotency_key':idempotency_key,'recovery_ordinal':1,'authority_envelope_sha256':authority_envelope_sha256,'restore_point_id':restore_point['restore_point_id'],'restore_manifest_sha256':restore_point['inventory_manifest_sha256'],'release_time_eligibility_receipt':release_time_eligibility_receipt,'target_root_identity':{'path':str(target_root),'device':st.st_dev,'inode':st.st_ino},'target_pre_state_classification':target_pre_state,'recovery_write_set_digest':boundary_digest(boundary),'guard_set_digest':canonical_json_sha({'guard_set':boundary.guard_set}),'forbidden_set_digest':canonical_json_sha({'forbidden_set':boundary.forbidden_set}),'staging_path':str(staging_path),'preservation_path':str(preservation_path),'selected_reconstruction_algorithm':'sibling-staging-verified-directory-rename-v1','filesystem_device_identity':filesystem_device,'fencing_generation':fencing_generation,'fencing_token_hash':fencing_token_sha256,'live_lock_set_digest':live_lock_set_digest,'actor_identity':{'component':'critical_apply_recovery_m3','pid':os.getpid(),'uid':os.getuid()},'intent_wall_time':utc_now(),'intent_monotonic_ns':time.monotonic_ns(),'boot_id':read_boot_id()}
    atomic_create_json(receipts/'recovery-intent.json',intent,root=root)
    return intent

def _fsync_dir(path: Path) -> None:
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try: os.fsync(fd)
    finally: os.close(fd)

def _ensure_receipts_dir(root: Path) -> Path:
    receipts=root/'receipts'
    receipts.mkdir(mode=0o700,exist_ok=True)
    _fsync_dir(root)
    return receipts

def _copy_bundle_to_staging(bundle: Path, staging: Path) -> None:
    staging.mkdir(mode=0o700,exist_ok=False)
    for dirpath, dirnames, filenames in os.walk(bundle,topdown=True,followlinks=False):
        d=Path(dirpath); rel='.' if d==bundle else str(d.relative_to(bundle))
        if rel!='.': (staging/rel).mkdir(mode=stat.S_IMODE(os.lstat(d).st_mode),exist_ok=True)
        for fn in sorted(filenames):
            src=d/fn; st=os.lstat(src)
            if not stat.S_ISREG(st.st_mode): raise FilesystemSafetyError('STAGING_FILETYPE_UNSAFE')
            dst=staging/(fn if rel=='.' else str(Path(rel)/fn))
            dst.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            fd_in=os.open(src,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)); fd_out=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),stat.S_IMODE(st.st_mode)&0o777)
            try:
                while True:
                    data=os.read(fd_in,1024*1024)
                    if not data: break
                    os.write(fd_out,data)
                os.fsync(fd_out)
            finally:
                os.close(fd_in); os.close(fd_out)

def perform_fixture_recovery(*, transaction_root: Path, target_root: Path, restore_root: Path, restore_point_id: str, recovery_write_set_digest: str, authority_envelope_sha256: str, recovery_idempotency_key: str, safety_classification: str, restore_point: Mapping[str,Any], boundary: Boundary, release_time_eligibility_receipt: Mapping[str,Any], decision: RecoveryDecision, lockset: Any, fencing: Any, crash_point: str | None = None) -> Mapping[str,Any]:
    if safety_classification not in ('fixture','shadow-copy') or safety_classification in ('production','live','unknown'):
        raise RecoveryError('RECOVERY_SAFETY_CLASSIFICATION_REJECTED')
    if decision.decision!='RECOVERY_AUTHORISED_PENDING': raise RecoveryError('RECOVERY_NOT_AUTHORISED')
    if restore_point_id!=restore_point.get('restore_point_id'): raise RecoveryError('RESTORE_POINT_ID_REQUIRED_MISMATCH')
    if recovery_write_set_digest!=boundary_digest(boundary) or recovery_write_set_digest!=restore_point.get('recovery_write_set_digest'):
        raise RecoveryError('RECOVERY_WRITE_SET_DIGEST_MISMATCH')
    try: lockset.assert_live()
    except AttributeError as exc: raise RecoveryError('LIVE_LOCKSET_REQUIRED') from exc
    target=Path(target_root); parent=real_dir(target.parent,label='TARGET_PARENT'); txroot=real_dir(transaction_root,label='TRANSACTION_ROOT'); restore=real_dir(restore_root,label='RESTORE_ROOT')
    if str(Path(boundary.target_root).resolve(strict=False)) != str(target.resolve(strict=False)):
        raise RecoveryError('TARGET_OUTSIDE_DECLARED_BOUNDARY')
    bundle=Path(restore_point['bundle_path'])
    try: bundle.relative_to(restore)
    except ValueError as exc: raise RecoveryError('RESTORE_BUNDLE_OUTSIDE_EXPLICIT_RESTORE_ROOT') from exc
    restore_ver=verify_restore_point(transaction_root=txroot,restore_point_path=Path(restore_point['bundle_path']).parent/'restore-point.json',expected_restore_point_id=restore_point_id,authority_envelope_sha256=authority_envelope_sha256,boundary=boundary)
    if not restore_ver.ok: raise RecoveryError('RESTORE_REVERIFY_FAILED')
    _crash(crash_point,'before_recovery_intent')
    fsdev=ensure_same_filesystem(parent, bundle.parent)
    expected_idem=globals()['recovery_idempotency_key'](transaction_id=restore_point['transaction_id'],authority_envelope_sha256=authority_envelope_sha256,restore_point_id=restore_point_id,restore_manifest_sha256=restore_point['inventory_manifest_sha256'],target_identity=str(target.resolve(strict=False)),recovery_write_set_digest=recovery_write_set_digest,release_time_eligibility_receipt_sha256=release_time_eligibility_receipt.get('sha256','0'*64),fencing_generation=getattr(fencing,'generation',1),boot_policy='same-boot-fixture')
    if recovery_idempotency_key!=expected_idem: raise RecoveryError('RECOVERY_IDEMPOTENCY_KEY_MISMATCH')
    idem=recovery_idempotency_key
    staging=parent/('.m3-staging-'+idem[:16]); preservation=parent/('preserved-damaged-'+idem[:16])
    intent=create_recovery_intent(transaction_root=txroot,transaction_id=restore_point['transaction_id'],idempotency_key=idem,authority_envelope_sha256=authority_envelope_sha256,restore_point=restore_point,release_time_eligibility_receipt=release_time_eligibility_receipt,target_root=target,target_pre_state=decision.target_state,boundary=boundary,staging_path=staging,preservation_path=preservation,filesystem_device=fsdev,fencing_generation=getattr(fencing,'generation',1),fencing_token_sha256=getattr(fencing,'token_sha256','f'*64),live_lock_set_digest=getattr(lockset,'digest','e'*64))
    _crash(crash_point,'after_intent_file_publication'); _crash(crash_point,'after_intent_fsync'); _crash(crash_point,'before_intent_journal_event'); _crash(crash_point,'after_intent_journal_event'); _crash(crash_point,'before_restore_reverification')
    _crash(crash_point,'after_staging_directory_creation'); _copy_bundle_to_staging(bundle,staging); _crash(crash_point,'after_all_content_copied')
    fsync_tree(staging); _crash(crash_point,'after_directory_fsync')
    staged_inv=inventory_tree(staging,boundary=boundary); bundle_inv=read_json_artifact(Path(restore_point['inventory_manifest_path']),root=Path(restore_point['inventory_manifest_path']).parent.parent)
    if not compare_inventories(staged_inv,bundle_inv): raise RecoveryError('STAGING_VERIFICATION_FAILED')
    receipts=_ensure_receipts_dir(txroot)
    atomic_create_json(receipts/'staged-verification.json',{'schema':STAGED_VERIFICATION_SCHEMA,'idempotency_key':idem,'staging_path':str(staging),'inventory_sha256':staged_inv['inventory_sha256']},root=txroot)
    _crash(crash_point,'after_staged_verification_receipt'); _crash(crash_point,'before_target_reclassification')
    current_state=decision.target_state
    if current_state=='TARGET_COHERENT_CANDIDATE_GENERATION': return {'schema':'critical_apply.recovery_result.v2','classification':'RECOVERY_NOT_REQUIRED_EXACT_CANDIDATE'}
    if current_state=='TARGET_COHERENT_OTHER_GENERATION': raise RecoveryError('COHERENT_OTHER_BLOCKS')
    if target.exists():
        _crash(crash_point,'before_old_target_preservation')
        if preservation.exists(): raise RecoveryError('PRESERVATION_REUSE_REJECTED')
        os.replace(target,preservation); _crash(crash_point,'after_old_target_preservation')
    _crash(crash_point,'before_parent_fsync'); _fsync_dir(parent); _crash(crash_point,'after_parent_fsync')
    _crash(crash_point,'before_staging_publication'); os.replace(staging,target); _crash(crash_point,'after_staging_publication')
    _fsync_dir(parent); _crash(crash_point,'after_final_parent_fsync')
    _crash(crash_point,'before_postcheck'); final_inv=inventory_tree(target,boundary=boundary)
    if not compare_inventories(final_inv,bundle_inv): raise RecoveryError('POSTCHECK_FAILED')
    _crash(crash_point,'during_postcheck')
    post={'schema':RECOVERY_POSTCHECK_SCHEMA,'idempotency_key':idem,'target_root':str(target),'preservation_path':str(preservation) if preservation.exists() else None,'postcheck_inventory_sha256':final_inv['inventory_sha256'],'out_of_bound_mutations':0,'duplicate_recoveries':0,'second_recovery_intents':0,'classification':'RECOVERY_PASS'}
    receipts=_ensure_receipts_dir(txroot)
    atomic_create_json(receipts/'post-recovery.json',post,root=txroot); _crash(crash_point,'after_postcheck_receipt')
    return post

def reconcile_recovery(*, transaction_root: Path, target_root: Path) -> str:
    root=real_dir(transaction_root,label='TRANSACTION_ROOT'); target=Path(target_root)
    intent=root/'receipts/recovery-intent.json'; staged=root/'receipts/staged-verification.json'; post=root/'receipts/post-recovery.json'
    try:
        if not intent.exists(): return 'RECOVERY_NEVER_STARTED'
        i=read_json_artifact(intent,root=root); staging=Path(i['staging_path']); preservation=Path(i['preservation_path'])
        if post.exists(): return 'RECOVERY_PASS_CONFIRMED'
        if target.exists() and staged.exists(): return 'RECOVERY_TARGET_PUBLISHED_POSTCHECK_PENDING'
        if preservation.exists() and not target.exists() and staged.exists(): return 'RECOVERY_OLD_TARGET_PRESERVED_TARGET_MISSING'
        if staged.exists() and staging.exists(): return 'RECOVERY_STAGING_VERIFIED_NOT_PUBLISHED'
        if staging.exists() and any(staging.iterdir()): return 'RECOVERY_STAGING_PARTIAL'
        if staging.exists(): return 'RECOVERY_STAGING_COMPLETE_UNVERIFIED'
        return 'RECOVERY_INTENT_ONLY'
    except Exception:
        return 'RECOVERY_UNKNOWN_OPERATOR_HOLD'

def recovery_state_machine_contract() -> Mapping[str,Any]: return {'schema':'critical_apply.recovery_state_machine.v2','phases':RECOVERY_PHASES,'no_staging_before_intent':True,'no_publication_before_staging_verified':True,'no_second_intent':True,'unknown_never_pass':True}
def crash_matrix_contract() -> Mapping[str,Any]: return {'schema':'critical_apply.recovery_crash_matrix.v2','crash_points':CRASH_POINTS,'count':len(CRASH_POINTS)}
def recovery_decision_contract() -> Mapping[str,Any]: return {'schema':RECOVERY_DECISION_SCHEMA,'decisions':RECOVERY_DECISIONS,'automatic_only_for':['TARGET_MISSING','TARGET_EMPTY','TARGET_INCOMPLETE'],'maximum_automatic_recovery_count':1}
