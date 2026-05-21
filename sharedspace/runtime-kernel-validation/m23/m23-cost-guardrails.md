# M23 Cost / Lane Guardrails

Owner instruction captured: 2026-05-19T02:11+10:00

During remaining M23 gates:

- Prefer deterministic scripts for high-volume or high-minute checks.
- Use the established intent-preselector path for routing/classification checks instead of repeatedly hitting high-lane LLMs.
- Do not run frequent high-lane LLM evals every few minutes.
- If LLM eval is genuinely necessary, skip short X/XX-minute flows and start at 1 hour, then move to 2h+ soaks.
- M23.4/M23.5 should use local probes, service health, route explain, fixture tests, logs, and artifact inspection as the default evidence path.
- Only use high-lane LLM eval when deterministic evidence is insufficient and the gate explicitly needs semantic judgment.
