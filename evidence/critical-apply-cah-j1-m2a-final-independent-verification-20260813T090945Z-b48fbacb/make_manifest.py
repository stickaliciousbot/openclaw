#!/usr/bin/env python3
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/'EVIDENCE-SHA256.txt'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
files=sorted(p for p in root.rglob('*') if p.is_file() and p!=out)
out.write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n' for p in files))
print(sha(out),len(files))
