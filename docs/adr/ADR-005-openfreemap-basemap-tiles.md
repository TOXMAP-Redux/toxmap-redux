# ADR-005: OpenFreeMap Hosted Tiles for Basemap (Supersedes PMTiles Self-Hosting in ADR-004)

| Field          | Value |
|----------------|-------|
| **ID**         | ADR-005 |
| **Title**      | Use OpenFreeMap Hosted Tiles for the MapLibre Basemap Instead of Self-Hosted Protomaps PMTiles on Cloudflare R2 |
| **Date**       | 2026-07-27 |
| **Status**     | **Accepted** |
| **Deciders**   | Project maintainer |
| **Amends**     | [ADR-004 §Option A](ADR-004-zero-budget-hosting.md) — specifically the assumption that the US basemap PMTiles file would be self-hosted on Cloudflare R2 |
| **Parent ADR** | [ADR-004](ADR-004-zero-budget-hosting.md) |

> This ADR does **not** change the overall hosting strategy in ADR-004 (Cloudflare Pages + R2 + DuckDB WASM). It changes only the source of the MapLibre basemap tiles from self-hosted Protomaps PMTiles to the OpenFreeMap hosted CDN.

---

## Context

ADR-004 specified that the MapLibre GL basemap would be served from a Protomaps PMTiles file uploaded to Cloudflare R2. The ADR estimated the file size as "~600 MB for US" and treated the upload as a routine one-time setup step.

During Phase 3 implementation on 2026-07-27, the actual upload process was attempted and revealed a series of compounding problems that invalidated the ADR-004 assumption.

### What ADR-004 assumed

> "PMTiles file (~600 MB for US)" stored on R2, uploaded once, served via R2's public URL.

### What was discovered during implementation

**1. The Protomaps world build is 127.64 GiB, not ~600 MB.**

The Protomaps Daily build available at [maps.protomaps.com/builds/](https://maps.protomaps.com/builds/) is a full-planet vector tile set. No pre-built US regional extract is published. The "~600 MB" figure in ADR-004 was incorrect by a factor of ~200×.

**2. A US bounding-box extract still produces a 2–5 GiB file.**

Using `pmtiles extract` with HTTP range requests against the remote world build and a US bounding box (`-127,17,-64,50`) with `--maxzoom=13` produced a ~4.5 GiB file. At `--maxzoom=14` (individual street detail) the extract is ~9.4 GiB — nearly exhausting R2's entire 10 GB free tier before Parquet data files are added.

**3. Wrangler CLI cannot upload files over 300 MiB.**

`wrangler r2 object put` has a hard 300 MiB limit. Wrangler 4.x also defaults to local simulation mode; without `--remote` it silently reports success while writing to a local fake bucket, leaving the real R2 bucket empty. The `--multipart-concurrency` flag suggested in initial documentation does not override the size limit.

**4. The Cloudflare dashboard has the same 300 MB limit.**

Dashboard drag-and-drop upload is also capped at 300 MB and cannot upload the file.

**5. Working upload requires a separate R2 S3 API credential flow.**

Files over 300 MiB require the R2 S3 Compatibility API (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`). This requires a separate "R2 API Token" (distinct from the Cloudflare API token used by Wrangler) with an Access Key ID and Secret Access Key. A boto3 Python script using `s3.upload_file()` was written to handle this (`scripts/upload_r2.py`).

**6. The upload must be repeated whenever the basemap is refreshed.**

Protomaps publishes a new world build daily. A production-quality setup requires either accepting stale basemap data or automating the extract-and-upload pipeline. This is additional CI/CD complexity.

**7. R2 storage headroom becomes a concern.**

A 2.47 GiB PMTiles file consumes 24.7% of R2's 10 GB free storage tier, leaving 7.5 GB for Parquet files. At `--maxzoom=14` the file would consume 94% of the free tier, with only 600 MB remaining.

**8. CORS configuration is required and bucket-specific.**

R2's public `.r2.dev` URL does not have CDN caching (requires a custom domain + Cloudflare proxy). Every tile request hits R2 storage directly and counts against the 10M free read operations per month. Cloudflare Rate Limiting rules cannot be applied to `.r2.dev` URLs without a custom domain (see ACCEPTED_RISKS.md RISK-005, RISK-006, RISK-007).

### Summary of ADR-004 assumptions vs. reality

| Assumption in ADR-004 | Reality discovered 2026-07-27 |
|-----------------------|-------------------------------|
| US PMTiles ≈ 600 MB | US extract (maxzoom=13) ≈ 2.47 GiB |
| Wrangler CLI can upload the file | Wrangler has a 300 MiB hard limit |
| Upload is a one-time step | Upload must repeat on each basemap refresh |
| R2 free tier comfortably fits basemap + data | Basemap alone consumes 25–94% of free tier |
| No credential complexity | R2 S3 API tokens are separate from Cloudflare API tokens |

---

## Options Considered

### Option A: Continue Self-Hosting on R2 (rejected)

Use `scripts/upload_r2.py` (boto3 S3 multipart) to upload the ~2.47 GiB extract. Configure CORS, enable public access, set `VITE_PMTILES_URL` to the R2.dev URL.

**Advantages:**
- Full control over tile data and versioning
- Consistent with ADR-004's described architecture
- No third-party runtime dependency for the basemap

**Disadvantages:**
- 2.47 GiB consumes 24.7% of R2 free tier (25% less headroom for future Parquet data)
- Upload requires two separate credential types (Cloudflare API token + R2 S3 API token)
- Annual/per-refresh extract-and-upload pipeline must be built and maintained
- No CDN caching on `.r2.dev` — every tile request hits R2 storage (see RISK-007)
- Security risks RISK-005, RISK-006, RISK-007 remain open without Phase 7 custom domain work
- Does not provide basemap auto-updates — stale tiles require manual intervention

**Decision: Rejected.** The operational complexity is high relative to the benefit. The basemap is purely a visual background layer — TOXMAP does not require custom tile styling, bespoke geographic data, or tile-level control in Phases 3–6.

---

### Option B: OpenFreeMap Hosted Tiles ✅ Selected

[OpenFreeMap](https://openfreemap.org) is a free, open-source vector tile service operated by Tilen Mrak. It publishes global vector tiles derived from OpenStreetMap data under the ODbL licence, served from a self-operated CDN. The tile style ("Liberty") is directly compatible with MapLibre GL JS. No API key is required. The service is free for any use.

**MapLibre configuration:**
```typescript
style: "https://tiles.openfreemap.org/styles/liberty"
```

**Advantages:**
- Zero R2 storage consumed — full 10 GB free tier available for Parquet data files
- No upload process — eliminates the entire upload toolchain (pmtiles CLI, boto3 script, R2 API tokens, CORS configuration)
- No credential management for the basemap
- Basemap updates automatically as OpenFreeMap publishes new OSM-derived builds
- CORS and CDN caching handled by OpenFreeMap's infrastructure
- RISK-005, RISK-006, RISK-007 in ACCEPTED_RISKS.md do not apply to the basemap layer

**Disadvantages:**
- **Runtime dependency on a third-party CDN.** If OpenFreeMap goes offline, the basemap goes blank. TRI facility markers, search, and all TOXMAP data functionality continue to work — only the visual background disappears.
- **No control over tile style changes.** OpenFreeMap may update the Liberty style; breaking visual changes are possible between Protomaps updates. Mitigation: pin to a specific style version URL if available.
- **No offline support for the basemap.** The static-first architecture (ADR-004) supports offline use via service worker for Parquet files, but tile caching depends on OpenFreeMap's CDN headers.
- **Service continuity risk.** OpenFreeMap is operated by a single developer. If the service is discontinued, a migration to self-hosted PMTiles (or a paid tile provider) is required. The self-hosting path is fully documented in `docs/deployment/PMTILES_R2_UPLOAD.md` and `scripts/upload_r2.py`.

---

### Option C: Paid Tile Providers (MapTiler, Stadia Maps) — not selected

MapTiler and Stadia Maps offer free tiers (100k–200k requests/month) with API keys. Both are more mature services than OpenFreeMap with better SLA guarantees.

**Rejected** because: (1) require an API key, which must be exposed as a `VITE_`-prefixed environment variable in the browser bundle — a minor security surface; (2) request-count limits could be exceeded under production load; (3) the $0 constraint in ADR-004 is maintained more cleanly with OpenFreeMap.

---

## Decision

Use **OpenFreeMap hosted tiles** for the MapLibre GL basemap. The frontend `VITE_MAPLIBRE_STYLE` environment variable is set to the OpenFreeMap Liberty style URL. No PMTiles file is uploaded to R2.

The self-hosting infrastructure (`scripts/upload_r2.py`, `docs/deployment/PMTILES_R2_UPLOAD.md`) is retained in the repository as a documented fallback — not deleted — because:
1. It represents real, verified knowledge about the upload process
2. Phase 7 may require it if OpenFreeMap reliability becomes a concern in production
3. Custom tile styling (beyond the Liberty defaults) would require self-hosting

---

## Consequences

### Immediate (Phase 3)

- **Blocker B-002 is cleared.** Phase 3 frontend development can begin without the PMTiles upload completing.
- `frontend/.env` `VITE_MAPLIBRE_STYLE` is set to `https://tiles.openfreemap.org/styles/liberty`
- `VITE_PMTILES_URL` is not required for Phase 3
- R2 bucket `toxmap-data` remains empty until Parquet files are uploaded in Phase 7
- ACCEPTED_RISKS RISK-005, RISK-006, RISK-007 remain open but are **non-applicable** to the basemap; they become relevant again only if self-hosting is reinstated

### Phase 7 — Production Considerations

- Add OpenFreeMap as a named external dependency in the README and DEPLOYMENT_GUIDE
- Add a fallback note in Phase 7 runbook: if OpenFreeMap is unreliable, switch `VITE_MAPLIBRE_STYLE` to the self-hosted R2 URL and execute the upload documented in `docs/deployment/PMTILES_R2_UPLOAD.md`
- Evaluate whether to pin to a versioned OpenFreeMap style URL for visual stability

### New Accepted Risk

| Risk | Description | Mitigation |
|------|-------------|------------|
| OpenFreeMap CDN unavailability | Basemap goes blank if service is offline | Map data and all TOXMAP functionality unaffected; self-hosting fallback documented; acceptable for zero-budget constraint |

This risk will be recorded in `ACCEPTED_RISKS.md` as RISK-008.

---

## References

- [OpenFreeMap](https://openfreemap.org) — service homepage, pricing, and usage policy
- [OpenFreeMap GitHub](https://github.com/hyperknot/openfreemap) — open-source infrastructure
- [Protomaps Daily Builds](https://maps.protomaps.com/builds/) — world build source; retained for self-hosting fallback
- [docs/deployment/PMTILES_R2_UPLOAD.md](../deployment/PMTILES_R2_UPLOAD.md) — self-hosting fallback procedure
- [scripts/upload_r2.py](../../scripts/upload_r2.py) — boto3 S3 multipart upload script (fallback)
- [ADR-004](ADR-004-zero-budget-hosting.md) — parent ADR; this record amends the tile-hosting assumption only
