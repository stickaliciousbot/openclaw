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
if __name__=='__main__': unittest.main()
