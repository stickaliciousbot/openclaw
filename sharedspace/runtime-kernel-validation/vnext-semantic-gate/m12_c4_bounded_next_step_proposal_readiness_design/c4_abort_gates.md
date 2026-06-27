# C4 Abort Gates

Report `M12_C4_READINESS_DESIGN_BLOCKED` or abort later C4 work if:

- C4 cannot be separated from execution authority.
- C4 requires production mutation.
- C4 requires external action execution.
- proposal authority cannot be made deterministic.
- source authority cannot be made deterministic.
- model prose would be authoritative.
- C4 weakens C1/C2/C3 boundaries.
- rollback readiness cannot be verified.
- mutation sentinels trip.
- cache/artifact-memory/global promotion would be required.
- direct provider bypass is required or observed.
- arbitrary path reads are required as authority.
