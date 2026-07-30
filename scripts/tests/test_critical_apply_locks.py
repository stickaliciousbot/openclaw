#!/usr/bin/env python3
from __future__ import annotations
import fcntl, os, shutil, sys, tempfile, unittest, pickle
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'scripts'; sys.path.insert(0,str(SCRIPTS))
from critical_apply_locks import *  # noqa
from critical_apply_contracts import is_sha256

class KernelLocksTest(unittest.TestCase):
    group='kernel_locks_order_exclusion'
    def setUp(self): self.tmp=Path(tempfile.mkdtemp(prefix='m2-locks-'))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def test_acquire_global_lock(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); lk.assert_held(); lk.release()
    def test_contention_blocks(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0)
        with self.assertRaises(LockAcquireBlocked): KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx2',surface_sets_sha256='a'*64,expected_rank=0)
        lk.release()
    def test_release_idempotent(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); lk.release(); lk.release(); self.assertTrue(lk.released)
    def test_use_after_release_rejected(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); lk.release(); self.assertRaises(LockError, lk.assert_held)
    def test_fd_cloexec_set(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); self.assertTrue(fcntl.fcntl(lk.fd, fcntl.F_GETFD)&fcntl.FD_CLOEXEC); lk.release()
    def test_pickle_rejected(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); self.assertTrue(pickle_roundtrip_rejected(lk)); lk.release()
    def test_lock_receipt_not_authority(self):
        with self.assertRaises(LockError): assert_lock_receipt_not_authority({'lock_id':'global:critical-apply'})
    def test_invalid_lock_id_traversal(self): self.assertRaises(LockError, canonical_lock_id, '../x')
    def test_unknown_lock_id_rejected(self): self.assertRaises(LockError, canonical_lock_id, 'wildcard:*')
    def test_alias_collision_rejected(self): self.assertRaises(LockError, canonicalize_surface_locks, ['npm-prefix','global-prefix'])
    def test_duplicate_surface_rejected(self): self.assertRaises(LockError, canonicalize_surface_locks, ['surface:npm-metadata','surface:npm-metadata'])
    def test_surface_order_canonicalised(self): self.assertEqual(canonicalize_surface_locks(['surface:npm-metadata','surface:gateway-lifecycle']), ('surface:gateway-lifecycle','surface:npm-metadata'))
    def test_surface_digest_stable(self): self.assertEqual(surface_set_digest(['surface:npm-metadata','surface:gateway-lifecycle']), surface_set_digest(['surface:gateway-lifecycle','surface:npm-metadata']))
    def test_rank_global(self): self.assertEqual(lock_rank('global:critical-apply'),0)
    def test_rank_prefix(self): self.assertEqual(lock_rank('package-manager:global-prefix'),1)
    def test_rank_surface(self): self.assertEqual(lock_rank('surface:npm-metadata'),2)
    def test_rank_journal(self): self.assertEqual(lock_rank('transaction:journal'),3)
    def test_expected_rank_mismatch(self): self.assertRaises(LockError, KernelLock.acquire, lock_root=self.tmp, lock_id='global:critical-apply', transaction_id='tx', surface_sets_sha256='a'*64, expected_rank=2)
    def test_bad_surface_hash_rejected(self): self.assertRaises(LockError, KernelLock.acquire, lock_root=self.tmp, lock_id='global:critical-apply', transaction_id='tx', surface_sets_sha256='bad', expected_rank=0)
    def test_lockset_acquires_all_ordered(self):
        ls=acquire_lockset(lock_root=self.tmp,transaction_id='tx',surfaces=['surface:npm-metadata','surface:gateway-lifecycle']); self.assertTrue(ls.acquisition_order[-1].startswith('transaction:journal:')); ls.release()
    def test_lockset_digest_sha(self):
        ls=acquire_lockset(lock_root=self.tmp,transaction_id='tx',surfaces=['surface:npm-metadata']); self.assertTrue(is_sha256(ls.digest)); ls.release()
    def test_lockset_release_invalidates(self):
        ls=acquire_lockset(lock_root=self.tmp,transaction_id='tx',surfaces=['surface:npm-metadata']); ls.release(); self.assertRaises(LockError, ls.assert_live)
    def test_closed_descriptor_invalidates(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); os.close(lk.fd); self.assertRaises(LockError, lk.assert_held)
    def test_symlink_root_rejected(self):
        d=self.tmp/'real'; d.mkdir(); l=self.tmp/'link'; l.symlink_to(d); self.assertRaises(Exception, KernelLock.acquire, lock_root=l, lock_id='global:critical-apply', transaction_id='tx', surface_sets_sha256='a'*64, expected_rank=0)
    def test_metadata_only_unlocked_not_live(self):
        lk=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx',surface_sets_sha256='a'*64,expected_rank=0); path=lk.path; lk.release(); self.assertTrue(path.exists()); lk2=KernelLock.acquire(lock_root=self.tmp,lock_id='global:critical-apply',transaction_id='tx2',surface_sets_sha256='a'*64,expected_rank=0); lk2.release()
    def test_stale_holder_requires_reconciliation(self): self.assertEqual(classify_stale_holder(live_lock_held=False,old_metadata=True,unfinalized_mutation_released=False,reconciliation_receipt=None),'STALE_HOLDER_RECONCILIATION_REQUIRED')
    def test_live_held_blocks(self): self.assertEqual(classify_stale_holder(live_lock_held=True,old_metadata=True,unfinalized_mutation_released=False,reconciliation_receipt=None),'LIVE_HELD_KERNEL_LOCK_BLOCKS')
    def test_unfinalized_released_blocks(self): self.assertEqual(classify_stale_holder(live_lock_held=False,old_metadata=False,unfinalized_mutation_released=True,reconciliation_receipt=None),'UNFINALIZED_RELEASED_TRANSACTION_BLOCKS')
    def test_valid_fixture_reconciliation(self): self.assertEqual(classify_stale_holder(live_lock_held=False,old_metadata=True,unfinalized_mutation_released=False,reconciliation_receipt={'schema':'critical_apply.stale_holder_reconciliation.v2','fixture_only':True,'journal_valid':True,'holder_gone':True,'mutation_child_remaining':False}),'STALE_HOLDER_RECONCILED_FIXTURE_ONLY')
    def test_invalid_fixture_reconciliation(self): self.assertEqual(classify_stale_holder(live_lock_held=False,old_metadata=True,unfinalized_mutation_released=False,reconciliation_receipt={'schema':'critical_apply.stale_holder_reconciliation.v2'}),'STALE_HOLDER_RECONCILIATION_INVALID')
    def test_fencing_generation_increments(self):
        a=issue_fencing(self.tmp,'tx1'); b=issue_fencing(self.tmp,'tx2'); self.assertGreater(b.generation,a.generation)
    def test_token_hash_only_sha(self): self.assertTrue(is_sha256(issue_fencing(self.tmp,'tx').token_sha256))
    def test_token_256_bits_hex_not_in_receipt(self):
        c=issue_fencing(self.tmp,'tx'); self.assertEqual(len(c._token),64); self.assertNotIn(c._token, str(c.to_receipt()))
    def test_old_token_rejected_after_reacquire(self):
        a=issue_fencing(self.tmp,'tx1'); issue_fencing(self.tmp,'tx2'); self.assertRaises(LockError, validate_fencing_current, self.tmp, a)
    def test_wrong_transaction_token_rejected(self):
        a=issue_fencing(self.tmp,'tx1'); self.assertRaises(LockError, a.assert_active, lock_root=self.tmp, transaction_id='tx2')
    def test_wrong_root_token_rejected(self):
        a=issue_fencing(self.tmp,'tx1'); other=Path(tempfile.mkdtemp(prefix='m2-other-'))
        try: self.assertRaises(LockError, a.assert_active, lock_root=other, transaction_id='tx1')
        finally: shutil.rmtree(other, ignore_errors=True)
    def test_corrupt_generation_blocks(self):
        p=self.tmp/'fencing'; p.mkdir(); (p/'generation.json').write_text('{"schema":"bad","generation":"x"}\n'); self.assertRaises(LockError, issue_fencing, self.tmp, 'tx')

if __name__=='__main__': unittest.main(verbosity=2)
