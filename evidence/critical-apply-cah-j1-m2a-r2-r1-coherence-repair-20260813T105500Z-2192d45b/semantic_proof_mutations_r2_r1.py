#!/usr/bin/env python3
from pathlib import Path
import copy,hashlib,json,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parent
DESIGN=Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-r2-r1-coherence-repair-2026-08-13.md')
sys.path.insert(0,str(ROOT));from validate_m2a_r2 import validate
def load(p):return json.loads(Path(p).read_text())
def dump(p,o):Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
CASES=[]
def c(i,f,fn,needle):CASES.append((i,f,fn,needle))
def proof(o,pid):return next(p for p in o['canonical_proofs']+o['artifact_lifecycle_proofs'] if p['id']==pid)
# Authority-role and design semantic attacks.
c('S01_FINAL_HASH_REPLACED_BY_PRELIM','R1-AUTHORITY-ROLES.json',lambda o:o['authoritative_finalized_r1_independent_manifest'].update(sha256='019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b'),'authority_role_coherence')
c('S02_SUPERSEDED_MARKED_AUTHORITY','R1-AUTHORITY-ROLES.json',lambda o:o['superseded_preliminary_r1_manifest'].update(authority=True),'authority_role_coherence')
c('S03_SUPERSEDED_GIVEN_PATH','R1-AUTHORITY-ROLES.json',lambda o:o['superseded_preliminary_r1_manifest'].update(path='evidence/fake/EVIDENCE-SHA256.txt'),'authority_role_coherence')
c('S04_SEALED_R1_USES_PRELIM','IMMUTABLE-INPUT-SEALS.json',lambda o:o['inputs']['r1_independent_hold_manifest'].update(sha256='019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b'),'authority_role_coherence')
c('S05_DESIGN_ROLE_CONTRADICTION','DESIGN',lambda p:p.write_text(p.read_text()+'\n019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b is authoritative.\n'),'authority_role_coherence')
# Pre-root / pre-lease / epoch families.
c('S06_T00_BEFORE_FAKE_COMMITTED_EPOCH','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T00-BEFORE_COMMIT').update(required_authoritydb_epoch='exact committed supervisor epoch'),'proof_semantic_inventory')
c('S07_T00_BEFORE_FAKE_ACTIVE_FENCE','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T00-BEFORE_COMMIT').update(required_authoritydb_fence='active exact scope fencing token'),'proof_semantic_inventory')
c('S08_T00_AFTER_FAKE_CAS','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T00-AFTER_COMMIT').update(required_cas_refs=['CAS_FAKE']),'proof_semantic_inventory')
c('S09_T01_BEFORE_WRONG_HEAD','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T01-BEFORE_COMMIT').update(required_journal_hashes=['CURRENT_HEAD=sha256(REGISTER_TRANSACTION_ROOT event bytes)']),'proof_semantic_inventory')
c('S10_T02_AFTER_EPOCH_ABSENT','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T02-AFTER_COMMIT').update(required_authoritydb_epoch='NONE_EPOCH_NOT_COMMITTED'),'proof_semantic_inventory')
c('S11_T04_AFTER_PREMATURE_FENCE','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T04-AFTER_COMMIT').update(required_authoritydb_fence='ACTIVE_FENCE=fake'),'proof_semantic_inventory')
# Reservation / bind / activation distinctions.
c('S12_T05_AFTER_ACTIVE_NOT_RESERVED','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T05-AFTER_COMMIT').update(required_authoritydb_fence='ACTIVE_FENCE=fake'),'proof_semantic_inventory')
c('S13_T06_AFTER_RESERVED_NOT_BOUND','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T06-AFTER_COMMIT').update(required_authoritydb_fence='RESERVED_FENCE=fake'),'proof_semantic_inventory')
c('S14_T07_BEFORE_ACTIVE_TOO_EARLY','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T07-BEFORE_COMMIT').update(required_authoritydb_state='AUTHORITYDB=SCOPE_LEASE_ACTIVE_EXACT_OWNER'),'proof_semantic_inventory')
c('S15_T07_AFTER_BOUND_NOT_ACTIVE','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T07-AFTER_COMMIT').update(required_authoritydb_fence='BOUND_FENCE=fake'),'proof_semantic_inventory')
# CAS phase families.
c('S16_T03_BEFORE_ENVELOPE_CAS_EARLY','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T03-BEFORE_COMMIT').update(required_cas_refs=['CAS_INGRESS_ENVELOPE=sha256(canonical ingress envelope bytes)']),'proof_semantic_inventory')
c('S17_T03_AFTER_ENVELOPE_CAS_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T03-AFTER_COMMIT').update(required_cas_refs=[]),'proof_semantic_inventory')
c('S18_T10_BEFORE_CHILD_RESULT_EARLY','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T10-BEFORE_COMMIT')['required_cas_refs'].append('CAS_CHILD_RESULT=fake'),'proof_semantic_inventory')
c('S19_T10_AFTER_CHILD_RESULT_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T10-AFTER_COMMIT').update(required_cas_refs=['CAS_INGRESS_ENVELOPE=sha256(canonical ingress envelope bytes)']),'proof_semantic_inventory')
c('S20_T11_AFTER_EXECUTION_EVIDENCE_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T11-AFTER_COMMIT').update(required_cas_refs=proof(o,'RP-T11-AFTER_COMMIT')['required_cas_refs'][:-1]),'proof_semantic_inventory')
c('S21_T16_AFTER_TERMINAL_SEAL_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T16-AFTER_COMMIT').update(required_cas_refs=proof(o,'RP-T16-AFTER_COMMIT')['required_cas_refs'][:-1]),'proof_semantic_inventory')
# Release/closed authority distinctions.
c('S22_T19_AFTER_RELEASED_TOO_EARLY','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T19-AFTER_COMMIT').update(required_authoritydb_state='AUTHORITYDB=SCOPE_LEASE_RELEASED_EXACT'),'proof_semantic_inventory')
c('S23_T20_AFTER_ACTIVE_FENCE_RETAINED','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T20-AFTER_COMMIT').update(required_authoritydb_fence='ACTIVE_FENCE=stale'),'proof_semantic_inventory')
c('S24_T21_AFTER_RELEASE_RECEIPT_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T21-AFTER_COMMIT').update(required_authoritydb_receipt='NONE_NO_AUTHORITYDB_RECEIPT'),'proof_semantic_inventory')
c('S25_T22_AFTER_GENERIC_CLOSED_STATE','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T22-AFTER_COMMIT').update(required_authoritydb_state='exact committed AuthorityDB projection matching journal head'),'proof_semantic_inventory')
c('S26_T22_AFTER_ACTIVE_FENCE','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T22-AFTER_COMMIT').update(required_authoritydb_fence='active exact scope fencing token'),'proof_semantic_inventory')
# Artifact/lifecycle semantics.
c('S27_AP01_AFTER_PREIMAGE_CAS_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'ALP-AP01_COMPLETION_RECEIPT_PREIMAGE-AFTER_COMMIT').update(required_cas_refs=proof(o,'ALP-AP01_COMPLETION_RECEIPT_PREIMAGE-AFTER_COMMIT')['required_cas_refs'][:-1]),'proof_semantic_inventory')
c('S28_LO01_AFTER_NONCANONICAL_JOURNAL_EVENT','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'ALP-LO01_COMPLETION_RECEIPT_PUBLICATION-AFTER_COMMIT').update(required_journal_events=['COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED_NONCANONICAL']),'proof_semantic_inventory')
c('S29_LO01_AFTER_PUBLICATION_CAS_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'ALP-LO01_COMPLETION_RECEIPT_PUBLICATION-AFTER_COMMIT').update(required_cas_refs=proof(o,'ALP-LO01_COMPLETION_RECEIPT_PUBLICATION-AFTER_COMMIT')['required_cas_refs'][:-1]),'proof_semantic_inventory')
c('S30_LO02_BEFORE_PUBLICATION_CAS_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'ALP-LO02_TRANSACTION_LOCK_RELEASE-BEFORE_COMMIT').update(required_cas_refs=[]),'proof_semantic_inventory')
c('S31_LO02_AFTER_ACTIVE_FENCE','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'ALP-LO02_TRANSACTION_LOCK_RELEASE-AFTER_COMMIT').update(required_authoritydb_fence='ACTIVE_FENCE=stale'),'proof_semantic_inventory')
c('S32_LO02_AFTER_LOCK_RECEIPT_MISSING','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'ALP-LO02_TRANSACTION_LOCK_RELEASE-AFTER_COMMIT').update(required_cas_refs=proof(o,'ALP-LO02_TRANSACTION_LOCK_RELEASE-AFTER_COMMIT')['required_cas_refs'][:-1]),'proof_semantic_inventory')
# Registry/vector mirror substitutions (inventory remains frozen).
c('S33_REGISTRY_GENERIC_RECEIPT','RECOVERY-PROOF-REGISTRY.json',lambda o:proof(o,'RP-T08-AFTER_COMMIT').update(required_authoritydb_receipt='something durable'),'proof_semantic_inventory')
c('S34_VECTOR_MIRROR_GENERIC_EPOCH','SUPERVISOR-CRASH-VECTORS.json',lambda o:o['proof_registry']['RP-T09-AFTER_COMMIT'].update(required_authoritydb_epoch='exact committed supervisor epoch'),'typed_proof_mirror')
c('S35_REGISTRY_CROSS_PHASE_CAS','RECOVERY-PROOF-REGISTRY.json',lambda o:proof(o,'RP-T02-AFTER_COMMIT').update(required_cas_refs=['CAS_TERMINAL_SEAL=future']),'proof_semantic_inventory')
c('S36_INVENTORY_UNKNOWN_FIELD','RECOVERY-PROOF-SEMANTIC-INVENTORY.json',lambda o:proof(o,'RP-T12-AFTER_COMMIT').update(generic=True),'proof_semantic_inventory')
base=validate(ROOT,DESIGN)
if base:print(json.dumps({'status':'HOLD_BASE','errors':base},indent=2));raise SystemExit(2)
results=[]
for cid,file,fn,needle in CASES:
 with tempfile.TemporaryDirectory(prefix='cah-j1-r2-r1-semantic-',dir='/tmp') as td:
  r=Path(td)/'root';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__','*RESULTS.json','*RECEIPT.json','EVIDENCE-SHA256.txt','MANIFEST.sha256'))
  d=Path(td)/'design.md';shutil.copy2(DESIGN,d)
  p=d if file=='DESIGN' else r/file
  if file=='DESIGN':fn(p);key='DESIGN'
  else:o=load(p);fn(o);dump(p,o);key=file
  seal=load(r/'ARTIFACT-SHA256.json');seal['files'][key]=sha(p);dump(r/'ARTIFACT-SHA256.json',seal)
  errors=validate(r,d);ok=needle in errors;results.append({'id':cid,'expected_error':needle,'validator_rejected':bool(errors),'specific_gate_pass':ok,'errors':errors})
obj={'schema':'critical_apply.m2a_r2_r1.semantic_mutations.v1','status':'PASS' if all(x['specific_gate_pass'] for x in results) else 'HOLD','case_count':len(results),'rejected_count':sum(x['validator_rejected'] for x in results),'unsafe_accepted_count':sum(not x['validator_rejected'] for x in results),'results':results}
print(json.dumps(obj,indent=2));raise SystemExit(0 if obj['status']=='PASS' else 2)
