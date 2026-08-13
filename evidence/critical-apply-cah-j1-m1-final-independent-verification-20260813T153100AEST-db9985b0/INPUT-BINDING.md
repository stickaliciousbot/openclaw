# INPUT BINDING

- Base commit: `b48fbacb12f07de334a0195e13992ce7237db910`
- Base tree: `e531eb81a0153fd066d9d5ea3bdb05f31bcacdb4`
- Patch: `/tmp/cah-j1-m1.patch`, 106031 bytes, SHA-256 `7cde7ec7bf858b06bdf22fc22d703457565059d5643909d55ac7c54020b8d4bc` before and after.
- Construction evidence root: `critical-apply-cah-j1-m1-offline-core-20260813T024009Z-59e3c41a`; `EVIDENCE-SHA256.txt` SHA-256 `882ed90a53356be07799003058e9984da76c10b75f09da3d877cb485ac07abf6`; every listed file verified OK.
- Frozen M0 root and final receipt root bound as assigned.
- Owner revision SHA-256 `6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af`.
- Adjudication SHA-256 `1d2853fba832ebc243423c3c2dac00def80c3c2b56d892ee8c83aeff96c34427`.
- Clean candidate materialized from Git object DB into `/tmp/cah-j1-m1-final-verifier-r1-db9985b0-v2/candidate`, exact patch applied, exact seven changed paths and resulting hashes matched sealed `SOURCE-MANIFEST.txt`.
- Repository HEAD remained the base commit. Workspace was dirty at baseline and remained treated by state/hash parity, not cleanliness. Index lock prevented a non-mutating post `write-tree`; no lock was removed or repository state mutated.
- Forbidden worktree was never accessed.
