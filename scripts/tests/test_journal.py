#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from critical_apply_journal import (  # noqa: E402
    GENESIS_PREVIOUS_SHA256,
    JournalClassification,
    JournalWriterToken,
    append_event,
    create_transaction_journal,
    encode_event_line,
    event_from_parts,
    event_hash,
    phase_terminal_fixture_events,
    rebuild_status_projection,
    rebuild_transaction_projection,
    validate_journal,
    verify_projection_parity,
    write_projections,
)
from critical_apply_atomic_io import atomic_create_json, atomic_replace_json, read_json_artifact, sha256_file  # noqa: E402
from critical_apply_contracts import Phase, Terminal, canonical_json_dumps  # noqa: E402


class JournalTestCase(unittest.TestCase):
    group = "journal_chain_and_projection_parity"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="m1-journal-"))
        self.txid = "critical-apply-m1-journal-20260730T000000Z-" + "a" * 32
        create_transaction_journal(self.tmp, transaction_id=self.txid)
        self.token = JournalWriterToken(self.txid, "writer-1", str(self.tmp.resolve()))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def event(self, phase=Phase.CREATED.value, event_type="phase"):
        return event_from_parts(self.txid, 1, event_type, phase, previous_event_sha256=GENESIS_PREVIOUS_SHA256)

    def append_n(self, n=2):
        out = []
        for i in range(n):
            out.append(append_event(self.tmp, self.event(Phase.CREATED.value if i == 0 else Phase.PREPARING.value), writer_token=self.token))
        return out

    def test_valid_empty_journal(self):
        v = validate_journal(self.tmp, transaction_id=self.txid)
        self.assertEqual(v.classification, JournalClassification.JOURNAL_VALID)
        self.assertEqual(v.committed_sequence, 0)

    def test_valid_genesis_append(self):
        r = append_event(self.tmp, self.event(), writer_token=self.token)
        self.assertEqual(r.committed_sequence, 1)
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_VALID)

    def test_multiple_valid_events(self):
        self.append_n(3)
        v = validate_journal(self.tmp, transaction_id=self.txid)
        self.assertEqual(v.committed_sequence, 3)
        self.assertEqual(v.classification, JournalClassification.JOURNAL_VALID)

    def test_event_hash_stable(self):
        e = self.event(); h1 = event_hash(e); h2 = event_hash(dict(reversed(list(e.items()))))
        self.assertEqual(h1, h2)

    def test_head_references_committed_hash(self):
        r = self.append_n(1)[0]
        head = read_json_artifact(self.tmp / "journal" / "journal-head.json", root=self.tmp)
        self.assertEqual(head["committed_event_sha256"], r.event_sha256)

    def test_tampered_historical_event(self):
        self.append_n(2)
        journal = self.tmp / "journal" / "events.jsonl"
        lines = journal.read_text().splitlines(); obj = json.loads(lines[0]); obj["event_sha256"] = "f" * 64; lines[0] = canonical_json_dumps(obj); journal.write_text("\n".join(lines)+"\n")
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_CHAIN_INVALID)

    def test_deleted_event_detected(self):
        self.append_n(2)
        journal = self.tmp / "journal" / "events.jsonl"
        journal.write_text(journal.read_text().splitlines(True)[0])
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA)

    def test_inserted_event_detected(self):
        self.append_n(1)
        journal = self.tmp / "journal" / "events.jsonl"
        journal.write_text(journal.read_text() + journal.read_text())
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL)

    def test_duplicate_sequence_detected(self):
        self.append_n(2)
        journal = self.tmp / "journal" / "events.jsonl"
        lines = journal.read_text().splitlines()
        obj = json.loads(lines[1]); obj["sequence"] = 1; obj["event_sha256"] = event_hash(obj)
        lines[1] = canonical_json_dumps(obj)
        journal.write_text("\n".join(lines) + "\n")
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_CHAIN_INVALID)

    def test_skipped_sequence_detected(self):
        self.append_n(2)
        journal = self.tmp / "journal" / "events.jsonl"
        lines = journal.read_text().splitlines(); obj = json.loads(lines[1]); obj["sequence"] = 3; obj["event_sha256"] = event_hash(obj); lines[1] = canonical_json_dumps(obj); journal.write_text("\n".join(lines)+"\n")
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_CHAIN_INVALID)

    def test_wrong_previous_hash_detected(self):
        self.append_n(2)
        journal = self.tmp / "journal" / "events.jsonl"
        lines = journal.read_text().splitlines(); obj = json.loads(lines[1]); obj["previous_event_sha256"] = "b"*64; obj["event_sha256"] = event_hash(obj); lines[1] = canonical_json_dumps(obj); journal.write_text("\n".join(lines)+"\n")
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_CHAIN_INVALID)

    def test_wrong_head_hash_detected(self):
        self.append_n(1)
        head = read_json_artifact(self.tmp / "journal" / "journal-head.json", root=self.tmp); head["committed_event_sha256"] = "c"*64
        atomic_replace_json(self.tmp / "journal" / "journal-head.json", head, root=self.tmp)
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_CHAIN_INVALID)

    def test_head_ahead_of_data_detected(self):
        self.append_n(1)
        head = read_json_artifact(self.tmp / "journal" / "journal-head.json", root=self.tmp); head["committed_journal_byte_offset"] += 9999
        atomic_replace_json(self.tmp / "journal" / "journal-head.json", head, root=self.tmp)
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA)

    def test_complete_uncommitted_tail_detected(self):
        self.append_n(1)
        committed = validate_journal(self.tmp, transaction_id=self.txid)
        tail = event_from_parts(self.txid, 2, "tail", Phase.PREPARING.value, previous_event_sha256=committed.committed_event_sha256)
        with (self.tmp / "journal" / "events.jsonl").open("ab") as f: f.write(encode_event_line(tail)); f.flush(); os.fsync(f.fileno())
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL)

    def test_torn_tail_detected(self):
        self.append_n(1)
        with (self.tmp / "journal" / "events.jsonl").open("ab") as f: f.write(b'{"schema"'); f.flush(); os.fsync(f.fileno())
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_TORN_TAIL)

    def test_wrong_transaction_id_detected(self):
        self.append_n(1)
        journal = self.tmp / "journal" / "events.jsonl"; lines = journal.read_text().splitlines(); obj=json.loads(lines[0]); obj["transaction_id"]="x" * len(obj["transaction_id"]); obj["event_sha256"]=event_hash(obj); lines[0]=canonical_json_dumps(obj); journal.write_text("\n".join(lines)+"\n")
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_IDENTITY_MISMATCH)

    def test_changed_journal_inode_detected(self):
        self.append_n(1)
        journal = self.tmp / "journal" / "events.jsonl"; data = journal.read_bytes(); replacement = self.tmp / "journal" / "events.tmp"; replacement.write_bytes(data); os.replace(replacement, journal)
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_IDENTITY_MISMATCH)

    def test_invalid_canonical_json_detected(self):
        self.append_n(1)
        (self.tmp / "journal" / "events.jsonl").write_text('{"a":1,"a":2}\n')
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA)

    def test_payload_changed_after_append(self):
        payload = atomic_create_json(self.tmp / "payload.json", {"schema":"payload","v":1}, root=self.tmp)
        e = event_from_parts(self.txid, 1, "payload", Phase.CREATED.value, previous_event_sha256=GENESIS_PREVIOUS_SHA256, payload_path=payload.relative_path, payload_sha256=payload.sha256, payload_byte_count=payload.byte_count)
        append_event(self.tmp, e, writer_token=self.token)
        (self.tmp / "payload.json").write_text('{"schema":"payload","v":2}\n')
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_TAMPERED)

    def test_payload_replaced_by_symlink(self):
        payload = atomic_create_json(self.tmp / "payload.json", {"schema":"payload","v":1}, root=self.tmp)
        e = event_from_parts(self.txid, 1, "payload", Phase.CREATED.value, previous_event_sha256=GENESIS_PREVIOUS_SHA256, payload_path=payload.relative_path, payload_sha256=payload.sha256, payload_byte_count=payload.byte_count)
        append_event(self.tmp, e, writer_token=self.token)
        (self.tmp / "payload.json").unlink(); (self.tmp / "payload.json").symlink_to(self.tmp / "other.json")
        self.assertEqual(validate_journal(self.tmp, transaction_id=self.txid).classification, JournalClassification.JOURNAL_TAMPERED)

    def test_rebuild_transaction_projection(self):
        self.append_n(2); v = validate_journal(self.tmp, transaction_id=self.txid); p = rebuild_transaction_projection(v)
        self.assertEqual(p["committed_sequence"], 2)

    def test_rebuild_status_projection(self):
        self.append_n(1); v = validate_journal(self.tmp, transaction_id=self.txid); p = rebuild_status_projection(v)
        self.assertEqual(p["status"], "IN_PROGRESS")

    def test_write_and_verify_projection_parity(self):
        self.append_n(1); v = validate_journal(self.tmp, transaction_id=self.txid); write_projections(self.tmp, v)
        self.assertTrue(verify_projection_parity(v, self.tmp / "projections" / "transaction.json").ok)

    def test_projection_manually_edited_detected(self):
        self.append_n(1); v = validate_journal(self.tmp, transaction_id=self.txid); write_projections(self.tmp, v)
        p = self.tmp / "projections" / "transaction.json"; obj=json.loads(p.read_text()); obj["event_count"]=99; p.write_text(json.dumps(obj, sort_keys=True)+"\n")
        self.assertFalse(verify_projection_parity(v, p).ok)

    def test_stale_projection_detected(self):
        self.append_n(1); v1=validate_journal(self.tmp, transaction_id=self.txid); write_projections(self.tmp, v1); self.append_n(1); v2=validate_journal(self.tmp, transaction_id=self.txid)
        self.assertFalse(verify_projection_parity(v2, self.tmp / "projections" / "transaction.json").ok)

    def test_missing_projection_rebuildable(self):
        self.append_n(1); v=validate_journal(self.tmp, transaction_id=self.txid)
        self.assertFalse(verify_projection_parity(v, self.tmp / "projections" / "transaction.json").ok)
        write_projections(self.tmp, v)
        self.assertTrue(verify_projection_parity(v, self.tmp / "projections" / "transaction.json").ok)

    def test_all_m0_phases_represented_by_fixture(self):
        events = phase_terminal_fixture_events(self.txid)
        self.assertEqual({e["phase"] for e in events if e["event_type"] == "phase_seen"}, {p.value for p in Phase})

    def test_all_m0_terminals_represented_by_fixture(self):
        events = phase_terminal_fixture_events(self.txid)
        self.assertEqual({e["terminal"] for e in events if e.get("terminal")}, {t.value for t in Terminal})

    def test_writer_token_root_mismatch_rejected(self):
        bad = JournalWriterToken(self.txid, "writer-1", "/tmp/not-root")
        with self.assertRaises(Exception): append_event(self.tmp, self.event(), writer_token=bad)

    def test_writer_token_transaction_mismatch_rejected(self):
        bad = JournalWriterToken("wrong", "writer-1", str(self.tmp.resolve()))
        with self.assertRaises(Exception): append_event(self.tmp, self.event(), writer_token=bad)

    def test_append_offset_mismatch_rejected(self):
        self.append_n(1)
        with (self.tmp / "journal" / "events.jsonl").open("ab") as f: f.write(b"{}\n")
        with self.assertRaises(Exception): append_event(self.tmp, self.event(), writer_token=self.token)

    def test_no_invalid_classification_is_pass(self):
        invalid = {JournalClassification.JOURNAL_TORN_TAIL, JournalClassification.JOURNAL_CHAIN_INVALID, JournalClassification.JOURNAL_TAMPERED, JournalClassification.JOURNAL_IDENTITY_MISMATCH, JournalClassification.JOURNAL_UNKNOWN}
        self.assertFalse(any("PASS" in x.value for x in invalid))


if __name__ == "__main__":
    unittest.main(verbosity=2)
