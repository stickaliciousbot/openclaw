import importlib.util
import pathlib
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "context_bridge_actions_l5r_redact_provenance.py"
spec = importlib.util.spec_from_file_location("context_bridge_actions_l5r_redact_provenance", SCRIPT_PATH)
l5r = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(l5r)


class ContextBridgeActionsL5RRedactionTests(unittest.TestCase):
    def test_placeholder_is_deterministic_and_sanitized(self):
        a = l5r.placeholder("chat_id", "123456789")
        b = l5r.placeholder("chat_id", "123456789")
        c = l5r.placeholder("message_id", "123456789")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertTrue(a.startswith("redacted:chat_account_message_id:"))
        self.assertNotIn("123456789", a)

    def test_redacts_private_identifier_fields(self):
        obj = {"actions": [{"id": "act-safe", "status": "done", "channelOrigin": {"chat_id": "123456789", "message_id": "987654321"}}]}
        redacted, findings = l5r.redact_obj(obj)
        self.assertEqual(len(findings), 2)
        self.assertEqual(redacted["actions"][0]["id"], "act-safe")
        self.assertEqual(redacted["actions"][0]["status"], "done")
        self.assertTrue(redacted["actions"][0]["channelOrigin"]["chat_id"].startswith("redacted:chat_account_message_id:"))
        self.assertTrue(redacted["actions"][0]["channelOrigin"]["message_id"].startswith("redacted:chat_account_message_id:"))

    def test_semantic_signature_ignores_private_channel_origin(self):
        before = {"actions": [{"id": "act-safe", "status": "done", "title": "Keep", "createdAt": "t1", "updatedAt": "t2", "channelOrigin": {"chat_id": "123456789"}}]}
        after, _ = l5r.redact_obj(before)
        self.assertEqual(l5r.semantic_signature(before), l5r.semantic_signature(after))


if __name__ == "__main__":
    unittest.main()
