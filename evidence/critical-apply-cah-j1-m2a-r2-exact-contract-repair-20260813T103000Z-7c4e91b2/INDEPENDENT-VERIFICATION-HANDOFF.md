# Fresh independent verification handoff

1. Rehash `EVIDENCE-SHA256.txt` and every listed file.
2. Rehash all `IMMUTABLE-INPUT-SEALS.json` authority files and supported manifest entries.
3. Copy the candidate exactly to disposable `/tmp`; run `py_compile`, `validate_m2a_r2.py`, prior 55, prior 26, fresh R1 56, and R2 combination suite without weakening.
4. Directly verify T22/SUPERVISOR_CLOSED is final canonical; LO01/LO02 and AP01 cannot mutate semantic/terminal/closeout heads; LO02 requires verified LO01 receipt.
5. Independently inspect typed proof content/resolution, strict schemas, cross-artifact equalities, design digest, privacy scanner identity, preservation, and zero effect.
6. Issue fresh PASS or exact HOLD. M2B remains not started and unauthorized.
