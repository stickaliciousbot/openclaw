#!/usr/bin/env python3
"""Verified fixture restore points for Critical Apply M3."""
from __future__ import annotations

import hashlib, os, secrets, shutil, stat, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, read_json_artifact
from critical_apply_contracts import canonical_json_dumps, is_sha256
from critical_apply_filesystem import (
    Boundary, FilesystemSafetyError, canonical_json_sha, inventory_tree, compare_inventories,
    stable_file_copy, real_dir, resolve_under, utc_now, read_boot_id, boundary_digest,
    PATH_SAFETY_POLICY_SHA256, OWNERSHIP_MODE_POLICY_SHA256, FILESYSTEM_POLICY_SHA256,
)

RESTORE_POINT_SCHEMA='critical_apply.restore_point.v2'
RESTORE_BOUNDARY_SCHEMA='critical_apply.restore_boundary.v2'
RESTORE_VERIFICATION_SCHEMA='critical_apply.restore_point_verification.v2'
RESTORE_CLASSIFICATIONS={
 'RESTORE_POINT_VERIFIED','RESTORE_POINT_MISSING','RESTORE_POINT_SCHEMA_INVALID','RESTORE_POINT_ID_MISMATCH','RESTORE_POINT_AUTHORITY_MISMATCH','RESTORE_POINT_BUNDLE_MISSING','RESTORE_POINT_BUNDLE_HASH_MISMATCH','RESTORE_POINT_MANIFEST_MISMATCH','RESTORE_POINT_PATH_UNSAFE','RESTORE_POINT_SOURCE_UNSTABLE','RESTORE_POINT_BOUNDARY_INVALID','RESTORE_POINT_FILETYPE_UNSAFE','RESTORE_POINT_SYMLINK_UNSAFE','RESTORE_POINT_HARDLINK_UNSAFE','RESTORE_POINT_FILESYSTEM_POLICY_MISMATCH','RESTORE_POINT_UNKNOWN'}

@dataclass(frozen=True)
class RestoreVerification:
    schema: str
    classification: str
    ok: bool
    restore_point_id: str | None = None
    reasons: tuple[str,...] = ()
    details: Mapping[str,Any] | None = None
    def to_json(self): return asdict(self)

def restore_point_id(transaction_id: str) -> str:
    return 'restore-'+hashlib.sha256((transaction_id+'|'+secrets.token_hex(16)).encode()).hexdigest()[:40]

def make_boundary(*, target_root: Path, allowed_relative_paths: Sequence[str], recovery_write_set: Sequence[str], guard_set: Sequence[str]=(), forbidden_set: Sequence[str]=(), **limits: Any) -> Boundary:
    if any(str(p) in ('.','*','**','/') for p in recovery_write_set):
        raise FilesystemSafetyError('BROAD_WILDCARD_RECOVERY_AUTHORITY_REJECTED')
    return Boundary(RESTORE_BOUNDARY_SCHEMA, str(Path(target_root).resolve(strict=False)), tuple(sorted(allowed_relative_paths)), tuple(sorted(recovery_write_set)), tuple(sorted(guard_set)), tuple(sorted(forbidden_set)), **limits)

def _copy_tree_stable(source_root: Path, bundle_tree: Path, *, boundary: Boundary, failed_attempts: list[Mapping[str,Any]]) -> Mapping[str,Any]:
    source=real_dir(source_root,label='SOURCE_ROOT')
    pre=inventory_tree(source,boundary=boundary)
    bundle_tree.mkdir(mode=0o700,parents=True,exist_ok=False)
    copied=[]
    for ent in pre['entries']:
        rel=ent['path']
        if ent['type']=='directory':
            (bundle_tree/rel).mkdir(mode=int(str(ent['mode']),8),parents=True,exist_ok=True)
        elif ent['type']=='regular':
            copied.append(stable_file_copy(source/rel,bundle_tree/rel,root=source))
        else:
            raise FilesystemSafetyError('RESTORE_POINT_FILETYPE_UNSAFE')
    post=inventory_tree(source,boundary=boundary)
    if not compare_inventories(pre,post):
        failed_attempts.append({'classification':'RESTORE_POINT_SOURCE_UNSTABLE','pre_sha':pre['inventory_sha256'],'post_sha':post['inventory_sha256']})
        raise FilesystemSafetyError('RESTORE_POINT_SOURCE_UNSTABLE')
    bundle_inv=inventory_tree(bundle_tree,boundary=boundary)
    if not compare_inventories(pre,bundle_inv): raise FilesystemSafetyError('RESTORE_POINT_MANIFEST_MISMATCH')
    return {'source_inventory':pre,'bundle_inventory':bundle_inv,'copied_files':copied}

def create_restore_point(*, transaction_root: Path, source_root: Path, restore_root: Path, restore_point_id: str, boundary: Boundary, transaction_id: str, campaign_id: str, authority_envelope_sha256: str, recovery_write_set_digest: str, forbidden_set_digest: str, source_classification: str='fixture', max_age_seconds: int=3600, retry_count: int=0) -> Mapping[str,Any]:
    if not is_sha256(authority_envelope_sha256) or not is_sha256(recovery_write_set_digest) or not is_sha256(forbidden_set_digest): raise ValueError('AUTHORITY_OR_SET_DIGEST_INVALID')
    txroot=real_dir(transaction_root,label='TRANSACTION_ROOT'); restore=real_dir(restore_root,label='RESTORE_ROOT'); source=real_dir(source_root,label='SOURCE_ROOT')
    if source_classification not in ('fixture','shadow-copy'): raise ValueError('SOURCE_CLASSIFICATION_UNSAFE')
    start_wall=utc_now(); start_mono=time.monotonic_ns(); failed=[]
    rp_dir=restore/restore_point_id; rp_dir.mkdir(mode=0o700,exist_ok=False)
    bundle_tree=rp_dir/'bundle-tree'; manifest_path=rp_dir/'inventory-manifest.json'; receipt_path=rp_dir/'restore-point.json'
    attempt=0
    while True:
        try:
            cap=_copy_tree_stable(source,bundle_tree,boundary=boundary,failed_attempts=failed); break
        except Exception:
            if bundle_tree.exists(): shutil.rmtree(bundle_tree)
            attempt += 1
            if attempt > retry_count: raise
    inv=cap['bundle_inventory']
    atomic_create_json(manifest_path, inv, root=txroot if str(manifest_path).startswith(str(txroot)) else restore)
    manifest_sha=hashlib.sha256((canonical_json_dumps(inv)+'\n').encode()).hexdigest()
    source_st=os.lstat(source); bundle_sha=canonical_json_sha({'bundle_inventory_sha256':inv['inventory_sha256'],'entries':inv['entries']})
    rp={'schema':RESTORE_POINT_SCHEMA,'restore_point_id':restore_point_id,'transaction_id':transaction_id,'campaign_id':campaign_id,'source_classification':source_classification,'source_root_canonical_path':str(source),'source_root_device':source_st.st_dev,'source_root_inode':source_st.st_ino,'source_filesystem_identity':str(source_st.st_dev),'source_capture_start_wall_time':start_wall,'source_capture_end_wall_time':utc_now(),'source_capture_start_monotonic_ns':start_mono,'source_capture_end_monotonic_ns':time.monotonic_ns(),'boot_id':read_boot_id(),'creator_actor_identity':{'component':'critical_apply_restore_m3','pid':os.getpid(),'uid':os.getuid()},'authority_envelope_sha256':authority_envelope_sha256,'restore_boundary':boundary.to_json(),'restore_boundary_sha256':boundary_digest(boundary),'recovery_write_set_digest':recovery_write_set_digest,'forbidden_set_digest':forbidden_set_digest,'capture_policy_sha256':hashlib.sha256(b'critical-apply-m3-stable-capture-v1').hexdigest(),'path_safety_policy_sha256':PATH_SAFETY_POLICY_SHA256,'ownership_and_mode_policy_sha256':OWNERSHIP_MODE_POLICY_SHA256,'bundle_format':'verified-directory-tree-v1','bundle_path':str(bundle_tree),'bundle_sha256':bundle_sha,'bundle_byte_count':inv['total_logical_bytes'],'inventory_manifest_path':str(manifest_path),'inventory_manifest_sha256':manifest_sha,'file_count':inv['file_count'],'directory_count':inv['directory_count'],'symlink_count':inv['symlink_count'],'total_logical_bytes':inv['total_logical_bytes'],'executable_link_fixture_authority':'fixture-only-if-present','metadata_fixture_authority':'fixture-only-if-present','source_stability_result':'STABLE_SOURCE_VERIFIED','failed_capture_attempts':failed,'created_wall_time':utc_now(),'created_monotonic_ns':time.monotonic_ns(),'maximum_release_time_age_seconds':max_age_seconds,'immutable':True}
    atomic_create_json(receipt_path,rp,root=restore)
    return rp

def verify_restore_point(*, transaction_root: Path, restore_point_path: Path, expected_restore_point_id: str, authority_envelope_sha256: str | None = None, boundary: Boundary | None = None) -> RestoreVerification:
    try:
        p=Path(restore_point_path)
        if not p.exists(): return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_MISSING',False)
        root=p.parent.parent if p.name=='restore-point.json' else p.parent
        rp=read_json_artifact(p, root=root)
        if rp.get('schema')!=RESTORE_POINT_SCHEMA: return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_SCHEMA_INVALID',False)
        if rp.get('restore_point_id')!=expected_restore_point_id: return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_ID_MISMATCH',False)
        if authority_envelope_sha256 and rp.get('authority_envelope_sha256')!=authority_envelope_sha256: return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_AUTHORITY_MISMATCH',False)
        if boundary and rp.get('restore_boundary_sha256')!=boundary_digest(boundary): return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_BOUNDARY_INVALID',False)
        bundle=Path(str(rp.get('bundle_path',''))); manifest=Path(str(rp.get('inventory_manifest_path','')))
        if not bundle.exists(): return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_BUNDLE_MISSING',False)
        inv=read_json_artifact(manifest, root=manifest.parent.parent if manifest.parent.name==rp.get('restore_point_id') else manifest.parent)
        actual=inventory_tree(bundle,boundary=boundary or Boundary(**rp['restore_boundary']))
        if not compare_inventories(inv,actual): return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_MANIFEST_MISMATCH',False)
        msha=hashlib.sha256((canonical_json_dumps(inv)+'\n').encode()).hexdigest()
        if msha!=rp.get('inventory_manifest_sha256'): return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_MANIFEST_MISMATCH',False)
        bsha=canonical_json_sha({'bundle_inventory_sha256':actual['inventory_sha256'],'entries':actual['entries']})
        if bsha!=rp.get('bundle_sha256'): return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_BUNDLE_HASH_MISMATCH',False)
        if rp.get('source_stability_result')!='STABLE_SOURCE_VERIFIED': return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_SOURCE_UNSTABLE',False)
        return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_VERIFIED',True,expected_restore_point_id,details={'file_count':actual['file_count'],'directory_count':actual['directory_count']})
    except FilesystemSafetyError as exc:
        s=str(exc)
        cls='RESTORE_POINT_SYMLINK_UNSAFE' if 'SYMLINK' in s else 'RESTORE_POINT_HARDLINK_UNSAFE' if 'HARDLINK' in s else 'RESTORE_POINT_FILETYPE_UNSAFE' if 'FILETYPE' in s else 'RESTORE_POINT_PATH_UNSAFE' if 'PATH' in s else 'RESTORE_POINT_BOUNDARY_INVALID'
        return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,cls,False,reasons=(s,))
    except Exception as exc:
        return RestoreVerification(RESTORE_VERIFICATION_SCHEMA,'RESTORE_POINT_UNKNOWN',False,reasons=(str(exc),))

def restore_bundle_format_contract() -> Mapping[str,Any]:
    return {'schema':'critical_apply.restore_bundle_format.v2','format':'verified-directory-tree-v1','generic_archive_extraction':False,'path_order_authoritative':False,'all_members_validated_before_publish':True,'staging_required_before_publish':True,'immutable_manifest_required':True}
