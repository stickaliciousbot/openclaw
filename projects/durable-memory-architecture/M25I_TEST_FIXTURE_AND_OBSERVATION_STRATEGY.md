# M25I Test Fixture and Observation Strategy

## Schema and contract

- valid
- malformed
- missing fields
- unknown major
- extension policy
- canonical hash
- replay
- duplicate receipt
- wrong surface/session/policy epoch

## Context reconstruction

- exact entity
- alias
- negative alias
- contradiction
- stale source
- missing unit
- unavailable private source
- malicious source instructions
- stale graph/index
- source changes after verification
- omission ledger

## Delivery

- quiet success
- delivery-required payload ready
- handler allow
- handler hold
- handler reject
- missing closeout anchor
- missing terminal anchor
- missing completion anchor
- duplicate idempotency key
- Telegram failure
- delayed duplicate
- delivery-required bare NO_REPLY rejection

## Broker/UMC

- grant allow/deny/expiry/revocation
- bypass
- timeout/cancel
- forged receipt
- prose-success without receipt
- postcondition mismatch

## Surface/privacy

- owner direct
- Web owner
- group/shared denial
- wrong identity/session
- private memory denial
- cross-surface replay
- redaction
- excerpt budget

## Resilience

- service crash
- Gateway restart
- partial evidence
- clock skew
- disk read-only/full for derived state
- source/graph/index watermark skew

## Observation

Every future milestone declares required GREEN checks, permitted YELLOW degradation, RED abort triggers, checkpoint cadence, observer owner, and independent terminal sentinel. Long observers use T+0/T+2/T+8/T+24 or an owner-approved equivalent.
