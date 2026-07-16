# M7 Model Eligibility Policy

Status: `PASS_M7_MODEL_ELIGIBILITY_POLICY_DEFINED`

Primary worker: `openai-codex/gpt-5.5` as `execution_worker` only. Route authority is `false`. Eligibility requires M5 manifest acceptance, M4 VerifiedRoute via the M6 contract-build lane, ContractEnvelope, DeliveryReceipt `no_send`, TerminalContractCloseout, and observe-only authority. Session/channel model pins remain route intent only.
