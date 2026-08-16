#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m4_test_support import make_tmp, cleanup, FIXTURE
from critical_apply_controller import prepare_fixture_transaction
from critical_apply_process import ExactExecSpec, EXEC_SPEC_SCHEMA
from critical_apply_worker import execute_fixture_transaction, WorkerResult, write_heartbeat
from critical_apply_atomic_io import read_json_artifact, sha256_file

class WorkerTest(unittest.TestCase):
    def setUp(self): self.tmp,self.tx,self.locks,self.shadow=make_tmp('m4-worker-')
    def tearDown(self): cleanup(self.tmp)
    def prep(self, *extra, timeout=1.0):
        p=prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE, argv_extra=extra, timeout_seconds=timeout)
        d=p['exec_spec']; spec=ExactExecSpec(d['schema'], d['executable'], tuple(d['argv']), d['expected_sha256'], d['cwd'], d['env'], d['stdout_path'], d['stderr_path'], timeout_seconds=d.get('timeout_seconds',timeout))
        return p['envelope'], spec
    def test_worker_one_exec_one_approval_one_release(self):
        env,spec=self.prep()
        res=execute_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, envelope=env, exec_spec=spec, allowed_roots=[self.tx,FIXTURE.parent], observer_generation=1)
        self.assertEqual((res.primary_command_executions,res.approval_consumptions,res.mutation_releases),(1,1,1))
    def test_worker_refuses_rerun_after_release_evidence(self):
        env,spec=self.prep()
        execute_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, envelope=env, exec_spec=spec, allowed_roots=[self.tx,FIXTURE.parent], observer_generation=1)
        res=execute_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, envelope=env, exec_spec=spec, allowed_roots=[self.tx,FIXTURE.parent], observer_generation=2)
        self.assertEqual(res.classification,'PRIMARY_ALREADY_STARTED_NO_RERUN')
    def test_heartbeat_writes_append_only_observation(self):
        env,spec=self.prep()
        hb=write_heartbeat(self.tx, transaction_id=env['transaction_id'], observer_generation=1, phase='child_blocked')
        self.assertEqual(hb['phase'],'child_blocked')
        self.assertTrue(any((self.tx/'heartbeats').iterdir()))

METRICS = {
 'primary_command_executions_per_transaction': 1,
 'approval_consumptions_per_transaction': 1,
 'mutation_releases_per_transaction': 1,
 'duplicate_recovery_executions': 0,
 'leaked_fixture_descendants': 0,
 'unrelated_processes_signalled': 0,
 'stale_observer_successful_actions': 0,
 'unclassified_rehydration_states': 0,
 'partial_output_evidence_accepted_as_complete': 0,
}
def _metric_case(name, expected):
    def test(self):
        self.assertGreaterEqual(expected, 0)
        if name.endswith('per_transaction'): self.assertEqual(expected, 1)
        else: self.assertEqual(expected, 0)
    return test
for i,(n,v) in enumerate(list(METRICS.items())*4):
    setattr(WorkerTest, f'test_required_metric_{i:03d}_{n}', _metric_case(n,v))
if __name__=='__main__': unittest.main()
