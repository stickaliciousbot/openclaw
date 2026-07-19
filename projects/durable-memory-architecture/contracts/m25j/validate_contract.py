from __future__ import annotations
import argparse, json, sys
from pathlib import Path
if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from m25j.validators import ContractValidationError, validate_json_text
else:
    from .validators import ContractValidationError, validate_json_text
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--schema'); ap.add_argument('--input', required=True); ap.add_argument('--fixture-category', default='unknown')
    ns=ap.parse_args(argv); path=Path(ns.input)
    try:
        result=validate_json_text(path.read_text()); result['fixtureCategory']=ns.fixture_category
        if ns.schema and result['schema'] != ns.schema: raise ContractValidationError('SCHEMA_MISMATCH', f"expected {ns.schema} got {result['schema']}")
        print(json.dumps(result, sort_keys=True)); return 0
    except ContractValidationError as exc:
        print(json.dumps({'schema':ns.schema,'inputHash':None,'validationTerminal':'FAIL','errorCodes':[exc.code],'contractHashResult':'UNKNOWN','privacyRuleResult':'UNKNOWN','fixtureCategory':ns.fixture_category}, sort_keys=True)); return 1
if __name__=='__main__': raise SystemExit(main())
