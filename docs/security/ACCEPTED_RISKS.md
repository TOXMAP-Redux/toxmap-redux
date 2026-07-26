# Accepted Security Risks

**Owner:** Security Engineer (SEC) + Maintainers  
**Review Cadence:** Annually (with each major release); immediately on any architectural change

> This document records security risks that have been deliberately accepted rather than mitigated.  
> Each entry requires: a written justification, the name of the responsible maintainer, a date, and a next review date.  
> Risks are never silently dropped — they must be explicitly re-evaluated or closed.

---

## Register Format

| Field | Description |
|-------|-------------|
| **Risk ID** | Unique ID: `RISK-NNN` |
| **Threat Ref** | Corresponding entry in `THREAT_MODEL.md` (T-SEC-xx) or governance §8, if applicable |
| **Description** | What the risk is |
| **Justification** | Why it is accepted (budget, design constraint, out-of-scope) |
| **Compensating Controls** | Any partial mitigations that reduce (but don't eliminate) the risk |
| **Accepted By** | Maintainer name / GitHub handle |
| **Date Accepted** | ISO 8601 |
| **Next Review Date** | ISO 8601 (must not be more than 12 months from acceptance) |
| **Status** | `Open` · `Closed` (risk eliminated) · `Superseded` |

---

## Active Accepted Risks

### RISK-001: No `Content-Security-Policy report-uri`

| Field | Value |
|-------|-------|
| **Threat Ref** | GOVERNANCE.md §8 |
| **Description** | CSP violations in production are undetected because there is no `report-uri` or `report-to` endpoint to receive browser reports. |
| **Justification** | No free-tier reporting endpoint is available at $0. Implementing a reporting endpoint would require a persistent server, violating the zero-budget constraint (ADR-004). |
| **Compensating Controls** | CI Semgrep scan prevents known CSP-bypassable patterns from being introduced. The `script-src` directive with `'wasm-unsafe-eval'` (not `'unsafe-eval'`) minimizes script injection surface. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-20 |
| **Next Review Date** | 2027-07-20 |
| **Status** | Open |

---

### RISK-002: `style-src 'unsafe-inline'` in CSP

| Field | Value |
|-------|-------|
| **Threat Ref** | T-SEC-10 |
| **Description** | The CSP allows inline styles (`'unsafe-inline'` in `style-src`). This is a defense-in-depth weakness: an attacker who achieves XSS can inject styled content. |
| **Justification** | Tailwind CSS and MapLibre GL JS both inject inline styles at runtime and cannot be nonce-based without significant framework changes. |
| **Compensating Controls** | `script-src` does NOT include `'unsafe-inline'` — only `'wasm-unsafe-eval'` is allowed. Injected styles cannot execute scripts. `frame-ancestors 'none'` prevents clickjacking. React's default escaping prevents DOM XSS from API data. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-20 |
| **Next Review Date** | 2027-07-20 |
| **Status** | Open |

---

### RISK-003: Parquet File Range-Request Integrity Not Verifiable via SRI

| Field | Value |
|-------|-------|
| **Threat Ref** | T-SEC-13 |
| **Description** | DuckDB WASM fetches Parquet files using HTTP Range requests (partial content). Browser Subresource Integrity (SRI) requires the complete resource to verify — it cannot validate partial range responses. Individual Parquet chunk integrity cannot be verified on the client. |
| **Justification** | This is a fundamental limitation of the HTTP Range request + SRI interaction. Mitigating it fully would require a different data delivery mechanism. |
| **Compensating Controls** | `manifest.json` includes a SHA-256 integrity field per Parquet file (story 7.4.3). The React app verifies the manifest over HTTPS before parsing. Parquet files are served only from the official R2 bucket via HTTPS. R2 write access is limited to the `build-data.yml` workflow token. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-20 |
| **Next Review Date** | 2027-07-20 |
| **Status** | Open |

---

### RISK-004: No Web Application Firewall on Cloudflare Pages Free Tier

| Field | Value |
|-------|-------|
| **Threat Ref** | GOVERNANCE.md §8 |
| **Description** | Cloudflare's WAF product is not available on the free Pages + R2 tier. Sophisticated application-layer attacks against the static bundle or R2 endpoint are not filtered before reaching the origin. |
| **Justification** | Zero-budget constraint (ADR-004). Production mode has no server, so the "origin" is Cloudflare's own CDN — volumetric attacks are absorbed by Cloudflare's network at no cost. |
| **Compensating Controls** | Cloudflare's anycast network provides volumetric DDoS protection. Production mode (DuckDB WASM) has no server-side application logic to attack. Rate limiting in FastAPI protects the dev mode API. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-20 |
| **Next Review Date** | 2027-07-20 |
| **Status** | Open |

---

## Closed / Superseded Risks

*None.*

