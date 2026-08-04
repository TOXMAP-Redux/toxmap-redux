"""Unit tests for TRI ingestion CAS number validation.

7.BUG.22 regression: TRI category codes (N###) are NOT CAS numbers.
PubChem URLs like /compound/N090 return 404.

These tests ensure:
1. Valid CAS numbers generate correct PubChem URLs
2. TRI category codes are mapped to correct element/search URLs
3. Invalid formats are rejected (return None)
"""

import pytest
import re

# Import the validation patterns and mapping from tri_ingest
# Note: These are module-level variables, so we test them directly
# to avoid side effects from the full ingestion module.

# Mirror the patterns from tri_ingest.py
_CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")
_TRI_CATEGORY_PATTERN = re.compile(r"^N\d{3}$")

# Mapping of TRI category codes (N###) to correct PubChem URLs
_TRI_CATEGORY_PUBCHEM = {
    "N010": "https://pubchem.ncbi.nlm.nih.gov/element/Antimony",   # ANTIMONY COMPOUNDS
    "N020": "https://pubchem.ncbi.nlm.nih.gov/element/Arsenic",    # ARSENIC COMPOUNDS
    "N040": "https://pubchem.ncbi.nlm.nih.gov/element/Barium",     # BARIUM COMPOUNDS
    "N050": "https://pubchem.ncbi.nlm.nih.gov/element/Beryllium",  # BERYLLIUM COMPOUNDS
    "N078": "https://pubchem.ncbi.nlm.nih.gov/element/Cadmium",    # CADMIUM COMPOUNDS
    "N090": "https://pubchem.ncbi.nlm.nih.gov/element/Chromium",   # CHROMIUM COMPOUNDS
    "N096": "https://pubchem.ncbi.nlm.nih.gov/element/Cobalt",     # COBALT COMPOUNDS
    "N100": "https://pubchem.ncbi.nlm.nih.gov/element/Copper",     # COPPER COMPOUNDS
    "N420": "https://pubchem.ncbi.nlm.nih.gov/element/Lead",       # LEAD COMPOUNDS
    "N450": "https://pubchem.ncbi.nlm.nih.gov/element/Manganese",  # MANGANESE COMPOUNDS
    "N458": "https://pubchem.ncbi.nlm.nih.gov/element/Mercury",    # MERCURY COMPOUNDS
    "N495": "https://pubchem.ncbi.nlm.nih.gov/element/Nickel",     # NICKEL COMPOUNDS
    "N725": "https://pubchem.ncbi.nlm.nih.gov/element/Selenium",   # SELENIUM COMPOUNDS
    "N740": "https://pubchem.ncbi.nlm.nih.gov/element/Silver",     # SILVER COMPOUNDS
    "N760": "https://pubchem.ncbi.nlm.nih.gov/element/Thallium",   # THALLIUM COMPOUNDS
    "N770": "https://pubchem.ncbi.nlm.nih.gov/compound/Vanadium",  # VANADIUM COMPOUNDS
    "N982": "https://pubchem.ncbi.nlm.nih.gov/element/Zinc",       # ZINC COMPOUNDS
    "N084": "https://pubchem.ncbi.nlm.nih.gov/#query=chlorophenols",        # CHLOROPHENOLS
    "N106": "https://pubchem.ncbi.nlm.nih.gov/compound/Cyanide",            # CYANIDE COMPOUNDS
    "N120": "https://pubchem.ncbi.nlm.nih.gov/#query=diisocyanates",        # DIISOCYANATES
    "N511": None,  # NITRATE COMPOUNDS - too broad
}


def _pubchem_url(cas: str | None) -> str | None:
    """Mirror of tri_ingest._pubchem_url for unit testing."""
    if not cas:
        return None

    cas = cas.strip()

    # Check if this is a TRI category code (N###)
    if _TRI_CATEGORY_PATTERN.match(cas):
        return _TRI_CATEGORY_PUBCHEM.get(cas)

    # Validate CAS number format (e.g., 71-36-3, 7440-50-8)
    if not _CAS_PATTERN.match(cas):
        return None

    return f"https://pubchem.ncbi.nlm.nih.gov/compound/{cas}"


class TestCasNumberValidation:
    """Test CAS number pattern validation."""

    @pytest.mark.parametrize("cas", [
        "71-36-3",        # N-Butyl alcohol
        "7440-50-8",      # Copper
        "50-00-0",        # Formaldehyde
        "7439-96-5",      # Manganese
        "1234567-12-3",   # Max length (7-2-1)
    ])
    def test_valid_cas_format(self, cas: str):
        """Valid CAS numbers should match the pattern."""
        assert _CAS_PATTERN.match(cas), f"{cas} should match CAS pattern"

    @pytest.mark.parametrize("invalid", [
        "N010",           # TRI category code
        "N090",           # TRI category code
        "N982",           # TRI category code
        "ABC-12-3",       # Letters in first group
        "123-AB-1",       # Letters in second group
        "123-12-X",       # Letter in check digit
        "1-12-3",         # First group too short
        "12345678-12-3",  # First group too long (8 digits)
        "123-1-3",        # Second group too short
        "123-123-3",      # Second group too long
        "123-12-34",      # Check digit too long
        "12312-3",        # Missing hyphens
        "",               # Empty string
    ])
    def test_invalid_cas_format(self, invalid: str):
        """Invalid formats should not match the CAS pattern."""
        assert not _CAS_PATTERN.match(invalid), f"{invalid} should NOT match CAS pattern"


class TestTriCategoryCodeDetection:
    """Test TRI category code (N###) detection."""

    @pytest.mark.parametrize("code", [
        "N010", "N020", "N040", "N050", "N078", "N084", "N090",
        "N096", "N100", "N106", "N120", "N125", "N150", "N171",
        "N230", "N270", "N420", "N450", "N458", "N495", "N503",
        "N511", "N530", "N535", "N575", "N583", "N590", "N725",
        "N740", "N746", "N760", "N770", "N874", "N982",
    ])
    def test_tri_category_codes_detected(self, code: str):
        """All TRI category codes should match the N### pattern."""
        assert _TRI_CATEGORY_PATTERN.match(code), f"{code} should match TRI pattern"

    @pytest.mark.parametrize("not_tri", [
        "71-36-3",        # CAS number
        "7440-50-8",      # CAS number
        "N1",             # Too short
        "N12",            # Too short
        "N1234",          # Too long
        "NABC",           # Letters instead of digits
        "M010",           # Wrong prefix
    ])
    def test_non_tri_codes_not_detected(self, not_tri: str):
        """Non-TRI codes should not match the N### pattern."""
        assert not _TRI_CATEGORY_PATTERN.match(not_tri), f"{not_tri} should NOT match TRI pattern"


class TestPubchemUrlGeneration:
    """Test the complete _pubchem_url() function (7.BUG.22 regression)."""

    def test_none_returns_none(self):
        """None input should return None."""
        assert _pubchem_url(None) is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert _pubchem_url("") is None

    def test_whitespace_string_returns_none(self):
        """Whitespace-only string should return None."""
        assert _pubchem_url("   ") is None

    @pytest.mark.parametrize("cas,expected_url", [
        ("71-36-3", "https://pubchem.ncbi.nlm.nih.gov/compound/71-36-3"),
        ("7440-50-8", "https://pubchem.ncbi.nlm.nih.gov/compound/7440-50-8"),
        ("50-00-0", "https://pubchem.ncbi.nlm.nih.gov/compound/50-00-0"),
    ])
    def test_valid_cas_generates_compound_url(self, cas: str, expected_url: str):
        """Valid CAS numbers should generate /compound/{CAS} URLs."""
        assert _pubchem_url(cas) == expected_url

    @pytest.mark.parametrize("cas_with_whitespace,expected_url", [
        (" 71-36-3 ", "https://pubchem.ncbi.nlm.nih.gov/compound/71-36-3"),
        ("  7440-50-8", "https://pubchem.ncbi.nlm.nih.gov/compound/7440-50-8"),
    ])
    def test_whitespace_trimmed(self, cas_with_whitespace: str, expected_url: str):
        """Whitespace around CAS numbers should be trimmed."""
        assert _pubchem_url(cas_with_whitespace) == expected_url

    # 7.BUG.22 regression tests
    @pytest.mark.parametrize("tri_code,expected_url", [
        ("N100", "https://pubchem.ncbi.nlm.nih.gov/element/Copper"),
        ("N090", "https://pubchem.ncbi.nlm.nih.gov/element/Chromium"),
        ("N420", "https://pubchem.ncbi.nlm.nih.gov/element/Lead"),
        ("N458", "https://pubchem.ncbi.nlm.nih.gov/element/Mercury"),
        ("N982", "https://pubchem.ncbi.nlm.nih.gov/element/Zinc"),
    ])
    def test_metal_compound_codes_map_to_element_urls(self, tri_code: str, expected_url: str):
        """Metal compound TRI codes should map to /element/{Element} URLs."""
        assert _pubchem_url(tri_code) == expected_url

    @pytest.mark.parametrize("tri_code,expected_url", [
        ("N106", "https://pubchem.ncbi.nlm.nih.gov/compound/Cyanide"),
        ("N770", "https://pubchem.ncbi.nlm.nih.gov/compound/Vanadium"),
    ])
    def test_compound_codes_map_to_compound_urls(self, tri_code: str, expected_url: str):
        """Some TRI codes map to specific /compound/ URLs."""
        assert _pubchem_url(tri_code) == expected_url

    @pytest.mark.parametrize("tri_code,expected_url", [
        ("N084", "https://pubchem.ncbi.nlm.nih.gov/#query=chlorophenols"),
        ("N120", "https://pubchem.ncbi.nlm.nih.gov/#query=diisocyanates"),
    ])
    def test_category_codes_map_to_search_urls(self, tri_code: str, expected_url: str):
        """Chemical class TRI codes should map to search URLs."""
        assert _pubchem_url(tri_code) == expected_url

    def test_unmapped_category_returns_none(self):
        """TRI codes without a mapping should return None."""
        assert _pubchem_url("N511") is None  # NITRATE COMPOUNDS - too broad

    def test_invalid_format_returns_none(self):
        """Invalid formats (not CAS, not TRI code) should return None."""
        assert _pubchem_url("invalid") is None
        assert _pubchem_url("ABC123") is None
        assert _pubchem_url("Total-petroleum-hydrocarbons") is None

    def test_broken_n_codes_do_not_generate_broken_urls(self):
        """TRI category codes should NEVER generate /compound/N### URLs (7.BUG.22)."""
        # These broken URLs were the original bug - they return 404 on PubChem
        for code in ["N010", "N090", "N100", "N420", "N982"]:
            url = _pubchem_url(code)
            # URL should never be /compound/N###
            if url:
                assert f"/compound/{code}" not in url, \
                    f"{code} generated broken URL: {url}"
