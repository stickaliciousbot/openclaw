from __future__ import annotations
import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'projects/durable-memory-architecture/contracts'))
from m25j.canonical import canonicalize_contract, contract_sha256, validate_contract_hash, load_json_strict, CanonicalizationError
from m25j.validators import ContractValidationError, validate_contract, validate_json_text
FIX=ROOT/'projects/durable-memory-architecture/contracts/m25j/fixtures'

class CanonicalizationTests(unittest.TestCase):
    def test_deterministic_field_order_and_hash(self):
        a={'b':2,'a':'é','nested':{'z':1,'a':0}}
        b={'nested':{'a':0,'z':1},'a':'é','b':2}
        self.assertEqual(canonicalize_contract(a), canonicalize_contract(b))
        self.assertEqual(contract_sha256(a), contract_sha256(b))
    def test_semantic_difference_changes_hash(self):
        self.assertNotEqual(contract_sha256({'a':1}), contract_sha256({'a':2}))
    def test_self_hash_exclusion_rule(self):
        obj=json.loads((FIX/'positive/sanitized_payload.json').read_text())
        self.assertTrue(validate_contract_hash(obj))
        obj['payloadText']='changed'; self.assertFalse(validate_contract_hash(obj))
    def test_duplicate_key_and_float_rejected(self):
        with self.assertRaises(CanonicalizationError): load_json_strict('{"a":1,"a":2}')
        with self.assertRaises(CanonicalizationError): canonicalize_contract({'n':1.5})
if __name__=='__main__': unittest.main()
