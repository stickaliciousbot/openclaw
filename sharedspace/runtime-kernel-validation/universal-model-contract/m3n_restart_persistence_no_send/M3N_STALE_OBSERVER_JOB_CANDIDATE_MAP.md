# M3N stale observer/job candidate map

Status: `BLOCKED_M3N_TARGETED_CLEANUP_NO_SAFE_TARGET`

Candidates inspected: `18`; safe cleanup candidates: `0`.

## Candidate 147
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `snapfuse /var/lib/snapd/snaps/flutter_149.snap /snap/flutter/149 -o ro,nodev,allow_other,suid`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 150
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `snapfuse /var/lib/snapd/snaps/core20_2769.snap /snap/core20/2769 -o ro,nodev,allow_other,suid`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 153
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `snapfuse /var/lib/snapd/snaps/snapd_26865.snap /snap/snapd/26865 -o ro,nodev,allow_other,suid`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 159
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `snapfuse /var/lib/snapd/snaps/core20_2866.snap /snap/core20/2866 -o ro,nodev,allow_other,suid`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 513
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/sbin/cron -f -P`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 632
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 714
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/local/bin/gog gmail watch serve --account stickaliciousbot@gmail.com --bind 127.0.0.1 --port 8788 --path /gmail-pubsub --hook-url http://127.0.0.1:18789/hooks/gmail`
- cwd: `/home/stickai`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate 730
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/node /home/stickai/.openclaw/workspace/services/token-solver-v4/src/server.js`
- cwd: `/home/stickai/.openclaw/workspace/services/token-solver-v4`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate 731
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/python3.12 /home/stickai/.openclaw/workspace/projects/memory-service-vmesh/memory_service_vmesh.py --port 18830`
- cwd: `/home/stickai/.openclaw/workspace`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate 733
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/python3 /home/stickai/.openclaw/workspace/services/thinmem-vector-search/bin/thinmem.py daemon`
- cwd: `/home/stickai/.openclaw/workspace/services/thinmem-vector-search`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate 2185
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/node /home/stickai/.openclaw/workspace/services/token-solver-v3/src/server.js`
- cwd: `/home/stickai/.openclaw/workspace`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate 2837
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/python3 /home/stickai/.openclaw/workspace/projects/token-broker-vmesh/token_broker_vmesh.py --host 127.0.0.1 --port 18840`
- cwd: `/home/stickai/.openclaw/workspace`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate 122580
- classification: `UNSAFE_ACTIVE_GATEWAY_OR_RUNTIME_PROCESS`
- type: `os_process`
- command: `/usr/bin/node /home/stickai/.npm-global/lib/node_modules/openclaw/dist/index.js gateway --port 18789`
- cwd: `/home/stickai`
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 190619
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `/usr/bin/python3.12 /tmp/m3n_targeted_cleanup_approval_card.py`
- cwd: `/home/stickai/.openclaw/workspace`
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 576791
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `os_process`
- command: `snapfuse /var/lib/snapd/snaps/snapd_27406.snap /snap/snapd/27406 -o ro,nodev,allow_other,suid`
- cwd: ``
- process alive: `True`
- expected alive: `False`
- artifact root: `None`

## Candidate 4097537
- classification: `EXPECTED_ACTIVE_PROCESS_DO_NOT_CLEANUP`
- type: `os_process`
- command: `node src/server.js`
- cwd: `/home/stickai/.openclaw/workspace/projects/noa-bridge-v1`
- process alive: `True`
- expected alive: `True`
- artifact root: `None`

## Candidate b29e6275-9bad-4622-8a56-041e5a2dc864
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `cron_internal_job`
- command: `cron isolated agentTurn -> python3 scripts/context_plus_semantic_shadow_pass_watch_quiet.py via agent exec`
- cwd: `/home/stickai/.openclaw/workspace`
- process alive: `False`
- expected alive: `True`
- artifact root: `not a single process artifact root; related script output is deterministic stdout`

## Candidate 5bd9c18f-98b0-44d4-a169-33e1f1af33de
- classification: `UNKNOWN_DO_NOT_CLEANUP`
- type: `cron_internal_job`
- command: `main-session systemEvent early-abort sentinel for M3M R2B`
- cwd: `/home/stickai/.openclaw/workspace`
- process alive: `False`
- expected alive: `True`
- artifact root: `sharedspace/runtime-kernel-validation/universal-model-contract/m3m_r2b_installed_shadow_soak`
