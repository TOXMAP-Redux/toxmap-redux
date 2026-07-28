"""Scrape IRIS AtoZ page to extract substance_nmbr → (name, CASRN) mapping.

Usage:
    # Scrape IRIS and write CSV:
    python scripts/scrape_iris_substance_nmbr.py [--output path/to/output.csv]

    # Resolve a TRI name or N-code to CAS via PubChem then to IRIS:
    python scripts/scrape_iris_substance_nmbr.py --resolve "LEAD COMPOUNDS"
    python scripts/scrape_iris_substance_nmbr.py --resolve N420

The IRIS ChemicalLanding URL format is:
    https://iris.epa.gov/ChemicalLanding/&substance_nmbr=<N>

The substance_nmbr values are opaque database IDs — they do NOT correspond to
the sequential row numbers in the AtoZ table, nor to any external identifier.

-----------------------------------------------------------------------
CAS resolution via PubChem Synonyms
-----------------------------------------------------------------------
For TRI chemicals that carry a CAS number, IRIS lookup is a direct CSV
match on that CAS.

For TRI *compound categories* (N-prefix IDs: N420, N100, …) that have no
single CAS number, PubChem's Synonyms API bridges the gap:

  Step 1. Query PubChem by the N-code or category name:
          GET /rest/pug/compound/name/{identifier}/synonyms/JSON

  Step 2. PubChem returns a Synonym list.  The CAS number appears as one
          of the first few entries and matches the pattern \d{1,7}-\d{2}-\d.
          Example: "N420" resolves to CID 5352425 (Lead) with synonyms
          ["LEAD", "7439-92-1", "Lead element", …, "N420", …]

  Step 3. Use the resolved CAS to look up the IRIS CSV → substance_nmbr.

PubChem also accepts CAS numbers directly in its compound URL:
    https://pubchem.ncbi.nlm.nih.gov/compound/7439-92-1  (redirects to CID)
This means pubchem_url values stored as numeric CIDs
(e.g., /compound/241 for benzene) can be normalised to the stable CAS form
(/compound/71-43-2) without any API call.

Output CSV columns:
    substance_nmbr  — IRIS opaque integer ID
    name            — Chemical name as listed on IRIS
    casrn           — CAS Registry Number (may be empty for mixtures)
    iris_url        — Full ChemicalLanding URL
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

IRIS_ATOZ_URL = "https://iris.epa.gov/AtoZ/alpha/"
IRIS_BASE_URL = "https://iris.epa.gov"
# Relative href in the raw HTML is: /ChemicalLanding/&substance_nmbr=NNN
# BeautifulSoup decodes &amp; → & so the pattern matches the decoded value.
CHEMICAL_LANDING_PATTERN = re.compile(
    r"(?:https://iris\.epa\.gov)?/ChemicalLanding/[&?]substance_nmbr=(\d+)"
)

PUBCHEM_SYNONYMS_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{identifier}/synonyms/JSON"
)
# CAS numbers follow the format N{1-7}-NN-N  (e.g. 7439-92-1, 71-43-2)
CAS_PATTERN = re.compile(r"^\d{1,7}-\d{2}-\d$")

# Respect EPA / NCBI rate limits
REQUEST_DELAY_SECONDS = 1.0


def fetch_page(url: str, session: requests.Session) -> str:
    """Fetch a URL and return its HTML text."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; TOXMAP-research-bot/1.0; "
            "+https://github.com/toxmap-redux)"
        )
    }
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def extract_mappings(html: str) -> list[dict[str, str]]:
    """Parse IRIS AtoZ HTML and return list of substance records.

    Each record has keys: substance_nmbr, name, casrn, iris_url.
    """
    soup = BeautifulSoup(html, "html.parser")

    # The interactive table has id="myTable" or similar; find all anchor tags
    # whose href contains substance_nmbr.
    records: list[dict[str, str]] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=CHEMICAL_LANDING_PATTERN):
        href = anchor["href"]
        match = CHEMICAL_LANDING_PATTERN.search(href)
        if not match:
            continue
        substance_nmbr = match.group(1)
        if substance_nmbr in seen:
            continue
        seen.add(substance_nmbr)

        name = anchor.get_text(strip=True)

        # CASRN is in the next <td> sibling of the anchor's parent <td>
        parent_td = anchor.find_parent("td")
        casrn = ""
        if parent_td:
            next_td = parent_td.find_next_sibling("td")
            if next_td:
                casrn = next_td.get_text(strip=True)

        iris_url = f"{IRIS_BASE_URL}/ChemicalLanding/&substance_nmbr={substance_nmbr}"
        records.append(
            {
                "substance_nmbr": substance_nmbr,
                "name": name,
                "casrn": casrn,
                "iris_url": iris_url,
            }
        )

    # Sort by substance_nmbr for deterministic output
    records.sort(key=lambda r: int(r["substance_nmbr"]))
    return records


def write_csv(records: list[dict[str, str]], output_path: str) -> None:
    """Write records to a CSV file."""
    fieldnames = ["substance_nmbr", "name", "casrn", "iris_url"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records to {output_path}", file=sys.stderr)


def pubchem_resolve_cas(
    identifier: str,
    session: requests.Session,
) -> tuple[str | None, int | None]:
    """Resolve a TRI name or N-code to (cas_number, pubchem_cid) via PubChem Synonyms.

    PubChem's Synonyms API accepts any registered synonym as the lookup key,
    including TRI N-codes (e.g. 'N420'), CAS numbers, chemical names, and
    trade names.  The synonym list for each compound includes its CAS number
    near the top of the list.

    Returns (cas, cid) on success, (None, None) on failure.

    Examples::
        pubchem_resolve_cas("N420", session)   → ("7439-92-1", 5352425)  # Lead
        pubchem_resolve_cas("N100", session)   → ("7440-50-8", 23978)    # Copper
        pubchem_resolve_cas("LEAD COMPOUNDS", session) → ("7439-92-1", 5352425)
    """
    url = PUBCHEM_SYNONYMS_URL.format(identifier=requests.utils.quote(identifier))
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 404:
            return None, None
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"  PubChem lookup failed for {identifier!r}: {exc}", file=sys.stderr)
        return None, None

    info_list = data.get("InformationList", {}).get("Information", [])
    if not info_list:
        return None, None

    info = info_list[0]
    cid: int | None = info.get("CID")
    synonyms: list[str] = info.get("Synonym", [])

    # First synonym matching the CAS pattern is the canonical CAS number
    cas = next((s for s in synonyms if CAS_PATTERN.match(s)), None)
    return cas, cid


def lookup_iris(cas: str, iris_records: list[dict[str, str]]) -> dict[str, str] | None:
    """Return the IRIS record whose casrn matches cas, or None."""
    cas_norm = cas.strip()
    return next((r for r in iris_records if r["casrn"] == cas_norm), None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="scripts/iris_substance_nmbr_map.csv",
        help="Output CSV path (default: scripts/iris_substance_nmbr_map.csv)",
    )
    parser.add_argument(
        "--resolve",
        metavar="IDENTIFIER",
        help=(
            "Resolve a single TRI name/N-code to its IRIS entry via PubChem. "
            "Requires --iris-csv (defaults to --output path if already generated)."
        ),
    )
    parser.add_argument(
        "--iris-csv",
        metavar="PATH",
        help="Path to existing iris_substance_nmbr_map.csv (used with --resolve).",
    )
    args = parser.parse_args()

    session = requests.Session()

    # ── Resolve mode ───────────────────────────────────────────────────────────
    if args.resolve:
        csv_path = args.iris_csv or args.output
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                iris_records = list(csv.DictReader(f))
        except FileNotFoundError:
            print(
                f"ERROR: IRIS CSV not found at {csv_path!r}.\n"
                "Run without --resolve first to generate it.",
                file=sys.stderr,
            )
            sys.exit(1)

        identifier = args.resolve
        print(f"Resolving {identifier!r} via PubChem ...", file=sys.stderr)
        cas, cid = pubchem_resolve_cas(identifier, session)
        if not cas:
            print(f"  PubChem: no CAS found for {identifier!r}", file=sys.stderr)
            sys.exit(1)

        pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cas}"
        iris_rec = lookup_iris(cas, iris_records)

        print(f"identifier : {identifier}")
        print(f"pubchem_cid: {cid}")
        print(f"cas_number : {cas}")
        print(f"pubchem_url: {pubchem_url}")
        if iris_rec:
            print(f"iris_nmbr  : {iris_rec['substance_nmbr']}")
            print(f"iris_name  : {iris_rec['name']}")
            print(f"iris_url   : {iris_rec['iris_url']}")
        else:
            print("iris_nmbr  : (no IRIS entry for this CAS)")
        return

    # ── Scrape mode ────────────────────────────────────────────────────────────
    print(f"Fetching {IRIS_ATOZ_URL} ...", file=sys.stderr)
    html = fetch_page(IRIS_ATOZ_URL, session)
    time.sleep(REQUEST_DELAY_SECONDS)

    records = extract_mappings(html)

    if not records:
        print(
            "WARNING: No substance_nmbr links found in page HTML.\n"
            "The page may require JavaScript rendering.\n"
            "\nSuggestion: Use the IRIS advanced search JSON API instead:\n"
            "  https://iris.epa.gov/AdvancedSearch/exportData\n"
            "  or inspect the DataTables AJAX source URL in browser DevTools.",
            file=sys.stderr,
        )
        sys.exit(1)

    write_csv(records, args.output)

    print("substance_nmbr,name,casrn,iris_url")
    for r in records[:10]:
        print(f"{r['substance_nmbr']},{r['name']!r},{r['casrn']},{r['iris_url']}")
    if len(records) > 10:
        print(f"... ({len(records) - 10} more rows in {args.output})")


if __name__ == "__main__":
    main()
