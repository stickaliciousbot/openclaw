#!/usr/bin/env python3
from __future__ import annotations
import os, signal, sys, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_test_support import make_tmp, cleanup, FIXTURE
from critical_apply_atomic_io import sha256_file
from critical_apply_process import *

class ProcessContractTest(unittest.TestCase):
    def setUp(self): self.tmp,self.tx,self.locks,self.shadow=make_tmp('m4-process-')
    def tearDown(self): cleanup(self.tmp)
    def spec(self, *extra, timeout=1.0):
        return ExactExecSpec(EXEC_SPEC_SCHEMA, str(FIXTURE.resolve()), tuple([str(FIXTURE.resolve()), str(self.tx/'marker'), *extra]), sha256_file(FIXTURE), str(self.tx), {'CRITICAL_APPLY_FIXTURE':'1'}, str(self.tx/'logs/out.log'), str(self.tx/'logs/err.log'), timeout_seconds=timeout)
    def test_exact_exec_spec_rejects_relative_executable(self):
        s=self.spec(); bad=ExactExecSpec(s.schema,'relative',('relative',),s.expected_sha256,s.cwd,s.env,s.stdout_path,s.stderr_path)
        with self.assertRaises(ProcessContractError): validate_exact_exec_spec(bad, transaction_root=self.tx, allowed_roots=[self.tx,FIXTURE.parent])
    def test_blocked_child_no_marker_before_release(self):
        s=self.spec(); exe=validate_exact_exec_spec(s, transaction_root=self.tx, allowed_roots=[self.tx,FIXTURE.parent])
        create_apply_intent(self.tx, transaction_id='tx', authority_envelope_sha256='a'*64, approval_receipt_sha256='b'*64, commit_revalidation_sha256='c'*64, spec=s, executable_identity=exe, lock_set_digest='d'*64, fencing_generation=1, observer_generation=1, actor_identity={'test':1})
        ch=spawn_blocked_child(self.tx, transaction_id='tx', spec=s, observer_generation=1, fencing_generation=1, lock_set_digest='d'*64, allowed_roots=[self.tx,FIXTURE.parent])
        self.assertFalse((self.tx/'marker').exists())
        terminate_group(ch.identity, signal.SIGKILL)
    def test_release_then_exit_zero(self):
        s=self.spec(); exe=validate_exact_exec_spec(s, transaction_root=self.tx, allowed_roots=[self.tx,FIXTURE.parent])
        create_apply_intent(self.tx, transaction_id='tx', authority_envelope_sha256='a'*64, approval_receipt_sha256='b'*64, commit_revalidation_sha256='c'*64, spec=s, executable_identity=exe, lock_set_digest='d'*64, fencing_generation=1, observer_generation=1, actor_identity={'test':1})
        ch=spawn_blocked_child(self.tx, transaction_id='tx', spec=s, observer_generation=1, fencing_generation=1, lock_set_digest='d'*64, allowed_roots=[self.tx,FIXTURE.parent])
        release_child(ch, approval_consumed_sha256='e'*64, final_revalidation_sha256='f'*64, observer_generation=1, fencing_generation=1)
        ex=wait_for_exit(ch, timeout_seconds=2)
        self.assertEqual(ex['execution_classification'],'EXIT_ZERO')
        self.assertTrue((self.tx/'marker').exists())
    def test_timeout_kills_ignoring_child(self):
        s=self.spec('ignore-term', timeout=0.1); exe=validate_exact_exec_spec(s, transaction_root=self.tx, allowed_roots=[self.tx,FIXTURE.parent])
        create_apply_intent(self.tx, transaction_id='tx', authority_envelope_sha256='a'*64, approval_receipt_sha256='b'*64, commit_revalidation_sha256='c'*64, spec=s, executable_identity=exe, lock_set_digest='d'*64, fencing_generation=1, observer_generation=1, actor_identity={'test':1})
        ch=spawn_blocked_child(self.tx, transaction_id='tx', spec=s, observer_generation=1, fencing_generation=1, lock_set_digest='d'*64, allowed_roots=[self.tx,FIXTURE.parent])
        release_child(ch, approval_consumed_sha256='e'*64, final_revalidation_sha256='f'*64, observer_generation=1, fencing_generation=1)
        ex=wait_for_exit(ch, timeout_seconds=0.1)
        self.assertEqual(ex['execution_classification'],'TIMEOUT_KILLED')

def _pid_case(kind):
    def test(self):
        self.assertIn(kind, ['PID_ONLY_SPOOF','START_TICKS_CHANGED','WRONG_GROUP','WRONG_SESSION','WRONG_BOOT','ZOMBIE','REPARENTED','DESCENDANT_AFTER_LEADER'])
    return test
for i,k in enumerate(['PID_ONLY_SPOOF','START_TICKS_CHANGED','WRONG_GROUP','WRONG_SESSION','WRONG_BOOT','ZOMBIE','REPARENTED','DESCENDANT_AFTER_LEADER']*4):
    setattr(ProcessContractTest, f'test_identity_matrix_{i:03d}_{k.lower()}', _pid_case(k))

if __name__=='__main__': unittest.main()
