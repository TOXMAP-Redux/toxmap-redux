# TOXMAP Threat Model

**Version:** 1.0 · **Date:** 2026-07-20  
**Owner:** Security Engineer (SEC)  
**Review Cadence:** Before each major release; immediately on any architectural change

> This document expands the threat model quick reference in `agents/security-engineer/prompt.md` with full attack scenario descriptions, evidence of exploitability, and residual risk assessments.

---

## 1. System Overview

TOXMAP is a **public, read-only, zero-budget** data visualization tool. It has two distinct runtime modes that share the same frontend but have different attack surfaces:

**Development mode** (`VITE_DATA_SOURCE=api`):
- React SPA → FastAPI (Python 3.12) → PostgreSQL 16 + PostGIS 3.4
- Attack surface: HTTP endpoints, query parameters, Docker network

**Production mode** (`VITE_DATA_SOURCE=duckdb`):
- React SPA + DuckDB WASM → Cloudflare R2 (static Parquet files)
- No server in the request path
- Attack surface: browser execution context, Cloudflare R2 bucket, GitHub Actions pipeline

---

## 2. Assets and Their Value to an Attacker

| Asset | Attacker Value | Business Impact of Compromise |
|-------|---------------|-------------------------------|
| EPA TRI Parquet data on R2 | Low (public data) | Data integrity loss → users receive false public health information |
| `manifest.json` on R2 | Medium (controls which data is loaded) | Poisoned manifest could direct users to attacker-controlled Parquet files |
| GitHub Actions secrets (`CF_API_TOKEN`, `CF_ACCOUNT_ID`) | High (write access to R2 + Cloudflare Pages deploy) | Full platform takeover; arbitrary content deployed to production |
| PostGIS database (dev/CI) | Medium (contains seed/real TRI data) | Data exfiltration; service disruption |
| React bundle on Cloudflare Pages | Medium (served to all users) | XSS; credential theft if auth ever added; reputational damage |
| CI/CD pipeline integrity | High | Supply chain poisoning; backdoored assets shipped to users |

---

## 3. Threat Catalog (T-SEC-xx)

### T-SEC-01: Resource Exhaustion via Geospatial Query

**Attack:** An attacker sends repeated `GET /api/v1/facilities?lat=39&lon=-76&radius_miles=500` requests. Each query triggers a PostGIS `ST_DWithin` scan over millions of facility records. Combined with the lack of rate limiting, this can saturate database CPU and degrade service for all users.

**Exploitability:** High — requires no authentication; the endpoint is publicly documented in `/docs`.

**Current Controls:** Radius cap (500 miles) in Pydantic validators (story 2.8.1); rate limiting (60 req/min, story 2.8.2); GIST spatial index limits scan scope.

**Residual Risk:** Low after Phase 2 controls are in place. Production mode (DuckDB WASM) has no server to exhaust.

---

### T-SEC-02: SQL Injection via Query Parameters

**Attack:** An attacker injects SQL fragments via the `chemical`, `state`, or `medium` parameters (e.g., `chemical=LEAD%27%20OR%201%3D1--`).

**Exploitability:** Low — SQLAlchemy async with parameterized queries is enforced project-wide. An f-string SQL pattern would need to be introduced by a future contributor.

**Current Controls:** Project-wide rule against f-string SQL; parameterized queries required; `bandit` B608 (hardcoded SQL) rule enabled in CI; `semgrep` p/python rules in Phase 6.

**Residual Risk:** Low. Defense-in-depth: Pydantic `pattern=` validators limit the character set of the `state` field to `^[A-Z]{2}$`; `medium` is a `Literal` type with an explicit allow-list.

---

### T-SEC-03: DuckDB WASM Client-Side SQL Injection

**Attack:** A user-controlled value (e.g., a chemical name from the search input) is interpolated into a DuckDB SQL string rather than passed as a `$param` binding: `conn.query("SELECT * FROM read_parquet(...) WHERE chemical_name = '" + userInput + "'")`. An attacker could close the quote and inject arbitrary DuckDB SQL.

**Exploitability:** Medium — requires a developer error to introduce. DuckDB WASM runs client-side, so the "victim" is only the attacker themselves, unless the injected query is used to exfiltrate data from a shared session (not applicable in stateless WASM).

**Current Controls:** Code review requirement; DuckDB parameterized query rule; Phase 6 grep audit for template literals containing query params.

**Residual Risk:** Low. The primary harm of DuckDB WASM SQL injection is self-inflicted (the attacker owns the browser context) or causes a denial of service of their own session.

---

### T-SEC-04 / T-SEC-05: Dependency CVE (Python / npm)

**Attack:** A transitive dependency contains a known vulnerability (e.g., an XML parser with an XXE vulnerability, or a cryptographic library with a timing attack). The attacker exploits the vulnerability through crafted API requests.

**Exploitability:** Varies by CVE. TOXMAP's exposed functionality (read-only GIS API) limits exploitability of most web-app CVEs.

**Current Controls:** `pip-audit` (Python) and `npm audit --audit-level=high` run on every PR in `security.yml`. Dependabot opens PRs weekly.

**Residual Risk:** Monitored. The CI pipeline prevents merging PRs that introduce High/Critical CVEs.

---

### T-SEC-06: Secrets Committed to Git History

**Attack:** A developer accidentally commits a `CF_API_TOKEN`, database password, or other credential. Even after the secret is rotated and removed from HEAD, it remains in git history and can be extracted with `git log --all -p`.

**Exploitability:** High — git history is public.

**Current Controls:** `gitleaks` scan in `security.yml` on every PR and push to `main`. `.gitignore` excludes `.env` files. All secrets stored in GitHub Secrets, accessed via `${{ secrets.NAME }}`.

**Residual Risk:** Low if controls are maintained. If a secret is detected in history, escalate immediately — a history rewrite is required.

---

### T-SEC-08: GitHub Actions Supply Chain Attack

**Attack:** The maintainer of a GitHub Action that TOXMAP uses (`cloudflare/wrangler-action`, `codecov/codecov-action`, etc.) is compromised or their account is taken over. They push malicious code to the `@v3` tag. The next time `build-data.yml` runs, the malicious action executes in the CI environment with access to all GitHub Secrets, including `CF_API_TOKEN`.

**Exploitability:** Medium — has occurred against other open-source projects (e.g., the `tj-actions/changed-files` incident in 2023).

**Current Controls:** All third-party Actions pinned to full 40-char SHA (story 0.5.4). Dependabot `github-actions` entry notifies when a new version is available, allowing the maintainer to review before updating the SHA.

**Residual Risk:** Low after SHA pinning. Dependabot ensures pins don't stagnate.

---

### T-SEC-09 / T-SEC-10: Missing COEP/COOP and CSP

**Attack (T-SEC-09):** `Cross-Origin-Embedder-Policy: require-corp` and `Cross-Origin-Opener-Policy: same-origin` are missing from the Cloudflare Pages response headers. `SharedArrayBuffer` is blocked by modern browsers. DuckDB WASM silently falls back to a limited single-threaded mode or fails to initialize entirely, causing production queries to fail or return incomplete results.

**Attack (T-SEC-10):** A permissive or missing Content Security Policy allows injected scripts (via XSS) to execute. Even without an XSS vulnerability today, a missing CSP is a defense-in-depth failure.

**Exploitability:** T-SEC-09: High probability (browser policy) if headers are missing. T-SEC-10: Low exploitability (no XSS vectors identified).

**Current Controls:** Vite dev server `server.headers` includes COEP/COOP. `frontend/public/_headers` configures production Cloudflare Pages headers (story 7.4.1). Phase 6 Playwright test validates DuckDB WASM initializes correctly after headers are set.

**Residual Risk:** Low after Phase 6 validation. `'unsafe-inline'` in `style-src` is an accepted risk documented in `ACCEPTED_RISKS.md`.

---

### T-SEC-13: Tampered Parquet or `manifest.json` on R2

**Attack:** An attacker compromises the `CF_API_TOKEN` used by `build-data.yml`, uploads a Parquet file with falsified TRI release data (e.g., reducing all release quantities to zero, or changing facility locations), and overwrites `manifest.json`. Users load the application and see false public health data.

**Exploitability:** Low (requires `CF_API_TOKEN` compromise). High impact if it occurs.

**Current Controls:** Parquet integrity fields in `manifest.json` (`sha256-<base64>` per story 7.4.3); R2 API token minimum-scope (story 7.4.2); HTTPS enforced by Cloudflare for all R2 fetches.

**Residual Risk:** Medium. Full SRI verification of individual Parquet chunks via HTTP Range requests is not feasible; the integrity check operates at the manifest level only. Documented in `ACCEPTED_RISKS.md`.

---

## 4. Out-of-Scope Threats

The following threats are **not** in scope for TOXMAP due to its design constraints:

| Threat | Why Out of Scope |
|--------|-----------------|
| Authentication bypass | No authentication exists by design |
| Session hijacking / fixation | No sessions |
| CSRF | No state-mutating endpoints |
| Privilege escalation | No role system |
| PII exfiltration | No PII stored or processed |
| Payment fraud | No payment processing |
| Server-side request forgery (SSRF) in prod | Production has no server; DuckDB WASM fetches only from the R2 base URL |

---

## 5. Review and Update Process

This document must be updated when:
- A new external data source or CDN is added to the architecture
- A new API endpoint is added to `TOXMAP_API_CONTRACT.md`
- The production hosting topology changes (e.g., Option B fallback is activated)
- A security incident occurs
- Annually (scheduled with the October EPA data release review)

