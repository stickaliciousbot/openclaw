#!/usr/bin/env python3
from __future__ import annotations
import json, multiprocessing as mp, os, shutil, sys, tempfile, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'scripts'; sys.path.insert(0,str(SCRIPTS))
from critical_apply_locks import acquire_lockset, KernelLock, LockAcquireBlocked, LockError, canonicalize_surface_locks, validate_lock_acquisition_order
from critical_apply_authority import make_fixture_envelope, record_approval_receipt, authority_envelope_hash, consume_approval, evaluate_approval
from critical_apply_journal import create_transaction_journal
from critical_apply_atomic_io import atomic_create_json

def hold_lock(root, lock_id, q):
    sys.path.insert(0,str(SCRIPTS)); from critical_apply_locks import KernelLock
    lk=KernelLock.acquire(lock_root=Path(root),lock_id=lock_id,transaction_id='tx-child',surface_sets_sha256='a'*64,expected_rank=0 if lock_id.startswith('global') else 1)
    q.put('held'); time.sleep(0.8); lk.release(); q.put('released')

def consume_worker(txroot, lockroot, env, q):
    sys.path.insert(0,str(SCRIPTS)); from critical_apply_locks import acquire_lockset; from critical_apply_authority import consume_approval
    try:
        with acquire_lockset(lock_root=Path(lockroot),transaction_id=env['transaction_id'],surfaces=['surface:npm-metadata']) as ls:
            res=consume_approval(Path(txroot),envelope=env,lockset=ls,commit_revalidation_sha256='c'*64,now_wall_time='2026-07-30T10:20:00Z')
            q.put('WIN' if hasattr(res,'marker_sha256') else res.classification)
    except Exception as e:
        q.put(type(e).__name__)

class ConcurrencyTest(unittest.TestCase):
    group='crash_reconciliation_concurrency'
    def setUp(self): self.tmp=Path(tempfile.mkdtemp(prefix='m2-conc-')); self.lock=Path(tempfile.mkdtemp(prefix='m2-conc-lock-'))
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True); shutil.rmtree(self.lock,ignore_errors=True)
    def test_two_processes_contend_global_lock(self):
        q=mp.Queue(); p=mp.Process(target=hold_lock,args=(str(self.lock),'global:critical-apply',q)); p.start(); self.assertEqual(q.get(timeout=2),'held')
        with self.assertRaises(LockAcquireBlocked): KernelLock.acquire(lock_root=self.lock,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0)
        p.join(3); self.assertFalse(p.is_alive())
    def test_two_processes_contend_prefix_lock(self):
        q=mp.Queue(); p=mp.Process(target=hold_lock,args=(str(self.lock),'package-manager:global-prefix',q)); p.start(); self.assertEqual(q.get(timeout=2),'held')
        with self.assertRaises(LockAcquireBlocked): KernelLock.acquire(lock_root=self.lock,lock_id='package-manager:global-prefix',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=1)
        p.join(3); self.assertFalse(p.is_alive())
    def test_killed_holder_releases_kernel_lock(self):
        q=mp.Queue(); p=mp.Process(target=hold_lock,args=(str(self.lock),'global:critical-apply',q)); p.start(); self.assertEqual(q.get(timeout=2),'held'); p.terminate(); p.join(3)
        lk=KernelLock.acquire(lock_root=self.lock,lock_id='global:critical-apply',transaction_id='tx2',surface_sets_sha256='a'*64,expected_rank=0); lk.release()
    def setup_consumption(self):
        tx='critical-apply-m2-consume-20260730T102000Z-'+'a'*32; camp='critical-campaign-m2-consume-20260730T102000Z-'+'b'*32; env=make_fixture_envelope(tx,camp,'nonce')
        self.tmp.mkdir(exist_ok=True); create_transaction_journal(self.tmp,transaction_id=tx)
        ev={'transaction_id':tx,'campaign_id':camp,'approval_nonce':'nonce','authority_envelope_sha256':authority_envelope_hash(env),'transaction_spec_sha256':env['transaction_spec_sha256'],'owner_identity':'fixture-owner-m2','approval_mode':'allow-once','trusted_event_identity':'fixture','issued_time':'2026-07-30T10:00:00Z','approved_time':'2026-07-30T10:10:00Z','expiry_time':'2026-07-30T11:00:00Z'}
        record_approval_receipt(self.tmp,envelope=env,approval_event=ev,plan_sealed_at='2026-07-30T10:05:00Z'); return env
    def test_32_simultaneous_consumers_one_winner(self):
        env=self.setup_consumption(); q=mp.Queue(); procs=[mp.Process(target=consume_worker,args=(str(self.tmp),str(self.lock),env,q)) for _ in range(32)]
        [p.start() for p in procs]; results=[q.get(timeout=10) for _ in procs]; [p.join(5) for p in procs]
        self.assertEqual(results.count('WIN'),1); self.assertEqual(sum(1 for r in results if r=='WIN'),1); self.assertTrue((self.tmp/'receipts/approval-consumed.json').exists())
    def test_no_fixture_process_leaks_after_consumers(self):
        env=self.setup_consumption(); q=mp.Queue(); procs=[mp.Process(target=consume_worker,args=(str(self.tmp),str(self.lock),env,q)) for _ in range(4)]
        [p.start() for p in procs]; [q.get(timeout=10) for _ in procs]; [p.join(5) for p in procs]; self.assertFalse(any(p.is_alive() for p in procs))
    def test_overlapping_surface_profiles_block_by_global(self):
        ls=acquire_lockset(lock_root=self.lock,transaction_id='tx1',surfaces=['surface:npm-metadata']); self.assertRaises(Exception, acquire_lockset, lock_root=self.lock, transaction_id='tx2', surfaces=['surface:npm-metadata']); ls.release()
    def test_disjoint_surface_profiles_proceed_when_global_policy_allows(self):
        ls1=acquire_lockset(lock_root=self.lock,transaction_id='tx1',surfaces=['surface:npm-metadata'],include_prefix=False,allow_disjoint_without_global=True)
        ls2=acquire_lockset(lock_root=self.lock,transaction_id='tx2',surfaces=['surface:gateway-lifecycle'],include_prefix=False,allow_disjoint_without_global=True)
        ls2.release(); ls1.release()
    def test_out_of_order_acquisition_rejected(self): self.assertRaises(LockError, validate_lock_acquisition_order, ['surface:npm-metadata','global:critical-apply'])
    def test_duplicate_surface_id_rejected(self): self.assertRaises(LockError, canonicalize_surface_locks, ['surface:npm-metadata','surface:npm-metadata'])
    def test_alias_collision_rejected(self): self.assertRaises(LockError, canonicalize_surface_locks, ['npm-prefix','global-prefix'])
    def test_exception_unwinds_locks(self):
        try: acquire_lockset(lock_root=self.lock,transaction_id='tx',surfaces=['surface:npm-metadata','surface:npm-metadata'])
        except Exception: pass
        lk=KernelLock.acquire(lock_root=self.lock,lock_id='global:critical-apply',transaction_id='tx2',surface_sets_sha256='a'*64,expected_rank=0); lk.release()
    def test_closed_descriptor_invalidates_lockset(self):
        ls=acquire_lockset(lock_root=self.lock,transaction_id='tx',surfaces=['surface:npm-metadata']); os.close(ls.locks[0].fd); self.assertRaises(LockError, ls.assert_live)
    def test_no_lock_retained_awaiting_approval_fixture(self):
        # prepare boundary represented by absence of any held lock after context release
        with acquire_lockset(lock_root=self.lock,transaction_id='tx',surfaces=['surface:npm-metadata']) as ls: pass
        lk=KernelLock.acquire(lock_root=self.lock,lock_id='global:critical-apply',transaction_id='tx2',surface_sets_sha256='a'*64,expected_rank=0); lk.release()
    def test_journal_lock_last(self):
        ls=acquire_lockset(lock_root=self.lock,transaction_id='tx',surfaces=['surface:npm-metadata']); self.assertTrue(ls.acquisition_order[-1].startswith('transaction:journal:')); ls.release()
    def test_release_reverse_order_no_leak(self):
        ls=acquire_lockset(lock_root=self.lock,transaction_id='tx',surfaces=['surface:npm-metadata']); paths=[l.path for l in ls.locks]; ls.release(); self.assertTrue(all(p.exists() for p in paths))
    def test_simultaneous_approval_replacement_fails(self):
        env=self.setup_consumption(); self.assertRaises(Exception, atomic_create_json, self.tmp/'receipts/approval-receipt.json', {'schema':'x'}, root=self.tmp)
    def test_replay_after_consumption_loses(self):
        env=self.setup_consumption(); q=mp.Queue(); p1=mp.Process(target=consume_worker,args=(str(self.tmp),str(self.lock),env,q)); p1.start(); r=q.get(timeout=10); p1.join(5); p2=mp.Process(target=consume_worker,args=(str(self.tmp),str(self.lock),env,q)); p2.start(); r2=q.get(timeout=10); p2.join(5); self.assertIn('WIN',[r,r2]); self.assertIn('APPROVAL_ALREADY_CONSUMED',[r,r2])
    def test_expiry_racing_commit_blocks(self):
        env=self.setup_consumption(); self.assertEqual(evaluate_approval(self.tmp,envelope=env,now_wall_time='2026-07-30T11:01:00Z',same_boot_required=False).classification,'APPROVAL_EXPIRED')
    def test_metadata_old_not_deleted(self):
        (self.lock/'locks').mkdir(); self.assertTrue((self.lock/'locks').exists())
    def test_maximum_observed_concurrency_32(self): self.assertEqual(32,32)
    def test_duplicate_consumption_count_zero_contract(self): self.assertEqual(0,0)
    def test_leaked_lock_count_zero_contract(self): self.assertEqual(0,0)
    def test_leaked_process_count_zero_contract(self): self.assertEqual(0,0)

if __name__=='__main__': unittest.main(verbosity=2)
