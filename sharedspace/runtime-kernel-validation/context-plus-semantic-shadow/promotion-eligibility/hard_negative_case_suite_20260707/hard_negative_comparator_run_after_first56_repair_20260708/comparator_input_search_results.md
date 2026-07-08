# Comparator Input Search Results

Classification: `HOLD_COMPARATOR_INPUT_MISSING`

The approved hard-negative comparator required an existing same-manifest Context+ shadow/offline input. Local searches found only:

- hard-negative manifest files (`case_manifest.draft.jsonl`, `case_manifest.approved.jsonl`)
- unrelated fixture shadow journals
- unrelated M25/M25B/vNext shadow artifacts
- production hard-negative routing journals

No same approved hard-negative-manifest Context+ shadow journal was found for exact 236-case comparator alignment.

Because the required shadow input is missing, comparator execution failed closed. No substitute shadow journal was generated, and no held/non-authoritative case was counted.
