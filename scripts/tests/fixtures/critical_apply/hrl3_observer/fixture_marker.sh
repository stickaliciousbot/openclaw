#!/usr/bin/env python3
from __future__ import annotations
import os, signal, stat, sys, time

def reject(code:int, msg:str)->None:
    print('fixture error: '+msg, file=sys.stderr)
    raise SystemExit(code)

if not os.environ.get('CRITICAL_APPLY_FIXTURE'):
    reject(23, 'missing fixture env')
if len(sys.argv) < 2:
    reject(24, 'missing marker')
if len(sys.argv) > 4:
    reject(25, 'unexpected argument')
marker = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) >= 3 else 'ok'
delay_arg = sys.argv[3] if len(sys.argv) >= 4 else None
root = os.environ.get('CRITICAL_APPLY_FIXTURE_ROOT') or os.getcwd()
try:
    root_real = os.path.realpath(root)
except Exception:
    reject(26, 'invalid authorised root')
if not os.path.isdir(root_real):
    reject(26, 'authorised root missing')
if marker == '':
    reject(27, 'empty marker')
if os.path.isabs(marker):
    target_norm = os.path.normpath(marker)
else:
    target_norm = os.path.normpath(os.path.join(root_real, marker))
parent = os.path.dirname(target_norm) or root_real
try:
    parent_real = os.path.realpath(parent)
except Exception:
    reject(28, 'invalid parent')
try:
    if os.path.commonpath([root_real, parent_real]) != root_real:
        reject(29, 'marker outside authorised root')
except ValueError:
    reject(29, 'marker outside authorised root')
try:
    rel_parent = os.path.relpath(os.path.normpath(parent), root_real)
except Exception:
    reject(29, 'marker outside authorised root')
if rel_parent.startswith('..') or os.path.isabs(rel_parent):
    reject(29, 'marker outside authorised root')
if rel_parent not in ('.', ''):
    cur = root_real
    for comp in rel_parent.split(os.sep):
        if comp in ('', '.'):
            continue
        if comp == '..':
            reject(30, 'traversal rejected')
        cur = os.path.join(cur, comp)
        try:
            st = os.lstat(cur)
        except FileNotFoundError:
            reject(31, 'parent missing')
        if stat.S_ISLNK(st.st_mode):
            reject(32, 'parent symlink rejected')
        if not stat.S_ISDIR(st.st_mode):
            reject(33, 'parent not directory')
if os.path.islink(target_norm):
    reject(34, 'target symlink rejected')
if os.path.exists(target_norm):
    try:
        st = os.lstat(target_norm)
    except OSError:
        reject(35, 'target stat failed')
    if not stat.S_ISREG(st.st_mode):
        reject(36, 'target not regular')
print('fixture stdout: start')
print('fixture stderr: start', file=sys.stderr)
if mode == 'ok':
    pass
elif mode == 'sleep':
    time.sleep(float(delay_arg if delay_arg is not None else '0.2'))
elif mode == 'ignore-term':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(float(delay_arg if delay_arg is not None else '10'))
elif mode == 'binary':
    sys.stdout.buffer.write(b'\000\377binary-no-newline')
    sys.stdout.buffer.flush()
elif mode == 'crash':
    raise SystemExit(19)
elif mode == 'fork':
    reject(37, 'fork mode disabled')
else:
    reject(38, 'unknown mode')
flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
if hasattr(os, 'O_NOFOLLOW'):
    flags |= os.O_NOFOLLOW
try:
    fd = os.open(target_norm, flags, 0o600)
except OSError as exc:
    reject(39, 'marker open failed: '+exc.__class__.__name__)
with os.fdopen(fd, 'wb') as f:
    f.write(b'MUTATED\n')
print('fixture stdout: done')
raise SystemExit(0)
