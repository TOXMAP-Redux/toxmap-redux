# TOXMAP Redux Project Governance

**Version:** 1.1 · **Date:** 2026-07-21  
**Human contributors:** See [CONTRIBUTING.md](../CONTRIBUTING.md)  
**AI agents:** See [AGENTS.md](../AGENTS.md)

---

## 1. Purpose

This document defines:
- Who has authority to make which decisions
- How architecture decisions are made and changed
- How requirements evolve
- How the project is maintained and released
- How conflicts are resolved

---

## 2. Roles

### 2.1 Maintainer

Maintainers have merge rights to `main` and final say on all architectural decisions. Responsibilities:
- Review and merge PRs
- Accept or reject RFCs
- Approve changes to protected files
- Cut releases
- Respond to security disclosures within 72 hours
- Keep the roadmap current

**Current maintainers:** See [MAINTAINERS.md](../MAINTAINERS.md) for the authoritative list with GitHub handles and areas of focus.

### 2.2 Contributor

Anyone who submits a PR. Contributors:
- May implement any story from the current sprint
- May open RFC issues for new features
- May review PRs (reviews are welcome from anyone; merge requires a Maintainer)
- Are subject to the Code of Conduct at all times

### 2.3 AI Agent

AI coding agents (LLM-backed automation) operating on the codebase. Agents:
- Operate under the additional constraints in [AGENTS.md](../AGENTS.md)
- May open PRs autonomously; PRs require at least **1 human maintainer approval** before merge
- May not approve other agents' PRs
- Must tag commits with `[agent]` suffix
- Are subject to the same CI gates as human contributors
- Must return a completion report to the Phase Manager upon finishing each work session (see [AGENTS.md §14](../AGENTS.md))

### 2.4 Data Steward

A contributor with specific authority over ingestion scripts and seed data accuracy. Responsibilities:
- Verify that seed data values trace to primary sources (NLM articles, UCD 2011 study, EPA datasets)
- Review all PRs with the `seed-data` label
- Approve or reject seed data modification RFCs

### 2.5 Security Engineer

A contributor (human or AI agent) with specific authority over the security posture of the project. Responsibilities:
- Own and maintain `SECURITY.md`, `.github/workflows/security.yml`, `.github/dependabot.yml`, `docs/security/`, and all security-related middleware
- Triage and prioritize vulnerability disclosures within 72 hours of receipt
- Review all PRs that introduce new dependencies, modify API parameter validation, or touch GitHub Actions workflows
- Maintain `docs/security/FINDINGS_REGISTER.md` (suppressed findings) and `docs/security/ACCEPTED_RISKS.md`
- Ensure every release passes the Phase 7 security sign-off checklist before Milestone M7 is declared

> **On small teams:** Security Engineer responsibilities may be distributed across BE, FE, and OPS contributors. The `agents/security-engineer/prompt.md` defines exactly which stories belong to the SEC role regardless of who performs them.

---

## 3. Decision Authority Matrix

| Decision Type                                              | Who Can Decide                 | Process                                                           |
|------------------------------------------------------------|--------------------------------|-------------------------------------------------------------------|
| Bug fix implementation                                     | Any contributor                | PR + 1 maintainer approval                                        |
| New story implementation                                   | Any contributor                | PR + 1 maintainer approval                                        |
| Adding an optional data layer                              | Any contributor                | PR + 1 maintainer approval + docs update                          |
| New npm/pip dependency                                     | Any contributor                | PR + maintainer review of license/CVE                             |
| Security finding suppression (`# nosec`, `# nosemgrep`)    | Security Engineer              | Entry in `docs/security/FINDINGS_REGISTER.md` + maintainer review |
| Accepted risk addition (`docs/security/ACCEPTED_RISKS.md`) | Security Engineer + Maintainer | Written justification + annual review date                        |
| New required feature (F-xx)                                | Maintainers only               | RFC → discussion → maintainer vote                                |
| API contract change                                        | Maintainers only               | RFC → discussion → maintainer vote                                |
| Gherkin scenario change                                    | Maintainers only               | RFC → discussion → maintainer vote                                |
| Seed data value change                                     | Data Steward + Maintainer      | RFC with primary source citation → 2 approvals                    |
| ADR change                                                 | Maintainers only               | Full ADR revision process (§4)                                    |
| New ADR                                                    | Maintainers only               | Full ADR creation process (§4)                                    |
| Release cut                                                | Maintainers only               | Release process (§7)                                              |
| Maintainer addition                                        | Existing maintainers           | Unanimous consent of current maintainers                          |

---

## 4. ADR Lifecycle

Architecture Decision Records (ADRs) capture significant technical decisions with long-term consequences. 
### ADR Statuses

| Status       | Meaning                                                 |
|--------------|---------------------------------------------------------|
| `Proposed`   | Under discussion; not yet binding                       |
| `Accepted`   | Binding; all implementation must conform                |
| `Rejected`   | Discussion finialized; ADR proposal not moving forward  |
| `Deprecated` | Superseded by a newer ADR; no new code should follow it |
| `Superseded` | Replaced by another ADR; link to the replacement        |

### Promoting an ADR from Proposed → Accepted

1. ADR has been in `Proposed` status for at least **5 business days**
2. All review checklist items in the ADR are completed
3. At least **2 maintainers** have reviewed and approved the ADR document
4. No open blocking concerns in the ADR's GitHub issue
5. A maintainer updates the `Status` field and merges

**Single-maintainer exception:** If the project has exactly one maintainer (e.g., founder stage
or between maintainer appointments), that maintainer's approval is sufficient to promote an
ADR from Proposed to Accepted. This exception is automatically voided the moment a second
maintainer is added.

### Changing an Accepted ADR

This is a **breaking change** and follows the full RFC process:

1. Open a GitHub issue titled `RFC: Revise ADR-00X — [reason]` with label `rfc` + `adr-change`
2. Describe: what is changing, why, what breaks, what migration is required
3. Minimum **7-day discussion period**
4. Requires **unanimous maintainer approval** (not just majority)
5. If approved: create a new ADR that supersedes the old one; mark the old ADR `Superseded`
6. Update all dependent documents that reference the changed decision

**Deadlock clause:** If unanimous consent cannot be reached within 14 calendar days of the RFC
opening, the RFC is escalated to a community vote (all contributors with ≥ 1 merged PR). A
simple majority of participating voters decides. Tie goes to the status quo (existing ADR).

### Creating a New ADR

New ADRs are required when:
- A significant technology choice is being made for the first time
- An existing architectural decision needs to be overridden
- A new deployment target or runtime environment is being adopted

Template for new ADRs: follow the structure of [ADR-001](adr/ADR-001-fastapi-postgis-react.md) exactly.

---

## 5. Requirements Change Process

### Adding a new Functional Requirement (F-xx)

1. Open an RFC issue: `RFC: Add F-xx — [capability name]`
2. RFC must include:
   - User story (As a... I want... So that...)
   - Data source (which EPA/NLM dataset supports this)
   - Proposed Gherkin scenario
   - ADR-001 or ADR-004 impact assessment
   - Effort estimate
3. Minimum **5-day discussion** period
4. Requires **1 maintainer approval**
5. If approved: maintainer adds to `TOXMAP_TECH_STACK_ANALYSIS.md §3`, creates a roadmap story, and closes the RFC

### Changing a Must/Should/Could Priority

Priority changes from `Could` → `Should` or `Should` → `Must` are **scope-increasing** changes and require an RFC. Downward priority changes (removing a `Must`) also require an RFC with documented justification.

### Removing a Functional Requirement

Requires a full RFC with justification. Cannot remove a requirement if there is an existing passing Gherkin scenario that tests it — the scenario must be deprecated first.

---

## 6. Conflict Resolution

### Technical disagreements in PRs

1. The PR author and reviewer attempt to resolve in PR comments
2. If unresolved after 3 exchanges, either party may escalate by tagging `@maintainers`
3. A third maintainer makes a binding decision within 2 business days
4. The decision is documented in the PR as a comment starting with `DECISION:`

### ADR disagreements

Follow the ADR Lifecycle process. If maintainers cannot reach unanimous consent on an ADR change, the status quo (existing ADR) is preserved.

### Code of Conduct violations

1. Reporter opens a **private** issue addressed to maintainers
2. Maintainers acknowledge within 24 hours
3. Resolution within 7 days
4. Actions range from a warning to a permanent ban from the project

---

## 7. Release Process

### Versioning

TOXMAP follows [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR: Breaking API contract change or ADR supersession
MINOR: New feature shipped (new Gherkin scenarios passing, new endpoint, new layer)
PATCH: Bug fix, performance improvement, documentation update
```

First stable release: `1.0.0` — when all 7 roadmap milestones (M0–M7) are achieved.

### Release Checklist

```markdown
## Pre-Release
- [ ] `pytest tests/ --tb=short` exits 0 (all Gherkin scenarios pass — count grows with phases)
- [ ] `pytest tests/features/e2e/ux_invariants.feature` exits 0 (all UX invariants pass)
- [ ] `pytest tests/benchmarks/ --benchmark-compare` exits 0 (all performance SLAs pass)
- [ ] Schemathesis passes with `--checks all`
- [ ] `CHANGELOG.md` updated with all changes since last release
- [ ] Version bumped in `pyproject.toml` and `package.json`

## Release
- [ ] Git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] GitHub Release created with changelog
- [ ] GitHub Actions `build-data.yml` triggered to refresh Parquet files
- [ ] Cloudflare Pages deployment confirmed live

## Post-Release
- [ ] `main` branch deployment smoke test: T-01 + T-03 against production
- [ ] Announce in project README: "Latest stable: vX.Y.Z"
```

### Data Release Cadence

EPA TRI data is released annually in late July/early August. A data release is triggered by:

1. EPA publishes the new TRI year on epa.gov
2. A maintainer triggers the `build-data.yml` GitHub Actions workflow manually *(created in Phase 0 story 0.3.2; upgraded to full pipeline in Phase 1 story 1.5.2)*
3. New Parquet files uploaded to Cloudflare R2
4. Smoke tests confirm new year is queryable
5. `(latest year)` label in the UI updates automatically on next deploy

Data releases do not increment the software version number.

---

## 8. Security Policy

### Supported Versions

Only the latest release on `main` is supported for security patches.

### Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

1. Open a private security advisory at `https://github.com/VictorCannestro/toxmap/security/advisories/new`
2. Include: affected component, reproduction steps, potential impact
3. Maintainers acknowledge within **72 hours**
4. If confirmed: patch developed in a private branch, coordinated disclosure, patch released within 14 days

### CVE Response SLAs

| Severity | CVSS Range | Response Target                       | Release Type            |
|----------|------------|---------------------------------------|-------------------------|
| Critical | ≥ 9.0      | Patch within **48 hours**             | Emergency patch release |
| High     | 7.0–8.9    | Patch within **7 days**               | Patch release           |
| Medium   | 4.0–6.9    | Address in **next scheduled release** | Minor or patch release  |
| Low      | < 4.0      | Address in **next scheduled release** | Best effort             |

### Security Scope

This project is a **public read-only data visualization tool** with no user authentication, no user data storage, and no payment processing. The security posture is shaped by this constraint: threats that require user accounts, persistent session state, or financial data handling are out of scope.

**In-scope attack surface:**

| Component | Threat | Mitigation |
|-----------|--------|-----------|
| FastAPI query parameters | SQL injection, resource exhaustion (oversized radius/bbox queries) | Pydantic validators (bounds, patterns, max values); parameterized queries; rate limiting (slowapi 60 req/min) |
| DuckDB WASM client-side SQL | Query injection via user input interpolated into SQL strings | Parameterized `$variable` syntax enforced in all query hooks; code audit in Phase 6 |
| Python and npm dependencies | Known CVEs in pinned versions | `pip-audit` + `npm audit --audit-level=high` in `security.yml` CI job on every PR |
| GitHub Actions workflows | Supply chain attack via mutable action tags (`@v3`) | All third-party actions pinned to full 40-char SHA; Dependabot tracks updates |
| Secrets in codebase or git history | Credential leakage | `gitleaks` scan in `security.yml`; `.gitignore` for `.env` files; no hardcoded credentials rule |
| Cloudflare R2 bucket | Object poisoning if write access misconfigured | R2 CORS policy limits to `GET` and `HEAD` only from approved origins; API token has minimum required scope |
| Browser Content Security Policy | XSS; `SharedArrayBuffer` blocked (DuckDB WASM failure) | `_headers` file configures COEP/COOP/CSP; `'wasm-unsafe-eval'` required for DuckDB WASM execution |
| FastAPI error responses | Internal path / stack trace disclosure | Global 500 handler returns generic message; full trace logged server-side only |
| EPA data ingestion (external URL fetches) | SSRF if download URL is parameterized | All EPA download URLs are module-level constants; allow-list prefix check before every `requests.get()` |
| `VITE_`-prefixed env vars | Secret inlined into browser bundle at build time | Policy: no `VITE_` var may contain a credential; CI `grep` check enforced |

**Out of scope (by design):**

- Authentication and authorization (no users; no accounts)
- CSRF protection (no state-mutating endpoints)
- Session fixation or hijacking (no sessions)
- Payment or PII data handling

### Security Tooling (CI-Enforced)

| Tool                     | Stage                     | Failure Condition                                           | Workflow                 |
|--------------------------|---------------------------|-------------------------------------------------------------|--------------------------|
| `gitleaks`               | Every PR + push to `main` | Any detected secret pattern                                 | `security.yml`           |
| `pip-audit`              | Every PR + push to `main` | Any Critical or High CVE in backend dependencies            | `security.yml`           |
| `npm audit`              | Every PR + push to `main` | Any High or Critical vulnerability in frontend dependencies | `security.yml`           |
| `bandit`                 | Every PR + push to `main` | Any Medium+ finding not in the suppression allow-list       | `security.yml`           |
| `semgrep` (OWASP Top 10) | Phase 6+ PRs              | Any High or Critical finding not in `FINDINGS_REGISTER.md`  | `security.yml`           |
| Dependabot               | Weekly                    | — (opens PRs automatically)                                 | `.github/dependabot.yml` |

### Dependency Vulnerability Policy

- **Critical CVE (CVSS ≥ 9.0):** Patch within 48 hours; emergency release if needed
- **High CVE (CVSS 7.0–8.9):** Patch within 7 days
- **Medium/Low CVE:** Address in next scheduled release

### Production Security Posture (Phase 7+)

The production deployment (Cloudflare Pages + DuckDB WASM) has no traditional server. The security boundary shifts to:

1. **Static asset integrity** — `manifest.json` includes SHA-256 integrity fields for all Parquet files
2. **HTTP security headers** — `frontend/public/_headers` enforces COEP, COOP, CSP, HSTS, and anti-clickjacking headers on every response
3. **R2 bucket hardening** — public `GET`/`HEAD` only; write access restricted to the Cloudflare API token used in `build-data.yml`
4. **GitHub Actions supply chain** — all third-party actions pinned to full SHA; Dependabot opens update PRs weekly

The Security Engineer agent's Phase 7 stories (7.4.1–7.4.3) must be complete before Milestone M7 is declared. See `agents/security-engineer/prompt.md §Phase 7` for acceptance criteria.

---

## 9. Data Provenance Policy

TOXMAP displays information about chemical releases and hazardous waste sites. Accuracy is a public health matter. The following provenance rules apply to all data in the system:

### Primary Sources (Authoritative)

| Data                          | Source                             | Verifiability         |
|-------------------------------|------------------------------------|-----------------------|
| TRI facility releases         | EPA TRI Basic Data Files (epa.gov) | Publicly downloadable |
| Superfund/NPL sites           | EPA NPL list (epa.gov)             | Publicly downloadable |
| HRS scores                    | EPA CERCLIS/SEMS                   | Publicly downloadable |
| Census demographics           | US Census Bureau TIGER/Line        | Publicly downloadable |
| ATSDR ToxFAQ URLs             | CDC/ATSDR                          | Public website        |
| Test seed values (T-03, T-04) | UCD Inc. usability study 2011      | PMC-archived          |

### Rules

1. **No synthetic data in production.** All facility data served to users must originate from an authoritative source listed above.
2. **Seed data is test-only.** The `seed.sql` file must never be used to populate a production database with fictional records.
3. **The co-occurrence disclaimer is mandatory** on any view that shows health outcomes overlaid with release data. This is not configurable.
4. **Removing data is not allowed via the UI.** The app is read-only by design.
5. **Version-pinned data.** Each production deployment must record which EPA TRI year(s) and which Census year(s) are loaded, surfaced via a `/api/v1/meta` endpoint.

---

## 10. Governance Changes

Changes to this document require:
1. A PR with the label `governance`
2. Minimum **7-day comment period** open to all contributors
3. **Unanimous maintainer approval**

The governance document version is tracked in the version header above. All changes are logged in `CHANGELOG.md`.

---

*This governance model is inspired by the [CNCF Templates](https://contribute.cncf.io/projects/best-practices/templates/) and adapted for a small open-source project.*

