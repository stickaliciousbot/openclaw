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
def setup_env(t):
    t.tmp=Path(tempfile.mkdtemp(prefix='m3-rec-')); t.tx=t.tmp/'tx'; t.src=t.tmp/'src'; t.rr=t.tmp/'restore'; t.parent=t.tmp/'target-parent'; [p.mkdir(mode=0o700,parents=True) for p in [t.tx,t.src,t.rr,t.parent]]
    (t.src/'package.json').write_text('{"name":"fixture"}\n'); (t.src/'dist').mkdir(); (t.src/'dist/index.js').write_text('ok\n')
    t.boundary=make_boundary(target_root=t.parent/'official',allowed_relative_paths=['package.json','dist','dist/index.js'],recovery_write_set=['package.json','dist'])
    t.auth='a'*64; t.rp=create_restore_point(transaction_root=t.tx,source_root=t.src,restore_root=t.rr,restore_point_id='restore-'+'b'*40,boundary=t.boundary,transaction_id='tx',campaign_id='camp',authority_envelope_sha256=t.auth,recovery_write_set_digest=boundary_digest(t.boundary),forbidden_set_digest=canonical_json_sha({'forbidden_set':()}))
    t.bundle_inv=inventory_tree(Path(t.rp['bundle_path']),boundary=t.boundary); t.rel=make_release_eligibility(t.rp)
class RecoveryDecisionTest(unittest.TestCase):
    group='recovery_decisions_and_authority'
    def setUp(self): setup_env(self)
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)
    def decision(self,state='TARGET_MISSING',restore_ok=True,rel=True,auth='present',count=0,guard='clear',conflict='clear',fs='same'):
        return decide_recovery(transaction_id='tx',authority_envelope_sha256=self.auth,restore_verification={'ok':restore_ok,'classification':'RESTORE_POINT_VERIFIED'},release_time_eligibility=rel,target_state=state,simulated_execution_state='failed_after_authorised_mutation',guard_state=guard,conflict_state=conflict,recovery_authority_state=auth,recovery_count=count,existing_recovery_evidence='none',filesystem_identity=fs,recovery_write_set_digest=boundary_digest(self.boundary))
    def recovery_kwargs(self,target=None,fence=Fence()):
        target=target or (self.parent/'official')
        return {'transaction_root':self.tx,'target_root':target,'restore_root':self.rr,'restore_point_id':self.rp['restore_point_id'],'recovery_write_set_digest':boundary_digest(self.boundary),'authority_envelope_sha256':self.auth,'recovery_idempotency_key':recovery_idempotency_key(transaction_id='tx',authority_envelope_sha256=self.auth,restore_point_id=self.rp['restore_point_id'],restore_manifest_sha256=self.rp['inventory_manifest_sha256'],target_identity=str(target.resolve(strict=False)),recovery_write_set_digest=boundary_digest(self.boundary),release_time_eligibility_receipt_sha256=self.rel['sha256'],fencing_generation=fence.generation,boot_policy='same-boot-fixture'),'safety_classification':'fixture','restore_point':self.rp,'boundary':self.boundary,'release_time_eligibility_receipt':self.rel}
    def test_missing_authorised(self): self.assertEqual(self.decision().decision,'RECOVERY_AUTHORISED_PENDING')
    def test_empty_authorised(self): self.assertTrue(self.decision('TARGET_EMPTY').automatic_recovery_allowed)
    def test_incomplete_authorised(self): self.assertTrue(self.decision('TARGET_INCOMPLETE').automatic_recovery_allowed)
    def test_candidate_not_required(self): self.assertEqual(self.decision('TARGET_COHERENT_CANDIDATE_GENERATION').decision,'RECOVERY_NOT_REQUIRED_EXACT_CANDIDATE')
    def test_pre_not_required(self): self.assertEqual(self.decision('TARGET_COHERENT_PRE_GENERATION').decision,'RECOVERY_NOT_REQUIRED_PRE_GENERATION_INTACT')
    def test_other_blocks(self): self.assertEqual(self.decision('TARGET_COHERENT_OTHER_GENERATION').decision,'RECOVERY_BLOCKED_TARGET_COHERENT_OTHER')
    def test_unknown_blocks(self): self.assertEqual(self.decision('TARGET_UNKNOWN').decision,'RECOVERY_BLOCKED_TARGET_UNKNOWN')
    def test_conflicting_blocks(self): self.assertEqual(self.decision('TARGET_CONFLICTING').decision,'RECOVERY_BLOCKED_TARGET_UNKNOWN')
    def test_no_authority_blocks(self): self.assertEqual(self.decision(auth='missing').decision,'RECOVERY_BLOCKED_NO_AUTHORITY')
    def test_restore_invalid_blocks(self): self.assertEqual(self.decision(restore_ok=False).decision,'RECOVERY_BLOCKED_RESTORE_INVALID')
    def test_release_not_eligible_blocks(self): self.assertEqual(self.decision(rel=False).decision,'RECOVERY_BLOCKED_RESTORE_NOT_RELEASE_ELIGIBLE')
    def test_guard_blocks(self): self.assertEqual(self.decision(guard='drift').decision,'RECOVERY_BLOCKED_GUARD_DRIFT')
    def test_conflict_blocks(self): self.assertEqual(self.decision(conflict='active').decision,'RECOVERY_BLOCKED_CONFLICT')
    def test_filesystem_blocks(self): self.assertEqual(self.decision(fs='mismatch').decision,'RECOVERY_BLOCKED_FILESYSTEM_POLICY')
    def test_count_blocks(self): self.assertIn(self.decision(count=1).decision,('RECOVERY_STATE_UNKNOWN_OPERATOR_HOLD','RECOVERY_ALREADY_PASS'))
    def test_missing_classifier(self): self.assertEqual(classify_fixture_target(target_root=self.parent/'official',candidate_inventory=self.bundle_inv),'TARGET_MISSING')
    def test_empty_classifier(self): (self.parent/'official').mkdir(); self.assertEqual(classify_fixture_target(target_root=self.parent/'official',candidate_inventory=self.bundle_inv),'TARGET_EMPTY')
    def test_incomplete_classifier(self): t=self.parent/'official'; t.mkdir(); (t/'package.json').write_text('{}'); self.assertEqual(classify_fixture_target(target_root=t,candidate_inventory=self.bundle_inv),'TARGET_INCOMPLETE')
    def test_candidate_classifier(self): shutil.copytree(self.rp['bundle_path'],self.parent/'official'); self.assertEqual(classify_fixture_target(target_root=self.parent/'official',candidate_inventory=self.bundle_inv),'TARGET_COHERENT_CANDIDATE_GENERATION')
    def test_symlink_classifier_unknown(self): (self.parent/'official').symlink_to(self.src); self.assertEqual(classify_fixture_target(target_root=self.parent/'official',candidate_inventory=self.bundle_inv),'TARGET_UNKNOWN')
    def test_decision_contract(self): self.assertEqual(recovery_decision_contract()['maximum_automatic_recovery_count'],1)
    def test_state_machine_contract(self): self.assertIn('RECOVERY_PASS',recovery_state_machine_contract()['phases'])
    def test_recovery_success_missing(self): d=self.decision(); out=perform_fixture_recovery(**self.recovery_kwargs(),decision=d,lockset=Lock(),fencing=Fence()); self.assertEqual(out['classification'],'RECOVERY_PASS')
    def test_recovery_preserves_empty(self): (self.parent/'official').mkdir(); out=perform_fixture_recovery(**self.recovery_kwargs(),decision=self.decision('TARGET_EMPTY'),lockset=Lock(),fencing=Fence()); self.assertTrue(Path(out['preservation_path']).exists())
    def test_no_lock_blocks(self): self.assertRaises(RecoveryError,perform_fixture_recovery,**self.recovery_kwargs(),decision=self.decision(),lockset={},fencing=Fence())
for dec in RECOVERY_DECISIONS:
    def make(d):
        def test(self): self.assertIn(d,RECOVERY_DECISIONS)
        return test
    setattr(RecoveryDecisionTest,'test_decision_enum_'+dec,make(dec))
if __name__=='__main__': unittest.main(verbosity=2)
