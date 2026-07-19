from __future__ import annotations
import hashlib, json, math, re
from typing import Any
class CanonicalizationError(ValueError): pass
HEX64=re.compile(r'^[0-9a-f]{64}$')
def _pairs(pairs):
    seen=set(); out={}
    for k,v in pairs:
        if k in seen: raise CanonicalizationError(f'duplicate JSON key: {k}')
        seen.add(k); out[k]=v
    return out
def load_json_strict(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_pairs)
def _walk(value: Any, path='$') -> None:
    if isinstance(value, float):
        raise CanonicalizationError(f'floating point numbers are outside the M25J exact-number subset at {path}')
    if isinstance(value, dict):
        for k,v in value.items():
            if not isinstance(k,str): raise CanonicalizationError(f'non-string key at {path}')
            _walk(v, path+'.'+k)
    elif isinstance(value, list):
        for i,v in enumerate(value): _walk(v, f'{path}[{i}]')
def canonicalize_contract(value: Any) -> str:
    _walk(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def contract_sha256(value: Any) -> str:
    return hashlib.sha256(canonicalize_contract(value).encode('utf-8')).hexdigest()
def hash_preimage(value: dict[str, Any], hash_field='contractHash') -> dict[str, Any]:
    return {k:v for k,v in value.items() if k != hash_field}
def compute_contract_hash(value: dict[str, Any]) -> str:
    return contract_sha256(hash_preimage(value, 'contractHash'))
def validate_contract_hash(value: dict[str, Any]) -> bool:
    expected=value.get('contractHash')
    return isinstance(expected,str) and bool(HEX64.match(expected)) and expected == compute_contract_hash(value)
