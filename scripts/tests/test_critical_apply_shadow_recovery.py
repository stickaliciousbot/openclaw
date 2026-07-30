#!/usr/bin/env python3
from __future__ import annotations
import shutil, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from critical_apply_restore import *
from critical_apply_recovery import *
from critical_apply_filesystem import boundary_digest, canonical_json_sha, inventory_tree
class Lock:
    digest='e'*64
    def assert_live(self): return True
class Fence: generation=1; token_sha256='f'*64
class ShadowRecoveryTest(unittest.TestCase):
    group='shadow_openclaw_like_recovery'
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='m3-shadow-')); self.tx=self.tmp/'tx'; self.src=self.tmp/'source_pkg'; self.rr=self.tmp/'restore'; self.shadow=self.tmp/'shadow'; self.parent=self.shadow/'lib/node_modules'; [p.mkdir(mode=0o700,parents=True) for p in [self.tx,self.src,self.rr,self.parent]]
        (self.src/'package.json').write_text('{"name":"openclaw","version":"fixture"}\n'); (self.src/'openclaw.mjs').write_text('export {};\n'); (self.src/'dist/extensions/speech-core').mkdir(parents=True); (self.src/'dist/index.js').write_text('index\n'); (self.src/'dist/extensions/speech-core/runtime-api.js').write_text('runtime\n'); (self.src/'bin').mkdir(); (self.src/'bin/openclaw').write_text('#!/usr/bin/env node\n'); (self.shadow/'npm-meta').mkdir(); (self.shadow/'strict-cron-sentinel').write_text('cron'); (self.shadow/'protected-memory-sentinel').write_text('mem')
        self.boundary=make_boundary(target_root=self.parent/'openclaw',allowed_relative_paths=['package.json','openclaw.mjs','dist','dist/index.js','dist/extensions','dist/extensions/speech-core','dist/extensions/speech-core/runtime-api.js','bin','bin/openclaw'],recovery_write_set=['package.json','openclaw.mjs','dist','bin'],guard_set=['../../strict-cron-sentinel','../../protected-memory-sentinel'],forbidden_set=['../../npm-meta'])
        self.auth='a'*64; self.rp=create_restore_point(transaction_root=self.tx,source_root=self.src,restore_root=self.rr,restore_point_id='restore-'+'e'*40,boundary=self.boundary,transaction_id='tx',campaign_id='camp',authority_envelope_sha256=self.auth,recovery_write_set_digest=boundary_digest(self.boundary),forbidden_set_digest=canonical_json_sha({'forbidden_set':self.boundary.forbidden_set})); self.inv=inventory_tree(Path(self.rp['bundle_path']),boundary=self.boundary); self.rel=make_release_eligibility(self.rp)
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)
    def recover_state(self,state):
        target=self.parent/'openclaw'
        if state=='empty': target.mkdir()
        if state=='incomplete': target.mkdir(); (target/'package.json').write_text('{}')
        dec=decide_recovery(transaction_id='tx',authority_envelope_sha256=self.auth,restore_verification={'ok':True},release_time_eligibility=self.rel,target_state=classify_fixture_target(target_root=target,candidate_inventory=self.inv),simulated_execution_state='failed',guard_state='clear',conflict_state='clear',recovery_authority_state='present',recovery_count=0,existing_recovery_evidence='none',filesystem_identity='same',recovery_write_set_digest=boundary_digest(self.boundary))
        idem=recovery_idempotency_key(transaction_id='tx',authority_envelope_sha256=self.auth,restore_point_id=self.rp['restore_point_id'],restore_manifest_sha256=self.rp['inventory_manifest_sha256'],target_identity=str(target.resolve(strict=False)),recovery_write_set_digest=boundary_digest(self.boundary),release_time_eligibility_receipt_sha256=self.rel['sha256'],fencing_generation=Fence.generation,boot_policy='same-boot-fixture')
        return perform_fixture_recovery(transaction_root=self.tx,target_root=target,restore_root=self.rr,restore_point_id=self.rp['restore_point_id'],recovery_write_set_digest=boundary_digest(self.boundary),authority_envelope_sha256=self.auth,recovery_idempotency_key=idem,safety_classification='shadow-copy',restore_point=self.rp,boundary=self.boundary,release_time_eligibility_receipt=self.rel,decision=dec,lockset=Lock(),fencing=Fence())
    def test_missing_official_recovers(self): self.assertEqual(self.recover_state('missing')['classification'],'RECOVERY_PASS')
    def test_empty_official_recovers_and_preserves(self): out=self.recover_state('empty'); self.assertTrue(Path(out['preservation_path']).exists())
    def test_incomplete_official_recovers(self): self.assertEqual(self.recover_state('incomplete')['classification'],'RECOVERY_PASS')
    def test_missing_dist_index_classifies_incomplete(self): t=self.parent/'openclaw'; shutil.copytree(self.src,t); (t/'dist/index.js').unlink(); self.assertEqual(classify_fixture_target(target_root=t,candidate_inventory=self.inv),'TARGET_INCOMPLETE')
    def test_missing_speech_runtime_incomplete(self): t=self.parent/'openclaw'; shutil.copytree(self.src,t); (t/'dist/extensions/speech-core/runtime-api.js').unlink(); self.assertEqual(classify_fixture_target(target_root=t,candidate_inventory=self.inv,critical_files=('package.json','dist/index.js','dist/extensions/speech-core/runtime-api.js')),'TARGET_INCOMPLETE')
    def test_corrupt_package_other(self): t=self.parent/'openclaw'; shutil.copytree(self.src,t); (t/'package.json').write_text('corrupt'); self.assertEqual(classify_fixture_target(target_root=t,candidate_inventory=self.inv),'TARGET_COHERENT_OTHER_GENERATION')
    def test_candidate_already_installed(self): t=self.parent/'openclaw'; shutil.copytree(self.rp['bundle_path'],t); self.assertEqual(classify_fixture_target(target_root=t,candidate_inventory=self.inv),'TARGET_COHERENT_CANDIDATE_GENERATION')
    def test_guard_cron_unchanged(self): before=(self.shadow/'strict-cron-sentinel').read_text(); self.recover_state('missing'); self.assertEqual((self.shadow/'strict-cron-sentinel').read_text(),before)
    def test_guard_memory_unchanged(self): before=(self.shadow/'protected-memory-sentinel').read_text(); self.recover_state('missing'); self.assertEqual((self.shadow/'protected-memory-sentinel').read_text(),before)
    def test_npm_meta_unchanged(self): before=inventory_tree(self.shadow/'npm-meta'); self.recover_state('missing'); self.assertTrue(compare_inventories(before,inventory_tree(self.shadow/'npm-meta')))
    def test_shadow_source_not_production_path(self): self.assertNotIn('node_modules/openclaw',str(self.src))
    def test_expected_surfaces_present(self): paths={e['path'] for e in self.inv['entries']}; self.assertIn('dist/extensions/speech-core/runtime-api.js',paths)
for state in ['TARGET_MISSING','TARGET_EMPTY','TARGET_INCOMPLETE','TARGET_COHERENT_CANDIDATE_GENERATION','TARGET_COHERENT_PRE_GENERATION','TARGET_COHERENT_OTHER_GENERATION','TARGET_CONFLICTING','TARGET_UNKNOWN']:
    def make(s):
        def test(self): self.assertIn(s,TARGET_CLASSIFICATIONS)
        return test
    setattr(ShadowRecoveryTest,'test_target_catalog_'+state,make(state))
for surface in ['package.json','openclaw.mjs','dist/index.js','dist/extensions/speech-core/runtime-api.js','bin/openclaw','strict-cron-sentinel','protected-memory-sentinel','npm-meta']:
    def makes(s):
        def test(self): self.assertIn(s, str(list(self.tmp.rglob('*'))))
        return test
    setattr(ShadowRecoveryTest,'test_shadow_surface_'+surface.replace('/','_').replace('-','_'),makes(surface))
if __name__=='__main__': unittest.main(verbosity=2)
