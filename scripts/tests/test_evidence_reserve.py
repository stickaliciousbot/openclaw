#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from critical_apply_atomic_io import (  # noqa: E402
    EvidenceIOError,
    classify_evidence_space_failure,
    create_evidence_reserve,
    minimal_emergency_receipt,
    release_evidence_reserve,
)
from critical_apply_manifest import build_evidence_manifest  # noqa: E402


class EvidenceReserveTestCase(unittest.TestCase):
    group = "evidence_reserve_enospc"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="m1-reserve-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reserve_creation(self):
        r = create_evidence_reserve(self.tmp, bytes_required=4096)
        self.assertEqual(r.path, "reserve/evidence-reserve.bin")
        self.assertTrue((self.tmp / r.path).is_file())

    def test_reserve_identity_verification(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        self.assertEqual(r.digest.mode, "0o600")
        self.assertGreater(r.digest.inode, 0)

    def test_allocation_method_classified(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        self.assertIn(r.allocation_method, {"posix_fallocate", "write_fsync_fallback"})

    def test_reserve_release(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        rel = release_evidence_reserve(r, transaction_root=self.tmp)
        self.assertTrue(rel.released)
        self.assertFalse((self.tmp / r.path).exists())

    def test_duplicate_release_idempotent(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        release_evidence_reserve(r, transaction_root=self.tmp)
        rel2 = release_evidence_reserve(r, transaction_root=self.tmp)
        self.assertTrue(rel2.already_released)

    def test_reserve_path_substitution_rejected(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        (self.tmp / r.path).unlink(); (self.tmp / r.path).mkdir()
        with self.assertRaises(EvidenceIOError): release_evidence_reserve(r, transaction_root=self.tmp)

    def test_reserve_symlink_rejected(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        (self.tmp / r.path).unlink(); (self.tmp / r.path).symlink_to(self.tmp / "other")
        with self.assertRaises(EvidenceIOError): release_evidence_reserve(r, transaction_root=self.tmp)

    def test_pre_release_enospc_policy_blocks_before_mutation(self):
        self.assertEqual(classify_evidence_space_failure("PRECHECK_PASS", mutation_released=False), "PRE_MUTATION_EVIDENCE_SPACE_HOLD_NO_APPROVAL_CONSUMED")

    def test_pre_release_inode_exhaustion_policy_blocks_before_mutation(self):
        self.assertIn("HOLD", classify_evidence_space_failure("PLAN_SEALED", mutation_released=False))

    def test_post_release_enospc_policy_degrades_after_mutation(self):
        self.assertEqual(classify_evidence_space_failure("MUTATION_RELEASED", mutation_released=True), "POST_MUTATION_EVIDENCE_DEGRADED_HOLD_NO_UNQUALIFIED_SUCCESS")

    def test_emergency_receipt_after_reserve_release(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024); release_evidence_reserve(r, transaction_root=self.tmp)
        receipt = minimal_emergency_receipt("MUTATION_RELEASED", "ENOSPC", reserve_released=True, journal_head={"seq": 1})
        self.assertTrue(receipt["evidence_degraded"])
        self.assertEqual(receipt["journal_head_preserved"], {"seq": 1})

    def test_failure_to_create_reserve_before_prepare(self):
        with self.assertRaises(EvidenceIOError): create_evidence_reserve(self.tmp, bytes_required=0)

    def test_failure_to_release_reserve_detected(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        with mock.patch("critical_apply_atomic_io.os.lstat", side_effect=PermissionError("blocked")):
            with self.assertRaises(PermissionError): release_evidence_reserve(r, transaction_root=self.tmp)

    def test_evidence_degradation_prevents_pass_wording(self):
        receipt = minimal_emergency_receipt("MUTATION_RELEASED", "ENOSPC", reserve_released=True, journal_head={})
        self.assertTrue(receipt["evidence_degraded"])
        self.assertNotIn("PASS", classify_evidence_space_failure("MUTATION_RELEASED", mutation_released=True))

    def test_reserve_excluded_from_manifest_after_release(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024); release_evidence_reserve(r, transaction_root=self.tmp)
        governed = []
        mr = build_evidence_manifest(self.tmp, governed_paths=governed, code_bundle_paths=[SCRIPTS / "critical_apply_atomic_io.py"])
        manifest = (self.tmp / "manifests" / "evidence-manifest.json").read_text()
        self.assertIn("reserve/evidence-reserve.bin", manifest)
        self.assertEqual(mr.entries_count, 0)

    def test_sparse_allocation_not_falsely_reported_when_short(self):
        with mock.patch("critical_apply_atomic_io.os.posix_fallocate", side_effect=OSError("no")):
            r = create_evidence_reserve(self.tmp, bytes_required=2048)
        self.assertGreaterEqual((self.tmp / r.path).stat().st_size, 2048)

    def test_reserve_root_must_be_explicit_on_release(self):
        r = create_evidence_reserve(self.tmp, bytes_required=1024)
        with self.assertRaises(TypeError): release_evidence_reserve(r)  # type: ignore[call-arg]

    def test_duplicate_reserve_create_rejected(self):
        create_evidence_reserve(self.tmp, bytes_required=1024)
        with self.assertRaises(EvidenceIOError): create_evidence_reserve(self.tmp, bytes_required=1024)


if __name__ == "__main__":
    unittest.main(verbosity=2)
