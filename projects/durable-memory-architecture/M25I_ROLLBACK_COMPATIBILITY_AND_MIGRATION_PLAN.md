# M25I Rollback Compatibility and Migration Plan

| Component/phase | Safe degraded state |
| --- | --- |
| schemas | feature flag disabled; keep draft schemas inert |
| delivery classification | old quiet behavior only for non-delivery jobs; delivery-required contracts fail closed |
| boundary envelope | disabled consumption; handler dormant/unarmed |
| payload generation | disable artifact writer; preserve existing evidence |
| Telegram adapter | off-switch; pending-send check before and after disable |
| final proof | disarm handler and remove proof job; never rewrite evidence |
| source registry | revert to prior accepted manifest |
| Ledger v0.2 | v0.1 read-only baseline; sidecar discarded if needed |
| graph/index | discard/rebuild projections |
| context reconstruction | disable service route |
| RSB | unregister/disable route |
| UMC adapter | accepted current baseline |
| SSB | previous accepted surface path |
| Context Bridge | existing sanitized presentation only |

Historical evidence is never deleted or rewritten. Rollback disables new consumption paths and preserves manifests. Ledger v0.1 remains frozen/read-only while v0.2 prototypes live in disposable sidecar storage until approved.
