#!/usr/bin/env python3
from __future__ import annotations
import shutil, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'scripts'; sys.path.insert(0,str(SCRIPTS))
from critical_apply_commit import *  # noqa
from critical_apply_authority import make_fixture_envelope, authority_envelope_hash, evaluate_restore_freshness, evaluate_conflict_set
from critical_apply_locks import acquire_lockset
from critical_apply_atomic_io import read_json_artifact, sha256_file

class CommitTest(unittest.TestCase):
    group='prepare_approve_commit_revalidation_drift'
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='m2-commit-')); self.lock=Path(tempfile.mkdtemp(prefix='m2-commit-lock-'))
        self.tx='critical-apply-m2-commit-20260730T102000Z-'+'a'*32; self.campaign='critical-campaign-m2-commit-20260730T102000Z-'+'b'*32
        self.env=make_fixture_envelope(self.tx,self.campaign,'nonce-commit')
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True); shutil.rmtree(self.lock,ignore_errors=True)
    def prep(self): return prepare_transaction(self.tmp,transaction_spec={'sha256':self.env['transaction_spec_sha256']},envelope=self.env,surfaces=['surface:npm-metadata'])
    def approved(self): p=self.prep(); record_synthetic_approval(self.tmp,envelope=self.env,plan=p); return p
    def lockset(self): return acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata'])
    def test_prepare_seals_plan(self): p=self.prep(); self.assertTrue((self.tmp/'plan-sealed.json').exists()); self.assertTrue(p.awaiting_approval)
    def test_prepare_releases_locks(self): p=self.prep(); self.assertFalse(p.production_locks_held)
    def test_prepare_never_commit_validated(self): self.prep(); self.assertNotIn('COMMIT_VALIDATED',(self.tmp/'journal/events.jsonl').read_text())
    def test_approve_records_no_execution(self): self.approved(); self.assertTrue((self.tmp/'receipts/approval-receipt.json').exists()); self.assertFalse((self.tmp/'synthetic-release-decision.json').exists())
    def test_commit_pass(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); self.assertTrue(cr.ok); self.assertEqual(cr.classification,'COMMIT_REVALIDATION_PASS'); ls.release()
    def test_commit_writes_receipt(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); self.assertTrue((self.tmp/'commit-revalidation.json').exists()); ls.release()
    def test_commit_field_count(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); self.assertGreaterEqual(len(cr.fields),40); ls.release()
    def test_commit_blocks_missing_approval(self):
        self.prep(); ls=self.lockset(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); self.assertEqual(cr.classification,'COMMIT_REVALIDATION_BLOCKED_APPROVAL'); ls.release()
    def test_commit_blocks_expired_approval(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[],now_wall_time='2026-07-30T11:20:00Z'); self.assertEqual(cr.classification,'COMMIT_REVALIDATION_BLOCKED_APPROVAL'); ls.release()
    def test_commit_blocks_restore_stale(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(False),conflicts=[]); self.assertEqual(cr.classification,'COMMIT_REVALIDATION_BLOCKED_RESTORE_STALE'); ls.release()
    def test_commit_blocks_conflict(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[{'category':'npm writer','state':'active'}]); self.assertEqual(cr.classification,'COMMIT_REVALIDATION_BLOCKED_CONFLICT'); ls.release()
    def test_commit_blocks_drift(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); actual=dict(exp); actual['candidate_sha']='changed'; cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=actual,lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); self.assertEqual(cr.classification,'COMMIT_REVALIDATION_BLOCKED_DRIFT'); ls.release()
    def test_allowed_scheduler_drift(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); actual=dict(exp); actual['scheduler_semantic']='timestamp2'; policy={'scheduler_semantic':{'sealed_before_approval':True,'policy_sha256':'f'*64,'actual_allowed':'timestamp2'}}; cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=actual,lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[],allowed_drift_policy=policy); self.assertTrue(cr.ok); ls.release()
    def test_immutable_candidate_drift_not_allowed_even_policy(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); actual=dict(exp); actual['candidate_sha']='changed'; policy={'candidate_sha':{'sealed_before_approval':True,'policy_sha256':'f'*64,'actual_allowed':'changed'}}; cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=actual,lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[],allowed_drift_policy=policy); self.assertFalse(cr.ok); ls.release()
    def test_synthetic_release_fixture(self):
        out=synthetic_release_fixture(self.tmp,self.lock); self.assertTrue(out['fixture_only']); self.assertFalse(out['child_identity']['executed']); self.assertFalse(out['transition_beyond_commit_validated'])
    def test_synthetic_release_consumes_once(self): synthetic_release_fixture(self.tmp,self.lock); self.assertTrue((self.tmp/'receipts/approval-consumed.json').exists())
    def test_release_decision_no_child(self): synthetic_release_fixture(self.tmp,self.lock); self.assertIn('NO_CHILD_EXECUTION', read_json_artifact(self.tmp/'synthetic-release-decision.json',root=self.tmp)['release_decision'])
    def test_journal_contains_plan_approval_commit(self): self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=dict(exp),lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); txt=(self.tmp/'journal/events.jsonl').read_text(); self.assertIn('PLAN_SEALED',txt); self.assertIn('APPROVAL_RECORDED',txt); self.assertIn('COMMIT_VALIDATED',txt); ls.release()
    def test_lock_receipt_alone_cannot_commit(self):
        self.approved(); exp=fixture_expected_state(self.env); cr=commit_revalidate(self.tmp, envelope=self.env, expected=exp, actual=dict(exp), lockset={'receipt':1}, restore_metadata=fixture_restore_metadata(True), conflicts=[])
        self.assertEqual(cr.classification, 'COMMIT_REVALIDATION_BLOCKED_LOCKS')

DRIFT_FIELDS_TO_TEST=['transaction_spec','authority_envelope','contract_bundle','runner_bundle','plugin_bundle','interpreter','supervisor_unit','candidate_path','candidate_file','candidate_sha','candidate_version','candidate_source_commit','executable','argv','environment_policy','working_directory','uid_gid','npm_global_prefix','restore_point_id','restore_manifest','restore_method','pre_state_fingerprint','strict_guard','scheduler_semantic','surface_set','resource_policy','timeout_policy','network_policy','recovery_policy','host','boot','mount_filesystem','lock_set','fencing_generation','conflict_set','approval_expiry','approval_nonce','owner_identity','restart_smoke_flags','maximum_mutation_count']
def _drift(field):
    def test(self):
        self.approved(); ls=self.lockset(); exp=fixture_expected_state(self.env); actual=dict(exp); actual[field]='DRIFTED'; cr=commit_revalidate(self.tmp,envelope=self.env,expected=exp,actual=actual,lockset=ls,restore_metadata=fixture_restore_metadata(True),conflicts=[]); self.assertFalse(cr.ok); self.assertIn(field,cr.blocked_reasons); ls.release()
    return test
for f in DRIFT_FIELDS_TO_TEST:
    setattr(CommitTest, 'test_drift_invalidates_'+f, _drift(f))

if __name__=='__main__': unittest.main(verbosity=2)
