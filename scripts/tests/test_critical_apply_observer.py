#!/usr/bin/env python3
from __future__ import annotations
import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_test_support import make_tmp, cleanup, FIXTURE
from critical_apply_controller import prepare_fixture_transaction, submit_execution_request, query_status
from critical_apply_observer import observe_once, observer_contract
from critical_apply_rehydrate import REHYDRATION_CLASSIFICATIONS

class ObserverIntegrationTest(unittest.TestCase):
    def setUp(self): self.tmp,self.tx,self.locks,self.shadow=make_tmp('m4-observer-')
    def tearDown(self): cleanup(self.tmp)
    def test_observer_executes_after_durable_request(self):
        prep=prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE)
        submit_execution_request(self.tx)
        res=observe_once(self.tx, lock_root=self.locks, allowed_roots=[self.tx, self.shadow, FIXTURE.parent])
        self.assertEqual(res['primary_command_executions'],1)
        self.assertEqual(res['approval_consumptions'],1)
        self.assertEqual(res['mutation_releases'],1)
        self.assertTrue((self.tx/'mutation.marker').exists())
    def test_controller_status_not_authoritative(self):
        prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE)
        st=query_status(self.tx)
        self.assertFalse(st['controller_authoritative'])
    def test_observer_contract_fixture_only(self):
        c=observer_contract(); self.assertTrue(c['fixture_only_in_m4']); self.assertFalse(c['production_install_authorised'])

def _make_case(clsname):
    def test(self):
        self.assertIn(clsname, REHYDRATION_CLASSIFICATIONS)
        self.assertTrue(clsname.startswith('REHYDRATED') or clsname.startswith('REHYDRATION'))
    return test
for i, cls in enumerate(REHYDRATION_CLASSIFICATIONS):
    setattr(ObserverIntegrationTest, f'test_rehydration_classification_declared_{i:02d}', _make_case(cls))

if __name__=='__main__': unittest.main()
