# Security Findings Register

**Owner:** Security Engineer (SEC)  
**Updated:** When any `# nosec` or `# nosemgrep` suppression is added to the codebase

> This register records every suppressed security finding. A suppression without an entry here is a CI failure.  
> Format: one entry per suppressed finding. Never remove entries — mark them `Resolved` when the suppression is lifted.

---

## Register Format

Each entry must include:

| Field | Description |
|-------|-------------|
| **Finding ID** | Unique ID: `FIND-NNNN` |
| **Tool** | `bandit` · `semgrep` |
| **Rule ID** | e.g., `B101`, `python.lang.security.audit.formatted-sql-query` |
| **File / Line** | Exact path and line number of the suppression |
| **Suppression Tag** | The inline comment used (`# nosec B101`, `# nosemgrep ...`) |
| **Justification** | Why this finding is a false positive or accepted risk |
| **Responsible** | Agent or contributor who added the suppression |
| **Date Added** | ISO 8601 date |
| **Status** | `Active` · `Resolved` (suppression lifted) |

---

## Active Suppressions

*No suppressions recorded yet. This register is populated as findings are evaluated during Phase 2+.*

---

## Resolved Suppressions

*None.*

---

## Notes

- Before adding a suppression, first try to fix the code. Suppressions are last resort.
- All `bandit` suppressions use `# nosec <RULE_ID>` (specify the rule — do not use bare `# nosec`).
- All `semgrep` suppressions use `# nosemgrep <rule-id>`.
- A PR that adds a `# nosec` or `# nosemgrep` comment without a corresponding entry in this register will fail CI.

