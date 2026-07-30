#!/usr/bin/env python3
from __future__ import annotations
import os, shutil, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'scripts'; sys.path.insert(0,str(SCRIPTS))
from critical_apply_authority import *  # noqa
from critical_apply_locks import acquire_lockset, LockError
from critical_apply_journal import create_transaction_journal
from critical_apply_atomic_io import atomic_create_json, sha256_file

class AuthorityTest(unittest.TestCase):
    group='authority_approval_consumption'
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='m2-auth-')); self.lock=Path(tempfile.mkdtemp(prefix='m2-lock-'))
        self.tx='critical-apply-m2-auth-20260730T102000Z-'+'a'*32; self.campaign='critical-campaign-m2-auth-20260730T102000Z-'+'b'*32; self.nonce='nonce-1'
        self.env=make_fixture_envelope(self.tx,self.campaign,self.nonce); create_transaction_journal(self.tmp, transaction_id=self.tx)
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True); shutil.rmtree(self.lock,ignore_errors=True)
    def approval_event(self, **kw):
        ev={'transaction_id':self.tx,'campaign_id':self.campaign,'approval_nonce':self.nonce,'authority_envelope_sha256':authority_envelope_hash(self.env),'transaction_spec_sha256':self.env['transaction_spec_sha256'],'owner_identity':'fixture-owner-m2','approval_mode':'allow-once','trusted_event_identity':'fixture-event','issued_time':'2026-07-30T10:00:00Z','approved_time':'2026-07-30T10:10:00Z','expiry_time':'2026-07-30T11:00:00Z'}; ev.update(kw); return ev
    def record(self, **kw): return record_approval_receipt(self.tmp,envelope=self.env,approval_event=self.approval_event(**kw),plan_sealed_at='2026-07-30T10:05:00Z')
    def test_envelope_valid(self): self.assertTrue(validate_m2_authority_envelope(self.env)[0])
    def test_envelope_missing_field_fails(self):
        e=dict(self.env); e.pop('owner'); self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_envelope_unknown_field_fails(self):
        e=dict(self.env); e['extra']=1; self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_max_primary_must_one(self):
        e=dict(self.env); e['max_primary_mutations']=2; self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_recoveries_zero_or_one(self):
        e=dict(self.env); e['max_automatic_recoveries']=2; self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_package_apply_cannot_restart(self):
        e=dict(self.env); e['restart_authorised']=True; self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_package_apply_cannot_smoke(self):
        e=dict(self.env); e['functional_smoke_authorised']=True; self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_generic_command_rejected(self):
        e=dict(self.env); e['transaction_type']='arbitrary_command'; self.assertFalse(validate_m2_authority_envelope(e)[0])
    def test_hash_deterministic(self): self.assertEqual(authority_envelope_hash(self.env), authority_envelope_hash(dict(reversed(list(self.env.items())))))
    def test_record_approval_success(self): self.assertEqual(self.record()['schema'], APPROVAL_RECEIPT_SCHEMA)
    def test_allow_always_rejected(self): self.assertRaises(AuthorityError, self.record, approval_mode='allow-always')
    def test_wrong_transaction_rejected(self): self.assertRaises(AuthorityError, self.record, transaction_id='wrong')
    def test_wrong_campaign_rejected(self): self.assertRaises(AuthorityError, self.record, campaign_id='wrong')
    def test_wrong_nonce_rejected(self): self.assertRaises(AuthorityError, self.record, approval_nonce='wrong')
    def test_wrong_envelope_hash_rejected(self): self.assertRaises(AuthorityError, self.record, authority_envelope_sha256='0'*64)
    def test_wrong_spec_hash_rejected(self): self.assertRaises(AuthorityError, self.record, transaction_spec_sha256='0'*64)
    def test_wrong_owner_rejected(self): self.assertRaises(AuthorityError, self.record, owner_identity='other')
    def test_approved_before_plan_rejected(self): self.assertRaises(AuthorityError, self.record, approved_time='2026-07-30T10:01:00Z')
    def test_after_expiry_rejected(self): self.assertRaises(AuthorityError, self.record, approved_time='2026-07-30T11:01:00Z')
    def test_inverted_time_rejected(self): self.assertRaises(AuthorityError, self.record, issued_time='2026-07-30T10:20:00Z')
    def test_duplicate_receipt_rejected(self): self.record(); self.assertRaises(EvidenceIOError, self.record)
    def test_eval_missing(self): self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,now_wall_time='2026-07-30T10:20:00Z').classification,'APPROVAL_MISSING')
    def test_eval_valid_unconsumed(self): self.record(); self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,now_wall_time='2026-07-30T10:20:00Z',same_boot_required=False).classification,'APPROVAL_VALID_UNCONSUMED')
    def test_eval_expired(self): self.record(); self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,now_wall_time='2026-07-30T11:20:00Z',same_boot_required=False).classification,'APPROVAL_EXPIRED')
    def test_eval_nonce_mismatch(self): self.record(); e=dict(self.env); e['one_time_nonce']='other'; self.assertEqual(evaluate_approval(self.tmp,envelope=e,now_wall_time='2026-07-30T10:20:00Z',same_boot_required=False).classification,'APPROVAL_ENVELOPE_MISMATCH')
    def test_eval_owner_mismatch(self): self.record(); self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,owner='other',now_wall_time='2026-07-30T10:20:00Z',same_boot_required=False).classification,'APPROVAL_OWNER_MISMATCH')
    def test_eval_mode_forbidden(self):
        r=self.record(); p=self.tmp/'receipts/approval-receipt.json'; obj=read_json_artifact(p, root=self.tmp); obj['approval_mode']='allow-always'; p.write_text(canonical_json_dumps(obj)+'\n'); self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,now_wall_time='2026-07-30T10:20:00Z',same_boot_required=False).classification,'APPROVAL_MODE_FORBIDDEN')
    def test_eval_boot_mismatch(self): self.record(approval_boot_id='other'); self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,now_wall_time='2026-07-30T10:20:00Z',same_boot_required=True).classification,'APPROVAL_BOOT_POLICY_MISMATCH')
    def test_consumption_success(self):
        self.record(); ls=acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata']); cap=consume_approval(self.tmp,envelope=self.env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z'); self.assertTrue(hasattr(cap,'marker_sha256')); ls.release()
    def test_consumption_requires_lockset(self): self.record(); self.assertRaises(AttributeError, consume_approval, self.tmp, envelope=self.env, lockset=None, commit_revalidation_sha256='c'*64, now_wall_time='2026-07-30T10:20:00Z')
    def test_consumption_replay_already_consumed(self):
        self.record(); ls=acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata']); cap=consume_approval(self.tmp,envelope=self.env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z'); res=consume_approval(self.tmp,envelope=self.env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z'); self.assertEqual(res.classification,'APPROVAL_ALREADY_CONSUMED'); ls.release()
    def test_consumption_invalidates_eval(self):
        self.record(); ls=acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata']); consume_approval(self.tmp,envelope=self.env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z'); self.assertEqual(evaluate_approval(self.tmp,envelope=self.env,now_wall_time='2026-07-30T10:20:00Z',same_boot_required=False).classification,'APPROVAL_ALREADY_CONSUMED'); ls.release()
    def test_consumption_marker_schema(self):
        self.record(); ls=acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata']); consume_approval(self.tmp,envelope=self.env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z'); self.assertEqual(read_json_artifact(self.tmp/'receipts/approval-consumed.json',root=self.tmp)['primary_mutation_ordinal'],1); ls.release()
    def test_consumption_wrong_hash_rejected(self):
        self.record(); ls=acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata']); self.assertRaises(AuthorityError, consume_approval, self.tmp, envelope=self.env, lockset=ls, commit_revalidation_sha256='bad', now_wall_time='2026-07-30T10:20:00Z'); ls.release()
    def test_consumed_capability_pickle_rejected(self):
        self.record(); ls=acquire_lockset(lock_root=self.lock,transaction_id=self.tx,surfaces=['surface:npm-metadata']); cap=consume_approval(self.tmp,envelope=self.env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z'); import pickle; self.assertRaises(TypeError,pickle.dumps,cap); ls.release()
    def test_classify_unconsumed(self): self.assertEqual(classify_consumption_state(self.tmp,envelope=self.env),'APPROVAL_UNCONSUMED')
    def test_classify_marker_missing_journal(self): self.record(); atomic_create_json(self.tmp/'receipts/approval-consumed.json',{'schema':APPROVAL_CONSUMED_SCHEMA,'transaction_id':self.tx,'approval_nonce':self.nonce,'authority_envelope_sha256':authority_envelope_hash(self.env)},root=self.tmp); self.assertEqual(classify_consumption_state(self.tmp,envelope=self.env),'APPROVAL_CONSUMED_JOURNAL_RECONCILIATION_REQUIRED')
    def test_crash_classifications_set_known(self): self.assertTrue(CONSUMPTION_CLASSIFICATIONS)

# Dynamic approval validity classifications and crash states.
def _crash(marker,journal,expected,**kw):
    def test(self): self.assertEqual(classify_consumption_crash_state(marker,journal,**kw), expected)
    return test
for i,(marker,journal,expected,kw) in enumerate([
    (False,False,'APPROVAL_UNCONSUMED',{}),(True,True,'APPROVAL_CONSUMED_VALID',{}),(True,False,'APPROVAL_CONSUMED_JOURNAL_RECONCILIATION_REQUIRED',{}),(False,True,'APPROVAL_CONSUMPTION_STATE_UNKNOWN_OPERATOR_HOLD',{}),(True,True,'APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD',{'corrupt_marker':True}),(True,True,'APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD',{'wrong_nonce':True}),(True,True,'APPROVAL_CONSUMPTION_CONFLICT_OPERATOR_HOLD',{'wrong_generation':True}),(False,False,'APPROVAL_CONSUMPTION_STATE_UNKNOWN_OPERATOR_HOLD',{'stale_token':True})]):
    setattr(AuthorityTest, f'test_consumption_crash_state_{i}', _crash(marker,journal,expected,**kw))

if __name__=='__main__': unittest.main(verbosity=2)
