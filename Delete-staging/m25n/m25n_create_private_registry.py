#!/usr/bin/env python3
import json, os, re, stat, hashlib
from pathlib import Path
workspace=Path('/home/stickai/.openclaw/workspace')
user_md=(workspace/'USER.md').read_text()
match=re.search(r'Telegram direct chat \(`([^`]+)`\)', user_md)
if not match:
    raise SystemExit('OWNER_DIRECT_TARGET_NOT_FOUND')
target=match.group(1).strip()
if not re.fullmatch(r'[0-9]{6,}', target):
    raise SystemExit('OWNER_DIRECT_TARGET_SHAPE_INVALID')
state=Path('/home/stickai/.openclaw/state/surface-response-targets/m25n')
state.mkdir(parents=True, exist_ok=True)
path=state/'registry.json'
entry={
  'schema':'stickbot.m25n.private_target_registry.v1',
  'alias':'operator-canary-target',
  'targetHandle':target,
  'active':True,
  'expiresAt':'2099-01-01T00:00:00.000Z'
}
fd=os.open(path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
with os.fdopen(fd,'w') as f:
    json.dump(entry,f,separators=(',',':'))
    f.write('\n')
os.chmod(path,0o600)
st=os.stat(path)
print(json.dumps({
  'status':'PRIVATE_REGISTRY_READY',
  'pathAlias':'m25n-private-runtime-local-registry',
  'mode':oct(stat.S_IMODE(st.st_mode)),
  'entryCount':1,
  'alias':'operator-canary-target',
  'targetHandleSha256':hashlib.sha256(target.encode()).hexdigest(),
}, sort_keys=True))
