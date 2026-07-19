from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from m25j.validators import ContractValidationError, validate_json_text
else:
    from .validators import ContractValidationError, validate_json_text
ROOT=Path(__file__).resolve().parent; FIX=ROOT/'fixtures'
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--strict', action='store_true'); ns=ap.parse_args(argv)
    results=[]; errors=[]
    for category in ['positive','negative','security']:
        for path in sorted((FIX/category).glob('*.json')):
            try:
                out=validate_json_text(path.read_text()); ok=(category=='positive')
                if not ok: errors.append({'path':str(path),'error':'expected failure but validated'})
                results.append({'path':str(path.relative_to(ROOT)),'fixtureCategory':category,'terminal':'PASS' if ok else 'UNEXPECTED_PASS','errorCodes':[] if ok else ['UNEXPECTED_PASS'],'schema':out['schema']})
            except ContractValidationError as exc:
                ok=(category!='positive')
                if not ok: errors.append({'path':str(path),'error':exc.code})
                results.append({'path':str(path.relative_to(ROOT)),'fixtureCategory':category,'terminal':'EXPECTED_FAIL' if ok else 'FAIL','errorCodes':[exc.code]})
    summary={'status':'PASS' if not errors else 'FAIL','positiveCount':sum(r['fixtureCategory']=='positive' for r in results),'negativeCount':sum(r['fixtureCategory']=='negative' for r in results),'securityCount':sum(r['fixtureCategory']=='security' for r in results),'errorCount':len(errors),'results':results}
    print(json.dumps(summary, indent=2, sort_keys=True)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
