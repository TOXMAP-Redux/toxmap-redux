# ADR-009: Cloudflare Workers Geocoding Proxy

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-04 |
| **Deciders** | Project maintainer |
| **Supersedes** | — |
| **Related** | ADR-004 (zero-budget hosting), ADR-006 (Photon geocoding) |

---

## Context

TOXMAP's production architecture (ADR-004) uses DuckDB WASM with no backend server. Each user's browser makes direct requests to third-party services:

```
User Browser ──► Photon (geocoding)
             ──► OpenFreeMap (basemap tiles)
             ──► Cloudflare R2 (Parquet data)
```

This creates an **aggregate overload problem**: per-client mitigations (200-entry LRU cache, 1-second throttle) limit individual abuse but cannot prevent aggregate load if TOXMAP becomes popular. 1,000 concurrent users each triggering one geocode = 1,000 requests/second to Photon from a single application.

Photon's terms state: *"Please be fair — extensive usage will be throttled."* A traffic spike could result in Photon blocking all TOXMAP users (identified by `Referer` header).

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A. Status quo (direct browser calls)** | $0, no infra | No aggregate control, fair-use risk |
| **B. Self-host Photon on VPS** | Full control | $16-105/month, operational burden |
| **C. Commercial geocoder (Google, HERE)** | SLA, high limits | Cost at scale, API key management |
| **D. Cloudflare Workers proxy** | ~$0, global cache, aggregate rate limit | Adds a dependency (our Worker) |

---

## Decision

**Implement a Cloudflare Workers proxy for geocoding requests.**

The Worker sits between the browser and Photon, providing:

1. **Global cache** — All users share one cache (not per-browser)
2. **Aggregate rate limiting** — Limits total requests to Photon, not just per-user
3. **Analytics** — Visibility into actual request volumes via Workers dashboard
4. **Graceful degradation** — Returns cached results when rate-limited

```
Browser ──► Workers Proxy ──► Photon
               │
               ├─► Cache API (global, edge-cached)
               ├─► KV (rate limit counters)
               └─► Analytics
```

### Cost Analysis

| Tier | Requests | Monthly Cost | Notes |
|------|----------|--------------|-------|
| **Free** | 100,000/day (~3M/month) | **$0** | Sufficient for <100K users/month |
| **Paid** | 10M/month included | **$5** | + $0.30 per additional million |
| **+ KV Cache** | 100K reads/day free | **$0** | 1 GB storage free |

For TOXMAP's expected traffic (public health research tool, not consumer app), the free tier is likely sufficient. Each search = 1 geocode request. 100K searches/day handles substantial traffic.

### Implementation

**Worker location:** `workers/geocode-proxy/index.ts`

**Key behaviors:**

1. **Cache-first:** Check Cloudflare Cache API before hitting Photon
2. **Rate limit:** KV-based sliding window counter (100 req/min to Photon)
3. **User-Agent:** Identify as TOXMAP with project URL
4. **CORS:** Allow requests from TOXMAP domains only
5. **Fallback:** Return 429 with error message if rate-limited and no cache

**Frontend change:** 

```typescript
// frontend/src/api/geocode.ts
const GEOCODE_URL = import.meta.env.VITE_GEOCODE_PROXY_URL 
  || 'https://photon.komoot.io/api/';
```

**Environment variable:**

```bash
# .env.production
VITE_GEOCODE_PROXY_URL=https://toxmap-geocode-proxy.<account>.workers.dev/api/geocode
```

---

## Consequences

### Positive

- **Aggregate rate limiting:** First time TOXMAP has central control over third-party request volume
- **Global cache:** Common searches (e.g., "New York", "Los Angeles") cached across all users — estimated 60-80% cache hit rate vs. 10-20% per-browser
- **Analytics:** Workers dashboard shows requests/day, cache hit rate, error rate, geographic distribution
- **Graceful scaling:** Clear path from free tier → paid tier → self-hosted Photon
- **Fair-use compliance:** Can demonstrate responsible usage to Komoot if questioned
- **$0 at low traffic:** Free tier handles ~100K searches/day

### Negative

- **Adds infrastructure:** One more thing to deploy and monitor (though minimal)
- **Single point of failure:** If Worker is misconfigured, all geocoding fails (but easy to revert to direct Photon calls)
- **Latency:** Adds one hop (~5-20ms at edge, often faster than direct due to caching)
- **Not fully serverless:** Technically adds a "server" (Worker), though it's edge-deployed and auto-scaling

### Neutral

- **Still depends on Photon:** The Worker proxies to Photon; if Photon is down, geocoding fails (but cached results still work)
- **OpenFreeMap unchanged:** Basemap tiles still go direct; Workers proxy for tiles would be complex (PMTiles byte-range handling)

---

## Deployment

```bash
# 1. Install Wrangler CLI
npm install -g wrangler

# 2. Login
wrangler login

# 3. Create KV namespace for rate limiting
wrangler kv:namespace create "RATE_LIMIT"
# Copy the ID to wrangler.toml

# 4. Deploy
cd workers/geocode-proxy
wrangler deploy

# 5. Update frontend .env.production with Worker URL
# 6. Redeploy frontend to Cloudflare Pages
```

---

## Monitoring

In Cloudflare dashboard (Workers & Pages → toxmap-geocode-proxy → Analytics):

- **Requests/day** — Traffic volume
- **Cache hit rate** — Should be >50% after warmup
- **Error rate** — Should be <1%
- **P50/P99 latency** — Should be <100ms

Set up Cloudflare notifications for:
- Requests exceed 80K/day (approaching free tier limit)
- Error rate exceeds 5%

---

## Alternatives Not Chosen

### Self-hosted Photon (Option B)

Full instructions in `docs/deployment/SELF_HOSTING_GUIDE.md`. Recommended only if:
- Workers proxy exceeds free tier consistently
- Need offline/air-gapped deployment
- Komoot discontinues public Photon service

Cost: ~$16/month (US-only) to ~$105/month (planet-wide).

### Commercial Geocoder (Option C)

Not chosen due to:
- Cost at scale (Google: $5/1000 requests after free tier)
- API key management complexity
- Vendor lock-in
- Overkill for TOXMAP's address-to-coordinate needs (no routing, no autocomplete)

### R2 Cache for Tiles (not implemented)

OpenFreeMap tiles could theoretically be cached on R2, but:
- Tiles are already CDN-cached by OpenFreeMap
- PMTiles byte-range caching is complex
- Risk-benefit ratio unfavorable

---

## References

- [Cloudflare Workers Pricing](https://developers.cloudflare.com/workers/platform/pricing/)
- [Cloudflare Cache API](https://developers.cloudflare.com/workers/runtime-apis/cache/)
- [Cloudflare Workers KV](https://developers.cloudflare.com/kv/)
- ADR-004: Zero-Budget Hosting
- ADR-006: Photon Geocoding
- RISK-009: Photon Third-Party Dependency
- RISK-010: Aggregate Third-Party Service Load
