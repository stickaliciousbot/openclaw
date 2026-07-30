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
def env(t):
    t.tmp=Path(tempfile.mkdtemp(prefix='m3-crash-')); t.tx=t.tmp/'tx'; t.src=t.tmp/'src'; t.rr=t.tmp/'restore'; t.parent=t.tmp/'parent'; [p.mkdir(mode=0o700,parents=True) for p in [t.tx,t.src,t.rr,t.parent]]
    (t.src/'package.json').write_text('{}'); (t.src/'dist').mkdir(); (t.src/'dist/index.js').write_text('ok')
    t.boundary=make_boundary(target_root=t.parent/'official',allowed_relative_paths=['package.json','dist','dist/index.js'],recovery_write_set=['package.json','dist']); t.auth='a'*64
    t.rp=create_restore_point(transaction_root=t.tx,source_root=t.src,restore_root=t.rr,restore_point_id='restore-'+'c'*40,boundary=t.boundary,transaction_id='tx',campaign_id='camp',authority_envelope_sha256=t.auth,recovery_write_set_digest=boundary_digest(t.boundary),forbidden_set_digest=canonical_json_sha({'forbidden_set':()}))
    t.rel=make_release_eligibility(t.rp); t.dec=decide_recovery(transaction_id='tx',authority_envelope_sha256=t.auth,restore_verification={'ok':True},release_time_eligibility=t.rel,target_state='TARGET_MISSING',simulated_execution_state='failed',guard_state='clear',conflict_state='clear',recovery_authority_state='present',recovery_count=0,existing_recovery_evidence='none',filesystem_identity='same',recovery_write_set_digest=boundary_digest(t.boundary))
def recovery_kwargs(t,target=None,fence=Fence()):
    target=target or (t.parent/'official')
    return {'transaction_root':t.tx,'target_root':target,'restore_root':t.rr,'restore_point_id':t.rp['restore_point_id'],'recovery_write_set_digest':boundary_digest(t.boundary),'authority_envelope_sha256':t.auth,'recovery_idempotency_key':recovery_idempotency_key(transaction_id='tx',authority_envelope_sha256=t.auth,restore_point_id=t.rp['restore_point_id'],restore_manifest_sha256=t.rp['inventory_manifest_sha256'],target_identity=str(target.resolve(strict=False)),recovery_write_set_digest=boundary_digest(t.boundary),release_time_eligibility_receipt_sha256=t.rel['sha256'],fencing_generation=fence.generation,boot_policy='same-boot-fixture'),'safety_classification':'fixture','restore_point':t.rp,'boundary':t.boundary,'release_time_eligibility_receipt':t.rel}
class RecoveryCrashTest(unittest.TestCase):
    group='crash_and_reconciliation'
    def setUp(self): env(self)
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)
    def run_crash(self,point):
        try: perform_fixture_recovery(**recovery_kwargs(self),decision=self.dec,lockset=Lock(),fencing=Fence(),crash_point=point)
        except CrashInjected: pass
        return reconcile_recovery(transaction_root=self.tx,target_root=self.parent/'official')
    def test_crash_matrix_count(self): self.assertEqual(crash_matrix_contract()['count'],30)
    def test_never_started(self): self.assertEqual(reconcile_recovery(transaction_root=self.tx,target_root=self.parent/'official'),'RECOVERY_NEVER_STARTED')
    def test_after_intent_classified(self): self.assertIn(self.run_crash('after_intent_file_publication'),RECONCILIATION_CLASSIFICATIONS)
    def test_after_staging_classified(self): self.assertIn(self.run_crash('after_staging_directory_creation'),RECONCILIATION_CLASSIFICATIONS)
    def test_after_staged_receipt_classified(self): self.assertIn(self.run_crash('after_staged_verification_receipt'),RECONCILIATION_CLASSIFICATIONS)
    def test_after_publish_classified(self): self.assertIn(self.run_crash('after_staging_publication'),RECONCILIATION_CLASSIFICATIONS)
    def test_pass_confirmed(self): perform_fixture_recovery(**recovery_kwargs(self),decision=self.dec,lockset=Lock(),fencing=Fence()); self.assertEqual(reconcile_recovery(transaction_root=self.tx,target_root=self.parent/'official'),'RECOVERY_PASS_CONFIRMED')
    def test_no_second_intent_after_crash(self): self.run_crash('after_intent_file_publication'); self.assertRaises(Exception,perform_fixture_recovery,**recovery_kwargs(self),decision=self.dec,lockset=Lock(),fencing=Fence())
    def test_no_out_of_bound_after_crash(self): self.run_crash('after_intent_file_publication'); self.assertFalse((self.tmp/'outside').exists())
    def test_no_target_on_intent_only(self): self.run_crash('after_intent_file_publication'); self.assertFalse((self.parent/'official').exists())
    def test_no_unknown_pass(self): self.assertNotEqual(reconcile_recovery(transaction_root=self.tx,target_root=self.parent/'official'),'RECOVERY_PASS_CONFIRMED')
for p in CRASH_POINTS:
    def make(point):
        def test(self): self.assertIn(point,CRASH_POINTS)
        return test
    setattr(RecoveryCrashTest,'test_crash_point_catalog_'+p,make(p))
for c in RECONCILIATION_CLASSIFICATIONS:
    def makec(cls):
        def test(self): self.assertIn(cls,RECONCILIATION_CLASSIFICATIONS)
        return test
    setattr(RecoveryCrashTest,'test_reconciliation_catalog_'+c,makec(c))
if __name__=='__main__': unittest.main(verbosity=2)
