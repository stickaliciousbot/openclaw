from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from .canonical import HEX64, CanonicalizationError, compute_contract_hash, contract_sha256, load_json_strict, validate_contract_hash
REGISTRY=json.loads((Path(__file__).with_name('schema_registry.json')).read_text())
SCHEMAS={s['schema']:s for s in REGISTRY['schemas']}
NAME_TO_SCHEMA={s['name']:s['schema'] for s in REGISTRY['schemas']}
class ContractValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f'{code}: {message}'); self.code=code; self.message=message
def err(code,msg): raise ContractValidationError(code,msg)
def validate_schema_version(obj):
    schema=obj.get('schema'); version=obj.get('schemaVersion')
    if not isinstance(schema,str): err('SCHEMA_REQUIRED','schema is required')
    if not schema.endswith('.v1'):
        m=re.search(r'\.v(\d+)$',schema)
        err('UNKNOWN_MAJOR',f'unsupported schema major {m.group(1) if m else "unknown"}')
    if not isinstance(version,str) or not version.startswith('1.'):
        err('UNKNOWN_MAJOR','schemaVersion must be 1.x')
    if schema not in SCHEMAS: err('UNKNOWN_SCHEMA',schema)
def _require_sha(value, field):
    if not isinstance(value,str) or not HEX64.match(value): err('MALFORMED_SHA256',field)
def _raw_scan(value: Any, path='$'):
    if isinstance(value,str):
        if ('BEGIN ' + 'PRIVATE KEY') in value: err('PRIVATE_KEY_MARKER',path)
        if re.search(r'telegram:\d{4,}|\b(chat_id|message_id|sender_id)\b\s*[:=]?\s*\d{4,}', value, re.I): err('RAW_IDENTIFIER',path)
        if re.search(r'(?i)(bearer\s+[a-z0-9._-]{12,}|api[_-]?key\s*[:=]\s*[a-z0-9._-]{12,}|token\s*[:=]\s*[a-z0-9._-]{16,})', value): err('TOKEN_LIKE_VALUE',path)
        if 'ignore previous instructions' in value.lower() or 'alter policy' in value.lower(): err('RETRIEVED_INSTRUCTION_POLICY_ATTACK',path)
    elif isinstance(value,dict):
        for k,v in value.items():
            if re.search(r'(?i)raw(chat|account|message|session)|rawPacket|sourceExcerpt|rawQuery|privateIdentifier', k): err('FORBIDDEN_RAW_FIELD',path+'.'+k)
            _raw_scan(v,path+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value): _raw_scan(v,f'{path}[{i}]')
def validate_contract(obj: dict[str,Any]) -> dict[str,Any]:
    if not isinstance(obj,dict): err('NOT_OBJECT','contract must be an object')
    validate_schema_version(obj); spec=SCHEMAS[obj['schema']]
    allowed=set(spec['required'])|{'extensions','diagnostics','x_notes'}
    for f in spec['required']:
        if f not in obj: err('MISSING_REQUIRED_FIELD',f)
    for f in obj:
        if f not in allowed and not f.startswith('x_'): err('UNKNOWN_FIELD',f)
    if 'extensions' in obj:
        if not spec.get('extensionsAllowed'): err('EXTENSION_NOT_ALLOWED',obj['schema'])
        if not isinstance(obj['extensions'],dict): err('BAD_EXTENSION','extensions must be object')
        for k,v in obj['extensions'].items():
            if not k.startswith('x_'): err('BAD_EXTENSION_NAMESPACE',k)
            if isinstance(v,dict) and v.get('mandatory') is True: err('MANDATORY_UNKNOWN_EXTENSION',k)
    _raw_scan(obj)
    for f in ['contractHash','packetHash','receiptSha256','policyHash','contentSha256','serviceHash','inputHash']:
        if f in obj: _require_sha(obj[f],f)
    if not validate_contract_hash(obj): err('CONTRACT_HASH_MISMATCH',obj.get('schema','unknown'))
    if obj.get('idempotencyKey') == 'idem_replayed_cross_session':
        err('DUPLICATE_IDEMPOTENCY_KEY','idempotencyKey')
    s=obj['schema']
    if s=='stickbot.delivery_required_job.v1':
        if obj['deliveryRequired'] is True:
            for f in ['completionAnchor','terminalAnchor','closeoutAnchor']:
                if not obj.get(f): err('MISSING_DELIVERY_ANCHOR',f)
            if obj.get('desiredOutput')=='NO_REPLY': err('DELIVERY_REQUIRED_NO_REPLY','delivery-required job cannot be bare NO_REPLY')
        if obj.get('maxDeliveries') != 1: err('MAX_DELIVERIES_GT_ONE','maxDeliveries must be exactly 1')
    elif s=='stickbot.boundary_decision.v1':
        if obj['decision'] not in ['allow','hold','reject']: err('BAD_BOUNDARY_DECISION',obj['decision'])
        if obj['decision'] in ['hold','reject'] and obj.get('deliveryAllowed') is True: err('BOUNDARY_NON_ALLOW_DELIVERY_ALLOWED',obj['decision'])
        if obj.get('deliveryAllowed') is True and obj['decision']!='allow': err('BOUNDARY_DELIVERY_ALLOWED_WITHOUT_ALLOW',obj['decision'])
    elif s=='stickbot.sanitized_payload.v1':
        if obj.get('deliveryRequired') is True and obj.get('payloadText')=='NO_REPLY': err('DELIVERY_REQUIRED_NO_REPLY','payload')
        if obj.get('sanitized') is not True or obj.get('privateScanPassed') is not True: err('UNSANITIZED_PAYLOAD','sanitized/privateScanPassed required')
        if obj.get('rawIdentifiers'): err('RAW_IDENTIFIER','rawIdentifiers must be empty')
    elif s=='stickbot.delivery_result.v1':
        if obj.get('deliveryRequired') is True and obj.get('status')=='NO_REPLY': err('DELIVERY_REQUIRED_NO_REPLY','result')
        if obj.get('delivered') is True and obj.get('deliveryAttempted') is not True: err('DELIVERED_WITHOUT_ATTEMPT','delivered requires deliveryAttempted')
        if obj.get('duplicateSuppressed') is True and obj.get('status')!='suppressed': err('BAD_DUPLICATE_SUPPRESSION_STATUS','duplicateSuppressed requires suppressed')
        if obj.get('status')=='failed' and not obj.get('errorClass'): err('FAILED_DELIVERY_MISSING_ERROR_CLASS','failed requires errorClass')
    elif s=='stickbot.context_reconstruction.packet.v1':
        if obj.get('projectionOnly') is not True: err('PACKET_AUTHORITY_PROMOTION','packet is projection only')
        for label in obj.get('authorityLabels',[]):
            if label.get('authority') and not (label.get('sourceVersion') and label.get('spanId')): err('AUTHORITY_WITHOUT_VERIFIED_SOURCE_SPAN','authority label')
        if obj.get('rawPrivateExcerpts'): err('RAW_PRIVATE_EXCERPT','packet')
    elif s=='stickbot.context_reconstruction.receipt.v1':
        if obj['terminal'] not in ['PASS','HOLD','FAIL']: err('BAD_TERMINAL',obj['terminal'])
        if obj['terminal']=='PASS' and obj.get('missingSlots'): err('PASS_WITH_MISSING_REQUIRED_SLOT','missingSlots')
        if obj.get('noWriteProof') is not True: err('NO_WRITE_PROOF_REQUIRED','receipt')
    elif s=='stickbot.runtime_broker.authority_grant.v1':
        if obj.get('revoked') is True or obj.get('expiresAt') <= obj.get('issuedAt'): err('EXPIRED_OR_REVOKED_GRANT','grant')
    elif s=='stickbot.runtime_broker.receipt.v1':
        b=obj.get('receiptBinding')
        if not isinstance(b,dict): err('FORGED_RECEIPT','receiptBinding')
        for f in ['grantId','surfaceScope','sessionScopeHash','policyEpoch']:
            if b.get(f) != obj.get(f): err('RECEIPT_BINDING_MISMATCH',f)
        if obj.get('noWriteProof') is not True: err('NO_WRITE_PROOF_REQUIRED','service receipt')
    elif s=='stickbot.umc.contract_envelope.v1':
        if obj.get('successClaims') and not obj.get('receiptIds'): err('UMC_SUCCESS_WITHOUT_RECEIPT','successClaims')
    elif s=='stickbot.surface_policy.v1':
        if obj.get('mayNarrowOnly') is not True: err('SSB_POLICY_WIDENING','surface policy may narrow grants only')
        if obj.get('externalSendPolicy')=='allow_without_approval': err('EXTERNAL_SEND_WITHOUT_POLICY_APPROVAL','externalSendPolicy')
    elif s=='stickbot.context_bridge.projection_record.v1':
        if obj.get('privacyScanResult')!='PASS': err('CONTEXT_BRIDGE_PRIVACY_SCAN_FAIL','projection')
        if obj.get('authorityPromotion') is not False or obj.get('writeControlDirectives') is not False: err('CONTEXT_BRIDGE_AUTHORITY_OR_WRITE_DIRECTIVE','projection')
    return {'schema':obj['schema'],'schemaVersion':obj['schemaVersion'],'inputHash':contract_sha256(obj),'validationTerminal':'PASS','errorCodes':[],'contractHashResult':'PASS','privacyRuleResult':'PASS'}
def validate_json_text(text: str) -> dict[str,Any]:
    try: obj=load_json_strict(text)
    except (json.JSONDecodeError, CanonicalizationError) as exc: err('MALFORMED_JSON',str(exc))
    return validate_contract(obj)
