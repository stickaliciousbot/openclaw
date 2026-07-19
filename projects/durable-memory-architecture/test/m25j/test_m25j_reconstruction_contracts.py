from __future__ import annotations
import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'projects/durable-memory-architecture/contracts'))
from m25j.canonical import canonicalize_contract, contract_sha256, validate_contract_hash, load_json_strict, CanonicalizationError
from m25j.validators import ContractValidationError, validate_contract, validate_json_text
FIX=ROOT/'projects/durable-memory-architecture/contracts/m25j/fixtures'

class ReconstructionTests(unittest.TestCase):
    def test_required_slot_coverage_and_no_write(self):
        self.assertEqual(validate_json_text((FIX/'positive/context_reconstruction_receipt_pass.json').read_text())['validationTerminal'],'PASS')
        with self.assertRaisesRegex(ContractValidationError,'PASS_WITH_MISSING_REQUIRED_SLOT'):
            validate_json_text((FIX/'negative/reconstruction_pass_missing_required_slot.json').read_text())
    def test_authority_requires_verified_source_span(self):
        with self.assertRaisesRegex(ContractValidationError,'AUTHORITY_WITHOUT_VERIFIED_SOURCE_SPAN'):
            validate_json_text((FIX/'negative/packet_authority_without_verified_source_span.json').read_text())
    def test_packet_projection_only(self):
        packet=json.loads((FIX/'positive/context_reconstruction_packet.json').read_text()); self.assertTrue(packet['projectionOnly'])
if __name__=='__main__': unittest.main()
