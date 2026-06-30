# GE2-R9 Native Handler Run/Status/Artifacts Report

Final classification: `GE2_R9_PLACEHOLDER_SUCCESS_FAIL`

Proof level: **P1 only**  
No P2/P3 claim: **true**

## Commands

- run: `/ge2 run r9-native-handler-smoke`
- status: `/ge2 status ge2-20260630091740-0c4c95a3`
- artifacts: `/ge2 artifacts ge2-20260630091740-0c4c95a3`

Run ID: `ge2-20260630091740-0c4c95a3`

## Results

- run matched native: true
- run no model/chat fallthrough: true
- status exact retrieval: true
- artifacts exact retrieval: true
- terminal status: completed
- milestone count: 7
- artifact count: 1

## Ledger/artifacts

Ledger path: `/home/stickai/.openclaw/workspace/state/ge2-native/runs/ge2-20260630091740-0c4c95a3.json`

- /home/stickai/.openclaw/workspace/state/ge2-native/artifacts/ge2-20260630091740-0c4c95a3/run-summary.json sha=55c0352bb2f5242096f64410700b572000c80cd815357830c13133959766b19d computed=55c0352bb2f5242096f64410700b572000c80cd815357830c13133959766b19d match=true

## Compression

- run response bytes: 162
- status response bytes: 169
- artifacts response bytes: 237
- all bounded under 4KB: true
- artifact refs/hashes in response: false

## Safety

- production touched: no
- GE2 runtime state touched: yes, intended by /ge2 run
- Gateway restarted: no
- rollback performed: no
- promoted: no

JSON: /home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r9_native_run_lifecycle_proof/GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_REPORT_20260630.json
