# Status flags and opportunity conventions

Use these fields consistently in opportunity YAML front matter and summary tables.

## Pipeline status

| Status | Meaning |
|---|---|
| `new` | Newly created opportunity or lead. Needs first qualification. |
| `in-progress` | Active customer engagement with discovery, demo, proposal, or commercial work underway. |
| `stale` | No recent movement. Needs revive/close decision. |
| `won` | Commercially or strategically won. Retain outcome notes. |
| `lost` | Explicitly lost, rejected, or superseded. Retain reason and lessons. |
| `inactive` | Not currently being pursued, but not necessarily lost. |

## Required flags

| Flag | Type | Meaning |
|---|---|---|
| `active` | boolean | True when the opportunity is currently being worked. |
| `inactive` | boolean | True when the opportunity is paused, dormant, or intentionally not pursued. |
| `action_required` | boolean | True when Lawrence or the team must do something. |
| `next_action` | string | The next concrete action, preferably owner + date. |

## Date and time standard

Use ISO-style dates where possible and include timezone context when the original event used local time.

Example:

```yaml
created_at: 2026-05-13T07:57:00+10:00
timezone: Australia/Sydney
source_time_note: 7:57am AEST on May 13, 2026
```

## File naming

Use lowercase slugs:

```text
customers/<customer-slug>/profile.md
customers/<customer-slug>/contacts/<contact-slug>.md
opportunities/<status>/<customer-slug>-<short-opportunity-slug>.md
```
