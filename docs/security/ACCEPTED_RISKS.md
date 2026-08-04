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
| **Compensating Controls** | Cloudflare's anycast network provides volumetric DDoS protection. Production mode (DuckDB WASM) has no server-side application logic to attack. Rate limiting in FastAPI (slowapi, 60 req/min) protects the dev mode API. |
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
| **Justification** | All objects in the bucket are derived from public-domain EPA TRI data (Parquet files). There is no confidential, proprietary, or personally identifiable data in the bucket. The basemap is served from OpenFreeMap (ADR-005), not R2. The static-first architecture (ADR-004) requires unauthenticated browser reads — DuckDB WASM fetches Parquet via HTTP range requests with no mechanism to present credentials. Restricting access to authenticated clients would require a server-side token issuance endpoint, which violates the zero-budget, zero-server constraint. |
| **Compensating Controls** | (1) CORS `AllowedOrigins` prevents cross-site browser embedding from unauthorized origins. (2) All bucket content (TRI Parquet files) is already freely available from the upstream source (EPA.gov), so exfiltrating it provides no advantage over the primary source. (3) R2 does not charge for egress bandwidth — only request count — so read abuse has bounded financial impact (see RISK-006). (4) Phase 7: connecting a custom domain + Cloudflare proxy enables IP-level access controls without a backend server. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-27 |
| **Next Review Date** | 2027-07-27 |
| **Status** | Open |

---

### RISK-006: R2 Free-Tier Read Quota Exhaustion via Unauthenticated Scraping

| Field | Value |
|-------|-------|
| **Threat Ref** | RISK-005 (prerequisite) |
| **Description** | Cloudflare R2's free tier grants 10 million Class B read operations (GET/HEAD) per month. Because the bucket is publicly accessible to any HTTP client (see RISK-005) and Cloudflare Rate Limiting rules cannot be applied to `.r2.dev` URLs (they require a Cloudflare-proxied custom domain), a malicious actor running a loop against the bucket URL could exhaust the monthly quota. Exceeding the free tier triggers per-request charges ($0.36 per million reads). A sustained attack could result in unexpected billing. Parquet files use HTTP range requests, meaning a single DuckDB WASM query generates many small byte-range GET operations, amplifying the request count relative to perceived "requests." Note: basemap tiles are served from OpenFreeMap (ADR-005), not R2, so tile requests do not count against the R2 quota. |
| **Justification** | Zero-budget constraint (ADR-004). Rate Limiting on Cloudflare requires a custom domain connected to Cloudflare's proxy, which requires owning a domain — a Phase 7 prerequisite. For Phase 3 (demo stage), the app is not publicly linked; the only users are the development team, making organic quota exhaustion implausible. |
| **Compensating Controls** | (1) Cloudflare's anycast network absorbs volumetric connection-flood attacks before they reach R2. (2) R2 billing requires an explicit opt-in to paid usage — by default, Cloudflare caps R2 to the free tier and returns errors rather than silently charging; verify this is set in the R2 billing settings. (3) Cloudflare dashboard provides usage metrics and can alert on quota spikes — set a notification at 80% of 10M reads. (4) **Phase 7 mitigation:** connect a custom domain to the R2 bucket through Cloudflare's proxy, then apply a Rate Limiting rule (1,000 requests per minute per IP) and a Cache Rule (edge TTL: 1 month) — cached Parquet reads do not count against the R2 quota. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-07-27 |
| **Next Review Date** | 2027-07-27 |
| **Status** | Open |

---

### RISK-007: No CDN Caching on `.r2.dev` URLs — Every Request Hits R2 Storage Directly

| Field | Value |
|-------|-------|
| **Threat Ref** | RISK-006 (exacerbating factor) |
| **Description** | Cloudflare Cache Rules are applied at the Cloudflare proxy layer and only activate when traffic flows through a Cloudflare-proxied hostname (the orange-cloud DNS record). The `.r2.dev` public access subdomain is served directly from R2 object storage and is not routed through Cloudflare's CDN proxy. As a result, no caching occurs at the edge: every Parquet byte-range request from every user hits R2 directly and is counted as a billable read operation. For Parquet data files where the same geographic regions are repeatedly queried by different users, the absence of CDN caching means the effective request multiplier is 1× per user per session rather than the near-zero marginal cost that a cached CDN provides. This directly exacerbates the quota exhaustion risk in RISK-006. Note: basemap tiles are served from OpenFreeMap (ADR-005), not R2, so tile caching is not a concern for the R2 quota. |
| **Justification** | CDN caching for R2 requires a custom domain with Cloudflare proxy enabled — a Phase 7 task. The `.r2.dev` URL is the appropriate endpoint for Phase 3 demo use where user count is small and repeated requests from the same session are minimal. |
| **Compensating Controls** | (1) DuckDB WASM caches fetched Parquet byte ranges in browser memory across a session — repeat queries for the same facilities within a session do not re-request the same byte ranges from R2. (2) Phase 7 mitigation: connect a custom domain to the bucket and deploy a Cloudflare Cache Rule with `Edge Cache TTL: 1 month` and `Browser Cache TTL: 1 day`. After deployment, monitor the Cloudflare Cache analytics panel to verify hit ratio exceeds 90% within 24 hours of traffic. |
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

### RISK-009: Photon Geocoder Third-Party Dependency and Fair Use Compliance

| Field | Value |
|-------|-------|
| **Threat Ref** | ADR-006 (decision record); T-SEC-12 (third-party service availability) |
| **Description** | TOXMAP uses the public Photon geocoder (`photon.komoot.io`) for address-to-coordinate conversion. Photon's [Terms of Use](https://photon.komoot.io/) state: *"You can use the API for your project, but please be fair - extensive usage will be throttled. We do not guarantee for the availability and usage might be subject of change in the future."* In production mode (DuckDB WASM), there is no backend server — each user's browser makes direct requests to Photon. While per-client mitigations (200-entry cache, 1-second throttle) limit individual user abuse, they do not prevent aggregate overload if TOXMAP gains significant traffic. 1,000 concurrent users each triggering one geocode request = 1,000 requests/second to Photon from a single application. Komoot may interpret this as abuse and block all TOXMAP users (identified by `Referer` header). |
| **Justification** | (1) The $0-budget constraint (ADR-004) precludes commercial geocoding APIs (Google, HERE, MapTiler). (2) Nominatim (the OSM Foundation's geocoder) blocks server IPs from cloud/datacenter ranges — the original backend proxy approach failed during Phase 3 testing. (3) Browser-direct calls to Photon work reliably because end-user IPs (residential/business) are not subject to the same IP-range blocks. (4) Photon is MIT-licensed and Docker-deployable — self-hosting is a viable fallback if TOXMAP exceeds fair-use bounds. See ADR-006 for the full decision record. |
| **Compensating Controls** | (1) **Per-client throttling:** `frontend/src/api/geocode.ts` enforces a 1-second minimum interval between Photon requests and caches up to 200 results per browser tab. Repeated queries generate zero network calls. (2) **User-triggered only:** Geocoding fires only on explicit Search button click — no keystroke-triggered requests, no polling, no batch geocoding. (3) **Attribution displayed:** Photon/Komoot and OpenStreetMap are credited in the map footer (see read_page output). (4) **Graceful degradation:** If Photon returns an error (rate-limit, timeout, or service change), `geocodeLocation()` throws a user-friendly error; the app does not crash. Users can retry or use a different search format. (5) **Self-hosting documented:** `docs/deployment/SELF_HOSTING_GUIDE.md` provides complete instructions for deploying Photon on a VPS (~$16/month for US-only). (6) **Workers proxy option:** A Cloudflare Workers proxy can provide global caching and aggregate rate limiting for ~$0-5/month — see `docs/deployment/DEPLOYMENT_GUIDE.md` §"Cloudflare Workers Proxy". This is the recommended production mitigation. (7) **Scaling trigger defined:** If average daily geocode requests exceed 10,000, implement Workers proxy or self-host. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-08-04 |
| **Next Review Date** | 2027-02-04 (6-month review for high-traffic risk) |
| **Status** | Open |

---

### RISK-010: Aggregate Third-Party Service Load in Zero-Server Production Mode

| Field | Value |
|-------|-------|
| **Threat Ref** | ADR-004 (zero-server architecture); ADR-005; ADR-006 |
| **Description** | The production architecture (DuckDB WASM, Cloudflare Pages, no backend server) means TOXMAP has no central point to monitor or control outbound requests to third-party services (Photon, OpenFreeMap, Cloudflare R2). Each browser is an independent client. If TOXMAP becomes popular (e.g., featured on a news site, cited in a public health report), a traffic spike could simultaneously: (a) overwhelm Photon's fair-use tolerance, (b) stress OpenFreeMap's single-developer infrastructure, and (c) exhaust the R2 free-tier read quota. There is no circuit breaker, no aggregate rate limiter, and no server-side analytics to detect these conditions before they cause service degradation or third-party complaints. |
| **Justification** | (1) The zero-server constraint is fundamental to the $0/month hosting goal (ADR-004). Adding a backend proxy to rate-limit outbound requests would reintroduce server costs and operational complexity. (2) The risk is proportional to traffic — for a low-traffic public health research tool, the probability of overwhelming free services is low. (3) The services chosen (OpenFreeMap, Photon) are explicitly free-for-all-use and designed for distributed browser access. Neither requires API keys or enforces per-application quotas. (4) If traffic exceeds expectations, the self-hosting fallback paths are documented and tested. |
| **Compensating Controls** | (1) **Cloudflare Workers proxy (recommended):** Deploy a thin Workers proxy for geocoding that provides global caching (not per-browser) and aggregate rate limiting (~$0-5/month). This adds central control without a full backend server. See `docs/deployment/DEPLOYMENT_GUIDE.md` §"Cloudflare Workers Proxy" for implementation. (2) **Cloudflare Pages analytics:** Enable Cloudflare Web Analytics (free, privacy-preserving) to monitor page views. If page views exceed 50,000/month, proactively evaluate third-party service load. (3) **Proactive outreach:** Before public launch, email the Photon maintainer (via Komoot) and OpenFreeMap operator (zsolt@openfreemap.org) to introduce the project, confirm fair-use compliance, and establish a point of contact if issues arise. (4) **README disclosure:** The project README and DEPLOYMENT_GUIDE clearly state that TOXMAP depends on free third-party services for geocoding and basemap tiles, with no SLA. (5) **Scaling thresholds:** Document thresholds at which self-hosting should be triggered: Photon >10,000 requests/day estimated; OpenFreeMap — if service degrades; R2 — if monthly reads exceed 5M (50% of free tier). (6) **Fallback documentation:** Self-hosting procedures for Photon (Docker), PMTiles (R2 + boto3 upload), and alternative geocoders (Geoapify free tier, Census TIGER) are documented in `docs/deployment/`. |
| **Accepted By** | Project maintainer |
| **Date Accepted** | 2026-08-04 |
| **Next Review Date** | 2027-02-04 |
| **Status** | Open |

---

## Closed / Superseded Risks

*None.*

