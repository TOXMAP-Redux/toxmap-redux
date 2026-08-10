# PMTiles Basemap Upload to Cloudflare R2

**Audience:** Anyone with zero prior Cloudflare experience  
**Goal:** Download a ~300 MB US basemap tile file and upload it to a Cloudflare R2 bucket so the TOXMAP map component can load it  
**Time to complete:** ~30–45 minutes (most of that is the download)  
**Prerequisite:** Node.js 22.0.0+ installed — run `node --version` to check. Wrangler 4.x requires Node 22+. **Use `nvm` to install Node 22** (see Step 5) — do not install Node via the system package manager or the official `.pkg` installer, as those require `sudo` for global installs and cause permission errors.

---

## What you are doing and why

MapLibre GL (the map library TOXMAP uses) needs a source of map tiles — the vector data that draws roads, state borders, water, and terrain. TOXMAP uses the **PMTiles** format: a single large binary file that contains the entire US basemap.

This file lives in **Cloudflare R2**, a free object-storage service (like Amazon S3). The map component fetches tiles directly from R2 in the browser — no server needed.

You will:
1. Create a free Cloudflare account
2. Install Wrangler (Cloudflare's CLI tool)
3. Create an R2 bucket and configure access
4. Download the US basemap PMTiles file from Protomaps
5. Upload it to R2
6. Set a CORS policy so browsers can read it
7. Confirm the upload worked

---

## Step 1 — Create a Cloudflare Account

1. Go to **[dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)**
2. Enter your email address and choose a password
3. Verify your email address (Cloudflare sends a confirmation link)
4. On the "Tell us about yourself" screen, select **Personal** and click **Continue**
5. Skip any domain/DNS setup prompts — click **"Skip, take me to the dashboard"** or equivalent

You are now on the Cloudflare dashboard. You do not need to add a domain.

> **Free tier covers everything in this guide.** R2 gives you 10 GB free storage and 10 million free read
> requests per month. Storage breakdown:
>
> | Data Type | Size | Notes |
> |-----------|------|-------|
> | US PMTiles (basemap) | ~3–8 GB | Depending on zoom level |
> | TRI Parquet files | ~50–100 MB | All years combined |
> | Census GeoJSON/Parquet | ~30 MB | County boundaries + demographics |
> | **Total** | ~3.5–8.5 GB | Fits within 10 GB free tier |

---

## Step 2 — Enable R2 on Your Account

R2 is not enabled by default. You need to activate it once.

1. In the left sidebar, click **R2**
2. Cloudflare will ask you to agree to R2 terms and enter a payment method  
   ⚠️ **You will not be charged.** Cloudflare requires a card on file to prevent abuse of free tiers, but the R2
   free tier is $0.00 and the upload in this guide fits entirely within it.
3. Enter a valid payment method and click **Enable R2**

You are now on the R2 overview page.

---

## Step 3 — Create the R2 Bucket

1. On the R2 overview page, click **Create bucket**
2. Set the bucket name to exactly: **`toxmap-data`**

   > The name must match what the frontend will reference. Use `toxmap-data` exactly — lowercase, hyphenated.

3. Under **Location**, leave it set to **Automatic** (Cloudflare picks the closest region)
4. Under **Default storage class**, leave it as **Standard**
5. Click **Create bucket**

You now have a bucket named `toxmap-data`.

---

## Step 4 — Create an API Token for Wrangler

Wrangler (the CLI tool) needs permission to write to your bucket. You grant this via an API token.

1. Click your profile avatar in the top-right corner → **My Profile**
2. In the left sidebar, click **API Tokens**
3. Click **Create Token**
4. Find the template called **"Edit Cloudflare Workers"** and click **Use template**

   > This template grants the exact permissions Wrangler needs. You will restrict it to R2 only in the next steps.

5. Under **Permissions**, the template adds several entries. Remove all of them **except** the two R2 entries.  
   - ✅ Keep: **Account** · **Workers R2 Storage** · **Edit**  
   - ❌ Remove: anything that says "Workers Scripts", "Workers Routes", "Zone", etc.  
   
   To remove an entry, click the **X** on the right side of that row.

6. Under **Account Resources**, set it to **Include** → **[your account name]**
7. Under **Zone Resources**, set it to **All zones**
8. Click **Continue to summary** → **Create Token**
9. **Copy the token now.** Cloudflare only shows it once. Paste it into a temporary text file on your desktop — you will use it in Step 6 and then delete it from there.

---

## Step 5 — Install Node 22 and Wrangler

Wrangler 4.x requires **Node 22+**. The safest way to install Node on macOS is with `nvm` (Node Version Manager) — it installs into your home directory so no `sudo` is needed.

### 5a — Install nvm

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

The installer appends nvm init lines to `~/.zshrc`. If you see a `Permission denied` error on `~/.zshrc`, your shell config is root-owned (common after a past `sudo node` install). Fix it with:

```bash
sudo chown $USER ~/.zshrc
cat >> ~/.zshrc << 'EOF'

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
EOF
```

### 5b — Install Node 22 and activate it

Load nvm in your current session and install Node 22:

```bash
export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
node --version   # should print v22.x.x
```

> After running `sudo chown` and adding the nvm lines to `.zshrc`, **new terminal windows** will load nvm automatically. For the current session, the `source` command above is needed once.

### 5c — Install Wrangler

```bash
npm install -g wrangler
```

Verify it installed:

```bash
wrangler --version
```

You should see `⛅️ wrangler 4.x.x`.

---

## Step 6 — Authenticate Wrangler with Your Token

In your terminal, set the API token as an environment variable. **Do not paste it into any file that gets committed to git.**

```bash
export CLOUDFLARE_API_TOKEN="paste-your-token-here"
```

> ⚠️ **`export` only lasts for the current terminal session.** If you close the terminal, open a new tab, or restart your machine, the variable is gone. You must re-run this `export` command at the start of every session before using Wrangler. A quick way to check: run `wrangler whoami` — if it says "You are not authenticated", re-export the token.

Verify Wrangler can reach your account:

```bash
wrangler whoami
```

Expected output:

```
 ⛅️ wrangler 4.x.x
──────────────────────
Getting User settings...
👋 You are logged in with an API Token, associated with the email: your@email.com
```

If `whoami` succeeds, do not close this terminal tab. Run all subsequent Wrangler commands (Steps 8, 11) in this same tab, or re-export the token in the new tab first.

> If you see `"You are not authenticated"`, double-check that you copied the full token and that the `export` command ran without a linebreak splitting the token.

---

## Step 7 — Extract the US PMTiles File

The Protomaps daily world build is **~128 GiB** — far too large to download or store on R2's 10 GB free tier. Instead, use the `pmtiles extract` command, which fetches **only the tiles for the US bounding box** via HTTP range requests against the remote file. You never download the full world build. The resulting US extract is approximately **3–8 GiB**.

### 7a — Install the pmtiles CLI

The `pmtiles` CLI is a Go binary from the [go-pmtiles](https://github.com/protomaps/go-pmtiles) project — separate from the `pmtiles` npm package (which is a JavaScript library with no CLI). On macOS, install via Homebrew:

```bash
brew install pmtiles
pmtiles version
```

> If you see `pmtiles dev, commit none, built at unknown` — that is correct output from Homebrew's build. The tool is working.

### 7b — Choose a zoom level cap before extracting

Each zoom level is approximately 4× more tiles than the one below it. Without a cap the full extract is ~9.4 GB — nearly exhausting R2's 10 GB free tier before Parquet files are added. Three options:

| Option | Command flag | Estimated size | Detail level | R2 headroom |
|--------|-------------|----------------|--------------|-------------|
| **✅ Selected — Option 1** | `--maxzoom=13` | ~2–3 GB | Labeled streets, neighborhoods | ~7 GB free |
| Option 2 | *(none — use hosted tiles)* | 0 GB on R2 | [OpenFreeMap](https://openfreemap.org) CDN — no API key, no storage | Full 10 GB free |
| Option 3 | `--maxzoom=14` | ~9.4 GB | Individual street detail | ~0.6 GB free — risky |

> **Option 2 (OpenFreeMap)** is worth reconsidering for the Phase 7 production deploy — it removes the basemap from R2 entirely, leaving the full 10 GB free for Parquet files. For the Phase 3 demo, Option 1 is simpler.

### 7c — Extract the US tiles from the remote build

Run this command. The `--bbox` covers the contiguous US, Puerto Rico, and the US Virgin Islands:

```bash
pmtiles extract \
  "https://build.protomaps.com/20260727.pmtiles" \
  ~/Downloads/basemap_us.pmtiles \
  --bbox="-127,17,-64,50" \
  --maxzoom=13
```

> **Explanation of the flags:**  
> `--bbox="-127,17,-64,50"` — minLon, minLat, maxLon, maxLat. Covers CONUS + Puerto Rico/USVI with a narrow buffer into Canada/Mexico for border context. Alaska and Hawaii are not included — can be added later.  
> `--maxzoom=13` — caps tile detail at zoom level 13 (labeled streets, neighborhoods). Sufficient for viewing and clicking TRI facility markers.

This will take **20–60 minutes** depending on your connection speed. You will see a progress indicator showing chunks being fetched. The tool downloads only the tile data for the selected region and zoom range via HTTP range requests — not the full 128 GiB world file.

> **If the date in the URL changes:** Go to [maps.protomaps.com/builds/](https://maps.protomaps.com/builds/) and replace `20260727` with the date shown on the latest build row.

---

## Step 8 — Upload the PMTiles File to R2

> ⚠️ **Do not use the Cloudflare dashboard drag-and-drop uploader.** It has a hard 300 MB limit.  
> ⚠️ **Do not use `wrangler r2 object put`.** Wrangler 4.x also has a 300 MiB hard limit and cannot upload the PMTiles extract regardless of flags.

Files over 300 MiB must use R2's **S3 Compatibility API**, which supports multipart upload with no size limit. The repo includes a Python script (`scripts/upload_r2.py`) that handles this.

### 8a — Create R2 API Tokens

R2 API tokens are **separate** from the Cloudflare API token used by Wrangler. You need a new token pair specifically for S3-compatible access.

1. Go to **[dash.cloudflare.com](https://dash.cloudflare.com)** → **R2**
2. On the R2 overview page, click **Manage R2 API Tokens** (top-right area)
3. Click **Create API Token**
4. Give it a name (e.g. `toxmap-upload`)
5. Under **Permissions**, select **Object Read & Write**
6. Under **Specify bucket**, select **`toxmap-data`**
7. Click **Create API Token**
8. Cloudflare shows you three values — **copy all three now**, they are only shown once:
   - **Token value** — this is your `R2_SECRET_ACCESS_KEY`
   - **Access Key ID** — this is your `R2_ACCESS_KEY_ID`
   - **Use jurisdiction-specific endpoints** — ignore this

9. Find your **Account ID**: in the Cloudflare dashboard, look at the URL — it is the 32-character hex string after `dash.cloudflare.com/`. Also visible on the R2 overview page right-hand panel under "Account ID".

### 8b — Install boto3

```bash
pip install boto3
```

### 8c — Run the upload script

Export the three credentials (do not commit these to git):

```bash
export R2_ACCOUNT_ID="your-32-char-account-id"
export R2_ACCESS_KEY_ID="your-access-key-id"
export R2_SECRET_ACCESS_KEY="your-secret-access-key"
```

Then run the upload:

```bash
python scripts/upload_r2.py \
  ~/Downloads/basemap_us.pmtiles \
  toxmap-data \
  basemap_us.pmtiles
```

You will see a live progress indicator:

```
Uploading /Users/you/Downloads/basemap_us.pmtiles
  → s3://toxmap-data/basemap_us.pmtiles
  Size: 2.47 GiB

   47.3%  1.17 / 2.47 GiB

✓ Upload complete: toxmap-data/basemap_us.pmtiles
```

Upload time is typically **20–60 minutes** depending on your connection. The script uses boto3's built-in multipart upload, which automatically splits the file into chunks, uploads them in parallel, and retries failed chunks.

---

## Step 9 — Enable Public Access on the Bucket

The bucket is private by default. The frontend must be able to read the file without authentication.

1. Go to the [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2** → click **`toxmap-data`**
2. Click the **Settings** tab
3. Scroll down to **Public access**
4. Click **Allow Access** (or **Enable R2.dev subdomain** depending on your dashboard version)
5. Cloudflare will show you a public URL like: `https://pub-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.r2.dev`
6. **Copy this URL.** You will need it when configuring the frontend environment variable.

> This URL is the base URL for all objects in the bucket. The PMTiles file will be at  
> `https://pub-xxxxxxxx....r2.dev/basemap_us.pmtiles`

---

## Step 10 — Configure the CORS Policy

The browser will be making requests to R2 from `localhost:3000` (during dev) and from your Cloudflare Pages domain (in production). Without a CORS policy, browsers will block these requests.

### Using the Dashboard

1. On your `toxmap-data` bucket page, click the **Settings** tab
2. Scroll to **CORS Policy**
3. Click **Add CORS policy** and paste the following JSON, then click **Save**:

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:3000",
      "https://toxmap.pages.dev"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "Content-Type"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
    "MaxAgeSeconds": 86400
  }
]
```

> ⚠️ Replace `https://toxmap.pages.dev` with your actual Cloudflare Pages URL once you set it up in Phase 7.
> For now, keeping it as `toxmap.pages.dev` is fine — it just won't match until Pages is deployed.

### Alternative: Using Wrangler (command line)

Save the JSON above to a file called `cors.json` and run:

```bash
wrangler r2 bucket cors put toxmap-data --rules cors.json --remote
```

---

## Step 11 — Verify the Upload

### Check the file exists in R2

```bash
wrangler r2 object get toxmap-data/basemap_us.pmtiles --pipe --remote | wc -c
```

This streams the file and counts bytes. You should see a number greater than `200000000` (~200 MB minimum). If you see `0` or an error, the upload did not succeed — go back to Step 8.

### Check public access works

Open this URL in your browser (replace the domain with your actual R2.dev public URL from Step 9):

```
https://pub-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.r2.dev/basemap_us.pmtiles
```

Your browser will either download the file or show a progress bar. That confirms public access is working.

> You do **not** need to download the whole file to confirm it works — you can stop the download after a few seconds.

---

## Step 12 — Record the URL and Clear Blocker B-002

Once the upload is confirmed:

1. Note the public R2 URL for `basemap_us.pmtiles`:
   ```
   https://pub-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.r2.dev/basemap_us.pmtiles
   ```

2. This URL will be set as `VITE_PMTILES_URL` in `frontend/.env` when Phase 3 map stories are implemented.

3. Update the progress tracker to clear blocker B-002 — you can tell the Phase Manager agent:
   > "PMTiles upload complete. Public URL: `https://pub-xxxx.r2.dev/basemap_us.pmtiles`. Clear B-002."

---

## Troubleshooting

### "Authentication error" from Wrangler

Your `CLOUDFLARE_API_TOKEN` environment variable is not set or was set incorrectly. Re-run:

```bash
export CLOUDFLARE_API_TOKEN="your-token-here"
wrangler whoami
```

Environment variables set with `export` only persist for the current terminal session. If you closed your terminal between steps, re-run the `export` command.

### "The specified bucket does not exist"

The bucket name in the command must exactly match the bucket name you created. Check for typos:

```bash
wrangler r2 bucket list
```

This lists all your buckets. Use the exact name shown.

### Upload stalls or fails partway through

Large files occasionally fail on flaky connections. Run the upload again — Wrangler will restart the multipart upload from the beginning:

```bash
wrangler r2 object put toxmap-data/basemap_us.pmtiles \
  --file ~/Downloads/basemap_us.pmtiles \
  --content-type application/octet-stream \
  --multipart-concurrency 2
```

Lowering concurrency to `2` reduces bandwidth pressure.

### "NoSuchBucket" on CORS command

Run `wrangler r2 bucket list` to confirm the bucket name, then re-run the CORS command with the correct name.

### Public URL returns 403 Forbidden

Public access was not enabled. Go back to Step 9 and click "Allow Access" on the Settings tab.

---

## Summary Checklist

Use this as a final verification before telling the Phase Manager that B-002 is cleared:

- [ ] Cloudflare account created and R2 enabled
- [ ] Bucket `toxmap-data` created
- [ ] API token created with R2 Edit permission
- [ ] Wrangler installed and authenticated (`wrangler whoami` succeeds)
- [ ] `basemap_us.pmtiles` downloaded and renamed
- [ ] Upload completed with `wrangler r2 object put` (success message shown)
- [ ] Public access enabled on bucket; R2.dev URL copied
- [ ] CORS policy applied (both `localhost:3000` and Pages domain in AllowedOrigins)
- [ ] Public URL loads in browser (partial download confirms access)
- [ ] `VITE_PMTILES_URL` value noted for Phase 3 frontend `.env` configuration
