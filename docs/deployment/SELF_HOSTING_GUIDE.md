# Self-Hosting Guide: Photon Geocoder & PMTiles Basemap

**Last Updated:** 2026-08-04  
**Audience:** Operators who need to move beyond free third-party services  
**Prerequisite:** Familiarity with Linux servers, SSH, and Docker  
**Related:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) · [ADR-005 (OpenFreeMap)](../adr/ADR-005-openfreemap-basemap-tiles.md) · [ADR-006 (Photon)](../adr/ADR-006-photon-geocoding.md) · [ACCEPTED_RISKS.md](../security/ACCEPTED_RISKS.md)

---

## When to Self-Host

Self-hosting is recommended when:

| Trigger | Service | Action |
|---------|---------|--------|
| >10,000 geocode requests/day | Photon | Self-host Photon |
| Users report "geocoding failed" errors | Photon | Self-host Photon immediately |
| OpenFreeMap tiles load slowly or fail | Basemap | Self-host PMTiles |
| Compliance requires no third-party data egress | Both | Self-host both |
| You want guaranteed uptime/SLA | Both | Self-host both |

---

## Part 1: Self-Hosting Photon Geocoder

### 1.1 Overview

[Photon](https://github.com/komoot/photon) is an open-source geocoder (Apache 2.0 license) that converts addresses to coordinates. It's backed by OpenStreetMap data and provides the same API as the public `photon.komoot.io` instance.

**Self-hosting options:**

| Option | Complexity | Time | Cost/month | Best for |
|--------|------------|------|------------|----------|
| **A. Pre-built database (US only)** | Low | 2 hours | ~$20–40 | TOXMAP (US-focused) |
| **B. Pre-built database (Planet)** | Medium | 4–6 hours | ~$80–150 | Global coverage |
| **C. Build from Nominatim** | High | 2–3 days | ~$80–150 | Custom languages/features |

**Recommendation for TOXMAP:** Option A (US-only) is sufficient and cheapest.

---

### 1.2 Server Requirements

#### For US-only coverage (Option A):

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| **RAM** | 8 GB | 16 GB | Index lives in memory for fast queries |
| **Disk** | 50 GB SSD | 100 GB NVMe | US database ~15–20 GB unpacked |
| **CPU** | 2 vCPU | 4 vCPU | More cores = more concurrent requests |
| **Bandwidth** | 1 TB/month | Unmetered | Each geocode ~1–5 KB response |
| **OS** | Ubuntu 22.04+ | Ubuntu 24.04 | Or any Linux with Java 21+ |

#### For Planet-wide coverage (Option B):

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| **RAM** | 32 GB | 64 GB | Planet index is large |
| **Disk** | 150 GB SSD | 200 GB NVMe | Planet database ~95 GB unpacked |
| **CPU** | 4 vCPU | 8 vCPU | Parallel query handling |
| **Bandwidth** | 2 TB/month | Unmetered | — |

---

### 1.3 Cost Estimates (VPS Providers)

#### US-Only (8–16 GB RAM):

| Provider | Plan | RAM | Disk | Price/month | Link |
|----------|------|-----|------|-------------|------|
| **Hetzner** | CPX21 | 8 GB | 160 GB | **€7.50** (~$8) | [hetzner.com/cloud](https://www.hetzner.com/cloud) |
| **Hetzner** | CPX31 | 16 GB | 160 GB | **€14.50** (~$16) | Best value |
| **DigitalOcean** | Basic 8GB | 8 GB | 160 GB | **$48** | [digitalocean.com](https://www.digitalocean.com/pricing/droplets) |
| **Vultr** | High Frequency 8GB | 8 GB | 256 GB | **$48** | [vultr.com](https://www.vultr.com/products/cloud-compute/) |
| **Linode** | Shared 8GB | 8 GB | 160 GB | **$48** | [linode.com](https://www.linode.com/pricing/) |
| **AWS Lightsail** | 8 GB | 8 GB | 160 GB | **$40** | [lightsail.aws.amazon.com](https://aws.amazon.com/lightsail/pricing/) |
| **Oracle Cloud** | VM.Standard.A1.Flex | 24 GB | 200 GB | **FREE** (always free tier) | [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) |

> **Best value:** Hetzner CPX31 (€14.50/month) or Oracle Cloud free tier (if you qualify).

#### Planet-Wide (32–64 GB RAM):

| Provider | Plan | RAM | Disk | Price/month |
|----------|------|-----|------|-------------|
| **Hetzner** | CCX23 | 32 GB | 240 GB | **€47** (~$52) |
| **Hetzner** | CCX33 | 64 GB | 360 GB | **€95** (~$105) |
| **DigitalOcean** | Basic 32GB | 32 GB | 400 GB | **$192** |
| **AWS EC2** | r6g.xlarge | 32 GB | EBS | ~$150 + storage |

---

### 1.4 Step-by-Step: Option A (US-Only, Pre-built Database)

This is the fastest path to self-hosted geocoding for TOXMAP.

#### Step 1: Provision a VPS

1. Sign up at [Hetzner Cloud](https://www.hetzner.com/cloud) (or your preferred provider)
2. Create a new server:
   - **Location:** US East or West (closest to your users)
   - **Image:** Ubuntu 24.04
   - **Type:** CPX21 (8 GB) or CPX31 (16 GB)
   - **Volume:** None (local disk is sufficient)
   - **Networking:** Public IPv4 enabled
   - **SSH Key:** Add your public key
3. Note the server's public IP address

#### Step 2: Connect and prepare the server

```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Update packages
apt update && apt upgrade -y

# Install Java 21 (required by Photon)
apt install -y openjdk-21-jre-headless

# Verify Java version
java -version
# Should show: openjdk version "21.x.x"

# Install bzip2 for extracting the database
apt install -y pbzip2 wget

# Create a directory for Photon
mkdir -p /opt/photon
cd /opt/photon
```

#### Step 3: Download Photon JAR

```bash
# Download the latest Photon release
wget https://github.com/komoot/photon/releases/download/1.2.1/photon-1.2.1.jar

# Rename for convenience
mv photon-1.2.1.jar photon.jar
```

#### Step 4: Download the US database extract

GraphHopper provides regional extracts. Unfortunately, as of 2026, **only the full planet database is available pre-built**. For US-only, you have two options:

**Option 4a: Use the full planet database (simpler, but larger)**

```bash
# Download the planet database (~62 GB compressed, ~95 GB unpacked)
# This takes 2-4 hours depending on your connection
wget -O - https://download1.graphhopper.com/public/photon-db-planet-1.0-latest.tar.bz2 | pbzip2 -cd | tar x

# Result: a photon_data/ directory containing the search index
ls -la photon_data/
```

**Option 4b: Import from a US-only JSON dump (advanced)**

If you need only US data to save disk space, you can:
1. Download the US OpenStreetMap extract from [Geofabrik](https://download.geofabrik.de/north-america/us.html)
2. Import it into Nominatim
3. Export to Photon format

This is significantly more complex — see [Photon documentation](https://github.com/komoot/photon/blob/master/docs/usage.md) for details.

#### Step 5: Start Photon

```bash
# Start Photon (uses ~4-8 GB RAM depending on index size)
java -Xmx6g -jar photon.jar serve

# Output:
# INFO  [main] photon.App - photon is listening on 0.0.0.0:2322
```

Test it:
```bash
# From another terminal on the server:
curl "http://localhost:2322/api/?q=Front%20Royal%2C%20VA&limit=1"
```

#### Step 6: Run as a systemd service

Create a systemd unit file so Photon starts on boot and restarts on failure:

```bash
cat > /etc/systemd/system/photon.service << 'EOF'
[Unit]
Description=Photon Geocoder
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/photon
ExecStart=/usr/bin/java -Xmx6g -jar photon.jar serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable photon
systemctl start photon

# Check status
systemctl status photon
```

#### Step 7: Configure a firewall

```bash
# Allow SSH and Photon
ufw allow 22/tcp
ufw allow 2322/tcp
ufw enable
```

#### Step 8: (Optional) Add HTTPS with Caddy

For production, use a reverse proxy with automatic HTTPS:

```bash
# Install Caddy
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy

# Configure Caddy (replace geocode.yourdomain.com with your domain)
cat > /etc/caddy/Caddyfile << 'EOF'
geocode.yourdomain.com {
    reverse_proxy localhost:2322
    
    # CORS headers for browser access
    header Access-Control-Allow-Origin "*"
    header Access-Control-Allow-Methods "GET, OPTIONS"
}
EOF

# Restart Caddy
systemctl restart caddy
```

#### Step 9: Update TOXMAP to use your self-hosted Photon

In `frontend/src/api/geocode.ts`, change:

```typescript
// Before:
const _PHOTON_URL = 'https://photon.komoot.io/api/'

// After:
const _PHOTON_URL = 'https://geocode.yourdomain.com/api/'
```

Rebuild and redeploy the frontend.

---

### 1.5 Keeping Photon Updated

Photon's OSM data becomes stale. To update:

```bash
cd /opt/photon

# Stop the service
systemctl stop photon

# Backup the old database
mv photon_data photon_data_old

# Download new database (2-4 hours)
wget -O - https://download1.graphhopper.com/public/photon-db-planet-1.0-latest.tar.bz2 | pbzip2 -cd | tar x

# Restart the service
systemctl start photon

# Verify it works
curl "http://localhost:2322/api/?q=test&limit=1"

# Delete old backup
rm -rf photon_data_old
```

**Recommended update frequency:** Monthly, or after major OSM data changes.

---

## Part 2: Self-Hosting PMTiles Basemap

### 2.1 Overview

[PMTiles](https://github.com/protomaps/PMTiles) is a single-file format for map tiles. Instead of relying on OpenFreeMap's CDN, you can host tiles yourself on Cloudflare R2 (or any S3-compatible storage).

**Why self-host tiles?**
- OpenFreeMap goes offline or becomes slow
- You need guaranteed uptime
- You want to customize the map style

**Trade-offs:**
- R2 storage costs (~$0.015/GB/month after free tier)
- R2 read operations count against free tier
- You manage updates (Protomaps publishes daily)

---

### 2.2 Storage Requirements

| Coverage | Max Zoom | File Size | Notes |
|----------|----------|-----------|-------|
| Planet | 6 | ~60 MB | Low detail, good for overview |
| Planet | 10 | ~2 GB | Medium detail |
| Planet | 14 | ~127 GB | Full street-level detail (impractical) |
| **US only** | 13 | ~2.5 GB | **Recommended for TOXMAP** |
| **US only** | 14 | ~8 GB | High detail, uses most of R2 free tier |

---

### 2.3 Cost Estimates

#### Cloudflare R2 (recommended):

| Resource | Free Tier | Overage |
|----------|-----------|---------|
| Storage | 10 GB/month | $0.015/GB |
| Class A ops (writes) | 1M/month | $4.50/M |
| Class B ops (reads) | 10M/month | $0.36/M |

**For TOXMAP with US-only tiles (~2.5 GB):**
- Storage: FREE (within 10 GB)
- Reads: Depends on traffic. 50,000 unique visitors/month × ~50 tiles/visitor = 2.5M reads → FREE
- **Total: $0/month** for moderate traffic

**For high traffic (500,000 visitors/month):**
- Reads: 25M/month → 15M overage × $0.36/M = **$5.40/month**

#### Alternative: Self-hosted tile server

You can run `pmtiles serve` on a VPS instead of R2:

```bash
# On your Photon server (or separate server)
wget https://github.com/protomaps/go-pmtiles/releases/download/v1.22.3/go-pmtiles_1.22.3_linux_amd64.tar.gz
tar xf go-pmtiles*.tar.gz
./pmtiles serve /path/to/basemap_us.pmtiles --port 8081
```

Cost: Included in your VPS price, but adds load to the server.

---

### 2.4 Step-by-Step: Self-Hosting PMTiles on Cloudflare R2

This procedure is already documented in detail in [PMTILES_R2_UPLOAD.md](PMTILES_R2_UPLOAD.md). Summary:

#### Step 1: Extract US tiles from the planet file

```bash
# Install pmtiles CLI
wget https://github.com/protomaps/go-pmtiles/releases/download/v1.22.3/go-pmtiles_1.22.3_darwin_arm64.tar.gz
tar xf go-pmtiles*.tar.gz

# Extract US region (takes 30-60 minutes, uses HTTP range requests)
./pmtiles extract \
  https://build.protomaps.com/20260803.pmtiles \
  basemap_us.pmtiles \
  --bbox=-127,17,-64,50 \
  --maxzoom=13

# Result: basemap_us.pmtiles (~2.5 GB)
```

#### Step 2: Upload to R2

Wrangler has a 300 MB limit, so use the S3 API:

```bash
# Set R2 credentials (create an R2 API token in Cloudflare dashboard)
export R2_ACCOUNT_ID="your-account-id"
export R2_ACCESS_KEY_ID="your-key-id"
export R2_SECRET_ACCESS_KEY="your-secret"

# Upload using the provided script
python scripts/upload_r2.py basemap_us.pmtiles toxmap-data basemap_us.pmtiles
```

#### Step 3: Configure CORS on R2

In Cloudflare dashboard → R2 → toxmap-data → Settings → CORS:

```json
[
  {
    "AllowedOrigins": ["https://your-toxmap-domain.pages.dev", "http://localhost:3000"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "If-None-Match"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges", "ETag"],
    "MaxAgeSeconds": 86400
  }
]
```

#### Step 4: Create a MapLibre style pointing to R2

Create `frontend/public/mapstyle.json`:

```json
{
  "version": 8,
  "sources": {
    "protomaps": {
      "type": "vector",
      "tiles": ["pmtiles://https://YOUR_R2_PUBLIC_URL/basemap_us.pmtiles/{z}/{x}/{y}"],
      "minzoom": 0,
      "maxzoom": 13
    }
  },
  "layers": [
    // Copy layers from OpenFreeMap's Liberty style
    // https://tiles.openfreemap.org/styles/liberty
  ]
}
```

Or use PMTiles with the `pmtiles` protocol adapter in MapLibre:

```typescript
// frontend/src/components/Map/MapContainer.tsx
import { Protocol } from 'pmtiles';
import maplibregl from 'maplibre-gl';

// Register PMTiles protocol
const protocol = new Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);
```

#### Step 5: Update TOXMAP configuration

```bash
# frontend/.env.production
VITE_MAPLIBRE_STYLE=pmtiles://https://YOUR_R2_PUBLIC_URL/basemap_us.pmtiles
```

---

### 2.5 Keeping Tiles Updated

Protomaps publishes daily builds. To update:

```bash
# 1. Extract new US tiles
./pmtiles extract \
  https://build.protomaps.com/20260901.pmtiles \
  basemap_us_new.pmtiles \
  --bbox=-127,17,-64,50 \
  --maxzoom=13

# 2. Upload to R2 (overwrites the old file)
python scripts/upload_r2.py basemap_us_new.pmtiles toxmap-data basemap_us.pmtiles

# 3. Done! Browser cache will eventually refresh.
# To force immediate update, change the filename and update VITE_MAPLIBRE_STYLE.
```

**Recommended update frequency:** Quarterly, or when OSM data for your region changes significantly.

---

## Part 3: Total Cost Summary

### Scenario A: US-Only Self-Hosting (Recommended)

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Photon VPS (Hetzner CPX31) | **€14.50** (~$16) | 16 GB RAM, 160 GB SSD |
| PMTiles on R2 | **$0** | Within free tier for <500K visitors |
| Domain (optional) | ~$1 | For `geocode.yourdomain.com` |
| **Total** | **~$17/month** | vs $0 with public services (but no SLA) |

### Scenario B: US-Only, Free Tier Only

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Photon on Oracle Cloud free tier | **$0** | 24 GB ARM, 200 GB (if you qualify) |
| PMTiles on R2 | **$0** | Free tier |
| **Total** | **$0/month** | Requires Oracle Cloud approval |

### Scenario C: Planet-Wide Coverage

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Photon VPS (Hetzner CCX33) | **€95** (~$105) | 64 GB RAM for planet index |
| PMTiles on R2 | **$0–5** | Depends on traffic |
| **Total** | **~$105–110/month** | |

---

## Part 4: Operational Considerations

### Monitoring

Add basic monitoring to your self-hosted services:

```bash
# Install simple uptime checker
apt install -y monit

# Configure Monit for Photon
cat > /etc/monit/conf.d/photon << 'EOF'
check process photon with pidfile /var/run/photon.pid
    start program = "/bin/systemctl start photon"
    stop program = "/bin/systemctl stop photon"
    if failed host localhost port 2322 protocol http
        request "/api/?q=test&limit=1"
        then restart
EOF

systemctl restart monit
```

### Backup

For Photon, the database can be re-downloaded. No backup needed unless you customized it.

For R2 PMTiles, the file can be regenerated from Protomaps. Enable R2 versioning if you want rollback capability.

### Scaling

If you outgrow a single server:
- **Photon:** Run multiple instances behind a load balancer
- **PMTiles:** R2 scales automatically; consider a CDN (Cloudflare proxy) for cache

---

## Part 5: Quick Reference Commands

### Photon

```bash
# Check status
systemctl status photon

# View logs
journalctl -u photon -f

# Test geocoding
curl "http://localhost:2322/api/?q=Front%20Royal%2C%20VA&limit=1" | jq

# Restart after update
systemctl restart photon
```

### PMTiles

```bash
# Inspect a PMTiles file
./pmtiles show basemap_us.pmtiles

# Extract a region
./pmtiles extract source.pmtiles output.pmtiles --bbox=WEST,SOUTH,EAST,NORTH --maxzoom=13

# Serve locally for testing
./pmtiles serve basemap_us.pmtiles --port 8081
```

---

## Appendix: Regional Bounding Boxes

| Region | Bounding Box (WEST,SOUTH,EAST,NORTH) |
|--------|--------------------------------------|
| Continental US | `-127,24,-66,50` |
| US + Alaska + Hawaii | `-180,15,-64,72` |
| California | `-124.4,32.5,-114.1,42.0` |
| Texas | `-106.6,25.8,-93.5,36.5` |
| New York | `-79.8,40.5,-71.9,45.0` |
| Florida | `-87.6,24.5,-80.0,31.0` |
| Europe | `-10,35,40,72` |
| UK | `-8.0,49.5,2.0,61.0` |

Use [bboxfinder.com](http://bboxfinder.com/) to find custom bounding boxes.

---

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) — Main deployment guide
- [PMTILES_R2_UPLOAD.md](PMTILES_R2_UPLOAD.md) — Detailed R2 upload instructions
- [ADR-005](../adr/ADR-005-openfreemap-basemap-tiles.md) — Why we chose OpenFreeMap
- [ADR-006](../adr/ADR-006-photon-geocoding.md) — Why we chose Photon
- [ACCEPTED_RISKS.md](../security/ACCEPTED_RISKS.md) — RISK-008, RISK-009, RISK-010 (third-party dependencies)
