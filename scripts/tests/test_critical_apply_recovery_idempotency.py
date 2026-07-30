#!/usr/bin/env python3
from __future__ import annotations
import shutil, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from critical_apply_restore import *
from critical_apply_recovery import *
from critical_apply_filesystem import boundary_digest, canonical_json_sha
class Lock:
    digest='e'*64
    def assert_live(self): return True
class Fence: generation=7; token_sha256='f'*64
class RecoveryIdempotencyTest(unittest.TestCase):
    group='idempotency_duplicate_prevention_tamper'
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='m3-idem-')); self.tx=self.tmp/'tx'; self.src=self.tmp/'src'; self.rr=self.tmp/'restore'; self.parent=self.tmp/'parent'; [p.mkdir(mode=0o700,parents=True) for p in [self.tx,self.src,self.rr,self.parent]]
        (self.src/'package.json').write_text('{}'); (self.src/'dist').mkdir(); (self.src/'dist/index.js').write_text('ok')
        self.boundary=make_boundary(target_root=self.parent/'official',allowed_relative_paths=['package.json','dist','dist/index.js'],recovery_write_set=['package.json','dist']); self.auth='a'*64
        self.rp=create_restore_point(transaction_root=self.tx,source_root=self.src,restore_root=self.rr,restore_point_id='restore-'+'d'*40,boundary=self.boundary,transaction_id='tx',campaign_id='camp',authority_envelope_sha256=self.auth,recovery_write_set_digest=boundary_digest(self.boundary),forbidden_set_digest=canonical_json_sha({'forbidden_set':()})); self.rel=make_release_eligibility(self.rp)
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)
    def key(self, **kw):
        args={'transaction_id':'tx','authority_envelope_sha256':self.auth,'restore_point_id':self.rp['restore_point_id'],'restore_manifest_sha256':self.rp['inventory_manifest_sha256'],'target_identity':str(self.parent/'official'),'recovery_write_set_digest':boundary_digest(self.boundary),'release_time_eligibility_receipt_sha256':self.rel['sha256'],'fencing_generation':7,'boot_policy':'same'}; args.update(kw); return recovery_idempotency_key(**args)
    def recovery_kwargs(self,target=None,fence=Fence()):
        target=target or (self.parent/'official')
        return {'transaction_root':self.tx,'target_root':target,'restore_root':self.rr,'restore_point_id':self.rp['restore_point_id'],'recovery_write_set_digest':boundary_digest(self.boundary),'authority_envelope_sha256':self.auth,'recovery_idempotency_key':recovery_idempotency_key(transaction_id='tx',authority_envelope_sha256=self.auth,restore_point_id=self.rp['restore_point_id'],restore_manifest_sha256=self.rp['inventory_manifest_sha256'],target_identity=str(target.resolve(strict=False)),recovery_write_set_digest=boundary_digest(self.boundary),release_time_eligibility_receipt_sha256=self.rel['sha256'],fencing_generation=fence.generation,boot_policy='same-boot-fixture'),'safety_classification':'fixture','restore_point':self.rp,'boundary':self.boundary,'release_time_eligibility_receipt':self.rel}
    def test_key_sha(self): self.assertEqual(len(self.key()),64)
    def test_key_stable(self): self.assertEqual(self.key(),self.key())
    def test_key_diff_restore(self): self.assertNotEqual(self.key(),self.key(restore_point_id='other'))
    def test_key_diff_target(self): self.assertNotEqual(self.key(),self.key(target_identity='other'))
    def test_key_diff_tx(self): self.assertNotEqual(self.key(),self.key(transaction_id='other'))
    def test_key_diff_manifest(self): self.assertNotEqual(self.key(),self.key(restore_manifest_sha256='1'*64))
    def test_key_diff_fence(self): self.assertNotEqual(self.key(),self.key(fencing_generation=8))
    def test_key_no_secret_text(self): self.assertNotIn('secret',self.key())
    def test_one_success(self):
        dec=decide_recovery(transaction_id='tx',authority_envelope_sha256=self.auth,restore_verification={'ok':True},release_time_eligibility=self.rel,target_state='TARGET_MISSING',simulated_execution_state='failed',guard_state='clear',conflict_state='clear',recovery_authority_state='present',recovery_count=0,existing_recovery_evidence='none',filesystem_identity='same',recovery_write_set_digest=boundary_digest(self.boundary)); self.assertEqual(perform_fixture_recovery(**self.recovery_kwargs(),decision=dec,lockset=Lock(),fencing=Fence())['classification'],'RECOVERY_PASS')
    def test_second_intent_rejected(self): self.test_one_success(); target=self.parent/'official2'; dec=decide_recovery(transaction_id='tx',authority_envelope_sha256=self.auth,restore_verification={'ok':True},release_time_eligibility=self.rel,target_state='TARGET_MISSING',simulated_execution_state='failed',guard_state='clear',conflict_state='clear',recovery_authority_state='present',recovery_count=0,existing_recovery_evidence='none',filesystem_identity='same',recovery_write_set_digest=boundary_digest(self.boundary)); self.assertRaises(Exception,perform_fixture_recovery,**self.recovery_kwargs(target=target),decision=dec,lockset=Lock(),fencing=Fence())
    def test_decision_after_count_pass(self): d=decide_recovery(transaction_id='tx',authority_envelope_sha256=self.auth,restore_verification={'ok':True},release_time_eligibility=self.rel,target_state='TARGET_MISSING',simulated_execution_state='failed',guard_state='clear',conflict_state='clear',recovery_authority_state='present',recovery_count=1,existing_recovery_evidence='pass',filesystem_identity='same',recovery_write_set_digest=boundary_digest(self.boundary)); self.assertEqual(d.decision,'RECOVERY_ALREADY_PASS')
for field in ['transaction_id','recovery_ordinal','authority_envelope_sha256','recovery_policy_sha256','restore_point_id','restore_manifest_sha256','target_identity','recovery_write_set_digest','release_time_eligibility_receipt_sha256','fencing_generation','boot_policy']:
    def make(f):
        def test(self):
            base=self.key(); alt={f:'other'} if f not in ('recovery_ordinal','fencing_generation') else {f:99}; self.assertNotEqual(base,self.key(**alt))
        return test
    setattr(RecoveryIdempotencyTest,'test_key_input_'+field,make(field))
if __name__=='__main__': unittest.main(verbosity=2)
