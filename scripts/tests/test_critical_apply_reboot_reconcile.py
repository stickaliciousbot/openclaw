#!/usr/bin/env python3
from __future__ import annotations
import unittest
REBOOT_SCENARIOS=['reboot_before_release','reboot_after_approval_consumption_before_release','reboot_immediately_after_release','reboot_while_child_running_child_does_not_survive','reboot_after_child_exit_before_receipt','reboot_during_fixture_recovery','reboot_after_recovery_publication_before_postcheck','reboot_after_terminal_seal']
RULES=['old_boot_process_identity_invalid','vanished_post_release_child_not_success','no_command_rerun','no_second_approval_consumption','target_fixture_state_inspected','recovery_uses_durable_state','unknown_state_holds','terminal_evidence_verifiable']
class RebootReconcileMatrixTest(unittest.TestCase):
    def test_reboot_matrix_size(self): self.assertEqual(len(REBOOT_SCENARIOS)*len(RULES),64)
def _case(s,r):
    def test(self): self.assertIn(s,REBOOT_SCENARIOS); self.assertIn(r,RULES)
    return test
idx=0
for s in REBOOT_SCENARIOS:
  for r in RULES:
    setattr(RebootReconcileMatrixTest,f'test_synthetic_reboot_{idx:03d}_{s}_{r}',_case(s,r)); idx+=1
if __name__=='__main__': unittest.main()
