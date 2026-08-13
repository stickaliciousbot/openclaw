#!/usr/bin/env python3
"""Independent adversarial verification for CAH-J1 M1; candidate is never repaired."""
from __future__ import annotations
import hashlib, json, multiprocessing as mp, os, shutil, sqlite3, stat, sys, tempfile, unittest
from pathlib import Path

CANDIDATE=Path('/tmp/cah-j1-m1-final-verifier-r1-db9985b0-v2/candidate')
sys.path.insert(0,str(CANDIDATE/'scripts'))
from critical_apply_authority_db import *  # noqa
from critical_apply_cas import CASCaptureHold,CASCrash,CASIntegrityError,DescriptorCAS,RegisteredRoot  # noqa
from critical_apply_journal import JournalIntegrityError,JournalWriterToken,append_event_idempotent,create_transaction_journal,validate_journal  # noqa
from critical_apply_progress import ProgressDB  # noqa


def journal_worker(root,tx,eid,value,q):
    sys.path.insert(0,str(CANDIDATE/'scripts'))
    from critical_apply_journal import JournalWriterToken,append_event_idempotent
    try:
        p={'schema':'critical_apply.event.v2','transaction_id':tx,'event_type':'VERIFY','phase':'PREPARING','value':value}
        a=append_event_idempotent(Path(root),p,event_id=eid,writer_token=JournalWriterToken(tx,'v',str(Path(root).resolve())))
        q.put(('OK',a.event_sha256,a.sequence))
    except Exception as e:q.put((type(e).__name__,str(e),None))


def nonce_worker(dbpath,txroot,tx,epoch,nonce,contract,request,q):
    sys.path.insert(0,str(CANDIDATE/'scripts'))
    from critical_apply_authority_db import AuthorityDB
    from critical_apply_journal import validate_journal
    try:
        with AuthorityDB(Path(dbpath),busy_timeout_ms=12000) as db:
            r=db.reserve_nonce(validated=validate_journal(Path(txroot),transaction_id=tx),nonce_sha256=nonce,transaction_id=tx,authority_id='authority-1',supervisor_epoch=epoch,authority_generation_token=1,contract_sha256=contract,request_sha256=request)
            q.put(('WIN',r.authority_receipt_sha256))
    except Exception as e:q.put((type(e).__name__,str(e)))


class IndependentJournalProgress(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='m1-r1-journal-')); self.tx='verify-journal-'+'a'*32
        create_transaction_journal(self.root,transaction_id=self.tx); self.token=JournalWriterToken(self.tx,'v',str(self.root.resolve()))
    def tearDown(self):shutil.rmtree(self.root,ignore_errors=True)
    def proposal(self,v='one'):return {'schema':'critical_apply.event.v2','transaction_id':self.tx,'event_type':'VERIFY','phase':'PREPARING','value':v}
    def test_progress_row_tamper_same_head_and_count_rebuilds_full_content(self):
        ack=append_event_idempotent(self.root,self.proposal(),event_id='e1',writer_token=self.token)
        db=self.root/'journal'/'progress.sqlite3'; con=sqlite3.connect(db); con.execute("UPDATE idempotency SET proposal_sha256=?",('f'*64,)); con.commit(); con.close()
        again=append_event_idempotent(self.root,self.proposal(),event_id='e1',writer_token=self.token)
        self.assertEqual(again,ack); con=sqlite3.connect(db); self.assertNotEqual(con.execute('SELECT proposal_sha256 FROM idempotency').fetchone()[0],'f'*64); con.close()
    def test_progress_transaction_id_mismatch_rebuilds(self):
        ack=append_event_idempotent(self.root,self.proposal(),event_id='e1',writer_token=self.token)
        db=self.root/'journal'/'progress.sqlite3'; con=sqlite3.connect(db); con.execute("UPDATE metadata SET value='wrong' WHERE key='transaction_id'"); con.commit(); con.close()
        self.assertEqual(append_event_idempotent(self.root,self.proposal(),event_id='e1',writer_token=self.token),ack)
        con=sqlite3.connect(db); self.assertEqual(dict(con.execute('SELECT key,value FROM metadata'))['transaction_id'],self.tx); con.close()
    def test_concurrent_distinct_ids_serialize_without_loss(self):
        q=mp.Queue(); ps=[mp.Process(target=journal_worker,args=(str(self.root),self.tx,f'e{i}',i,q)) for i in range(12)]
        [p.start() for p in ps]; results=[q.get(timeout=60) for _ in ps]; [p.join(20) for p in ps]
        self.assertTrue(all(r[0]=='OK' for r in results),results); self.assertEqual(validate_journal(self.root,transaction_id=self.tx).committed_sequence,12)
    def test_conflicting_same_id_proposals_hold_and_single_commit(self):
        q=mp.Queue(); ps=[mp.Process(target=journal_worker,args=(str(self.root),self.tx,'same',i%2,q)) for i in range(10)]
        [p.start() for p in ps]; results=[q.get(timeout=60) for _ in ps]; [p.join(20) for p in ps]
        self.assertEqual(validate_journal(self.root,transaction_id=self.tx).committed_sequence,1)
        self.assertEqual(sum(r[0]=='OK' for r in results),5,results); self.assertEqual(sum('INTEGRITY_CONFLICT_HOLD' in r[1] for r in results),5,results)


class IndependentCAS(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='m1-r1-cas-')); self.src=self.root/'src'; self.src.mkdir(); self.txroot=self.root/'tx'; self.txroot.mkdir(); self.tx='verify-cas-'+'b'*32
        self.data=b'A'*(2*1024*1024+33); (self.src/'x').write_bytes(self.data); create_transaction_journal(self.txroot,transaction_id=self.tx); self.token=JournalWriterToken(self.tx,'v',str(self.txroot.resolve()))
    def tearDown(self):shutil.rmtree(self.root,ignore_errors=True)
    def capture(self,eid='e',**kw):
        with RegisteredRoot(self.src) as rr,rr.open_source('x') as s,DescriptorCAS(self.txroot,writer_token=self.token) as cas:return cas.capture(s,event_id=eid,**kw)
    def test_preexisting_shard_symlink_and_non_directory_refuse(self):
        sha=hashlib.sha256(self.data).hexdigest()
        for kind in ('symlink','file'):
            r=self.root/kind; r.mkdir(); create_transaction_journal(r,transaction_id=self.tx+kind); (r/'cas').mkdir(); p=r/'cas'/sha[:2]
            p.symlink_to(self.src,target_is_directory=True) if kind=='symlink' else p.write_bytes(b'x')
            tok=JournalWriterToken(self.tx+kind,'v',str(r.resolve()))
            with RegisteredRoot(self.src) as rr,rr.open_source('x') as s,DescriptorCAS(r,writer_token=tok) as cas:self.assertRaises(Exception,cas.capture,s,event_id='e')
    def test_orphan_publish_crash_then_dedupe_recovery(self):
        with self.assertRaises(CASCrash):self.capture(failpoint='after_rehash_before_journal')
        sha=hashlib.sha256(self.data).hexdigest(); self.assertTrue((self.txroot/'cas'/sha[:2]/sha).exists()); self.assertEqual(validate_journal(self.txroot,transaction_id=self.tx).committed_sequence,0)
        ack=self.capture(); self.assertTrue(ack.deduplicated); self.assertEqual(validate_journal(self.txroot,transaction_id=self.tx).committed_sequence,1)
    def test_corrupt_destination_never_overwritten(self):
        sha=hashlib.sha256(self.data).hexdigest(); p=self.txroot/'cas'/sha[:2]/sha; p.parent.mkdir(parents=True); p.write_bytes(b'evil')
        with self.assertRaises(CASIntegrityError):self.capture()
        self.assertEqual(p.read_bytes(),b'evil'); self.assertEqual(validate_journal(self.txroot,transaction_id=self.tx).committed_sequence,0)
    def _mutation_holds(self,mutator):
        fired=False
        def hook(_):
            nonlocal fired
            if not fired:fired=True;mutator()
        with self.assertRaises(CASCaptureHold):self.capture(chunk_hook=hook)
        self.assertEqual(validate_journal(self.txroot,transaction_id=self.tx).committed_sequence,0)
    def test_source_append_during_capture_holds(self):self._mutation_holds(lambda:(self.src/'x').open('ab').write(b'append'))
    def test_source_truncate_during_capture_holds(self):self._mutation_holds(lambda:os.truncate(self.src/'x',17))
    def test_source_metadata_mutation_during_capture_holds(self):self._mutation_holds(lambda:os.chmod(self.src/'x',0o600))


class IndependentAuthority(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='m1-r1-auth-')); self.txroot=self.root/'tx'; self.txroot.mkdir(mode=0o700); self.dbdir=self.root/'db'; self.dbdir.mkdir(mode=0o700); self.dbpath=self.dbdir/'authority.sqlite3'
        self.tx='verify-auth-'+'c'*32; self.epoch='epoch-1'; self.contract='3'*64; self.request='4'*64; self.nonce='2'*64; self.scope='1'*64
        create_transaction_journal(self.txroot,transaction_id=self.tx); self.token=JournalWriterToken(self.tx,'v',str(self.txroot.resolve())); self.event('SUPERVISOR_STARTED','start'); self.db=AuthorityDB(self.dbpath)
    def tearDown(self):
        try:self.db.close()
        except Exception:pass
        shutil.rmtree(self.root,ignore_errors=True)
    def valid(self):return validate_journal(self.txroot,transaction_id=self.tx)
    def event(self,t,eid,**b):
        b.setdefault('supervisor_epoch',self.epoch);b.setdefault('contract_sha256',self.contract);b.setdefault('authority_id','authority-1')
        return append_event_idempotent(self.txroot,{'schema':'critical_apply.event.v2','transaction_id':self.tx,'event_type':t,'phase':'PREPARING',**b},event_id=eid,writer_token=self.token)
    def reserve_nonce_bound(self):
        p=self.db.reserve_nonce(validated=self.valid(),nonce_sha256=self.nonce,transaction_id=self.tx,authority_id='authority-1',supervisor_epoch=self.epoch,authority_generation_token=1,contract_sha256=self.contract,request_sha256=self.request)
        self.event('CALL_AUTHORITY_RESERVED','reserved',nonce_sha256=self.nonce,request_sha256=self.request,authority_receipt_sha256=p.authority_receipt_sha256)
        return self.db.bind_nonce_reservation(validated=self.valid(),nonce_sha256=self.nonce,epoch=self.epoch)
    def start_nonce(self):
        c=self.reserve_nonce_bound();self.event('CALL_START_COMMITTED','start-call',nonce_sha256=self.nonce,request_sha256=self.request,authority_receipt_sha256=c.authority_receipt_sha256);return self.db.consume_call_start(validated=self.valid(),nonce_sha256=self.nonce,epoch=self.epoch)
    def test_identity_schema_application_user_version_and_pragmas(self):
        p=self.db.pragma_snapshot();self.assertEqual((str(p['journal_mode']).lower(),p['synchronous'],p['application_id'],p['user_version']),('wal',2,AUTHORITY_APPLICATION_ID,AUTHORITY_USER_VERSION));self.assertEqual(stat.S_IMODE(self.dbpath.stat().st_mode),0o600)
        self.db.close(); con=sqlite3.connect(self.dbpath);con.execute('PRAGMA application_id=7');con.commit();con.close();self.assertRaises(AuthorityIntegrityError,AuthorityDB,self.dbpath)
    def test_receipt_tamper_refused_on_reopen(self):
        self.db.reserve_scope(validated=self.valid(),scope_hash=self.scope,transaction_id=self.tx,supervisor_epoch=self.epoch,contract_sha256=self.contract);self.db.close()
        con=sqlite3.connect(self.dbpath); text=con.execute('SELECT receipt_json FROM authority_receipts LIMIT 1').fetchone()[0]; d=json.loads(text);d['to_state']='ACTIVE';con.execute('UPDATE authority_receipts SET receipt_json=?',(json.dumps(d),));con.commit();con.close()
        self.assertRaises(AuthorityIntegrityError,AuthorityDB,self.dbpath)
    def test_busy_is_fail_closed(self):
        other=sqlite3.connect(self.dbpath,isolation_level=None);other.execute('BEGIN IMMEDIATE');self.db.con.execute('PRAGMA busy_timeout=20')
        try:self.assertRaises(AuthorityBusyHold,self.db.reserve_scope,validated=self.valid(),scope_hash=self.scope,transaction_id=self.tx,supervisor_epoch=self.epoch,contract_sha256=self.contract)
        finally:other.rollback();other.close()
    def test_cross_epoch_and_stale_fence_do_not_authorize(self):
        p=self.db.reserve_scope(validated=self.valid(),scope_hash=self.scope,transaction_id=self.tx,supervisor_epoch=self.epoch,contract_sha256=self.contract);self.event('SCOPE_LEASE_RESERVATION_COMMITTED','r',scope_hash=self.scope,fencing_token=p.fencing_token,authority_receipt_sha256=p.authority_receipt_sha256);self.db.bind_scope_reservation(validated=self.valid(),scope_hash=self.scope,epoch=self.epoch);a=self.db.activate_scope(validated=self.valid(),scope_hash=self.scope,epoch=self.epoch);self.event('SCOPE_LEASE_ACQUIRED','a',scope_hash=self.scope,fencing_token=a.fencing_token,authority_receipt_sha256=a.authority_receipt_sha256)
        self.assertFalse(self.db.scope_action_allowed(validated=self.valid(),scope_hash=self.scope,transaction_id=self.tx,supervisor_epoch='epoch-2',fencing_token=a.fencing_token));self.assertFalse(self.db.scope_action_allowed(validated=self.valid(),scope_hash=self.scope,transaction_id=self.tx,supervisor_epoch=self.epoch,fencing_token=a.fencing_token+1))
    def test_lease_crash_state_transitions_fail_closed(self):
        self.assertEqual(classify_scope_crash_state(reservation=False,acquisition=False,release_intent=False,release_recorded=False,db_state='RESERVED_PENDING_JOURNAL'),'ORPHAN_PENDING');self.assertEqual(classify_scope_crash_state(reservation=True,acquisition=False,release_intent=False,release_recorded=False,db_state='ACTIVE'),'ACTIVE_UNACKNOWLEDGED');self.assertEqual(classify_scope_crash_state(reservation=True,acquisition=True,release_intent=True,release_recorded=False,db_state='RELEASE_PENDING'),'RELEASE_IN_PROGRESS')
    def test_N04_refuses_without_journal_first_recovery_authorization(self):
        self.reserve_nonce_bound();self.assertRaises(AuthorityIntegrityError,self.db.safe_resume_rebind,validated=self.valid(),nonce_sha256=self.nonce,epoch='epoch-2')
    def test_N07_refuses_journal_record_without_valid_CAS_reference(self):
        used=self.start_nonce();self.event('CALL_OUTCOME_RECORDED','fake',nonce_sha256=self.nonce,request_sha256=self.request,authority_receipt_sha256=used.authority_receipt_sha256,response_sha256='7'*64)
        self.assertRaises(AuthorityIntegrityError,self.db.record_outcome,validated=self.valid(),nonce_sha256=self.nonce,epoch=self.epoch)
    def test_unknown_consumed_survives_reopen_and_is_nonretryable(self):
        self.start_nonce();r=self.db.classify_unknown_consumed(validated=self.valid(),nonce_sha256=self.nonce,epoch=self.epoch);self.assertEqual(r.to_state,'UNKNOWN_CONSUMED');self.db.close();self.db=AuthorityDB(self.dbpath);self.assertFalse(self.db.nonce_call_allowed(validated=self.valid(),nonce_sha256=self.nonce,epoch=self.epoch));self.assertRaises(AuthorityConflict,self.db.consume_call_start,validated=self.valid(),nonce_sha256=self.nonce,epoch=self.epoch)
    def test_contention_2_5_20_exactly_one_winner(self):
        self.db.close()
        for n in (2,5,20):
            d=self.root/f'db{n}';d.mkdir(mode=0o700);p=d/'a.sqlite3';AuthorityDB(p).close();q=mp.Queue();nonce=hashlib.sha256(f'n{n}'.encode()).hexdigest();ps=[mp.Process(target=nonce_worker,args=(str(p),str(self.txroot),self.tx,self.epoch,nonce,self.contract,self.request,q)) for _ in range(n)];[x.start() for x in ps];res=[q.get(timeout=90) for _ in ps];[x.join(30) for x in ps];self.assertEqual(sum(x[0]=='WIN' for x in res),1,res);self.assertTrue(all(not x.is_alive() for x in ps))
        self.db=AuthorityDB(self.dbpath)

if __name__=='__main__':unittest.main(verbosity=2)
