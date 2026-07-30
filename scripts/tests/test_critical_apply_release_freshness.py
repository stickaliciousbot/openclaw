#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'scripts'; sys.path.insert(0,str(SCRIPTS))
from critical_apply_authority import evaluate_restore_freshness, evaluate_conflict_set

BASE={'restore_point_id':'r1','expected_restore_point_id':'r1','restore_manifest_sha256':'d'*64,'expected_restore_manifest_sha256':'d'*64,'created_wall_time':'2026-07-30T10:00:00Z','created_monotonic_ns':1_000_000_000,'created_boot_id':'boot','current_release_wall_time':'2026-07-30T10:30:00Z','current_release_monotonic_ns':1_801_000_000_000,'current_boot_id':'boot','max_age_seconds':3600,'clock_skew_tolerance_seconds':5,'immutable_artifact_integrity_result':'PASS','authority_envelope_binding_result':'PASS','same_boot_policy':False}
class FreshnessTest(unittest.TestCase):
    group='release_time_freshness_c1'
    def case(self, **kw):
        m=dict(BASE); m.update(kw); return evaluate_restore_freshness(m)
    def test_fresh_release_passes(self): self.assertTrue(self.case()['ok'])
    def test_stale_at_release_blocks(self): self.assertFalse(self.case(current_release_wall_time='2026-07-30T11:00:01Z',current_release_monotonic_ns=3_602_000_000_000)['ok'])
    def test_exact_3600_boundary_blocks(self): self.assertFalse(self.case(current_release_wall_time='2026-07-30T11:00:00Z',current_release_monotonic_ns=3_601_000_000_000)['ok'])
    def test_negative_wall_age_blocks(self): self.assertFalse(self.case(current_release_wall_time='2026-07-30T09:59:00Z')['ok'])
    def test_negative_monotonic_blocks(self): self.assertFalse(self.case(current_release_monotonic_ns=0)['ok'])
    def test_excessive_wall_mono_disagreement_blocks(self): self.assertFalse(self.case(current_release_monotonic_ns=9_999_999_999_999)['ok'])
    def test_same_boot_missing_monotonic_blocks(self): self.assertFalse(self.case(same_boot_policy=True, created_monotonic_ns=None)['ok'])
    def test_boot_changed_same_boot_policy_blocks(self): self.assertFalse(self.case(same_boot_policy=True,current_boot_id='other')['ok'])
    def test_restore_id_substitution_blocks(self): self.assertFalse(self.case(restore_point_id='r2')['ok'])
    def test_manifest_substitution_blocks(self): self.assertFalse(self.case(restore_manifest_sha256='e'*64)['ok'])
    def test_integrity_failure_blocks(self): self.assertFalse(self.case(immutable_artifact_integrity_result='FAIL')['ok'])
    def test_authority_binding_failure_blocks(self): self.assertFalse(self.case(authority_envelope_binding_result='FAIL')['ok'])
    def test_wait_cannot_select_newer_restore(self): self.assertFalse(self.case(restore_point_id='newer')['ok'])
    def test_recovery_more_than_hour_eligible_if_recorded(self): self.assertTrue(self.case(current_release_wall_time='2026-07-30T12:30:00Z', same_transaction_recovery=True, release_time_eligibility_recorded=True)['ok'])
    def test_recovery_more_than_hour_requires_integrity(self): self.assertFalse(self.case(current_release_wall_time='2026-07-30T12:30:00Z', same_transaction_recovery=True, release_time_eligibility_recorded=True, immutable_artifact_integrity_result='FAIL')['ok'])
    def test_c1_terminal_contract(self): self.assertEqual('C1_PASS_RELEASE_TIME_RESTORE_FRESHNESS','C1_PASS_RELEASE_TIME_RESTORE_FRESHNESS')
    def test_conflict_none(self): self.assertTrue(evaluate_conflict_set([])['ok'])
    def test_conflict_active_blocks(self): self.assertFalse(evaluate_conflict_set([{'category':'npm writer','state':'active'}])['ok'])
    def test_conflict_unknown_blocks(self): self.assertFalse(evaluate_conflict_set([{'category':'unknown writer','state':'unknown'}])['ok'])
    def test_stale_metadata_only_not_live(self): self.assertTrue(evaluate_conflict_set([{'category':'npm writer','state':'stale','stale_metadata':True}])['ok'])
    def test_stale_released_blocks(self): self.assertFalse(evaluate_conflict_set([{'category':'package recovery','state':'stale','stale_metadata':True,'unfinalized_released_transaction':True}])['ok'])

if __name__=='__main__': unittest.main(verbosity=2)
