#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
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
    atomic_create_bytes,
    atomic_create_json,
    atomic_replace_bytes,
    atomic_replace_json,
    classify_temp_artifacts,
    read_json_artifact,
    sha256_file,
    validate_existing_regular,
)


class AtomicIOTestCase(unittest.TestCase):
    group = "atomic_immutable_replaceable_io"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="m1-atomic-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_child_failpoint(self, failpoint: str, op: str = "create"):
        code = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(SCRIPTS)!r})
from critical_apply_atomic_io import atomic_create_json, atomic_replace_json
root=Path({str(self.tmp)!r})
path=root/'artifact.json'
if {op!r} == 'replace':
    atomic_replace_json(path, {{'schema':'x','v':1}}, root=root)
    atomic_replace_json(path, {{'schema':'x','v':2}}, root=root, failpoint={failpoint!r})
else:
    atomic_create_json(path, {{'schema':'x','v':1}}, root=root, failpoint={failpoint!r})
"""
        return subprocess.run([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)

    def test_atomic_create_json_success(self):
        d = atomic_create_json(self.tmp / "a.json", {"schema": "x", "b": 2}, root=self.tmp)
        self.assertEqual(d.byte_count, len(b'{"b":2,"schema":"x"}\n'))
        self.assertEqual(read_json_artifact(self.tmp / "a.json", root=self.tmp)["b"], 2)

    def test_immutable_target_already_exists_rejected(self):
        atomic_create_json(self.tmp / "a.json", {"schema": "x"}, root=self.tmp)
        with self.assertRaises(EvidenceIOError):
            atomic_create_json(self.tmp / "a.json", {"schema": "x2"}, root=self.tmp)

    def test_atomic_replace_json_success(self):
        atomic_replace_json(self.tmp / "p.json", {"schema": "x", "v": 1}, root=self.tmp)
        atomic_replace_json(self.tmp / "p.json", {"schema": "x", "v": 2}, root=self.tmp)
        self.assertEqual(read_json_artifact(self.tmp / "p.json", root=self.tmp)["v"], 2)

    def test_atomic_create_bytes_success(self):
        d = atomic_create_bytes(self.tmp / "blob.bin", b"abc", root=self.tmp)
        self.assertEqual(d.sha256, sha256_file(self.tmp / "blob.bin"))

    def test_atomic_replace_bytes_success(self):
        atomic_replace_bytes(self.tmp / "blob.bin", b"old", root=self.tmp)
        d = atomic_replace_bytes(self.tmp / "blob.bin", b"new", root=self.tmp)
        self.assertEqual(d.byte_count, 3)
        self.assertEqual((self.tmp / "blob.bin").read_bytes(), b"new")

    def test_path_traversal_rejected(self):
        with self.assertRaises(EvidenceIOError):
            atomic_create_json(self.tmp / ".." / "x.json", {"schema": "x"}, root=self.tmp)

    def test_outside_root_rejected(self):
        with self.assertRaises(EvidenceIOError):
            atomic_create_json(Path(tempfile.gettempdir()) / "outside-m1.json", {"schema": "x"}, root=self.tmp)

    def test_symlink_target_rejected_for_create(self):
        target = self.tmp / "real.json"; target.write_text("{}\n")
        link = self.tmp / "link.json"; link.symlink_to(target)
        with self.assertRaises(EvidenceIOError):
            atomic_create_json(link, {"schema": "x"}, root=self.tmp)

    def test_symlink_target_rejected_for_replace(self):
        target = self.tmp / "real.json"; target.write_text("{}\n")
        link = self.tmp / "link.json"; link.symlink_to(target)
        with self.assertRaises(EvidenceIOError):
            atomic_replace_json(link, {"schema": "x"}, root=self.tmp)

    def test_directory_target_rejected_for_replace(self):
        d = self.tmp / "d.json"; d.mkdir()
        with self.assertRaises(EvidenceIOError):
            atomic_replace_json(d, {"schema": "x"}, root=self.tmp)

    def test_nan_rejected(self):
        with self.assertRaises(Exception):
            atomic_create_json(self.tmp / "nan.json", {"schema": "x", "n": float("nan")}, root=self.tmp)

    def test_duplicate_keys_rejected_on_read(self):
        p = self.tmp / "dup.json"; p.write_text('{"a":1,"a":2}\n')
        with self.assertRaises(Exception):
            read_json_artifact(p, root=self.tmp)

    def test_classify_abandoned_temp(self):
        p = self.tmp / ".a.json.critical-apply-tmp-deadbeef"
        p.write_text("partial")
        c = classify_temp_artifacts(self.tmp, root=self.tmp, target_name="a.json")
        self.assertEqual(c[0].classification, "CLASSIFIED_ABANDONED_TEMP")

    def test_mode_is_restrictive(self):
        d = atomic_create_json(self.tmp / "m.json", {"schema": "x"}, root=self.tmp)
        self.assertEqual(d.mode, "0o600")

    def test_regular_final_object(self):
        atomic_create_json(self.tmp / "r.json", {"schema": "x"}, root=self.tmp)
        _p, st, _rel = validate_existing_regular(self.tmp / "r.json", root=self.tmp)
        self.assertTrue(oct(st.st_mode & 0o777), "0o600")

    def test_eintr_write_retry(self):
        calls = {"n": 0}
        real_write = os.write
        def flaky(fd, data):
            calls["n"] += 1
            if calls["n"] == 1:
                raise InterruptedError()
            return real_write(fd, data)
        with mock.patch("critical_apply_atomic_io.os.write", side_effect=flaky):
            atomic_create_bytes(self.tmp / "eintr.bin", b"abc", root=self.tmp)
        self.assertEqual((self.tmp / "eintr.bin").read_bytes(), b"abc")

    def test_short_write_zero_rejected(self):
        with mock.patch("critical_apply_atomic_io.os.write", return_value=0):
            with self.assertRaises(EvidenceIOError):
                atomic_create_bytes(self.tmp / "short.bin", b"abc", root=self.tmp)


_FAILPOINTS = [
    "before_temp_create",
    "after_temp_create",
    "during_partial_write",
    "after_complete_write_before_file_fsync",
    "after_file_fsync",
    "immediately_before_publication",
    "immediately_after_publication",
    "before_parent_dir_fsync",
    "after_parent_dir_fsync",
    "before_final_digest_verification",
    "after_final_digest_verification",
]


def _make_failpoint_test(fp):
    def test(self):
        cp = self.run_child_failpoint(fp)
        self.assertNotEqual(cp.returncode, 0)
        p = self.tmp / "artifact.json"
        if p.exists():
            obj = json.loads(p.read_text())
            self.assertEqual(obj, {"schema": "x", "v": 1})
        temps = classify_temp_artifacts(self.tmp, root=self.tmp, target_name="artifact.json")
        for t in temps:
            self.assertIn(t.classification, {"CLASSIFIED_ABANDONED_TEMP", "UNSAFE_TEMP_NOT_REGULAR"})
    return test


for _fp in _FAILPOINTS:
    setattr(AtomicIOTestCase, f"test_crash_failpoint_{_fp}", _make_failpoint_test(_fp))


def _make_replace_failpoint_test(fp):
    def test(self):
        cp = self.run_child_failpoint(fp, op="replace")
        self.assertNotEqual(cp.returncode, 0)
        p = self.tmp / "artifact.json"
        if p.exists():
            self.assertIn(json.loads(p.read_text())["v"], {1, 2})
    return test


for _fp in ["after_file_fsync", "immediately_after_publication", "before_parent_dir_fsync"]:
    setattr(AtomicIOTestCase, f"test_replace_crash_failpoint_{_fp}", _make_replace_failpoint_test(_fp))


if __name__ == "__main__":
    unittest.main(verbosity=2)
