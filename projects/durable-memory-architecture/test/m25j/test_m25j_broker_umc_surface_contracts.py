from __future__ import annotations
import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'projects/durable-memory-architecture/contracts'))
from m25j.canonical import canonicalize_contract, contract_sha256, validate_contract_hash, load_json_strict, CanonicalizationError
from m25j.validators import ContractValidationError, validate_contract, validate_json_text
FIX=ROOT/'projects/durable-memory-architecture/contracts/m25j/fixtures'

class BrokerUmcSurfaceTests(unittest.TestCase):
    def test_wrong_surface_forged_replay_denied(self):
        for name in ['wrong_surface_session_binding','forged_receipt','replayed_receipt_cross_surface']:
            with self.subTest(name=name):
                with self.assertRaises(ContractValidationError): validate_json_text((FIX/f'negative/{name}.json').read_text())
    def test_umc_success_requires_receipt(self):
        with self.assertRaisesRegex(ContractValidationError,'UMC_SUCCESS_WITHOUT_RECEIPT'):
            validate_json_text((FIX/'negative/umc_success_claim_without_receipt.json').read_text())
    def test_ssb_least_privilege_only_narrows(self):
        with self.assertRaisesRegex(ContractValidationError,'SSB_POLICY_WIDENING'):
            validate_json_text((FIX/'negative/ssb_policy_widening_grant.json').read_text())
    def test_context_bridge_privacy_and_no_authority(self):
        self.assertEqual(validate_json_text((FIX/'positive/context_bridge_projection_record.json').read_text())['validationTerminal'],'PASS')
        for name in ['context_bridge_raw_packet_content','context_bridge_authority_directive']:
            with self.subTest(name=name):
                with self.assertRaises(ContractValidationError): validate_json_text((FIX/f'negative/{name}.json').read_text())
if __name__=='__main__': unittest.main()
