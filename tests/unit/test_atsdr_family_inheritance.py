"""Unit tests for ATSDR URL family inheritance per ADR-007.

Regression tests for bug fix 7.BUG.20:
- TRI chemicals like "ZINC COMPOUNDS" should inherit ATSDR URL from parent "ZINC"
- Backfill script should populate atsdr_url for family members
- tri_ingest.py should populate atsdr_url on new ingestion

These tests validate the lookup behavior without requiring a database.
"""

import pytest

from app.services.superfund_cas_lookup import _ATSDR as ATSDR_LOOKUP


class TestATSDRFamilyLookup:
    """Test that ATSDR lookup dict has entries for parent chemicals.

    The _ATSDR dict should contain entries for parent chemicals (ZINC, LEAD)
    so that child chemicals (ZINC COMPOUNDS, LEAD AND LEAD COMPOUNDS) can
    inherit the ATSDR URL via family relationship.
    """

    # Chemical families per ADR-007
    METAL_FAMILIES = [
        # (parent_name, expected_in_atsdr, toxid_in_url)
        ("LEAD", True, "22"),
        ("ZINC", True, "54"),
        ("MERCURY", True, "24"),
        ("CHROMIUM", True, "17"),
        ("ARSENIC", True, "3"),
        ("CADMIUM", True, "15"),
        ("NICKEL", True, "18"),
        ("COPPER", True, "37"),
        ("MANGANESE", True, "23"),
        ("BARIUM", True, "57"),
        ("COBALT", True, "19"),
        ("BERYLLIUM", True, "12"),
        ("ANTIMONY", True, "6"),
        ("SELENIUM", True, "46"),
        ("SILVER", True, "47"),
        ("THALLIUM", True, "49"),
        ("VANADIUM", True, "50"),
    ]

    @pytest.mark.parametrize("parent,expected_present,expected_toxid", METAL_FAMILIES)
    def test_parent_chemical_in_atsdr_lookup(
        self, parent: str, expected_present: bool, expected_toxid: str
    ):
        """Verify parent chemicals have ATSDR entries for family inheritance."""
        atsdr_url = ATSDR_LOOKUP.get(parent)

        if expected_present:
            assert atsdr_url is not None, (
                f"REGRESSION 7.BUG.20: Parent chemical {parent} missing from _ATSDR lookup. "
                f"Child chemicals like '{parent} COMPOUNDS' cannot inherit ATSDR URL."
            )
            assert f"toxid={expected_toxid}" in atsdr_url, (
                f"Parent {parent} has wrong toxid. Expected toxid={expected_toxid}, "
                f"got URL: {atsdr_url}"
            )


class TestFamilyInheritanceLogic:
    """Test the family inheritance lookup algorithm.

    When a chemical like "ZINC COMPOUNDS" is not directly in _ATSDR,
    the backfill script should check if the chemical's family parent
    (e.g., "ZINC") has an entry and use that URL.
    """

    # Chemical variants that should inherit from parent
    FAMILY_INHERITANCE_CASES = [
        # (child_chemical, parent_family, should_inherit)
        ("ZINC COMPOUNDS", "ZINC", True),
        ("ZINC (FUME OR DUST)", "ZINC", True),
        ("LEAD COMPOUNDS", "LEAD", True),  # Actually has its own entry, but could inherit
        ("LEAD AND LEAD COMPOUNDS", "LEAD", True),
        ("MERCURY COMPOUNDS", "MERCURY", True),
        ("MERCURY AND MERCURY COMPOUNDS", "MERCURY", True),
        ("CHROMIUM COMPOUNDS", "CHROMIUM", True),
        ("ARSENIC COMPOUNDS", "ARSENIC", True),
        ("CADMIUM COMPOUNDS", "CADMIUM", True),
        ("NICKEL COMPOUNDS", "NICKEL", True),
        ("COPPER COMPOUNDS", "COPPER", True),
        ("MANGANESE COMPOUNDS", "MANGANESE", True),
        ("MANGANESE AND MANGANESE COMPOUNDS", "MANGANESE", True),
        ("BARIUM COMPOUNDS", "BARIUM", True),
        ("COBALT COMPOUNDS", "COBALT", True),
        ("ANTIMONY COMPOUNDS", "ANTIMONY", True),
        ("SELENIUM COMPOUNDS", "SELENIUM", True),
        ("SILVER COMPOUNDS", "SILVER", True),
        ("THALLIUM COMPOUNDS", "THALLIUM", True),
        ("VANADIUM COMPOUNDS", "VANADIUM", True),
        ("CYANIDE COMPOUNDS", "CYANIDE", True),
    ]

    @pytest.mark.parametrize("child,parent,should_inherit", FAMILY_INHERITANCE_CASES)
    def test_family_parent_has_atsdr_for_child_inheritance(
        self, child: str, parent: str, should_inherit: bool
    ):
        """Verify parent has ATSDR URL so child can inherit via family lookup.

        This test validates that when `backfill_atsdr_urls.py` looks up
        a child chemical's family parent, the parent has an ATSDR URL.
        """
        if not should_inherit:
            return

        # Check if child has direct entry (preferred over inheritance)
        child_url = ATSDR_LOOKUP.get(child)
        parent_url = ATSDR_LOOKUP.get(parent)

        # Either child has direct URL or parent must have URL for inheritance
        assert child_url is not None or parent_url is not None, (
            f"REGRESSION 7.BUG.20: {child} has no ATSDR URL and parent {parent} "
            f"has no URL for inheritance. ToxFAQs link will not appear."
        )

    def test_inheritance_algorithm(self):
        """Test the exact algorithm used by backfill_atsdr_urls.py.

        1. Try exact name match: ATSDR_LOOKUP.get(chemical_name)
        2. If no match, try family name: ATSDR_LOOKUP.get(family_name)
        """
        # Simulate the backfill algorithm
        def get_atsdr_url(chemical_name: str, family_name: str | None) -> str | None:
            """Replicate the logic from backfill_atsdr_urls.py."""
            # 1. Try exact name match
            url = ATSDR_LOOKUP.get(chemical_name.upper())
            if url:
                return url

            # 2. Try family name inheritance
            if family_name:
                url = ATSDR_LOOKUP.get(family_name.upper())
                if url:
                    return url

            return None

        # Test cases
        test_cases = [
            # Direct matches
            ("LEAD", None, True, "direct"),
            ("ZINC", None, True, "direct"),
            ("BENZENE", None, True, "direct"),
            # Family inheritance
            ("ZINC COMPOUNDS", "ZINC", True, "family"),
            ("LEAD AND LEAD COMPOUNDS", "LEAD", True, "family"),
            ("MERCURY COMPOUNDS", "MERCURY", True, "family"),
            # No match (no family)
            ("SOME RANDOM CHEMICAL", None, False, "none"),
            # No match (unknown family)
            ("UNKNOWN COMPOUNDS", "UNKNOWN", False, "none"),
        ]

        for chemical, family, should_have_url, source in test_cases:
            url = get_atsdr_url(chemical, family)
            if should_have_url:
                assert url is not None, (
                    f"Expected ATSDR URL for {chemical} (family={family}, source={source})"
                )
            else:
                assert url is None, (
                    f"Did not expect ATSDR URL for {chemical} (family={family})"
                )


class TestCommonTRIChemicals:
    """Test ATSDR coverage for the most commonly reported TRI chemicals.

    These are the chemicals that appear most frequently in TRI data.
    Citizens searching for these should see ToxFAQs links.
    """

    # Top TRI chemicals that should have ATSDR coverage
    TOP_TRI_CHEMICALS = [
        "AMMONIA",
        "METHANOL",  # NOTE: Not in ATSDR - acceptable gap
        "TOLUENE",
        "XYLENES",
        "N-HEXANE",
        "HYDROGEN SULFIDE",
        "SULFURIC ACID",
        "HYDROCHLORIC ACID",
        "NITRIC ACID",
        "ZINC COMPOUNDS",  # Via family
        "LEAD COMPOUNDS",  # Via family
        "MANGANESE",
        "COPPER",
        "CHROMIUM",
        "NICKEL",
        "FORMALDEHYDE",
        "STYRENE",
        "ETHYLENE GLYCOL",
        "BENZENE",
        "ETHYLBENZENE",
    ]

    # Known gaps - chemicals without ATSDR ToxFAQs
    KNOWN_GAPS = {"METHANOL", "CERTAIN GLYCOL ETHERS", "N-BUTYL ALCOHOL"}

    @pytest.mark.parametrize("chemical", TOP_TRI_CHEMICALS)
    def test_top_tri_chemical_coverage(self, chemical: str):
        """Verify common TRI chemicals have ATSDR URL or are known gaps."""
        # Skip known gaps
        if chemical in self.KNOWN_GAPS:
            pytest.skip(f"{chemical} is a known gap without ATSDR coverage")

        # For compound chemicals, check family parent too
        url = ATSDR_LOOKUP.get(chemical)

        # If exact match fails, try stripping " COMPOUNDS" suffix
        if url is None and "COMPOUNDS" in chemical:
            parent = chemical.replace(" COMPOUNDS", "").replace(" AND ", "").strip()
            url = ATSDR_LOOKUP.get(parent)

        assert url is not None, (
            f"REGRESSION 7.BUG.20: Top TRI chemical {chemical} has no ATSDR coverage. "
            f"Consider adding to known gaps or fixing _ATSDR lookup."
        )


class TestRedDogOperationsCoverage:
    """Regression test for RED DOG OPERATIONS (Kotzebue, AK).

    This facility was the original test case for 7.BUG.20.
    It reports ZINC COMPOUNDS, LEAD AND LEAD COMPOUNDS, MANGANESE AND MANGANESE COMPOUNDS,
    MERCURY AND MERCURY COMPOUNDS, and AMMONIA - all should have ToxFAQs links.
    """

    RED_DOG_CHEMICALS = [
        ("ZINC COMPOUNDS", "ZINC"),
        ("LEAD AND LEAD COMPOUNDS", "LEAD"),
        ("MANGANESE AND MANGANESE COMPOUNDS", "MANGANESE"),
        ("MERCURY AND MERCURY COMPOUNDS", "MERCURY"),
        ("AMMONIA", None),  # Direct match, no family needed
    ]

    @pytest.mark.parametrize("chemical,family", RED_DOG_CHEMICALS)
    def test_red_dog_chemical_has_atsdr_coverage(self, chemical: str, family: str | None):
        """Ensure all RED DOG OPERATIONS chemicals have ToxFAQs links."""
        # Try direct match
        url = ATSDR_LOOKUP.get(chemical)

        # Try family inheritance
        if url is None and family:
            url = ATSDR_LOOKUP.get(family)

        assert url is not None, (
            f"REGRESSION 7.BUG.20 (Red Dog): {chemical} has no ATSDR URL. "
            f"Family parent: {family}. ToxFAQs link will not appear in drawer."
        )


class TestBallMetalCoverage:
    """Regression test for BALL METAL BEVERAGE CONTAINER CORP (Golden, CO).

    This facility was the original test case showing LEAD without ToxFAQs link.
    """

    BALL_METAL_CHEMICALS = [
        ("LEAD", None),  # Direct match
        ("FORMALDEHYDE", None),  # Direct match
        ("N-BUTYL ALCOHOL", None),  # Known gap - no ATSDR
        ("CERTAIN GLYCOL ETHERS", None),  # Known gap - no ATSDR
    ]

    KNOWN_GAPS = {"N-BUTYL ALCOHOL", "CERTAIN GLYCOL ETHERS"}

    @pytest.mark.parametrize("chemical,family", BALL_METAL_CHEMICALS)
    def test_ball_metal_chemical_coverage(self, chemical: str, family: str | None):
        """Ensure key BALL METAL chemicals have ToxFAQs links."""
        if chemical in self.KNOWN_GAPS:
            pytest.skip(f"{chemical} is a known gap without ATSDR coverage")

        url = ATSDR_LOOKUP.get(chemical)
        if url is None and family:
            url = ATSDR_LOOKUP.get(family)

        assert url is not None, (
            f"REGRESSION 7.BUG.20 (Ball Metal): {chemical} has no ATSDR URL. "
            f"ToxFAQs link will not appear in drawer."
        )
