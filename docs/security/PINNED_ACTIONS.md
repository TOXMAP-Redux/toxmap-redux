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

> **Status:** Workflow files `.github/workflows/ci.yml` and `.github/workflows/security.yml`
> now exist and use mutable version tags (`@v4`, `@v5`, `@v2`).
> Story **0.5.4** (Security Engineer) must replace all tags with full 40-char SHAs
> and update this table before the first production CI run.

| Action | Pinned SHA | Corresponds to Tag | Workflow(s) Used In | Last Verified |
|--------|-----------|-------------------|---------------------|--------------|
| `actions/checkout` | *(pin before first use — see story 0.5.4)* | v4.x | `ci.yml`, `security.yml`, `build-data.yml` | — |
| `actions/setup-python` | *(pin before first use — see story 0.5.4)* | v5.x | `ci.yml`, `security.yml` | — |
| `actions/setup-node` | *(pin before first use — see story 0.5.4)* | v4.x | `ci.yml`, `security.yml` | — |
| `actions/upload-artifact` | *(pin before first use — see story 0.5.4)* | v4.x | `ci.yml`, `security.yml` | — |
| `codecov/codecov-action` | *(pin before first use — see story 0.5.4)* | v4.x | `ci.yml` *(future)* | — |
| `cloudflare/wrangler-action` | *(pin before first use — see story 0.5.4)* | v3.x | `build-data.yml` *(future)* | — |
| `gitleaks/gitleaks-action` | *(pin before first use — see story 0.5.4)* | v2.x | `security.yml` | — |

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

