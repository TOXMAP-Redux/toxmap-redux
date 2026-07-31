"""Unit tests for Superfund CAS lookup and ATSDR ToxFAQs URL validation.

Regression tests for bug fixes:
- 7.BUG.17: Comprehensive CAS lookup coverage
- 7.BUG.18: ATSDR ToxFAQs toxid correctness (MANGANESE→23, not 42)
- 7.BUG.19: ToxFAQs™ URL format validation

These tests run without Docker/database — they test the lookup table directly.
"""

import re
import pytest

from app.services.superfund_cas_lookup import SUPERFUND_CAS_LOOKUP


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

        cas, atsdr_url = entry
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
        cas, atsdr_url = entry

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
        for chemical, (cas, atsdr_url) in SUPERFUND_CAS_LOOKUP.items():
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
        for chemical, (cas, atsdr_url) in SUPERFUND_CAS_LOOKUP.items():
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

        actual_cas, _ = entry
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
            cas, _ = entry
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
            _, url = SUPERFUND_CAS_LOOKUP[v]
            if url:
                urls.add(url)

        assert len(urls) == 1, f"TCE variants have different ATSDR URLs: {urls}"
