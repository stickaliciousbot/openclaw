from __future__ import annotations
import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'projects/durable-memory-architecture/contracts'))
from m25j.canonical import canonicalize_contract, contract_sha256, validate_contract_hash, load_json_strict, CanonicalizationError
from m25j.validators import ContractValidationError, validate_contract, validate_json_text
FIX=ROOT/'projects/durable-memory-architecture/contracts/m25j/fixtures'

class SchemaFixtureTests(unittest.TestCase):
    def test_every_positive_fixture_validates(self):
        files=sorted((FIX/'positive').glob('*.json')); self.assertGreaterEqual(len(files), 28)
        for p in files:
            with self.subTest(p=p.name): self.assertEqual(validate_json_text(p.read_text())['validationTerminal'],'PASS')
    def test_every_negative_fixture_fails(self):
        files=sorted((FIX/'negative').glob('*.json')); self.assertGreaterEqual(len(files), 24)
        for p in files:
            with self.subTest(p=p.name):
                with self.assertRaises(ContractValidationError): validate_json_text(p.read_text())
    def test_security_fixtures_fail(self):
        files=sorted((FIX/'security').glob('*.json')); self.assertGreaterEqual(len(files), 7)
        for p in files:
            with self.subTest(p=p.name):
                with self.assertRaises(ContractValidationError): validate_json_text(p.read_text())
    def test_srtr_schemas_are_registered(self):
        from m25j.validators import NAME_TO_SCHEMA
        self.assertEqual(NAME_TO_SCHEMA['SurfaceResponseTargetRequest'],'stickbot.surface_response_target.request.v1')
        self.assertEqual(NAME_TO_SCHEMA['SurfaceResponseTargetGrant'],'stickbot.surface_response_target.grant.v1')
        self.assertEqual(NAME_TO_SCHEMA['SurfaceResponseTargetReceipt'],'stickbot.surface_response_target.receipt.v1')
    def test_unsafe_realistic_telegram_pattern_removed_from_security_fixture(self):
        text=(FIX/'security/raw_telegram_identifier.json').read_text()
        prior_target_pattern='telegram:' + '123456789'
        prior_message_pattern='message_id=' + '41672'
        self.assertNotIn(prior_target_pattern, text)
        self.assertNotIn(prior_message_pattern, text)
        self.assertIn('<RAW_TELEGRAM_TARGET_ID_FORBIDDEN>', text)
    def test_required_fields_enforced_and_unknown_major_fails(self):
        obj=json.loads((FIX/'positive/sanitized_payload.json').read_text()); obj.pop('payloadType')
        with self.assertRaisesRegex(ContractValidationError,'MISSING_REQUIRED_FIELD'): validate_contract(obj)
        obj=json.loads((FIX/'positive/sanitized_payload.json').read_text()); obj['schema']='stickbot.sanitized_payload.v99'; obj['schemaVersion']='99.0.0'
        with self.assertRaisesRegex(ContractValidationError,'UNKNOWN_MAJOR'): validate_contract(obj)
if __name__=='__main__': unittest.main()
