"""Unit tests for Superfund CAS lookup and ATSDR ToxFAQs URL validation.

Regression tests for bug fixes:
- 7.BUG.17: Comprehensive CAS lookup coverage
- 7.BUG.18: ATSDR ToxFAQs toxid correctness (MANGANESE→23, not 42)
- 7.BUG.19: ToxFAQs™ URL format validation
- 7.BUG.21: PubChem URL validation for petroleum mixtures

These tests run without Docker/database — they test the lookup table directly.
"""

import re
import pytest

from app.services.superfund_cas_lookup import SUPERFUND_CAS_LOOKUP


def _get_entry_fields(entry):
    """Extract fields from lookup entry (handles both 2-tuple and 3-tuple).

    Returns: (cas, atsdr_url, pubchem_url) where pubchem_url may be None.
    """
    if len(entry) == 2:
        return entry[0], entry[1], None
    return entry[0], entry[1], entry[2]


class TestATSDRToxidCorrectness:
    """Regression tests for 7.BUG.18: ATSDR links pointing to wrong chemicals.

    The root cause was fabricated toxid values instead of using verified data
    from scripts/atsdr_toxid_map.csv. These tests ensure the correct mappings.
    """

    @pytest.mark.parametrize(
        "chemical,expected_toxid",
        [
            # Critical regression cases that were wrong before fix
            ("MANGANESE", "23"),  # Was incorrectly 42 (Methylene Chloride)
            ("MERCURY", "24"),
            ("BARIUM", "57"),
            ("LEAD", "22"),
            ("ARSENIC", "3"),
            ("CHROMIUM", "17"),
            ("COPPER", "37"),
            ("ZINC", "54"),
            ("DIELDRIN", "56"),
            # TCE family
            ("TRICHLOROETHENE", "30"),
            ("TRICHLOROETHYLENE", "30"),
            ("TCE", "30"),
            # PERC family
            ("TETRACHLOROETHYLENE", "48"),
            ("PERCHLOROETHYLENE", "48"),
            ("PCE", "48"),
            # TPH
            ("TOTAL PETROLEUM HYDROCARBONS", "75"),
            ("TPH", "75"),
            # PFAS
            ("PFOA", "237"),
            ("PFOS", "237"),
            # PCBs
            ("AROCLOR 1254", "26"),
            ("PCBS", "26"),
            # PAHs
            ("BENZO[A]PYRENE", "25"),
            ("PAHS", "25"),
            # Other
            ("BENZENE", "14"),
            ("CADMIUM", "15"),
            ("VINYL CHLORIDE", "51"),
        ],
    )
    def test_atsdr_toxid_is_correct(self, chemical, expected_toxid):
        """Verify each chemical has the correct ATSDR toxid in its URL."""
        entry = SUPERFUND_CAS_LOOKUP.get(chemical)
        assert entry is not None, f"{chemical} not found in lookup"

        cas, atsdr_url, _ = _get_entry_fields(entry)
        assert atsdr_url is not None, f"{chemical} has no ATSDR URL"

        # Extract toxid from URL
        match = re.search(r"toxid=(\d+)", atsdr_url)
        assert match is not None, f"{chemical} ATSDR URL missing toxid: {atsdr_url}"

        actual_toxid = match.group(1)
        assert actual_toxid == expected_toxid, (
            f"REGRESSION: {chemical} has toxid={actual_toxid}, expected {expected_toxid}. "
            f"URL: {atsdr_url}"
        )

    def test_manganese_not_methylene_chloride(self):
        """Explicit regression test: MANGANESE must NOT link to Methylene Chloride."""
        entry = SUPERFUND_CAS_LOOKUP.get("MANGANESE")
        assert entry is not None
        cas, atsdr_url, _ = _get_entry_fields(entry)

        # toxid=42 is Methylene Chloride — MANGANESE must not have this
        assert "toxid=42" not in atsdr_url, (
            f"REGRESSION: MANGANESE links to Methylene Chloride (toxid=42): {atsdr_url}"
        )

        # MANGANESE should be toxid=23
        assert "toxid=23" in atsdr_url, f"MANGANESE should have toxid=23: {atsdr_url}"


class TestATSDRUrlFormat:
    """Validate ATSDR ToxFAQs URL format (7.BUG.19 regression)."""

    TOXFAQS_PATTERN = re.compile(
        r"^https://wwwn\.cdc\.gov/TSP/ToxFAQs/ToxFAQsDetails\.aspx\?faqid=\d+&toxid=\d+$"
    )

    def test_all_atsdr_urls_use_toxfaqs_format(self):
        """All ATSDR URLs should use ToxFAQs format, not ToxSubstance."""
        invalid_urls = []
        for chemical, entry in SUPERFUND_CAS_LOOKUP.items():
            _, atsdr_url, _ = _get_entry_fields(entry)
            if atsdr_url is None:
                continue

            if not self.TOXFAQS_PATTERN.match(atsdr_url):
                invalid_urls.append((chemical, atsdr_url))

        assert not invalid_urls, (
            f"Found {len(invalid_urls)} invalid ATSDR URL formats:\n"
            + "\n".join(f"  {chem}: {url}" for chem, url in invalid_urls[:10])
        )

    def test_no_toxsubstance_urls(self):
        """No ATSDR URLs should use the old ToxSubstance.aspx pattern."""
        toxsubstance_urls = []
        for chemical, entry in SUPERFUND_CAS_LOOKUP.items():
            _, atsdr_url, _ = _get_entry_fields(entry)
            if atsdr_url and "ToxSubstance.aspx" in atsdr_url:
                toxsubstance_urls.append((chemical, atsdr_url))

        assert not toxsubstance_urls, (
            f"Found ToxSubstance.aspx URLs (should be ToxFAQsDetails.aspx):\n"
            + "\n".join(f"  {chem}: {url}" for chem, url in toxsubstance_urls)
        )


class TestCASNumberCoverage:
    """Test CAS number lookup coverage (7.BUG.17 regression)."""

    @pytest.mark.parametrize(
        "chemical,expected_cas",
        [
            # Metals
            ("MANGANESE", "7439-96-5"),
            ("MERCURY", "7439-97-6"),
            ("LEAD", "7439-92-1"),
            ("ARSENIC", "7440-38-2"),
            ("CHROMIUM", "7440-47-3"),
            ("CADMIUM", "7440-43-9"),
            ("COPPER", "7440-50-8"),
            ("ZINC", "7440-66-6"),
            # PCBs (Aroclors)
            ("AROCLOR 1254", "11097-69-1"),
            ("AROCLOR 1260", "11096-82-5"),
            # PAHs
            ("BENZO[A]PYRENE", "50-32-8"),
            ("NAPHTHALENE", "91-20-3"),
            ("CHRYSENE", "218-01-9"),
            # Chlorinated solvents
            ("TRICHLOROETHENE", "79-01-6"),
            ("TETRACHLOROETHYLENE", "127-18-4"),
            ("CHLOROFORM", "67-66-3"),
            ("CARBON TETRACHLORIDE", "56-23-5"),
            ("1,1,1-TRICHLOROETHANE", "71-55-6"),
            # CFCs (added in 7.BUG.18)
            ("DICHLORODIFLUOROMETHANE", "75-71-8"),
            ("TRICHLOROFLUOROMETHANE", "75-69-4"),
            # Alkylbenzenes (added in 7.BUG.18)
            ("BUTAN-2-YLBENZENE", "135-98-8"),
            ("PROPYLBENZENE", "103-65-1"),
            ("P-CYMENE", "99-87-6"),
            # Pesticides
            ("DDT", "50-29-3"),
            ("DIELDRIN", "60-57-1"),
            ("CHLORDANE", "57-74-9"),
            # PFAS
            ("PFOA", "335-67-1"),
            ("PFOS", "1763-23-1"),
            # Inorganic
            ("SULFATE", "14808-79-8"),
            ("SULFURIC ACID", "7664-93-9"),
        ],
    )
    def test_cas_number_correct(self, chemical, expected_cas):
        """Verify CAS numbers are correct for key chemicals."""
        entry = SUPERFUND_CAS_LOOKUP.get(chemical)
        assert entry is not None, f"{chemical} not found in lookup"

        actual_cas, _, _ = _get_entry_fields(entry)
        assert actual_cas == expected_cas, (
            f"{chemical} has CAS={actual_cas}, expected {expected_cas}"
        )

    def test_lookup_has_minimum_coverage(self):
        """Lookup should have at least 200 entries for comprehensive coverage."""
        assert len(SUPERFUND_CAS_LOOKUP) >= 200, (
            f"Lookup has only {len(SUPERFUND_CAS_LOOKUP)} entries, expected 200+"
        )

    def test_metal_oxides_have_cas(self):
        """Metal oxide compounds should have CAS numbers."""
        for chemical in ["ALUMINUM OXIDE"]:
            entry = SUPERFUND_CAS_LOOKUP.get(chemical)
            assert entry is not None, f"{chemical} not found"
            cas, _, _ = _get_entry_fields(entry)
            assert cas and cas != "N/A", f"{chemical} missing CAS"


class TestChemicalNameVariants:
    """Test that common name variants are all covered."""

    @pytest.mark.parametrize(
        "variants",
        [
            # TCE variants
            ("TRICHLOROETHENE", "TRICHLOROETHYLENE", "TCE"),
            # PERC variants
            ("TETRACHLOROETHENE", "TETRACHLOROETHYLENE", "PERCHLOROETHYLENE", "PCE"),
            # DCE variants
            ("CIS-1,2-DICHLOROETHENE", "CIS-1,2-DICHLOROETHYLENE"),
            # Methylene chloride
            ("DICHLOROMETHANE", "METHYLENE CHLORIDE"),
            # MTBE
            ("METHYL TERT-BUTYL ETHER", "MTBE"),
            # DDT family
            ("DDT", "4,4'-DDT", "P,P'-DDT"),
            # Xylenes
            ("XYLENE", "XYLENES", "XYLENES (TOTAL)", "XYLENE (MIXED ISOMERS)"),
        ],
    )
    def test_all_variants_present(self, variants):
        """All chemical name variants should be in the lookup."""
        missing = [v for v in variants if v not in SUPERFUND_CAS_LOOKUP]
        assert not missing, f"Missing variants: {missing}"

    def test_variants_have_same_atsdr(self):
        """Name variants should link to the same ATSDR page."""
        tce_variants = ["TRICHLOROETHENE", "TRICHLOROETHYLENE", "TCE"]
        urls = set()
        for v in tce_variants:
            _, url, _ = _get_entry_fields(SUPERFUND_CAS_LOOKUP[v])
            if url:
                urls.add(url)

        assert len(urls) == 1, f"TCE variants have different ATSDR URLs: {urls}"


class TestPubChemUrlValidation:
    """Regression tests for 7.BUG.21: PubChem URLs for petroleum mixtures.

    The root cause was that PubChem `/compound/` URLs don't work for complex
    mixtures. For example:
    - `/compound/Total-petroleum-hydrocarbons` returns 404
    - `/compound/JP-5` redirects to wrong compound (organic molecule, not jet fuel)

    Fix: Use explicit PubChem URLs in 3-tuple format:
    - TPH → /substance/135312467
    - JP-5 → /substance/135356845
    - JP-8 → /substance/505788256
    - Fuel Oils → /compound/Fuel-Oils (works for reference chemicals)
    """

    PUBCHEM_COMPOUND_PATTERN = re.compile(
        r"^https://pubchem\.ncbi\.nlm\.nih\.gov/compound/.+$"
    )
    PUBCHEM_SUBSTANCE_PATTERN = re.compile(
        r"^https://pubchem\.ncbi\.nlm\.nih\.gov/substance/\d+$"
    )
    PUBCHEM_SEARCH_PATTERN = re.compile(
        r"^https://pubchem\.ncbi\.nlm\.nih\.gov/#query=.+$"
    )

    @pytest.mark.parametrize(
        "chemical,expected_url_type,expected_path_contains",
        [
            # Petroleum mixtures must use /substance/ URLs
            ("TOTAL PETROLEUM HYDROCARBONS", "substance", "135312467"),
            ("TOTAL PETROLEUM HYDROCARBONS (TPH)", "substance", "135312467"),
            ("TPH", "substance", "135312467"),
            ("JP-5", "substance", "135356845"),
            ("JP-8", "substance", "505788256"),
            # Fuel oils use /compound/Fuel-Oils (working refchem URL)
            ("FUEL OIL", "compound", "Fuel-Oils"),
            ("FUEL OIL NO. 2", "compound", "Fuel-Oils"),
            ("FUEL OIL NO. 4", "compound", "Fuel-Oils"),
            ("FUEL OIL NO. 6", "compound", "Fuel-Oils"),
            ("HEATING OIL", "compound", "Fuel-Oils"),
            # Other petroleum products use /compound/ with correct names
            ("GASOLINE", "compound", "Gasoline"),
            ("DIESEL FUEL", "compound", "Diesel-Fuel"),
            ("DIESEL", "compound", "Diesel-Fuel"),
            ("KEROSENE", "compound", "Kerosene"),
            ("MINERAL OIL", "compound", "Mineral-oil"),
        ],
    )
    def test_petroleum_mixture_pubchem_urls(
        self, chemical, expected_url_type, expected_path_contains
    ):
        """Verify petroleum mixtures have correct explicit PubChem URLs."""
        entry = SUPERFUND_CAS_LOOKUP.get(chemical)
        assert entry is not None, f"{chemical} not found in lookup"

        _, _, pubchem_url = _get_entry_fields(entry)
        assert pubchem_url is not None, (
            f"REGRESSION: {chemical} missing explicit PubChem URL (3-tuple required)"
        )

        # Verify URL type
        if expected_url_type == "substance":
            assert self.PUBCHEM_SUBSTANCE_PATTERN.match(pubchem_url), (
                f"REGRESSION: {chemical} should use /substance/ URL, got: {pubchem_url}"
            )
        else:
            assert self.PUBCHEM_COMPOUND_PATTERN.match(pubchem_url), (
                f"{chemical} should use /compound/ URL, got: {pubchem_url}"
            )

        # Verify path contains expected identifier
        assert expected_path_contains in pubchem_url, (
            f"REGRESSION: {chemical} URL should contain '{expected_path_contains}', "
            f"got: {pubchem_url}"
        )

    def test_tph_not_compound_url(self):
        """Explicit regression test: TPH must NOT use /compound/ URL."""
        entry = SUPERFUND_CAS_LOOKUP.get("TOTAL PETROLEUM HYDROCARBONS")
        assert entry is not None
        _, _, pubchem_url = _get_entry_fields(entry)

        # /compound/Total-petroleum-hydrocarbons returns 404
        assert "/compound/" not in pubchem_url, (
            f"REGRESSION: TPH uses /compound/ URL (returns 404): {pubchem_url}"
        )

    def test_jp5_not_compound_url(self):
        """Explicit regression test: JP-5 must NOT use /compound/JP-5 URL.

        /compound/JP-5 redirects to a complex organic molecule (CID 156012505),
        not JP-5 jet fuel.
        """
        entry = SUPERFUND_CAS_LOOKUP.get("JP-5")
        assert entry is not None
        _, _, pubchem_url = _get_entry_fields(entry)

        # /compound/JP-5 redirects to wrong compound
        assert "/compound/JP-5" not in pubchem_url, (
            f"REGRESSION: JP-5 uses /compound/JP-5 URL (wrong compound): {pubchem_url}"
        )

    def test_all_pubchem_urls_are_valid_format(self):
        """All explicit PubChem URLs should use valid patterns.
        
        Valid patterns:
        - /compound/{name_or_cid} - for specific compounds
        - /substance/{sid} - for mixtures (e.g., TPH, JP-5)
        - /#query={term} - for search URLs (compound classes like dioxins)
        """
        invalid_urls = []
        for chemical, entry in SUPERFUND_CAS_LOOKUP.items():
            _, _, pubchem_url = _get_entry_fields(entry)
            if pubchem_url is None:
                continue

            is_valid = (
                self.PUBCHEM_COMPOUND_PATTERN.match(pubchem_url)
                or self.PUBCHEM_SUBSTANCE_PATTERN.match(pubchem_url)
                or self.PUBCHEM_SEARCH_PATTERN.match(pubchem_url)
            )
            if not is_valid:
                invalid_urls.append((chemical, pubchem_url))

        assert not invalid_urls, (
            f"Found {len(invalid_urls)} invalid PubChem URL formats:\n"
            + "\n".join(f"  {chem}: {url}" for chem, url in invalid_urls[:10])
        )

    def test_3tuple_entries_have_explicit_pubchem(self):
        """All 3-tuple entries should have non-None PubChem URL."""
        missing = []
        for chemical, entry in SUPERFUND_CAS_LOOKUP.items():
            if len(entry) == 3 and entry[2] is None:
                missing.append(chemical)

        assert not missing, (
            f"3-tuple entries with None PubChem URL (should use 2-tuple instead): "
            f"{missing[:10]}"
        )


class TestDioxinPubChemUrls:
    """Regression tests for 7.BUG.23: PubChem URLs for dioxins and furans.

    Issue: DIOXINS (CHLORINATED DIBENZODIOXINS) and similar compound classes
    had no PubChem URL because CAS was "N/A" and no explicit URL was provided.

    Fix: Add explicit PubChem URLs:
    - Specific dioxins (e.g., 2,3,7,8-TCDD) → /compound/{CID}
    - Dioxin classes → /#query={search_term} (search URLs)
    """

    PUBCHEM_SEARCH_PATTERN = re.compile(
        r"^https://pubchem\.ncbi\.nlm\.nih\.gov/#query=.+$"
    )
    PUBCHEM_COMPOUND_PATTERN = re.compile(
        r"^https://pubchem\.ncbi\.nlm\.nih\.gov/compound/.+$"
    )

    @pytest.mark.parametrize(
        "chemical,expected_url_type,expected_path_contains",
        [
            # Specific dioxins use /compound/ with CID
            ("2,3,7,8-TETRACHLORODIBENZO-P-DIOXIN", "compound", "15625"),
            ("2,3,7,8-TCDD", "compound", "15625"),
            ("TCDD", "compound", "15625"),
            # Dioxin/furan classes use search URLs
            ("DIOXINS (CHLORINATED DIBENZODIOXINS)", "search", "dibenzodioxins"),
            ("CHLORINATED DIOXINS AND FURANS", "search", "dioxins"),
            ("DIOXINS AND DIBENZOFURANS", "search", "dioxins"),
            # Specific furan compound
            ("2,3,7,8-TETRACHLORODIBENZOFURAN", "compound", "39227"),
        ],
    )
    def test_dioxin_pubchem_urls(
        self, chemical, expected_url_type, expected_path_contains
    ):
        """Verify dioxin compounds have correct PubChem URLs."""
        entry = SUPERFUND_CAS_LOOKUP.get(chemical)
        assert entry is not None, f"{chemical} not found in lookup"

        _, _, pubchem_url = _get_entry_fields(entry)
        assert pubchem_url is not None, (
            f"REGRESSION: {chemical} missing PubChem URL"
        )

        # Verify URL type
        if expected_url_type == "search":
            assert self.PUBCHEM_SEARCH_PATTERN.match(pubchem_url), (
                f"REGRESSION: {chemical} should use search URL, got: {pubchem_url}"
            )
        else:
            assert self.PUBCHEM_COMPOUND_PATTERN.match(pubchem_url), (
                f"{chemical} should use /compound/ URL, got: {pubchem_url}"
            )

        # Verify path contains expected identifier
        assert expected_path_contains in pubchem_url, (
            f"REGRESSION: {chemical} URL should contain '{expected_path_contains}', "
            f"got: {pubchem_url}"
        )

    def test_dioxins_not_missing_urls(self):
        """All dioxin/furan class entries should have PubChem URLs.
        
        Note: DIBENZO(A,H)ANTHRACENE is a PAH (polycyclic aromatic hydrocarbon),
        not a dioxin, so it's excluded from this check. It has a CAS number
        so it gets an auto-generated PubChem URL.
        """
        # Only check actual dioxin/furan entries, not PAHs with "DIBENZO" in name
        dioxin_entries = [
            name for name in SUPERFUND_CAS_LOOKUP
            if ("DIOXIN" in name or "DIBENZOFURAN" in name)
            and "ANTHRACENE" not in name  # Exclude PAH
        ]
        missing = []
        for name in dioxin_entries:
            _, _, pubchem_url = _get_entry_fields(SUPERFUND_CAS_LOOKUP[name])
            if pubchem_url is None:
                missing.append(name)

        assert not missing, (
            f"REGRESSION: Dioxin entries missing PubChem URLs: {missing}"
        )
