#!/usr/bin/env python3
from __future__ import annotations
import os, shutil, sys, tempfile, unittest, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from critical_apply_restore import *
from critical_apply_filesystem import inventory_tree, boundary_digest, canonical_json_sha

class RestorePointTest(unittest.TestCase):
    group='restore_point_creation_and_verification'
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='m3-restore-')); self.tx=self.tmp/'tx'; self.src=self.tmp/'src'; self.rr=self.tmp/'restore'; self.tx.mkdir(mode=0o700); self.src.mkdir(); self.rr.mkdir(mode=0o700)
        (self.src/'package.json').write_text('{"name":"fixture","version":"1"}\n'); (self.src/'openclaw.mjs').write_text('export {};\n'); (self.src/'dist/extensions/speech-core').mkdir(parents=True); (self.src/'dist/index.js').write_text('console.log(1)\n'); (self.src/'dist/extensions/speech-core/runtime-api.js').write_text('export const runtime=1\n')
        self.boundary=make_boundary(target_root=self.src,allowed_relative_paths=['package.json','openclaw.mjs','dist/index.js','dist/extensions/speech-core/runtime-api.js','dist','dist/extensions','dist/extensions/speech-core'],recovery_write_set=['package.json','openclaw.mjs','dist'],guard_set=['../guard'],forbidden_set=['../forbidden'])
        self.auth='a'*64; self.rws=boundary_digest(self.boundary); self.fbd=canonical_json_sha({'forbidden_set':self.boundary.forbidden_set}); self.rpid='restore-'+'b'*40
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)
    def create(self): return create_restore_point(transaction_root=self.tx,source_root=self.src,restore_root=self.rr,restore_point_id=self.rpid,boundary=self.boundary,transaction_id='tx',campaign_id='camp',authority_envelope_sha256=self.auth,recovery_write_set_digest=self.rws,forbidden_set_digest=self.fbd)
    def test_create_restore_point_schema(self): self.assertEqual(self.create()['schema'],RESTORE_POINT_SCHEMA)
    def test_restore_point_verified(self): rp=self.create(); v=verify_restore_point(transaction_root=self.tx,restore_point_path=Path(rp['bundle_path']).parent/'restore-point.json',expected_restore_point_id=self.rpid,authority_envelope_sha256=self.auth,boundary=self.boundary); self.assertTrue(v.ok)
    def test_manifest_immutable_present(self): rp=self.create(); self.assertTrue(Path(rp['inventory_manifest_path']).exists())
    def test_bundle_tree_present(self): rp=self.create(); self.assertTrue(Path(rp['bundle_path']).is_dir())
    def test_file_count(self): self.assertEqual(self.create()['file_count'],4)
    def test_directory_count(self): self.assertGreaterEqual(self.create()['directory_count'],3)
    def test_symlink_count_zero(self): self.assertEqual(self.create()['symlink_count'],0)
    def test_total_bytes_nonzero(self): self.assertGreater(self.create()['total_logical_bytes'],0)
    def test_bundle_hash_sha(self): self.assertTrue(is_sha256(self.create()['bundle_sha256']))
    def test_inventory_manifest_sha(self): self.assertTrue(is_sha256(self.create()['inventory_manifest_sha256']))
    def test_boundary_hash_bound(self): self.assertEqual(self.create()['restore_boundary_sha256'],boundary_digest(self.boundary))
    def test_authority_bound(self): self.assertEqual(self.create()['authority_envelope_sha256'],self.auth)
    def test_write_set_bound(self): self.assertEqual(self.create()['recovery_write_set_digest'],self.rws)
    def test_forbidden_set_bound(self): self.assertEqual(self.create()['forbidden_set_digest'],self.fbd)
    def test_source_stable(self): self.assertEqual(self.create()['source_stability_result'],'STABLE_SOURCE_VERIFIED')
    def test_immutable_true(self): self.assertTrue(self.create()['immutable'])
    def test_format_contract(self): self.assertEqual(restore_bundle_format_contract()['format'],'verified-directory-tree-v1')
    def test_wrong_id(self): rp=self.create(); self.assertEqual(verify_restore_point(transaction_root=self.tx,restore_point_path=Path(rp['bundle_path']).parent/'restore-point.json',expected_restore_point_id='wrong').classification,'RESTORE_POINT_ID_MISMATCH')
    def test_wrong_authority(self): rp=self.create(); self.assertEqual(verify_restore_point(transaction_root=self.tx,restore_point_path=Path(rp['bundle_path']).parent/'restore-point.json',expected_restore_point_id=self.rpid,authority_envelope_sha256='c'*64).classification,'RESTORE_POINT_AUTHORITY_MISMATCH')
    def test_missing_restore_point(self): self.assertEqual(verify_restore_point(transaction_root=self.tx,restore_point_path=self.rr/'x.json',expected_restore_point_id='x').classification,'RESTORE_POINT_MISSING')
    def test_bundle_missing(self): rp=self.create(); shutil.rmtree(rp['bundle_path']); self.assertEqual(verify_restore_point(transaction_root=self.tx,restore_point_path=Path(rp['bundle_path']).parent/'restore-point.json',expected_restore_point_id=self.rpid).classification,'RESTORE_POINT_BUNDLE_MISSING')
    def test_bundle_hash_mismatch(self): rp=self.create(); (Path(rp['bundle_path'])/'package.json').write_text('changed'); self.assertIn(verify_restore_point(transaction_root=self.tx,restore_point_path=Path(rp['bundle_path']).parent/'restore-point.json',expected_restore_point_id=self.rpid).classification,('RESTORE_POINT_MANIFEST_MISMATCH','RESTORE_POINT_BUNDLE_HASH_MISMATCH'))
    def test_manifest_mismatch(self): rp=self.create(); Path(rp['inventory_manifest_path']).write_text('{"schema":"critical_apply.inventory.v2","entries":[]}\n'); self.assertEqual(verify_restore_point(transaction_root=self.tx,restore_point_path=Path(rp['bundle_path']).parent/'restore-point.json',expected_restore_point_id=self.rpid).classification,'RESTORE_POINT_MANIFEST_MISMATCH')
    def test_duplicate_restore_id_rejected(self): self.create(); self.assertRaises(FileExistsError, self.rr.joinpath(self.rpid).mkdir)
    def test_non_fixture_source_rejected(self): self.assertRaises(ValueError, create_restore_point, transaction_root=self.tx,source_root=self.src,restore_root=self.rr,restore_point_id='r',boundary=self.boundary,transaction_id='tx',campaign_id='c',authority_envelope_sha256=self.auth,recovery_write_set_digest=self.rws,forbidden_set_digest=self.fbd,source_classification='production')
    def test_bad_hash_rejected(self): self.assertRaises(ValueError, create_restore_point, transaction_root=self.tx,source_root=self.src,restore_root=self.rr,restore_point_id='r',boundary=self.boundary,transaction_id='tx',campaign_id='c',authority_envelope_sha256='bad',recovery_write_set_digest=self.rws,forbidden_set_digest=self.fbd)

for field in ['restore_point_id','transaction_id','campaign_id','source_classification','source_root_canonical_path','source_root_device','source_root_inode','source_filesystem_identity','source_capture_start_wall_time','source_capture_end_wall_time','source_capture_start_monotonic_ns','source_capture_end_monotonic_ns','boot_id','creator_actor_identity','authority_envelope_sha256','restore_boundary','restore_boundary_sha256','recovery_write_set_digest','forbidden_set_digest','capture_policy_sha256','path_safety_policy_sha256','ownership_and_mode_policy_sha256','bundle_format','bundle_path','bundle_sha256','bundle_byte_count','inventory_manifest_path','inventory_manifest_sha256','file_count','directory_count','symlink_count','total_logical_bytes','executable_link_fixture_authority','metadata_fixture_authority','source_stability_result','created_wall_time','created_monotonic_ns','maximum_release_time_age_seconds','immutable']:
    def make(f):
        def test(self): self.assertIn(f,self.create())
        return test
    setattr(RestorePointTest,'test_schema_field_'+field,make(field))

if __name__=='__main__': unittest.main(verbosity=2)
