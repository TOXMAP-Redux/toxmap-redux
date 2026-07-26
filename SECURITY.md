# Security Policy

**Project:** TOXMAP — Open-source EPA/NLM TOXMAP clone  
**Maintained by:** [MAINTAINERS](MAINTAINERS.md)  
**Full security posture:** [GOVERNANCE.md §8](docs/GOVERNANCE.md#8-security-policy)

---

## Supported Versions

Only the latest release on the `main` branch receives security patches.

| Version            | Supported |
|--------------------|-----------|
| Latest (`main`)    | ✅         |
| All prior releases | ❌         |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

1. Open a **private** security advisory at:  
   👉 `https://github.com/VictorCannestro/toxmap/security/advisories/new`
2. Include:
   - Affected component (backend / frontend / CI / data pipeline)
   - Steps to reproduce
   - Potential impact assessment
3. Maintainers acknowledge within **72 hours**.
4. If confirmed: patch developed in a private branch → coordinated disclosure → patch released within **14 days**.

---

## CVE Response SLAs

| Severity | CVSS Range | Response Target                   | Release Type            |
|----------|------------|-----------------------------------|-------------------------|
| Critical | ≥ 9.0      | Patch within **48 hours**         | Emergency patch release |
| High     | 7.0–8.9    | Patch within **7 days**           | Patch release           |
| Medium   | 4.0–6.9    | Address in next scheduled release | Minor or patch          |
| Low      | < 4.0      | Address in next scheduled release | Best effort             |

---

## Security Scope

TOXMAP is a **public read-only data visualization tool** with no user authentication, no user data
storage, and no payment processing. This shapes the threat model significantly.

### In-scope Attack Surface

| Component                   | Threat                               | Mitigation                                                                                     |
|-----------------------------|--------------------------------------|------------------------------------------------------------------------------------------------|
| FastAPI query parameters    | SQL injection, resource exhaustion   | Pydantic validators; parameterized queries; rate limiting (slowapi 60 req/min)                 |
| DuckDB WASM client-side SQL | Query injection via user input       | Parameterized `$variable` syntax in all query hooks                                            |
| Python/npm dependencies     | Known CVEs                           | `pip-audit` + `npm audit --audit-level=high` in `security.yml` on every PR                     |
| GitHub Actions workflows    | Supply chain attack via mutable tags | All actions pinned to full 40-char SHA; Dependabot tracks updates (see `PINNED_ACTIONS.md`)    |
| Secrets in codebase         | Credential leakage                   | `gitleaks` scan in `security.yml`; `.gitignore` covers `.env`; no hardcoded credentials        |
| Cloudflare R2 bucket        | Object poisoning                     | CORS policy limits to `GET`/`HEAD` only; minimum-scope API token                               |
| Browser CSP                 | XSS; `SharedArrayBuffer` blocked     | `_headers` file configures COEP/COOP/CSP; `'wasm-unsafe-eval'` for DuckDB WASM                 |
| FastAPI error responses     | Internal path/stack trace disclosure | Global 500 handler returns generic message; traces logged server-side only                     |
| EPA data ingestion          | SSRF                                 | All EPA URLs are module-level constants; allow-list prefix check before every `requests.get()` |
| `VITE_`-prefixed env vars   | Secret inlined into browser bundle   | Policy: no `VITE_` var may contain a credential; CI `grep` check enforced                      |

### Out of Scope (by design)

- Authentication and authorization (no user accounts)
- CSRF protection (no state-mutating endpoints)
- Session fixation or hijacking (no sessions)
- Payment or PII data handling

---

## Security Tooling (CI-Enforced)

| Tool                     | Trigger                   | Failure Condition                               | Workflow                 |
|--------------------------|---------------------------|-------------------------------------------------|--------------------------|
| `gitleaks`               | Every PR + push to `main` | Any detected secret pattern                     | `security.yml`           |
| `pip-audit`              | Every PR + push to `main` | Any Critical or High CVE                        | `security.yml`           |
| `npm audit`              | Every PR + push to `main` | Any High or Critical CVE                        | `security.yml`           |
| `bandit`                 | Every PR + push to `main` | Any Medium+ finding not suppressed              | `security.yml`           |
| `semgrep` (OWASP Top 10) | Phase 6+ PRs              | Any High/Critical not in `FINDINGS_REGISTER.md` | `security.yml`           |
| Dependabot               | Weekly                    | — (opens PRs automatically)                     | `.github/dependabot.yml` |

Suppressed findings are documented in [`docs/security/FINDINGS_REGISTER.md`](docs/security/FINDINGS_REGISTER.md).  
Accepted risks are documented in [`docs/security/ACCEPTED_RISKS.md`](docs/security/ACCEPTED_RISKS.md).

---

## Dependency Vulnerability Policy

Adding a new dependency requires:
1. `pip-audit` / `npm audit` check — no Critical or High CVEs
2. License check — MIT, Apache 2.0, BSD only (GPL/AGPL require maintainer discussion)
3. Bundle size impact check for npm packages (use bundlephobia.com)
4. Justification in the PR description

See [CONTRIBUTING.md §11](CONTRIBUTING.md#11-dependency-policy) for the full policy.

---

*Security policy version: 1.0 — 2026-07-21*  
*Governance reference: [GOVERNANCE.md §8](docs/GOVERNANCE.md#8-security-policy)*

