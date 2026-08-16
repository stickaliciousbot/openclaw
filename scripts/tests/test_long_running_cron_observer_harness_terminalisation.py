#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json, shutil, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import long_running_cron_observer_harness as h

def dump(p: Path, obj): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj, sort_keys=True)+'\n')
class HarnessTerminalisationTests(unittest.TestCase):
    def setUp(self): self.tmp=Path(tempfile.mkdtemp(prefix='harness-terminal-'))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def make(self, semantic_status='PASS', terminal='M4_PASS'):
        dump(self.tmp/'status.json', {'schema':'x','status':'RUNNING','pid':123,'harness_pass_anchor':h.PASS_ANCHOR})
        sem=self.tmp/'semantic'; sem.mkdir()
        dump(sem/'status.json', {'status':semantic_status,'terminal_status':terminal,'closeout_status':semantic_status})
        return sem
    def test_pass_terminal_replaces_running(self):
        sem=self.make('PASS','PASS_TERM'); out=h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem); self.assertEqual(out['classification'],'HARNESS_TERMINALISED_CLEANLY'); self.assertEqual(json.loads((self.tmp/'status.json').read_text())['status'],'TERMINAL')
    def test_hold_terminal_replaces_running(self):
        sem=self.make('HOLD','HOLD_TERM'); out=h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem); self.assertEqual(out['classification'],'HARNESS_TERMINALISED_CLEANLY')
    def test_missing_stderr_key_cleanup_safe(self): self.assertIn('stderr_missing', h.cleanup_warning_from_result({'stdout':'x'}))
    def test_missing_stdout_key_cleanup_safe(self): self.assertIn('stdout_missing', h.cleanup_warning_from_result({'stderr':'x'}))
    def test_cleanup_warning_recorded(self):
        sem=self.make(); out=h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem, cleanup_result={'stdout':'x'}); self.assertEqual(out['cleanup_state'],'warning')
    def test_semantic_terminal_preserved_through_cleanup_exception_shape(self):
        sem=self.make('PASS','PASS_TERM'); out=h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem, cleanup_result={}); self.assertEqual(out['terminal_status'],'PASS_TERM')
    def test_status_atomicity_file_exists(self):
        sem=self.make(); h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem); self.assertTrue((self.tmp/'status.json').stat().st_size > 0)
    def test_stale_status_reader_classification(self):
        sem=self.make(); h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem); self.assertEqual(json.loads((self.tmp/'status.json').read_text())['semantic_state'],'PASS')
    def test_duplicate_finalisation_idempotent(self):
        sem=self.make(); a=h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem); b=h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem); self.assertEqual(b['classification'], a['classification'])
    def test_no_terminal_is_blocked(self):
        dump(self.tmp/'status.json', {'status':'RUNNING'}); sem=self.tmp/'semantic'; sem.mkdir(); dump(sem/'status.json', {'status':'RUNNING'}); self.assertEqual(h.terminalise_harness_status(self.tmp, semantic_artifact_dir=sem)['classification'],'HARNESS_STATUS_STALE_BLOCKED')

class HarnessAlertTests(unittest.TestCase):
    def setUp(self): self.tmp=Path(tempfile.mkdtemp(prefix='harness-alert-'))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def test_semantic_artifact_paths_prefers_env_root_over_harness_status(self):
        sem=self.tmp/'semantic'
        row={'command':['/usr/bin/env',f'TEST_ROOT={sem}','python3','observer.py'],'status_path':str(self.tmp/'harness'/'status.json')}
        paths=h.semantic_artifact_paths(row)
        self.assertEqual(paths['semantic_artifact_dir'], str(sem))
        self.assertEqual(paths['semantic_status_path'], str(sem/'status.json'))
    def test_semantic_artifact_paths_accepts_receipt_root_child_flag(self):
        sem=self.tmp/'semantic'
        row={'command':['/workspace/scripts/critical_apply_restore_root_prereq.py','--restore-root','/tmp/restore','--receipt-root',str(sem)],'status_path':str(self.tmp/'harness'/'status.json')}
        paths=h.semantic_artifact_paths(row)
        self.assertEqual(paths['semantic_artifact_dir'], str(sem))
        self.assertEqual(paths['semantic_status_path'], str(sem/'status.json'))
        self.assertEqual(paths['semantic_summary_path'], str(sem/'summary.json'))
    def test_raise_alert_writes_json_and_jsonl(self):
        row={'run_id':'alert-test','artifact_dir':str(self.tmp)}
        event=h.build_alert_event(row, classification='TERMINAL', closeout_status='HOLD', terminal_status='HOLD_TERM', detail='done', paths={'semantic_artifact_dir':str(self.tmp/'semantic'),'semantic_status_path':None,'semantic_summary_path':None})
        result=h.raise_alert(row,event)
        self.assertTrue(Path(result['alert_path']).exists())
        self.assertIn('alert-test.alert.jsonl', result['alert_log_path'])
    def test_watch_alert_detects_semantic_terminal_and_terminalises_harness(self):
        harness=self.tmp/'harness'; sem=self.tmp/'semantic'; reg=self.tmp/'registry.json'
        harness.mkdir(); sem.mkdir()
        dump(harness/'status.json', {'status':'RUNNING','pid':999999,'harness_pass_anchor':h.PASS_ANCHOR})
        dump(sem/'status.json', {'status':'HOLD','closeout_status':'HOLD','terminal_status':'HOLD_TERM'})
        dump(reg, {'schema':h.SCHEMA+'.registry','runs':[{'run_id':'watch-alert-test','pid':999999,'proc_starttime':None,'artifact_dir':str(harness),'status_path':str(harness/'status.json'),'command':['/usr/bin/env',f'TEST_ROOT={sem}','python3','observer.py']}]} )
        code=h.watch_alert(argparse.Namespace(run_id='watch-alert-test', registry=str(reg), artifact_dir=str(harness), interval_sec=0.01, timeout_sec=1.0, alert_command_json=None))
        self.assertEqual(code, 3)
        self.assertEqual(json.loads((harness/'status.json').read_text())['status'], 'TERMINAL')
        self.assertTrue((harness/'alerts'/'watch-alert-test.alert.json').exists())
if __name__ == '__main__': unittest.main()
