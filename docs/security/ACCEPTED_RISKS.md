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

### RISK-005: R2 Bucket Publicly Readable by Any HTTP Client — CORS Does Not Restrict Non-Browser Access

| Field | Value |
|-------|-------|
| **Threat Ref** | RISK-004 (related — no WAF) |
| **Description** | The `toxmap-data` R2 bucket has public read access enabled. CORS headers (`AllowedOrigins`) restrict which origins browsers will permit, but CORS is enforced exclusively by browsers. Any non-browser HTTP client (`curl`, `wget`, Python `requests`, etc.) ignores CORS headers entirely and can read any object in the bucket without restriction. The bucket's `.r2.dev` public URL is guessable once the account ID is known, and R2 public bucket URLs follow a predictable format (`pub-<account_hash>.r2.dev`). |
| **Justification** | All objects in the bucket are derived from public-domain sources: OpenStreetMap (ODbL licence) for the PMTiles basemap and EPA TRI public data for Parquet files. There is no confidential, proprietary, or personally identifiable data in the bucket. The static-first architecture (ADR-004) requires unauthenticated browser reads — MapLibre GL JS fetches tiles and DuckDB WASM fetches Parquet via HTTP range requests with no mechanism to present credentials. Restricting access to authenticated clients would require a server-side token issuance endpoint, which violates the zero-budget, zero-server constraint. |
| **Compensating Controls** | (1) CORS `AllowedOrigins` prevents cross-site browser embedding from unauthorized origins. (2) All bucket content is already freely available from upstream sources (Protomaps builds, EPA.gov), so exfiltrating it provides no advantage over the primary source. (3) R2 does not charge for egress bandwidth — only request count — so read abuse has bounded financial impact (see RISK-006). (4) Phase 7: connecting a custom domain + Cloudflare proxy enables IP-level access controls without a backend server. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-27 |
| **Next Review Date** | 2027-07-27 |
| **Status** | Open |

---

### RISK-006: R2 Free-Tier Read Quota Exhaustion via Unauthenticated Scraping

| Field | Value |
|-------|-------|
| **Threat Ref** | RISK-005 (prerequisite) |
| **Description** | Cloudflare R2's free tier grants 10 million Class B read operations (GET/HEAD) per month. Because the bucket is publicly accessible to any HTTP client (see RISK-005) and Cloudflare Rate Limiting rules cannot be applied to `.r2.dev` URLs (they require a Cloudflare-proxied custom domain), a malicious actor running a loop against the bucket URL could exhaust the monthly quota. Exceeding the free tier triggers per-request charges ($0.36 per million reads). A sustained attack could result in unexpected billing. Protomaps tile files use HTTP range requests, meaning a single logical tile map interaction generates many small byte-range GET operations, amplifying the request count relative to perceived "requests." |
| **Justification** | Zero-budget constraint (ADR-004). Rate Limiting on Cloudflare requires a custom domain connected to Cloudflare's proxy, which requires owning a domain — a Phase 7 prerequisite. For Phase 3 (demo stage), the app is not publicly linked; the only users are the development team, making organic quota exhaustion implausible. |
| **Compensating Controls** | (1) Cloudflare's anycast network absorbs volumetric connection-flood attacks before they reach R2. (2) R2 billing requires an explicit opt-in to paid usage — by default, Cloudflare caps R2 to the free tier and returns errors rather than silently charging; verify this is set in the R2 billing settings. (3) Cloudflare dashboard provides usage metrics and can alert on quota spikes — set a notification at 80% of 10M reads. (4) **Phase 7 mitigation:** connect a custom domain to the R2 bucket through Cloudflare's proxy, then apply a Rate Limiting rule (1,000 requests per minute per IP) and a Cache Rule (edge TTL: 1 month) — cached tile reads do not count against the R2 quota. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-27 |
| **Next Review Date** | 2027-07-27 |
| **Status** | Open |

---

### RISK-007: No CDN Caching on `.r2.dev` URLs — Every Request Hits R2 Storage Directly

| Field | Value |
|-------|-------|
| **Threat Ref** | RISK-006 (exacerbating factor) |
| **Description** | Cloudflare Cache Rules are applied at the Cloudflare proxy layer and only activate when traffic flows through a Cloudflare-proxied hostname (the orange-cloud DNS record). The `.r2.dev` public access subdomain is served directly from R2 object storage and is not routed through Cloudflare's CDN proxy. As a result, no caching occurs at the edge: every tile byte-range request from every user hits R2 directly and is counted as a billable read operation. For a PMTiles basemap where the same geographic tiles are repeatedly requested by different users, the absence of CDN caching means the effective request multiplier is 1× per user per session rather than the near-zero marginal cost that a cached CDN provides. This directly exacerbates the quota exhaustion risk in RISK-006. |
| **Justification** | CDN caching for R2 requires a custom domain with Cloudflare proxy enabled — a Phase 7 task. The `.r2.dev` URL is the appropriate endpoint for Phase 3 demo use where user count is small and repeated requests from the same session are minimal. |
| **Compensating Controls** | (1) MapLibre GL JS caches vector tiles in browser memory and IndexedDB across a session — repeat pan/zoom interactions within a session do not re-request the same tile bytes from R2. (2) Phase 7 mitigation: connect a custom domain to the bucket and deploy a Cloudflare Cache Rule with `Edge Cache TTL: 1 month` and `Browser Cache TTL: 1 day`. After deployment, monitor the Cloudflare Cache analytics panel to verify hit ratio exceeds 90% within 24 hours of traffic. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-27 |
| **Next Review Date** | 2027-07-27 |
| **Status** | Open |

---

### RISK-008: OpenFreeMap Third-Party CDN Dependency for Basemap Tiles

| Field | Value |
|-------|-------|
| **Threat Ref** | ADR-005 (decision record for this change) |
| **Description** | Per ADR-005, the MapLibre GL basemap is served from [OpenFreeMap](https://openfreemap.org), a free hosted tile CDN operated by a single independent developer. If the service experiences an outage, is discontinued, or changes its URL structure, the map background goes blank for all users. Unlike R2 (which TOXMAP operates), OpenFreeMap has no SLA, no uptime guarantee, and no contractual commitment to continued operation. |
| **Justification** | Self-hosting Protomaps PMTiles on R2 was evaluated during Phase 3 (2026-07-27) and found impractical within the zero-budget constraint: the US basemap extract is ~2.5 GiB, Wrangler CLI has a 300 MiB hard limit, and working upload requires a separate S3 API credential flow. The operational complexity was disproportionate to the benefit for a visual background layer. See ADR-005 for the full decision record. |
| **Compensating Controls** | (1) A basemap outage affects only the visual tile background — TRI facility markers, chemical search, results table, facility detail, and all TOXMAP data functionality remain fully operational. Users can search and find facilities even with a blank background. (2) The complete self-hosting fallback procedure is documented and verified in `docs/deployment/PMTILES_R2_UPLOAD.md` and `scripts/upload_r2.py`. Switching to self-hosted tiles requires only updating `VITE_MAPLIBRE_STYLE` and executing the upload. (3) OpenFreeMap is open-source — if the hosted service is discontinued, the infrastructure can be self-operated. (4) Phase 7 runbook includes a monitoring note: verify the OpenFreeMap style URL is responsive before each production deployment. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-27 |
| **Next Review Date** | 2027-07-27 |
| **Status** | Open |

---

## Closed / Superseded Risks

*None.*

