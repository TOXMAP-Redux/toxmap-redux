# Pinned GitHub Actions — SHA Registry

**Owner:** Security Engineer (SEC) + DevOps (OPS)  
**Updated:** When any GitHub Action version is bumped in a workflow file

> All third-party GitHub Actions used in TOXMAP workflows are pinned to a full 40-character commit SHA.  
> This file documents the SHA → human-readable tag mapping.  
> When Dependabot opens a PR to update an action, the reviewer must verify the new SHA here before approving.

---

## Purpose

Mutable version tags (e.g., `@v3`, `@latest`) are a supply chain attack vector (T-SEC-08). If the upstream repository is compromised, a new commit can be silently pushed to the `v3` tag, and the next CI run will execute malicious code with access to all GitHub Secrets.

SHA pinning ensures the exact code that was reviewed is the exact code that runs.

---

## Registry

Update this table every time an Action version is changed in any workflow file.

> **Status:** All workflow files pinned to full 40-char SHAs as of 2026-07-25.
> Story **0.5.4** (Security Engineer) complete — zero mutable `@vX` tags remain in any workflow file.
> `cloudflare/wrangler-action` is listed but not yet used; pin it when story 1.5.2 (OPS) lands.

| Action | Pinned SHA | Corresponds to Tag | Workflow(s) Used In | Last Verified |
|--------|-----------|-------------------|---------------------|--------------|
| `actions/checkout` | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` | v5.1.0 | `ci.yml`, `security.yml` | 2026-07-25 |
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | v4.4.0 | `build-data.yml` | 2026-07-25 |
| `actions/setup-python` | `0b93645e9fea7318ecaed2b359559ac225c90a2b` | v5.3.0 | `ci.yml`, `security.yml` | 2026-07-25 |
| `actions/setup-node` | `a0853c24544627f65ddf259abe73b1d18a591444` | v5.0.0 | `ci.yml`, `security.yml` | 2026-07-25 |
| `actions/upload-artifact` | `330a01c490aca151604b8cf639adc76d48f6c5d4` | v5.0.0 | `ci.yml`, `security.yml` | 2026-07-25 |
| `codecov/codecov-action` | `b9fd7d16f6d7d1b5d2bec1a2887e65ceed900238` | v4.6.0 | `ci.yml` | 2026-07-25 |
| `cloudflare/wrangler-action` | *(pin before first use — see story 0.5.4)* | v3.x | `build-data.yml` *(future)* | — |
| `gitleaks/gitleaks-action` | `ff98106e4c7b2bc287b24eaf42907196329070c7` | v2.3.9 | `security.yml` | 2026-07-25 |

> **Instructions for the Security Engineer agent (story 0.5.4):**  
> 1. For each Action listed above, run: `gh api repos/<owner>/<repo>/git/ref/tags/<tag>` to resolve the tag to a commit SHA.  
> 2. Replace the `@v4` / `@v5` / `@v2` mutable tags in each workflow file with the full SHA.  
> 3. In each workflow file, use the SHA with an inline comment: `uses: actions/checkout@<SHA> # v4.x.x`  
> 4. Replace the `*(pin before first use)*` placeholders in this table with the verified SHA.  
> 5. Update the "Last Verified" date to the date the SHA was resolved.  
> 6. Open a PR with the `chore(sec): pin GitHub Actions to full SHAs` commit message.

---

## How to Update a Pinned Action

When Dependabot opens a PR to bump an action version:

1. Note the new SHA in the Dependabot PR description.
2. Verify the SHA on the upstream repository's releases page or by running `gh api repos/<owner>/<repo>/git/ref/tags/<new-tag>`.
3. Update the SHA in the workflow file and in this table.
4. Approve and merge the Dependabot PR if the release looks legitimate and the changelog contains no red flags.
5. Update "Last Verified" in this table.

