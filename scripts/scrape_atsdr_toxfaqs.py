#!/usr/bin/env python3
"""
Scrape ATSDR ToxFAQs and ToxProfiles pages to create a mapping registry.

This script extracts chemical names and their opaque query string parameters
from saved HTML pages (ToxProfiles A-Z) and pre-extracted CSV (ToxFAQs) to 
create a lookup table that maps chemical names to stable URLs.

The ToxFAQs data was extracted via Playwright automation since the page uses
JavaScript to load content dynamically when clicking A-Z letter buttons.

Usage:
    python scripts/scrape_atsdr_toxfaqs.py --output scripts/atsdr_toxid_map.csv

The output CSV has columns:
    - chemical_name: Display name of the chemical
    - toxid: The opaque toxid parameter (shared between ToxFAQs and ToxProfiles)
    - toxprofiles_id: The 'id' parameter for ToxProfiles URLs
    - toxfaqs_faqid: The 'faqid' parameter for ToxFAQs URLs (may be null)
    - toxprofiles_url: Full URL to the ToxProfiles page
    - toxfaqs_url: Full URL to the ToxFAQs page (may be null)

Note: The toxid/tid is the canonical cross-reference key between systems.
      toxfaqs_faqid is only available for substances with ToxFAQs entries.

Author: TOXMAP Agent
Date: 2026-07-29
"""

import argparse
import csv
import html
import re
from pathlib import Path


def parse_toxprofiles_html(html_content: str) -> list[dict]:
    """
    Parse ToxProfiles A-Z Index HTML to extract chemical mappings.
    
    Pattern: ToxProfiles.aspx?id=XXX&tid=YYY">Chemical Name
    
    Returns list of dicts with:
        - chemical_name
        - toxprofiles_id (the 'id' parameter)
        - toxid (the 'tid' parameter - this is the canonical key)
    """
    # Pattern to match ToxProfiles links
    # Example: ToxProfiles.aspx?id=5&amp;tid=1">Acetone
    pattern = r'ToxProfiles\.aspx\?id=(\d+)&(?:amp;)?tid=(\d+)">([^<]+)'
    
    matches = re.findall(pattern, html_content)
    results = []
    
    for profile_id, toxid, name in matches:
        # Decode HTML entities in the name
        clean_name = html.unescape(name.strip())
        # Handle multiline names (some names span lines)
        clean_name = re.sub(r'\s+', ' ', clean_name)
        
        results.append({
            'chemical_name': clean_name,
            'toxprofiles_id': profile_id,
            'toxid': toxid,
        })
    
    return results


def parse_toxfaqs_csv(csv_path: Path) -> dict[str, dict]:
    """
    Parse ToxFAQs CSV (extracted via Playwright) to get faqid mappings.
    
    CSV columns: chemical_name, letter, faqid, toxid
    
    Returns dict keyed by toxid with:
        - chemical_name
        - toxfaqs_faqid
        - toxid
    """
    results = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            toxid = row['toxid']
            results[toxid] = {
                'chemical_name': row['chemical_name'],
                'toxfaqs_faqid': row['faqid'],
                'toxid': toxid,
            }
    
    return results


def build_registry(toxprofiles: list[dict], toxfaqs: dict[str, dict]) -> list[dict]:
    """
    Merge ToxProfiles and ToxFAQs data into a unified registry.
    
    ToxProfiles is the primary source (187 entries).
    ToxFAQs data is merged where available.
    """
    registry = []
    
    for profile in toxprofiles:
        toxid = profile['toxid']
        
        # Build full URLs
        toxprofiles_url = (
            f"https://wwwn.cdc.gov/TSP/ToxProfiles/ToxProfiles.aspx"
            f"?id={profile['toxprofiles_id']}&tid={toxid}"
        )
        
        # Check if there's a ToxFAQs entry for this toxid
        toxfaqs_entry = toxfaqs.get(toxid)
        
        if toxfaqs_entry:
            toxfaqs_url = (
                f"https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx"
                f"?faqid={toxfaqs_entry['toxfaqs_faqid']}&toxid={toxid}"
            )
            toxfaqs_faqid = toxfaqs_entry['toxfaqs_faqid']
        else:
            toxfaqs_url = None
            toxfaqs_faqid = None
        
        registry.append({
            'chemical_name': profile['chemical_name'],
            'toxid': toxid,
            'toxprofiles_id': profile['toxprofiles_id'],
            'toxfaqs_faqid': toxfaqs_faqid,
            'toxprofiles_url': toxprofiles_url,
            'toxfaqs_url': toxfaqs_url,
        })
    
    # Also add ToxFAQs-only entries (chemicals with ToxFAQs but no ToxProfile)
    toxprofiles_toxids = {p['toxid'] for p in toxprofiles}
    for toxid, entry in toxfaqs.items():
        if toxid not in toxprofiles_toxids:
            toxfaqs_url = (
                f"https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx"
                f"?faqid={entry['toxfaqs_faqid']}&toxid={toxid}"
            )
            registry.append({
                'chemical_name': entry['chemical_name'],
                'toxid': toxid,
                'toxprofiles_id': None,
                'toxfaqs_faqid': entry['toxfaqs_faqid'],
                'toxprofiles_url': None,
                'toxfaqs_url': toxfaqs_url,
            })
    
    return registry


def write_csv(registry: list[dict], output_path: Path) -> None:
    """Write registry to CSV file."""
    fieldnames = [
        'chemical_name',
        'toxid',
        'toxprofiles_id', 
        'toxfaqs_faqid',
        'toxprofiles_url',
        'toxfaqs_url',
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Sort by chemical name for easier browsing
        for row in sorted(registry, key=lambda x: x['chemical_name'].lower()):
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description='Scrape ATSDR ToxFAQs and ToxProfiles to create a mapping registry'
    )
    parser.add_argument(
        '--toxprofiles-html',
        type=Path,
        default=Path('docs/product/A-Z Index of Tox Profiles _ Toxicological Profiles _ ATSDR.html'),
        help='Path to saved ToxProfiles A-Z HTML file'
    )
    parser.add_argument(
        '--toxfaqs-csv',
        type=Path,
        default=Path('scripts/atsdr_toxfaqs_raw.csv'),
        help='Path to ToxFAQs CSV (extracted via Playwright)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('scripts/atsdr_toxid_map.csv'),
        help='Output CSV path'
    )
    
    args = parser.parse_args()
    
    # Read and parse ToxProfiles
    print(f"Reading ToxProfiles HTML from: {args.toxprofiles_html}")
    with open(args.toxprofiles_html, 'r', encoding='utf-8') as f:
        toxprofiles_html = f.read()
    toxprofiles = parse_toxprofiles_html(toxprofiles_html)
    print(f"  Found {len(toxprofiles)} ToxProfiles entries")
    
    # Read and parse ToxFAQs CSV
    print(f"Reading ToxFAQs CSV from: {args.toxfaqs_csv}")
    toxfaqs = parse_toxfaqs_csv(args.toxfaqs_csv)
    print(f"  Found {len(toxfaqs)} ToxFAQs entries")
    
    # Build merged registry
    print("Building merged registry...")
    registry = build_registry(toxprofiles, toxfaqs)
    
    # Count stats
    with_both = sum(1 for r in registry if r['toxfaqs_url'] and r['toxprofiles_url'])
    with_toxprofiles_only = sum(1 for r in registry if r['toxprofiles_url'] and not r['toxfaqs_url'])
    with_toxfaqs_only = sum(1 for r in registry if r['toxfaqs_url'] and not r['toxprofiles_url'])
    
    print(f"  Total entries: {len(registry)}")
    print(f"  With both ToxProfiles and ToxFAQs: {with_both}")
    print(f"  ToxProfiles only: {with_toxprofiles_only}")
    print(f"  ToxFAQs only: {with_toxfaqs_only}")
    
    # Write output
    print(f"Writing to: {args.output}")
    write_csv(registry, args.output)
    print("Done!")


if __name__ == '__main__':
    main()
