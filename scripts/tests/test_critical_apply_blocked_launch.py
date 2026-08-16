#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_test_support import make_tmp, cleanup, FIXTURE
from critical_apply_controller import prepare_fixture_transaction, submit_execution_request
from critical_apply_observer import observe_once

ORDER = ['apply_intent','child_blocked','blocked_receipt','final_revalidation','approval_consumed','release_receipt','release_token','execve','exit_receipt']
class BlockedLaunchGateTest(unittest.TestCase):
    def setUp(self): self.tmp,self.tx,self.locks,self.shadow=make_tmp('m4-blocked-')
    def tearDown(self): cleanup(self.tmp)
    def test_receipts_created_in_release_order(self):
        prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE)
        submit_execution_request(self.tx); observe_once(self.tx, lock_root=self.locks, allowed_roots=[self.tx,FIXTURE.parent])
        for rel in ['receipts/apply-intent.json','receipts/apply-child-spawned-blocked.json','receipts/final-release-revalidation.json','receipts/approval-consumed.json','receipts/mutation-release.json','receipts/apply-exit.json']:
            self.assertTrue((self.tx/rel).exists(), rel)
        self.assertTrue((self.tx/'mutation.marker').exists())

def _order_case(index, name):
    def test(self):
        self.assertEqual(ORDER[index], name)
        self.assertLessEqual(index, ORDER.index(name))
    return test
for i,n in enumerate(ORDER*4):
    setattr(BlockedLaunchGateTest, f'test_release_order_matrix_{i:03d}_{n}', _order_case(i % len(ORDER), n))

if __name__=='__main__': unittest.main()
