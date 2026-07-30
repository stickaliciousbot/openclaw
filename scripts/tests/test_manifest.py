#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from critical_apply_atomic_io import atomic_create_json, atomic_replace_json, sha256_file  # noqa: E402
from critical_apply_journal import GENESIS_PREVIOUS_SHA256, JournalWriterToken, append_event, create_transaction_journal, event_from_parts, validate_journal, write_projections, read_boot_id  # noqa: E402
from critical_apply_manifest import (  # noqa: E402
    EXCLUDED_FROM_GOVERNED,
    NON_CIRCULAR_POLICY,
    build_evidence_manifest,
    build_manifest_object,
    classify_finalization_integrity,
    compute_code_bundle_digest,
    create_terminal_seal,
    verify_manifest_sidecar,
    verify_terminal_seal,
)
from critical_apply_contracts import Phase, Terminal  # noqa: E402


class ManifestSealTestCase(unittest.TestCase):
    group = "manifest_and_terminal_seal"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="m1-manifest-"))
        self.txid = "critical-apply-m1-manifest-20260730T000000Z-" + "b" * 32
        create_transaction_journal(self.tmp, transaction_id=self.txid)
        self.token = JournalWriterToken(self.txid, "writer-1", str(self.tmp.resolve()))
        (self.tmp / "receipts").mkdir(mode=0o700)
        self.payload = atomic_create_json(self.tmp / "receipts" / "payload.json", {"schema":"fixture.payload","value":1}, root=self.tmp)
        e = event_from_parts(self.txid, 1, "terminal", Phase.TERMINAL.value, previous_event_sha256=GENESIS_PREVIOUS_SHA256, payload_path=self.payload.relative_path, payload_sha256=self.payload.sha256, payload_byte_count=self.payload.byte_count, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value)
        append_event(self.tmp, e, writer_token=self.token)
        self.vj = validate_journal(self.tmp, transaction_id=self.txid)
        self.proj_digests = write_projections(self.tmp, self.vj)
        self.final_report = atomic_create_json(self.tmp / "final-report.json", {"schema":"critical_apply.final_report_fixture.v2","terminal":Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value}, root=self.tmp)
        self.code_paths = [SCRIPTS / "critical_apply_contracts.py", SCRIPTS / "critical_apply_atomic_io.py", SCRIPTS / "critical_apply_journal.py", SCRIPTS / "critical_apply_manifest.py"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def governed(self):
        return [self.tmp / "receipts" / "payload.json", self.tmp / "journal" / "events.jsonl", self.tmp / "journal" / "journal-head.json", self.tmp / "projections" / "transaction.json", self.tmp / "projections" / "status.json", self.tmp / "final-report.json"]

    def build_manifest(self):
        return build_evidence_manifest(self.tmp, governed_paths=self.governed(), code_bundle_paths=self.code_paths)

    def seal(self, manifest_result=None):
        manifest_result = manifest_result or self.build_manifest()
        bundle = compute_code_bundle_digest(self.code_paths)
        return create_terminal_seal(self.tmp, transaction_id=self.txid, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, journal_head_sha256=self.vj.committed_event_sha256, evidence_manifest_sha256=manifest_result.manifest_sha256, runner_code_bundle_sha256=bundle.sha256, boot_id=read_boot_id())

    def test_complete_valid_sealed_fixture(self):
        mr = self.build_manifest(); bundle=compute_code_bundle_digest(self.code_paths); self.seal(mr)
        ver = verify_terminal_seal(self.tmp, transaction_id=self.txid, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, journal_head_sha256=self.vj.committed_event_sha256, evidence_manifest_sha256=mr.manifest_sha256, runner_code_bundle_sha256=bundle.sha256)
        self.assertTrue(ver.ok)

    def test_manifest_excludes_itself(self):
        mr = self.build_manifest(); manifest = json.loads((self.tmp / "manifests" / "evidence-manifest.json").read_text())
        self.assertIn("manifests/evidence-manifest.json", manifest["exclusions"])
        self.assertFalse(any(e["relative_path"] == "manifests/evidence-manifest.json" for e in manifest["entries"]))

    def test_manifest_excludes_sidecar(self):
        self.build_manifest(); manifest = json.loads((self.tmp / "manifests" / "evidence-manifest.json").read_text())
        self.assertIn("manifests/evidence-manifest.sha256", manifest["exclusions"])

    def test_manifest_excludes_seal(self):
        self.build_manifest(); manifest = json.loads((self.tmp / "manifests" / "evidence-manifest.json").read_text())
        self.assertIn("terminal-seal.json", manifest["exclusions"])

    def test_manifest_policy_recorded(self):
        self.build_manifest(); manifest = json.loads((self.tmp / "manifests" / "evidence-manifest.json").read_text())
        self.assertEqual(manifest["policy"], NON_CIRCULAR_POLICY)

    def test_sidecar_verifies(self):
        self.build_manifest(); self.assertTrue(verify_manifest_sidecar(self.tmp))

    def test_manifest_without_sidecar_detected(self):
        self.build_manifest(); (self.tmp / "manifests" / "evidence-manifest.sha256").unlink()
        with self.assertRaises(Exception): verify_manifest_sidecar(self.tmp)

    def test_changed_manifest_detected_by_sidecar(self):
        self.build_manifest(); p=self.tmp/"manifests"/"evidence-manifest.json"; obj=json.loads(p.read_text()); obj["entries"]=[]; p.write_text(json.dumps(obj,sort_keys=True)+"\n")
        with self.assertRaises(Exception): verify_manifest_sidecar(self.tmp)

    def test_seal_binds_manifest(self):
        mr=self.build_manifest(); bundle=compute_code_bundle_digest(self.code_paths); self.seal(mr)
        ver=verify_terminal_seal(self.tmp, transaction_id=self.txid, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, journal_head_sha256=self.vj.committed_event_sha256, evidence_manifest_sha256="0"*64, runner_code_bundle_sha256=bundle.sha256)
        self.assertFalse(ver.ok)

    def test_seal_binds_journal_head(self):
        mr=self.build_manifest(); bundle=compute_code_bundle_digest(self.code_paths); self.seal(mr)
        self.assertFalse(verify_terminal_seal(self.tmp, transaction_id=self.txid, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, journal_head_sha256="1"*64, evidence_manifest_sha256=mr.manifest_sha256, runner_code_bundle_sha256=bundle.sha256).ok)

    def test_seal_binds_code_bundle(self):
        mr=self.build_manifest(); bundle=compute_code_bundle_digest(self.code_paths); self.seal(mr)
        self.assertFalse(verify_terminal_seal(self.tmp, transaction_id=self.txid, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, journal_head_sha256=self.vj.committed_event_sha256, evidence_manifest_sha256=mr.manifest_sha256, runner_code_bundle_sha256="2"*64).ok)

    def test_final_report_without_seal_holds(self):
        self.assertEqual(classify_finalization_integrity(final_report_exists=True, terminal_event_exists=False, terminal_seal_valid=False), "EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD")

    def test_terminal_event_without_seal_holds(self):
        self.assertEqual(classify_finalization_integrity(final_report_exists=False, terminal_event_exists=True, terminal_seal_valid=False), "EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD")

    def test_changed_governed_artifact_detected_by_new_manifest_sha(self):
        mr1=self.build_manifest(); (self.tmp/"receipts"/"payload.json").write_text('{"schema":"fixture.payload","value":2}\n'); mr2=self.build_manifest()
        self.assertNotEqual(mr1.manifest_sha256, mr2.manifest_sha256)

    def test_changed_journal_detected_by_new_manifest_sha(self):
        mr1=self.build_manifest(); (self.tmp/"journal"/"events.jsonl").write_text((self.tmp/"journal"/"events.jsonl").read_text()+"{}\n"); mr2=self.build_manifest()
        self.assertNotEqual(mr1.manifest_sha256, mr2.manifest_sha256)

    def test_changed_head_detected_by_new_manifest_sha(self):
        mr1=self.build_manifest(); head=self.tmp/"journal"/"journal-head.json"; obj=json.loads(head.read_text()); obj["note"]="changed"; head.write_text(json.dumps(obj,sort_keys=True)+"\n"); mr2=self.build_manifest()
        self.assertNotEqual(mr1.manifest_sha256, mr2.manifest_sha256)

    def test_changed_projection_detected_by_new_manifest_sha(self):
        mr1=self.build_manifest(); p=self.tmp/"projections"/"status.json"; obj=json.loads(p.read_text()); obj["status"]="BOGUS"; p.write_text(json.dumps(obj,sort_keys=True)+"\n"); mr2=self.build_manifest()
        self.assertNotEqual(mr1.manifest_sha256, mr2.manifest_sha256)

    def test_changed_code_bundle_detected(self):
        f=self.tmp/"code.py"; f.write_text("a=1\n"); os.chmod(f,0o600); b1=compute_code_bundle_digest([f]); f.write_text("a=2\n"); b2=compute_code_bundle_digest([f]); self.assertNotEqual(b1.sha256,b2.sha256)

    def test_duplicate_manifest_path_rejected(self):
        with self.assertRaises(Exception): build_evidence_manifest(self.tmp, governed_paths=[self.governed()[0], self.governed()[0]], code_bundle_paths=self.code_paths)

    def test_path_traversal_rejected(self):
        with self.assertRaises(Exception): build_evidence_manifest(self.tmp, governed_paths=[Path("../bad")], code_bundle_paths=self.code_paths)

    def test_symlinked_governed_artifact_rejected(self):
        link=self.tmp/"link.json"; link.symlink_to(self.tmp/"receipts"/"payload.json")
        with self.assertRaises(Exception): build_evidence_manifest(self.tmp, governed_paths=[link], code_bundle_paths=self.code_paths)

    def test_mode_policy_rejects_world_readable(self):
        p=self.tmp/"open.json"; p.write_text("{}\n"); os.chmod(p,0o644)
        with self.assertRaises(Exception): build_evidence_manifest(self.tmp, governed_paths=[p], code_bundle_paths=self.code_paths)

    def test_file_changed_while_hashing_rejected(self):
        real = sha256_file
        calls = {"n":0}
        def mutate(path):
            calls["n"] += 1
            if calls["n"] == 1 and Path(path).name == "payload.json":
                (self.tmp/"receipts"/"payload.json").write_text('{"schema":"fixture.payload","value":9}\n')
            return real(Path(path))
        with mock.patch("critical_apply_manifest.sha256_file", side_effect=mutate):
            with self.assertRaises(Exception): self.build_manifest()

    def test_seal_replacement_attempt_rejected(self):
        self.seal(self.build_manifest())
        with self.assertRaises(Exception): self.seal(self.build_manifest())

    def test_second_seal_creation_attempt_rejected(self):
        self.seal(self.build_manifest())
        mr=self.build_manifest(); bundle=compute_code_bundle_digest(self.code_paths)
        with self.assertRaises(Exception): create_terminal_seal(self.tmp, transaction_id=self.txid, terminal=Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, journal_head_sha256=self.vj.committed_event_sha256, evidence_manifest_sha256=mr.manifest_sha256, runner_code_bundle_sha256=bundle.sha256, boot_id=read_boot_id())

    def test_invalid_hash_rejected_for_seal(self):
        mr=self.build_manifest(); bundle=compute_code_bundle_digest(self.code_paths)
        with self.assertRaises(Exception): create_terminal_seal(self.tmp, transaction_id=self.txid, terminal="T", journal_head_sha256="bad", evidence_manifest_sha256=mr.manifest_sha256, runner_code_bundle_sha256=bundle.sha256, boot_id=read_boot_id())

    def test_absolute_outside_governed_path_rejected(self):
        outside=Path(tempfile.gettempdir())/"outside-m1-manifest.json"; outside.write_text("{}\n")
        try:
            with self.assertRaises(Exception): build_evidence_manifest(self.tmp, governed_paths=[outside], code_bundle_paths=self.code_paths)
        finally:
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
