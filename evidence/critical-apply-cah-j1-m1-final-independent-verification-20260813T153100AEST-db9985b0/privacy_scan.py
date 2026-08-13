#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
patterns={
 'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'aws_access_key':re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
 'github_token':re.compile(r'\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b'),
 'generic_secret_assignment':re.compile(r'(?i)\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*[\"\'][^\"\'\n]{8,}[\"\']'),
 'ipv4':re.compile(r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)'),
 'email':re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
}
files=[Path(x) for x in sys.argv[1:]]; findings=[]
for p in files:
 text=p.read_text(errors='replace')
 for name,pat in patterns.items():
  for m in pat.finditer(text):findings.append({'file':str(p),'detector':name,'literal':m.group(0)[:160]})
print(json.dumps({'files':len(files),'findings':findings},indent=2))
