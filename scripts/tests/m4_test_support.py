from __future__ import annotations
import os, shutil, sys, tempfile, time, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
FIXTURE = ROOT/'scripts/tests/fixtures/critical_apply/hrl3_observer/fixture_marker.sh'

def make_tmp(prefix='m4-'):
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    tx = tmp/'tx'; locks = tmp/'locks'; shadow = tmp/'shadow'
    for p in (tx, locks, shadow): p.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(FIXTURE, 0o700)
    except PermissionError:
        pass
    return tmp, tx, locks, shadow

def cleanup(path): shutil.rmtree(path, ignore_errors=True)

def many_cases(prefix, count):
    return [f'{prefix}_{i:03d}' for i in range(count)]
