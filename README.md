# webworkspace

Private workspace for multiclient collaboration, application scaffolds, customer opportunity tracking, and lightweight markdown-first operating records.

## Top-level spaces

| Space | Purpose |
|---|---|
| `apps/` | New application ideas, prototypes, and build notes. |
| `opportunities/` | Opportunity pipeline records organized by status. |
| `customers/` | Customer profiles, contacts, account context, and relationship notes. |
| `config/` | Shared conventions, status flags, field definitions, and operating rules. |

## Opportunity workflow

Opportunities are tracked as markdown files with YAML front matter. Each opportunity should have:

- a customer folder under `customers/`
- a pipeline record under `opportunities/<status>/`
- linked contacts under `customers/<customer-slug>/contacts/`
- explicit status flags for `Active`, `Inactive`, `Action`, and `Next Action`

Current statuses:

- `new`
- `in-progress`
- `stale`
- `won`
- `lost`
- `inactive`

See `opportunities/README.md` and `config/status-flags.md` for the conventions.
