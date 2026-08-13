# Offline reconstruction from permanent inputs

This package does not depend on `/tmp`. Run only in a disposable, non-Git destination outside the production worktree.

```bash
set -euo pipefail
workspace=/home/stickai/.openclaw/workspace
base=b48fbacb12f07de334a0195e13992ce7237db910
patch="$workspace/evidence/critical-apply-cah-j1-m1-permanent-preservation-20260813T083100Z-5e3fa595/candidate/cah-j1-m1.patch"
dest="$(mktemp -d /tmp/cah-j1-m1-reconstruct.XXXXXXXX)"
git -C "$workspace" archive "$base" | tar -x -C "$dest"
git -C "$workspace" apply --unsafe-paths --directory="$dest" "$patch"
sha256sum \
  "$dest/scripts/critical_apply_journal.py" \
  "$dest/scripts/critical_apply_progress.py" \
  "$dest/scripts/critical_apply_cas.py" \
  "$dest/scripts/critical_apply_authority_db.py" \
  "$dest/scripts/tests/test_critical_apply_journal_idempotency.py" \
  "$dest/scripts/tests/test_critical_apply_cas.py" \
  "$dest/scripts/tests/test_critical_apply_authority_db.py"
```

Compare the seven hashes to `PRESERVATION-MANIFEST.json`. The preservation-time proof used the same Git object and permanent patch in `/tmp/cah-j1-m1-preservation-reconstruct-5e3fa595`, a disposable non-Git directory, and all seven hashes matched.
