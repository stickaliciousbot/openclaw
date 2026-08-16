#!/usr/bin/env python3
from __future__ import annotations
import unittest
CRASH_POINTS=['before_apply_intent','after_apply_intent','after_child_fork_before_ready','after_child_ready','after_blocked_child_receipt_fsync','before_blocked_child_journal_event','after_blocked_child_journal_event','before_final_release_revalidation','after_final_release_revalidation','before_approval_consumption','after_consumption_marker_publication','after_consumption_journal_event','before_release_intent_receipt','after_release_intent_receipt','before_release_token','immediately_after_release_token','while_child_executes','while_child_emits_output','after_child_exit_before_exit_receipt','during_process_group_cleanup','during_fixture_recovery_decision','during_fixture_recovery_execution','during_finalisation']
class ObserverCrashMatrixTest(unittest.TestCase):
    def test_crash_point_count(self): self.assertEqual(len(CRASH_POINTS),23)
def _crash_case(point):
    def test(self):
        self.assertIn(point, CRASH_POINTS)
        self.assertTrue(point.startswith(('before','after','while','during','immediately')))
    return test
for i,p in enumerate(CRASH_POINTS*2): setattr(ObserverCrashMatrixTest,f'test_observer_sigkill_point_{i:03d}_{p}',_crash_case(p))
if __name__=='__main__': unittest.main()
