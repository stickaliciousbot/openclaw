from __future__ import annotations
import json, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'projects/durable-memory-architecture/contracts'))
from m25j.canonical import canonicalize_contract, contract_sha256, validate_contract_hash, load_json_strict, CanonicalizationError
from m25j.validators import ContractValidationError, validate_contract, validate_json_text
FIX=ROOT/'projects/durable-memory-architecture/contracts/m25j/fixtures'

class DeliveryTests(unittest.TestCase):
    def test_no_reply_valid_for_quiet_job_only(self):
        quiet=json.loads((FIX/'positive/quiet_job_delivery_not_required.json').read_text())
        quiet['deliveryIntent']='NO_REPLY'; quiet['contractHash']='0'*64
        from m25j.canonical import compute_contract_hash; quiet['contractHash']=compute_contract_hash(quiet)
        self.assertEqual(validate_contract(quiet)['validationTerminal'],'PASS')
        req=json.loads((FIX/'positive/delivery_required_job_all_anchors.json').read_text()); req['deliveryIntent']='NO_REPLY'
        from m25j.canonical import compute_contract_hash; req['contractHash']=compute_contract_hash(req)
        with self.assertRaisesRegex(ContractValidationError,'DELIVERY_REQUIRED_NO_REPLY'): validate_contract(req)
    def test_boundary_hold_reject_cannot_authorize_delivery(self):
        for name in ['boundary_hold','boundary_reject']:
            obj=json.loads((FIX/f'positive/{name}.json').read_text()); obj['deliveryAllowed']=True
            from m25j.canonical import compute_contract_hash; obj['contractHash']=compute_contract_hash(obj)
            with self.assertRaisesRegex(ContractValidationError,'BOUNDARY_NON_ALLOW_DELIVERY_ALLOWED'): validate_contract(obj)
    def test_delivery_result_invariants(self):
        for name in ['delivered_true_without_attempt','duplicate_suppression_wrong_status','failed_delivery_missing_error_class']:
            with self.subTest(name=name):
                with self.assertRaises(ContractValidationError): validate_json_text((FIX/f'negative/{name}.json').read_text())
    def test_srtr_request_grant_receipt_valid_path(self):
        for name in ['surface_response_target_request_owner_direct','surface_response_target_grant_owner_direct','surface_response_target_receipt_resolved']:
            with self.subTest(name=name):
                self.assertEqual(validate_json_text((FIX/f'positive/{name}.json').read_text())['validationTerminal'],'PASS')
    def test_srtr_rejects_raw_target_markers_and_fallback(self):
        for name in ['target_request_raw_chat_id','target_request_raw_message_id','target_grant_raw_provider_target_id','target_request_fallback_target_field']:
            with self.subTest(name=name):
                with self.assertRaises(ContractValidationError): validate_json_text((FIX/f'negative/{name}.json').read_text())
    def test_srtr_enforces_verification_single_delivery_and_no_raw_receipt(self):
        for name in ['target_grant_without_identity_verification','target_grant_without_session_verification','target_grant_max_deliveries_gt_one','target_receipt_raw_target_exposed','target_receipt_resolved_without_identity','target_receipt_resolved_without_session']:
            with self.subTest(name=name):
                with self.assertRaises(ContractValidationError): validate_json_text((FIX/f'negative/{name}.json').read_text())
    def test_delivery_result_requires_target_grant_chain(self):
        for name in ['delivery_without_target_grant','delivery_target_idempotency_mismatch']:
            with self.subTest(name=name):
                with self.assertRaises(ContractValidationError): validate_json_text((FIX/f'negative/{name}.json').read_text())
if __name__=='__main__': unittest.main()
