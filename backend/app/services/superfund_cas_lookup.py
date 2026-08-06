"""Supplementary CAS and ATSDR lookup for Superfund contaminants not in TRI chemicals table.

Refactored per ADR-007 pattern: canonical entries + aliases for name variations.
All name variations are sourced from actual EPA Superfund contaminant listings.

Architecture:
  - ATSDR_URLS (from atsdr_urls.py): ATSDR ToxFAQs URL lookup by substance category
  - _CANONICAL: One entry per unique chemical (CAS, ATSDR, PubChem)
  - _ALIASES: EPA name variations → canonical name mapping
  - SUPERFUND_CAS_LOOKUP: Built programmatically from both (exported)

Format: {CHEMICAL_NAME_UPPER: (CAS_NUMBER, ATSDR_URL or None, PUBCHEM_URL or None)}
  - 2-tuple: (CAS, ATSDR) - PubChem URL auto-generated from CAS by service
  - 3-tuple: (CAS, ATSDR, PUBCHEM) - explicit PubChem URL for mixtures without CAS

CAS numbers verified against PubChem (https://pubchem.ncbi.nlm.nih.gov/).
ATSDR ToxFAQs URLs from CDC/ATSDR Toxic Substances Portal (scraped 2024).
"""

from __future__ import annotations

from app.services.atsdr_urls import ATSDR_URLS as _ATSDR


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL CHEMICAL ENTRIES
# One entry per unique chemical substance (CAS + ATSDR combination)
# Format: "CANONICAL_NAME": (CAS, ATSDR_URL, PUBCHEM_URL or None)
# ═══════════════════════════════════════════════════════════════════════════════
_CANONICAL: dict[str, tuple[str, str | None] | tuple[str, str | None, str]] = {
    # ───────────────────────────────────────────────────────────────────────────
    # PAHs - Polycyclic Aromatic Hydrocarbons (ATSDR toxid=25)
    # ───────────────────────────────────────────────────────────────────────────
    "BENZO[A]PYRENE": ("50-32-8", _ATSDR["PAHS"]),
    "BENZO[B]FLUORANTHENE": ("205-99-2", _ATSDR["PAHS"]),
    "BENZO[K]FLUORANTHENE": ("207-08-9", _ATSDR["PAHS"]),
    "BENZO[A]ANTHRACENE": ("56-55-3", _ATSDR["PAHS"]),
    "DIBENZO[A,H]ANTHRACENE": ("53-70-3", _ATSDR["PAHS"]),
    "INDENO[1,2,3-CD]PYRENE": ("193-39-5", _ATSDR["PAHS"]),
    "CHRYSENE": ("218-01-9", _ATSDR["PAHS"]),
    "FLUORANTHENE": ("206-44-0", _ATSDR["PAHS"]),
    "FLUORENE": ("86-73-7", _ATSDR["PAHS"]),
    "PYRENE": ("129-00-0", _ATSDR["PAHS"]),
    "ANTHRACENE": ("120-12-7", _ATSDR["PAHS"]),
    "PHENANTHRENE": ("85-01-8", _ATSDR["PAHS"]),
    "ACENAPHTHENE": ("83-32-9", _ATSDR["PAHS"]),
    "ACENAPHTHYLENE": ("208-96-8", _ATSDR["PAHS"]),
    "NAPHTHALENE": ("91-20-3", _ATSDR["NAPHTHALENE"]),
    "1-METHYLNAPHTHALENE": ("90-12-0", _ATSDR["NAPHTHALENE"]),
    "2-METHYLNAPHTHALENE": ("91-57-6", _ATSDR["NAPHTHALENE"]),
    "BENZO[G,H,I]PERYLENE": ("191-24-2", _ATSDR["PAHS"]),
    "BENZO[E]PYRENE": ("192-97-2", _ATSDR["PAHS"]),
    "DIBENZ[A,H]ACRIDINE": ("226-36-8", _ATSDR["PAHS"]),
    "DIBENZ[A,J]ANTHRACENE": ("224-41-9", _ATSDR["PAHS"]),
    "BENZO[A]ACEANTHRYLENE": ("203-33-8", _ATSDR["PAHS"]),
    "ANTHANTHRENE": ("191-26-4", _ATSDR["PAHS"]),
    "DIBENZO[A,H]PYRENE": ("189-64-0", _ATSDR["PAHS"]),
    "DIBENZO[A,E]PYRENE": ("192-65-4", _ATSDR["PAHS"]),
    # PAH categories/mixtures (no discrete CAS)
    "POLYCYCLIC AROMATIC HYDROCARBONS": ("130498-29-2", _ATSDR["PAHS"]),
    "PAH": ("N/A", _ATSDR["PAHS"]),
    "CARCINOGENIC PAHS": ("N/A", _ATSDR["PAHS"], "https://pubchem.ncbi.nlm.nih.gov/#query=carcinogenic+polycyclic+aromatic+hydrocarbons"),
    "HIGH MW PAHS": ("N/A", _ATSDR["PAHS"], "https://pubchem.ncbi.nlm.nih.gov/#query=polycyclic+aromatic+hydrocarbons+high+molecular+weight"),
    "LOW MW PAHS": ("N/A", _ATSDR["PAHS"], "https://pubchem.ncbi.nlm.nih.gov/#query=polycyclic+aromatic+hydrocarbons+low+molecular+weight"),
    "BENZO[A]PYRENE EQUIVALENTS": ("N/A", _ATSDR["PAHS"], "https://pubchem.ncbi.nlm.nih.gov/#query=benzo+pyrene+equivalents"),
    "TOTAL BENZOFLUORANTHENES": ("N/A", _ATSDR["PAHS"], "https://pubchem.ncbi.nlm.nih.gov/#query=benzofluoranthene"),

    # ───────────────────────────────────────────────────────────────────────────
    # PCBs - Polychlorinated Biphenyls (ATSDR toxid=26)
    # ───────────────────────────────────────────────────────────────────────────
    "AROCLOR 1016": ("12674-11-2", _ATSDR["PCBS"]),
    "AROCLOR 1221": ("11104-28-2", _ATSDR["PCBS"]),
    "AROCLOR 1232": ("11141-16-5", _ATSDR["PCBS"]),
    "AROCLOR 1242": ("53469-21-9", _ATSDR["PCBS"]),
    "AROCLOR 1248": ("12672-29-6", _ATSDR["PCBS"]),
    "AROCLOR 1254": ("11097-69-1", _ATSDR["PCBS"]),
    "AROCLOR 1260": ("11096-82-5", _ATSDR["PCBS"]),
    "AROCLOR 1262": ("37324-23-5", _ATSDR["PCBS"]),
    "AROCLOR 1268": ("11100-14-4", _ATSDR["PCBS"]),
    "POLYCHLORINATED BIPHENYLS": ("1336-36-3", _ATSDR["PCBS"]),
    "POLYCHLORINATED TERPHENYLS": ("61788-33-8", _ATSDR["PCBS"]),

    # ───────────────────────────────────────────────────────────────────────────
    # Chlorinated Solvents / VOCs
    # ───────────────────────────────────────────────────────────────────────────
    "1,1-DICHLOROETHENE": ("75-35-4", _ATSDR["1,1-DICHLOROETHENE"]),
    "CIS-1,2-DICHLOROETHENE": ("156-59-2", _ATSDR["1,2-DICHLOROETHENE"]),
    "TRANS-1,2-DICHLOROETHENE": ("156-60-5", _ATSDR["1,2-DICHLOROETHENE"]),
    "1,2-DICHLOROETHENE (TOTAL)": ("540-59-0", _ATSDR["1,2-DICHLOROETHENE"]),
    "TETRACHLOROETHYLENE": ("127-18-4", _ATSDR["TETRACHLOROETHYLENE"]),
    "TRICHLOROETHYLENE": ("79-01-6", _ATSDR["TRICHLOROETHYLENE"]),
    "METHYLENE CHLORIDE": ("75-09-2", _ATSDR["METHYLENE CHLORIDE"]),
    "VINYL CHLORIDE": ("75-01-4", _ATSDR["VINYL CHLORIDE"]),
    "1,1,1-TRICHLOROETHANE": ("71-55-6", _ATSDR["1,1,1-TRICHLOROETHANE"]),
    "1,1,2-TRICHLOROETHANE": ("79-00-5", _ATSDR["1,1,2-TRICHLOROETHANE"]),
    "1,1,2,2-TETRACHLOROETHANE": ("79-34-5", _ATSDR["1,1,2,2-TETRACHLOROETHANE"]),
    "1,1-DICHLOROETHANE": ("75-34-3", _ATSDR["1,1-DICHLOROETHANE"]),
    "1,2-DIBROMOETHANE": ("106-93-4", _ATSDR["1,2-DIBROMOETHANE"]),
    "1,2-DICHLOROPROPANE": ("78-87-5", _ATSDR["1,2-DICHLOROPROPANE"]),
    "1,2-DICHLOROBENZENE": ("95-50-1", _ATSDR["DICHLOROBENZENES"]),
    "1,3-DICHLOROBENZENE": ("541-73-1", _ATSDR["DICHLOROBENZENES"]),
    "1,4-DICHLOROBENZENE": ("106-46-7", _ATSDR["DICHLOROBENZENES"]),
    "1,2,4-TRICHLOROBENZENE": ("120-82-1", _ATSDR["TRICHLOROBENZENES"]),
    "1,2,3-TRICHLOROBENZENE": ("87-61-6", _ATSDR["TRICHLOROBENZENES"]),
    "HEXACHLOROBENZENE": ("118-74-1", _ATSDR["HEXACHLOROBENZENE"]),
    "1,4-DIOXANE": ("123-91-1", _ATSDR["1,4-DIOXANE"]),
    "1,3-BUTADIENE": ("106-99-0", _ATSDR["1,3-BUTADIENE"]),
    "CHLOROBENZENE": ("108-90-7", _ATSDR["CHLOROBENZENE"]),
    "CHLOROFORM": ("67-66-3", _ATSDR["CHLOROFORM"]),
    "CARBON TETRACHLORIDE": ("56-23-5", _ATSDR["CARBON TETRACHLORIDE"]),
    "1,2-DICHLOROETHANE": ("107-06-2", _ATSDR["1,2-DICHLOROETHANE"]),
    "HEXACHLOROETHANE": ("67-72-1", _ATSDR["HEXACHLOROETHANE"]),
    "HEXACHLOROBUTADIENE": ("87-68-3", _ATSDR["HEXACHLOROBUTADIENE"]),
    "CHLOROMETHANE": ("74-87-3", _ATSDR["CHLOROMETHANE"]),
    "BROMOMETHANE": ("74-83-9", _ATSDR["BROMOMETHANE"]),
    "1,3-DICHLOROPROPENE": ("542-75-6", _ATSDR["DICHLOROPROPENES"]),
    "CIS-1,3-DICHLOROPROPENE": ("10061-01-5", _ATSDR["DICHLOROPROPENES"]),
    "TRANS-1,3-DICHLOROPROPENE": ("10061-02-6", _ATSDR["DICHLOROPROPENES"]),
    "1,2,3-TRICHLOROPROPANE": ("96-18-4", None),
    "TRICHLOROETHANE (MIXED)": ("N/A", _ATSDR["1,1,1-TRICHLOROETHANE"], "https://pubchem.ncbi.nlm.nih.gov/compound/1,1,1-Trichloroethane"),

    # ───────────────────────────────────────────────────────────────────────────
    # Trihalomethanes (THMs)
    # ───────────────────────────────────────────────────────────────────────────
    "BROMODICHLOROMETHANE": ("75-27-4", None),
    "DIBROMOCHLOROMETHANE": ("124-48-1", None),
    "BROMOCHLOROMETHANE": ("74-97-5", None),
    "BROMOFORM": ("75-25-2", None),
    "DIBROMOMETHANE": ("74-95-3", None),
    "1,1,2,2-TETRABROMOETHANE": ("79-27-6", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Ethers
    # ───────────────────────────────────────────────────────────────────────────
    "BIS(2-CHLOROETHYL)ETHER": ("111-44-4", None),
    "BIS(2-CHLOROISOPROPYL) ETHER": ("108-60-1", None),
    "2-CHLOROETHYL VINYL ETHER": ("110-75-8", None),
    "DIETHYL ETHER": ("60-29-7", None),
    "DIISOPROPYL ETHER": ("108-20-3", None),
    "BIS(2-CHLOROETHOXY) METHANE": ("111-91-1", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Phthalates
    # ───────────────────────────────────────────────────────────────────────────
    "DEHP": ("117-81-7", _ATSDR["DEHP"]),
    "DIETHYL PHTHALATE": ("84-66-2", _ATSDR["DIETHYL PHTHALATE"]),
    "DIBUTYL PHTHALATE": ("84-74-2", _ATSDR["DI-N-BUTYL PHTHALATE"]),
    "DI-N-OCTYL PHTHALATE": ("117-84-0", _ATSDR["DI-N-OCTYLPHTHALATE"]),
    "BUTYL BENZYL PHTHALATE": ("85-68-7", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Metals
    # ───────────────────────────────────────────────────────────────────────────
    "ALUMINUM": ("7429-90-5", _ATSDR["ALUMINUM"]),
    "ANTIMONY": ("7440-36-0", _ATSDR["ANTIMONY"]),
    "ARSENIC": ("7440-38-2", _ATSDR["ARSENIC"]),
    "BARIUM": ("7440-39-3", _ATSDR["BARIUM"]),
    "BARIUM CHLORIDE": ("10361-37-2", _ATSDR["BARIUM"]),
    "BERYLLIUM": ("7440-41-7", _ATSDR["BERYLLIUM"]),
    "BORON": ("7440-42-8", _ATSDR["BORON"]),
    "CADMIUM": ("7440-43-9", _ATSDR["CADMIUM"]),
    "CHROMIUM": ("7440-47-3", _ATSDR["CHROMIUM"]),
    "CHROMIUM(VI)": ("18540-29-9", _ATSDR["CHROMIUM"]),
    "CHROMIUM(III) CHLORIDE": ("10025-73-7", _ATSDR["CHROMIUM"]),
    "CHROMIUM(III) SULFATE": ("10101-53-8", _ATSDR["CHROMIUM"]),
    "COBALT": ("7440-48-4", _ATSDR["COBALT"]),
    "COPPER": ("7440-50-8", _ATSDR["COPPER"]),
    "LEAD": ("7439-92-1", _ATSDR["LEAD"]),
    "TETRAETHYL LEAD": ("78-00-2", _ATSDR["LEAD"]),
    "LEAD(II) ACETATE": ("301-04-2", _ATSDR["LEAD"]),
    "MANGANESE": ("7439-96-5", _ATSDR["MANGANESE"]),
    "MERCURY": ("7439-97-6", _ATSDR["MERCURY"]),
    "METHYLMERCURY": ("22967-92-6", _ATSDR["MERCURY"]),
    "MERCURY(II) CHLORIDE": ("7487-94-7", _ATSDR["MERCURY"]),
    "METHYLMERCURY DICYANDIAMIDE": ("502-39-6", _ATSDR["MERCURY"]),
    "DIMETHYLMERCURY": ("593-74-8", _ATSDR["MERCURY"]),
    "NICKEL": ("7440-02-0", _ATSDR["NICKEL"]),
    "SELENIUM": ("7782-49-2", _ATSDR["SELENIUM"]),
    "SILVER": ("7440-22-4", _ATSDR["SILVER"]),
    "THALLIUM": ("7440-28-0", _ATSDR["THALLIUM"]),
    "TIN": ("7440-31-5", _ATSDR["TIN"]),
    "VANADIUM": ("7440-62-2", _ATSDR["VANADIUM"]),
    "VANADIUM PENTOXIDE": ("1314-62-1", _ATSDR["VANADIUM"]),
    "ZINC": ("7440-66-6", _ATSDR["ZINC"]),
    "BORON OXIDE": ("1303-86-2", _ATSDR["BORON"]),
    # Metals without ATSDR ToxFAQs
    "CALCIUM": ("7440-70-2", None),
    "IRON": ("7439-89-6", None),
    "LITHIUM": ("7439-93-2", None),
    "MAGNESIUM": ("7439-95-4", None),
    "MOLYBDENUM": ("7439-98-7", None),
    "POTASSIUM": ("7440-09-7", None),
    "SODIUM": ("7440-23-5", None),
    "TITANIUM": ("7440-32-6", None),
    "ZIRCONIUM": ("7440-67-7", None),
    "SILICON": ("7440-21-3", None),
    # Metal compound categories (no specific CAS)
    "BERYLLIUM COMPOUNDS": ("N/A", _ATSDR["BERYLLIUM"]),
    "COPPER COMPOUNDS": ("N/A", _ATSDR["COPPER"]),
    "LEAD COMPOUNDS": ("N/A", _ATSDR["LEAD"]),
    "MERCURY COMPOUNDS": ("N/A", _ATSDR["MERCURY"]),
    "NICKEL COMPOUNDS": ("N/A", _ATSDR["NICKEL"]),
    "ZINC COMPOUNDS": ("N/A", _ATSDR["ZINC"]),
    "THALLIUM COMPOUNDS": ("N/A", _ATSDR["THALLIUM"], "https://pubchem.ncbi.nlm.nih.gov/#query=thallium+compounds"),
    "CHROMIUM COMPOUNDS": ("N/A", _ATSDR["CHROMIUM"], "https://pubchem.ncbi.nlm.nih.gov/#query=chromium+compounds"),
    "CHROMIUM (HEXAVALENT COMPOUNDS)": ("N/A", _ATSDR["CHROMIUM"], "https://pubchem.ncbi.nlm.nih.gov/#query=hexavalent+chromium"),
    "MANGANESE COMPOUNDS": ("N/A", _ATSDR["MANGANESE"], "https://pubchem.ncbi.nlm.nih.gov/#query=manganese+compounds"),
    "BARIUM COMPOUNDS": ("N/A", _ATSDR["BARIUM"], "https://pubchem.ncbi.nlm.nih.gov/#query=barium+compounds"),
    "PHOSPHORUS COMPOUNDS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=phosphorus+compounds"),

    # ───────────────────────────────────────────────────────────────────────────
    # Dioxins and Furans
    # ───────────────────────────────────────────────────────────────────────────
    "2,3,7,8-TCDD": ("1746-01-6", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "TCDD TEQ": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "2,3,7,8-TCDF": ("51207-31-9", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/39227"),
    "DIOXINS AND FURANS": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=dioxins+dibenzofurans"),
    "CHLORINATED DIOXINS AND FURANS": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=chlorinated+dioxins"),
    "CHLORINATED DIOXINS": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=chlorinated+dibenzodioxins"),
    # Octachloro
    "OCDF": ("39001-02-0", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/33318"),
    "OCDD": ("3268-87-9", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15771"),
    # Heptachloro
    "1,2,3,4,6,7,8-HPCDD": ("35822-46-9", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/37036"),
    "HPCDD (MIXED)": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=heptachlorodibenzodioxin"),
    "1,2,3,4,7,8,9-HPCDF": ("55673-89-7", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/38981"),
    "1,2,3,4,6,7,8-HPCDF": ("67562-39-4", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/38982"),
    "HPCDF (MIXED)": ("N/A", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/#query=heptachlorodibenzofuran"),
    # Hexachloro
    "1,2,3,4,7,8-HXCDF": ("70648-26-9", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/62853"),
    "1,2,3,4,7,8-HXCDD": ("39227-28-6", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/36831"),
    "1,2,3,6,7,8-HXCDF": ("57117-44-9", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/62855"),
    "1,2,3,6,7,8-HXCDD": ("57653-85-7", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/39925"),
    "1,2,3,7,8,9-HXCDD": ("19408-74-3", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/36830"),
    "1,2,3,7,8,9-HXCDF": ("72918-21-9", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/62857"),
    "2,3,4,6,7,8-HXCDF": ("60851-34-5", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/62856"),
    "HXCDD (MIXED)": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=hexachlorodibenzodioxin"),
    "HXCDF (MIXED)": ("N/A", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/#query=hexachlorodibenzofuran"),
    # Pentachloro
    "1,2,3,7,8-PECDF": ("57117-41-6", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/62858"),
    "1,2,3,7,8-PECDD": ("40321-76-4", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/38990"),
    "2,3,4,7,8-PECDF": ("57117-31-4", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/62859"),
    "PECDD (MIXED)": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=pentachlorodibenzodioxin"),
    "PECDF (MIXED)": ("N/A", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/#query=pentachlorodibenzofuran"),

    # ───────────────────────────────────────────────────────────────────────────
    # Pesticides
    # ───────────────────────────────────────────────────────────────────────────
    "DDT": ("50-29-3", _ATSDR["DDT"]),
    "DDE": ("72-55-9", _ATSDR["DDE"]),
    "DDD": ("72-54-8", _ATSDR["DDD"]),
    "ALDRIN": ("309-00-2", _ATSDR["ALDRIN"]),
    "DIELDRIN": ("60-57-1", _ATSDR["DIELDRIN"]),
    "ENDRIN": ("72-20-8", _ATSDR["ENDRIN"]),
    "ENDRIN ALDEHYDE": ("7421-93-4", _ATSDR["ENDRIN"]),
    "ENDRIN KETONE": ("53494-70-5", _ATSDR["ENDRIN"]),
    "HEPTACHLOR": ("76-44-8", _ATSDR["HEPTACHLOR"]),
    "HEPTACHLOR EPOXIDE": ("1024-57-3", _ATSDR["HEPTACHLOR"]),
    "CHLORDANE": ("57-74-9", _ATSDR["CHLORDANE"]),
    "ALPHA-CHLORDANE": ("5103-71-9", _ATSDR["CHLORDANE"]),
    "GAMMA-CHLORDANE": ("5103-74-2", _ATSDR["CHLORDANE"]),
    "TOXAPHENE": ("8001-35-2", _ATSDR["TOXAPHENE"]),
    "LINDANE": ("58-89-9", _ATSDR["LINDANE"]),
    "ALPHA-HCH": ("319-84-6", _ATSDR["HCH"]),
    "BETA-HCH": ("319-85-7", _ATSDR["HCH"]),
    "DELTA-HCH": ("319-86-8", _ATSDR["HCH"]),
    "METHOXYCHLOR": ("72-43-5", _ATSDR["METHOXYCHLOR"]),
    "MIREX": ("2385-85-5", _ATSDR["MIREX"]),
    "CHLORDECONE": ("143-50-0", _ATSDR["CHLORDECONE"]),
    "ENDOSULFAN": ("115-29-7", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN I": ("959-98-8", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN II": ("33213-65-9", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN SULFATE": ("1031-07-8", _ATSDR["ENDOSULFAN"]),
    "ATRAZINE": ("1912-24-9", _ATSDR["ATRAZINE"]),
    "DIAZINON": ("333-41-5", _ATSDR["DIAZINON"]),
    "DISULFOTON": ("298-04-4", None),
    "MALATHION": ("121-75-5", _ATSDR["MALATHION"]),
    "PARATHION": ("56-38-2", _ATSDR["PARATHION"]),
    "CHLORPYRIFOS": ("2921-88-2", _ATSDR["CHLORPYRIFOS"]),
    "PENTACHLOROPHENOL": ("87-86-5", _ATSDR["PENTACHLOROPHENOL"]),
    "2,4-D": ("94-75-7", _ATSDR["2,4-D"]),
    "MCPA": ("94-74-6", _ATSDR["2,4-D"]),
    "2,4-DB": ("94-82-6", None),
    "2,4,5-T": ("93-76-5", _ATSDR["2,4-D"]),
    "SILVEX": ("93-72-1", None),
    "DICAMBA": ("1918-00-9", None),
    "DIURON": ("330-54-1", None),
    "MONURON": ("150-68-5", None),
    "DINOSEB": ("88-85-7", None),
    # Organophosphates without ATSDR
    "FENSULFOTHION": ("115-90-2", None),
    "AZINPHOS-METHYL": ("86-50-0", None),
    "ETHION": ("563-12-2", None),
    "RONNEL": ("299-84-3", None),
    "OXAMYL": ("23135-22-0", None),
    "PHORATE": ("298-02-2", None),
    "MEVINPHOS": ("7786-34-7", None),
    "EPN": ("2104-64-5", None),
    # Mycotoxins
    "ZEARALENONE": ("17924-92-4", None),

    # ───────────────────────────────────────────────────────────────────────────
    # N-Nitrosamines
    # ───────────────────────────────────────────────────────────────────────────
    "N-NITROSODIBUTYLAMINE": ("924-16-3", None),
    "N-NITROSODIPHENYLAMINE": ("86-30-6", None),
    "N-NITROSODIPROPYLAMINE": ("621-64-7", None),
    "N-NITROSOPYRROLIDINE": ("930-55-2", None),
    "NDMA": ("62-75-9", _ATSDR["NDMA"]),
    "N-NITROSODIETHYLAMINE": ("55-18-5", _ATSDR["NDMA"]),

    # ───────────────────────────────────────────────────────────────────────────
    # BTEX compounds
    # ───────────────────────────────────────────────────────────────────────────
    "BENZENE": ("71-43-2", _ATSDR["BENZENE"]),
    "ETHYLBENZENE": ("100-41-4", _ATSDR["ETHYLBENZENE"]),
    "TOLUENE": ("108-88-3", _ATSDR["TOLUENE"]),
    "XYLENES (MIXED)": ("1330-20-7", _ATSDR["XYLENES"]),
    "O-XYLENE": ("95-47-6", _ATSDR["XYLENES"]),
    "M-XYLENE": ("108-38-3", _ATSDR["XYLENES"]),
    "P-XYLENE": ("106-42-3", _ATSDR["XYLENES"]),
    "STYRENE": ("100-42-5", _ATSDR["STYRENE"]),
    "1,2,4-TRIMETHYLBENZENE": ("95-63-6", None),
    "1,3,5-TRIMETHYLBENZENE": ("108-67-8", None),
    "TRIMETHYLBENZENE (MIXED)": ("25551-13-7", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Inorganic compounds
    # ───────────────────────────────────────────────────────────────────────────
    "NITRATE": ("14797-55-8", _ATSDR["NITRATE"]),
    "NITRATE/NITRITE": ("N/A", _ATSDR["NITRATE"], "https://pubchem.ncbi.nlm.nih.gov/#query=nitrate+nitrite"),
    "CYANIDE": ("57-12-5", _ATSDR["CYANIDE"]),
    "HYDROGEN CYANIDE": ("74-90-8", _ATSDR["CYANIDE"]),
    "FLUORIDE": ("16984-48-8", _ATSDR["FLUORIDES"]),
    "AMMONIA": ("7664-41-7", _ATSDR["AMMONIA"]),
    "AMMONIUM HYDROXIDE": ("1336-21-6", _ATSDR["AMMONIA"]),
    "AMMONIUM NITRATE": ("6484-52-2", None),
    "ASBESTOS": ("1332-21-4", _ATSDR["ASBESTOS"]),
    "PERCHLORATE": ("14797-73-0", _ATSDR["PERCHLORATE"]),
    "SULFATE": ("14808-79-8", None),
    "SULFIDE": ("18496-25-8", None),
    "CHLORIDE": ("16887-00-6", None),
    "PHOSPHATE": ("14265-44-2", None),
    "SULFUR": ("7704-34-9", None),
    "SULFUR DIOXIDE": ("7446-09-5", None),
    "HYDROGEN": ("1333-74-0", None),
    "PHOSPHORUS": ("7723-14-0", None),
    "IODINE": ("7553-56-2", None),
    "BROMINE": ("7726-95-6", None),
    "HYDROGEN CHLORIDE": ("7647-01-0", None),
    "POTASSIUM PERMANGANATE": ("7722-64-7", None),
    "CALCIUM CARBONATE": ("471-34-1", None),
    "ALUMINUM OXIDE": ("1344-28-1", None),
    # Acids
    "SULFURIC ACID": ("7664-93-9", None),
    "HYDROCHLORIC ACID": ("7647-01-0", None),
    "NITRIC ACID": ("7697-37-2", None),
    "PHOSPHORIC ACID": ("7664-38-2", None),
    "HYDROFLUORIC ACID": ("7664-39-3", _ATSDR["FLUORIDES"]),
    "CHROMIC ACID": ("7738-94-5", _ATSDR["CHROMIUM"]),

    # ───────────────────────────────────────────────────────────────────────────
    # Radionuclides
    # ───────────────────────────────────────────────────────────────────────────
    "RADIUM": ("7440-14-4", _ATSDR["RADIUM"]),
    "RADIUM-226": ("13982-63-3", _ATSDR["RADIUM"]),
    "RADIUM-228": ("15262-20-1", _ATSDR["RADIUM"]),
    "URANIUM": ("7440-61-1", _ATSDR["URANIUM"]),
    "URANIUM-234": ("13966-29-5", _ATSDR["URANIUM"]),
    "URANIUM-235": ("15117-96-1", _ATSDR["URANIUM"]),
    "URANIUM-238": ("7440-61-1", _ATSDR["URANIUM"]),
    "URANIUM-233": ("13968-55-3", _ATSDR["URANIUM"]),
    "URANIUM (COMBINED)": ("N/A", _ATSDR["URANIUM"]),
    "THORIUM": ("7440-29-1", _ATSDR["THORIUM"]),
    "THORIUM-230": ("14269-63-7", _ATSDR["THORIUM"]),
    "THORIUM-232": ("7440-29-1", _ATSDR["THORIUM"]),
    "THORIUM-228": ("14274-82-9", _ATSDR["THORIUM"]),
    "THORIUM-234": ("15065-10-8", _ATSDR["THORIUM"]),
    "RADON": ("10043-92-2", _ATSDR["RADON"]),
    "RADON-222": ("14859-67-7", _ATSDR["RADON"]),
    "CESIUM": ("7440-46-2", _ATSDR["CESIUM"]),
    "CESIUM-137": ("10045-97-3", _ATSDR["CESIUM"]),
    "CESIUM-134": ("13967-70-9", _ATSDR["CESIUM"]),
    "STRONTIUM": ("7440-24-6", _ATSDR["STRONTIUM"]),
    "STRONTIUM-90": ("10098-97-2", _ATSDR["STRONTIUM"]),
    "PLUTONIUM": ("7440-07-5", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-238": ("13981-16-3", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-239": ("15117-48-3", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-240": ("14119-33-6", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-239/240": ("N/A", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-241": ("14119-32-5", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-242": ("13982-10-0", _ATSDR["PLUTONIUM"]),
    "AMERICIUM": ("7440-35-9", _ATSDR["AMERICIUM"]),
    "AMERICIUM-241": ("14596-10-2", _ATSDR["AMERICIUM"]),
    "COBALT-60": ("10198-40-0", _ATSDR["COBALT"]),
    "COBALT-57": ("13981-50-5", _ATSDR["COBALT"]),
    "CARBON-14": ("14762-75-5", None),
    "EUROPIUM": ("7440-53-1", None),
    "EUROPIUM-152": ("14683-23-9", None),
    "EUROPIUM-154": ("15585-10-1", None),
    "EUROPIUM-155": ("14391-16-3", None),
    "NICKEL-63": ("13981-37-8", _ATSDR["NICKEL"]),
    "TECHNETIUM-99": ("14133-76-7", None),
    "TRITIUM": ("10028-17-8", None),
    "IODINE-129": ("15046-84-1", None),
    "IODINE-131": ("10043-66-0", None),
    "NEPTUNIUM": ("7439-99-8", None),
    "NEPTUNIUM-237": ("13994-20-2", None),
    "CURIUM": ("7440-51-9", None),
    "ACTINIUM-228": ("14331-83-0", None),
    "LEAD-210": ("14255-04-0", _ATSDR["LEAD"]),
    "LEAD-212": ("15092-94-1", _ATSDR["LEAD"]),
    "LEAD-214": ("15067-28-4", _ATSDR["LEAD"]),
    "BISMUTH-214": ("14733-03-0", None),
    "MANGANESE-54": ("13966-31-9", _ATSDR["MANGANESE"]),
    "POTASSIUM-40": ("13966-00-2", None),
    "SODIUM-22": ("13966-32-0", None),
    "ALPHA GROSS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=alpha+radiation"),
    "BETA GROSS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=beta+radiation"),
    "RADIONUCLIDES": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=radionuclides"),

    # ───────────────────────────────────────────────────────────────────────────
    # Explosives
    # ───────────────────────────────────────────────────────────────────────────
    "TNT": ("118-96-7", _ATSDR["TNT"]),
    "RDX": ("121-82-4", _ATSDR["RDX"]),
    "HMX": ("2691-41-0", _ATSDR["HMX"]),
    "2,4-DINITROTOLUENE": ("121-14-2", _ATSDR["DINITROTOLUENES"]),
    "2,6-DINITROTOLUENE": ("606-20-2", _ATSDR["DINITROTOLUENES"]),
    "1,3,5-TRINITROBENZENE": ("99-35-4", _ATSDR["TNT"]),
    "1,3-DINITROBENZENE": ("99-65-0", _ATSDR["DINITROTOLUENES"]),
    "NITROTOLUENE (MIXED ISOMERS)": ("1321-12-6", _ATSDR["DINITROTOLUENES"]),
    "2-NITROTOLUENE": ("88-72-2", _ATSDR["DINITROTOLUENES"]),
    "3-NITROTOLUENE": ("99-08-1", _ATSDR["DINITROTOLUENES"]),
    "4-NITROTOLUENE": ("99-99-0", _ATSDR["DINITROTOLUENES"]),
    "TETRYL": ("479-45-8", None),
    "NITROAROMATICS": ("N/A", _ATSDR["NITROBENZENE"], "https://pubchem.ncbi.nlm.nih.gov/#query=nitroaromatics"),
    "2,4,6-TRINITROPHENOL": ("88-89-1", None),
    "4-AMINO-2,6-DINITROTOLUENE": ("35572-78-2", _ATSDR["DINITROTOLUENES"]),
    "2-AMINO-4,6-DINITROTOLUENE": ("35572-78-2", _ATSDR["DINITROTOLUENES"]),
    "2-NITROANILINE": ("88-74-4", None),
    "3-NITROANILINE": ("99-09-2", None),
    "4-NITROANILINE": ("100-01-6", None),

    # ───────────────────────────────────────────────────────────────────────────
    # PFAS
    # ───────────────────────────────────────────────────────────────────────────
    "PFOA": ("335-67-1", _ATSDR["PFAS"]),
    "PFOS": ("1763-23-1", _ATSDR["PFAS"]),
    "PFNA": ("375-95-1", _ATSDR["PFAS"]),
    "PFDA": ("335-76-2", _ATSDR["PFAS"]),
    "PFBS": ("375-73-5", _ATSDR["PFAS"]),
    "PFHXA": ("307-24-4", _ATSDR["PFAS"]),
    "PFHXS": ("355-46-4", _ATSDR["PFAS"]),

    # ───────────────────────────────────────────────────────────────────────────
    # Phenols and Cresols
    # ───────────────────────────────────────────────────────────────────────────
    "PHENOL": ("108-95-2", _ATSDR["PHENOL"]),
    "CRESOLS (MIXED)": ("1319-77-3", _ATSDR["CRESOLS"]),
    "O-CRESOL": ("95-48-7", _ATSDR["CRESOLS"]),
    "M-CRESOL": ("108-39-4", _ATSDR["CRESOLS"]),
    "P-CRESOL": ("106-44-5", _ATSDR["CRESOLS"]),
    "2-CHLOROPHENOL": ("95-57-8", None),
    "4-CHLOROPHENOL": ("106-48-9", None),
    "2,4-DICHLOROPHENOL": ("120-83-2", None),
    "2,4,5-TRICHLOROPHENOL": ("95-95-4", None),
    "2,4,6-TRICHLOROPHENOL": ("88-06-2", None),
    "2,3,5,6-TETRACHLOROPHENOL": ("935-95-5", None),
    "4-CHLORO-3-METHYLPHENOL": ("59-50-7", None),
    "4-METHOXYPHENOL": ("150-76-5", None),
    "4-CHLOROANILINE": ("106-47-8", None),
    "2-METHYLANILINE": ("95-53-4", None),
    "DINITRO-O-CRESOL": ("534-52-1", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Other organic compounds
    # ───────────────────────────────────────────────────────────────────────────
    "CARBON DISULFIDE": ("75-15-0", _ATSDR["CARBON DISULFIDE"]),
    "ACETONE": ("67-64-1", _ATSDR["ACETONE"]),
    "2-BUTANONE": ("78-93-3", _ATSDR["2-BUTANONE"]),
    "2-HEXANONE": ("591-78-6", _ATSDR["2-HEXANONE"]),
    "METHYL ISOBUTYL KETONE": ("108-10-1", None),
    "ISOPHORONE": ("78-59-1", None),
    "CYCLOHEXANONE": ("108-94-1", None),
    "MTBE": ("1634-04-4", _ATSDR["MTBE"]),
    "FORMALDEHYDE": ("50-00-0", _ATSDR["FORMALDEHYDE"]),
    "ACRYLONITRILE": ("107-13-1", _ATSDR["ACRYLONITRILE"]),
    "ACROLEIN": ("107-02-8", _ATSDR["ACROLEIN"]),
    "ETHYLENE OXIDE": ("75-21-8", _ATSDR["ETHYLENE OXIDE"]),
    "HYDRAZINE": ("302-01-2", _ATSDR["HYDRAZINES"]),
    "ETHYLENE GLYCOL": ("107-21-1", _ATSDR["ETHYLENE GLYCOL"]),
    "DIETHYLENE GLYCOL": ("111-46-6", _ATSDR["ETHYLENE GLYCOL"]),
    "BENZIDINE": ("92-87-5", _ATSDR["BENZIDINE"]),
    "3,3'-DIMETHYLBENZIDINE": ("838-88-0", None),
    "PYRIDINE": ("110-86-1", _ATSDR["PYRIDINE"]),
    "NITROBENZENE": ("98-95-3", _ATSDR["NITROBENZENE"]),
    "ACETOPHENONE": ("98-86-2", None),
    "CARBAZOLE": ("86-74-8", None),
    "TETRAHYDROFURAN": ("109-99-9", None),
    "DIMETHYLFORMAMIDE": ("68-12-2", None),
    "DIMETHYL SULFIDE": ("75-18-3", None),
    "BENZOIC ACID": ("65-85-0", None),
    "METHYL ACETATE": ("79-20-9", None),
    "METHYL METHACRYLATE": ("80-62-6", None),
    "METHYL ACRYLATE": ("96-33-3", None),
    "ETHYL ACRYLATE": ("140-88-5", None),
    "PROPYLENE OXIDE": ("75-56-9", None),
    "ISOPRENE": ("78-79-5", None),
    "BENZOYL PEROXIDE": ("94-36-0", None),
    "4-NITROSODIPHENYLAMINE": ("156-10-5", None),
    "TRIETHANOLAMINE": ("102-71-6", None),
    "CHLOROACETOPHENONE": ("532-27-4", None),
    "ETHANOL": ("64-17-5", None),
    "ISOPROPANOL": ("67-63-0", None),
    "N-BUTANOL": ("71-36-3", None),
    "METHANE": ("74-82-8", None),
    "PHENOTHIAZINE": ("92-84-2", None),
    "CHLORENDIC ACID": ("115-28-6", None),
    "2-CHLOROBENZOIC ACID": ("118-91-2", None),
    "2-NAPHTHALENAMINE": ("91-59-8", None),
    "2-CHLOROANILINE": ("95-51-2", None),
    "DIPHENYLAMINE": ("122-39-4", None),
    "2-BUTOXYETHANOL": ("111-76-2", None),
    "CAPROLACTAM": ("105-60-2", None),
    "1,4-DITHIANE": ("505-29-3", None),
    "ETHANETHIOL": ("75-08-1", None),
    "ETHYL CHLOROFORMATE": ("541-41-3", None),
    "BENZALDEHYDE": ("100-52-7", None),
    "TRIPHENYL PHOSPHATE": ("115-86-6", None),
    "BIPHENYL": ("92-52-4", None),
    "1-BROMO-4-PHENOXYBENZENE": ("101-55-3", None),
    "1-CHLORO-4-PHENOXYBENZENE": ("7005-72-3", None),

    # ───────────────────────────────────────────────────────────────────────────
    # TPH and fuels
    # ───────────────────────────────────────────────────────────────────────────
    "TPH": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "DIESEL": ("68476-34-6", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "DRO": ("N/A", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "GASOLINE": ("8006-61-9", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    "GRO": ("N/A", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    "KEROSENE": ("8008-20-6", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "FUEL OIL": ("N/A", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "FUEL OIL NO. 2": ("68476-30-2", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "FUEL OIL NO. 4": ("68476-31-3", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "FUEL OIL NO. 6": ("68553-00-4", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "JET FUEL": ("N/A", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "JP-4": ("50815-00-4", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "JP-5": ("N/A", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/substance/135356845"),
    "JP-8": ("N/A", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/substance/505788256"),
    "MINERAL OIL": ("8042-47-5", None, "https://pubchem.ncbi.nlm.nih.gov/compound/Mineral-oil"),
    "RRO": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "STODDARD SOLVENT": ("8052-41-3", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/compound/Stoddard-solvent"),
    # TPH fractions (all map to TPH ATSDR)
    "C5-C8 ALIPHATICS": ("N/A", _ATSDR["TPH"]),
    "C9-C10 AROMATICS": ("N/A", _ATSDR["TPH"]),
    "C9-C12 ALIPHATICS": ("N/A", _ATSDR["TPH"]),
    "C9-C18 ALIPHATICS": ("N/A", _ATSDR["TPH"]),
    "C11-C22 AROMATICS": ("N/A", _ATSDR["TPH"]),
    "C13-C18 ALIPHATICS": ("N/A", _ATSDR["TPH"]),
    "C19-C36 ALIPHATICS": ("N/A", _ATSDR["TPH"]),
    "HYDROCARBONS": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/#query=hydrocarbons"),

    # ───────────────────────────────────────────────────────────────────────────
    # CFCs / Refrigerants
    # ───────────────────────────────────────────────────────────────────────────
    "CFC-12": ("75-71-8", None),
    "CFC-11": ("75-69-4", None),
    "HCFC-22": ("75-45-6", None),
    "CFC-113": ("76-13-1", None),
    "CFC-112": ("76-12-0", None),
    "CFC-114": ("76-14-2", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Alkylbenzenes
    # ───────────────────────────────────────────────────────────────────────────
    "SEC-BUTYLBENZENE": ("135-98-8", None),
    "N-PROPYLBENZENE": ("103-65-1", None),
    "CUMENE": ("98-82-8", None),
    "P-CYMENE": ("99-87-6", None),
    "N-BUTYLBENZENE": ("104-51-8", None),
    "TERT-BUTYLBENZENE": ("98-06-6", None),
    "TRANS-1-PROPENYLBENZENE": ("873-66-5", None),
    "CIS-1-PROPENYLBENZENE": ("766-90-5", None),
    "BENZYL ALCOHOL": ("100-51-6", None),
    "BENZYL CHLORIDE": ("100-44-7", None),
    "ETHYL METHYL BENZENE (MIXED)": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=ethyl+methyl+benzene"),

    # ───────────────────────────────────────────────────────────────────────────
    # Solvents and alkanes
    # ───────────────────────────────────────────────────────────────────────────
    "N-HEXANE": ("110-54-3", _ATSDR["N-HEXANE"]),
    "N-HEPTANE": ("142-82-5", None),
    "ISOOCTANE": ("540-84-1", None),
    "PROPYLENE": ("115-07-1", None),
    "N-OCTANE": ("111-65-9", None),
    "N-PENTANE": ("109-66-0", None),
    "N-NONANE": ("111-84-2", None),
    "METHYLCYCLOHEXANE": ("108-87-2", None),
    "METHYLCYCLOHEXANOL (MIXED)": ("25639-42-3", None),
    "PROPYLENE GLYCOL": ("57-55-6", None),
    "TRIBUTYLTIN": ("688-73-3", None),
    "2-CHLORONAPHTHALENE": ("91-58-7", _ATSDR["NAPHTHALENE"]),
    "TETRABUTYL SILICATE": ("4766-57-8", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Chemical warfare agents
    # ───────────────────────────────────────────────────────────────────────────
    "MUSTARD GAS": ("505-60-2", None),
    "LEWISITE": ("541-25-3", None),

    # ───────────────────────────────────────────────────────────────────────────
    # Generic categories
    # ───────────────────────────────────────────────────────────────────────────
    "INORGANICS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=inorganics"),
    "METALS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=metals"),
    "VOC": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=volatile+organic+compounds"),
    "SVOC": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=semivolatile+organic+compounds"),
    "ORGANICS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=organics"),
    "PESTICIDES": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=pesticides"),
    "HERBICIDES": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=herbicides"),
    "BASE NEUTRAL ACIDS": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=base+neutral+acids"),
    "UXO": ("N/A", None),
    "NOT PROVIDED": ("N/A", None),
    "LEACHATE": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=leachate"),
    "PETROLEUM": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/#query=petroleum"),
    "BUTYLTIN TEQ": ("N/A", None, "https://pubchem.ncbi.nlm.nih.gov/#query=butyltin"),
    "DICHLOROPROPANE (MIXED)": ("N/A", _ATSDR["1,2-DICHLOROPROPANE"], "https://pubchem.ncbi.nlm.nih.gov/#query=dichloropropane"),
    "CHLOROCRESOL (MIXED)": ("N/A", _ATSDR["CRESOLS"], "https://pubchem.ncbi.nlm.nih.gov/#query=chlorocresol"),
    "PHENAZOPYRIDINE": ("94-78-0", None),
    "4-(4-AMINO-3-CHLOROPHENYL)-2-CHLOROANILINE": ("42389-30-0", None),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ALIASES - EPA Superfund name variations → canonical names
# Each key is an exact match from EPA data; each value is the canonical key
# ═══════════════════════════════════════════════════════════════════════════════
_ALIASES: dict[str, str] = {
    # PAH variations (parentheses vs brackets, abbreviations)
    "BENZO(A)PYRENE": "BENZO[A]PYRENE",
    "BENZO(B)FLUORANTHENE": "BENZO[B]FLUORANTHENE",
    "BENZO(K)FLUORANTHENE": "BENZO[K]FLUORANTHENE",
    "BENZO(A)ANTHRACENE": "BENZO[A]ANTHRACENE",
    "DIBENZO(A,H)ANTHRACENE": "DIBENZO[A,H]ANTHRACENE",
    "DIBENZ(A,H)ANTHRACENE": "DIBENZO[A,H]ANTHRACENE",
    "INDENO(1,2,3-CD)PYRENE": "INDENO[1,2,3-CD]PYRENE",
    "9H-FLUORENE": "FLUORENE",
    "1,2-DIHYDROACENAPHTHYLENE": "ACENAPHTHENE",
    "BENZO(GHI)PERYLENE": "BENZO[G,H,I]PERYLENE",
    "BENZO(E)PYRENE": "BENZO[E]PYRENE",
    "POLYCYCLIC AROMATIC HYDROCARBONS (PAHS)": "POLYCYCLIC AROMATIC HYDROCARBONS",
    "PAHS": "POLYCYCLIC AROMATIC HYDROCARBONS",
    # PAH is canonical now - do not alias
    "CARCINOGENIC POLYCYCLIC AROMATIC HYDROCARBONS (CPAH)": "CARCINOGENIC PAHS",
    "POLYCYCLIC AROMATIC HYDROCARBONS, HIGH MOLECULAR WEIGHT (HPAHS)": "HIGH MW PAHS",
    "POLYCYCLIC AROMATIC HYDROCARBONS, LOW MOLECULAR WEIGHT (LPAHS)": "LOW MW PAHS",
    "BENZO[A]PYRENE EQUIVALENTS (BAPEQ)": "BENZO[A]PYRENE EQUIVALENTS",
    "BAPEQ": "BENZO[A]PYRENE EQUIVALENTS",

    # PCB variations
    "POLYCHLORINATED BIPHENYLS (PCBS)": "POLYCHLORINATED BIPHENYLS",
    "PCBS": "POLYCHLORINATED BIPHENYLS",
    "PCTS": "POLYCHLORINATED TERPHENYLS",

    # Chlorinated solvent variations
    "1,1-DICHLOROETHYLENE": "1,1-DICHLOROETHENE",
    "CIS-1,2-DICHLOROETHYLENE": "CIS-1,2-DICHLOROETHENE",
    "TRANS-1,2-DICHLOROETHYLENE": "TRANS-1,2-DICHLOROETHENE",
    "1,2-DICHLOROETHENE (CIS AND TRANS MIXTURE)": "1,2-DICHLOROETHENE (TOTAL)",
    "TETRACHLOROETHENE": "TETRACHLOROETHYLENE",
    "PERCHLOROETHYLENE": "TETRACHLOROETHYLENE",
    "PCE": "TETRACHLOROETHYLENE",
    "TRICHLOROETHENE": "TRICHLOROETHYLENE",
    "TCE": "TRICHLOROETHYLENE",
    "DICHLOROMETHANE": "METHYLENE CHLORIDE",
    "DICHLOROMETHANE (METHYLENE CHLORIDE)": "METHYLENE CHLORIDE",
    "CHLOROETHENE (VINYL CHLORIDE)": "VINYL CHLORIDE",
    "ETHYLENE DIBROMIDE": "1,2-DIBROMOETHANE",
    "METHYL BROMIDE": "BROMOMETHANE",
    "1,3-DICHLOROPROPENE (EZ MIXTURE)": "1,3-DICHLOROPROPENE",
    "(Z)-1,3-DICHLORO-1-PROPENE": "CIS-1,3-DICHLOROPROPENE",
    "(E)-1,3-DICHLORO-1-PROPENE": "TRANS-1,3-DICHLOROPROPENE",
    "TRICHLOROETHANE (MIXED ISOMERS)": "TRICHLOROETHANE (MIXED)",
    "TRIBROMOMETHANE": "BROMOFORM",

    # Ether variations
    "1-CHLORO-2-ETHENOXYETHANE": "2-CHLOROETHYL VINYL ETHER",
    "2-PROPAN-2-YLOXYPROPANE": "DIISOPROPYL ETHER",

    # Phthalate variations
    "BIS(2-ETHYLHEXYL)PHTHALATE": "DEHP",
    "DI(2-ETHYLHEXYL)PHTHALATE": "DEHP",

    # Metal variations
    "HEXAVALENT CHROMIUM": "CHROMIUM(VI)",
    "CHROMIUM (VI)": "CHROMIUM(VI)",
    "CHROMIUM (III)": "CHROMIUM",
    "METHYL MERCURY": "METHYLMERCURY",
    "TETRAETHYLLEAD": "TETRAETHYL LEAD",
    "MERCURIC CHLORIDE": "MERCURY(II) CHLORIDE",
    "VANADIUM, METAL AND/OR ALLOY": "VANADIUM",

    # Dioxin/furan variations
    "2,3,7,8-TETRACHLORODIBENZO-P-DIOXIN": "2,3,7,8-TCDD",
    "2,3,7,8-TETRACHLORODIBENZO-P-DIOXIN (TCDD)": "2,3,7,8-TCDD",
    "TCDD": "2,3,7,8-TCDD",
    "2,3,7,8-TETRACHLORODIBENZO-p-DIOXIN (TCDD) TOXICITY EQUIVALENTS (TEq)": "TCDD TEQ",
    "2,3,7,8-TETRACHLORODIBENZO-P-DIOXIN (TCDD) TOXICITY EQUIVALENTS (TEQ)": "TCDD TEQ",
    "2,3,7,8-TETRACHLORODIBENZOFURAN": "2,3,7,8-TCDF",
    "TETRACHLORODIBENZOFURAN (TCDF)": "2,3,7,8-TCDF",
    "TCDF": "2,3,7,8-TCDF",
    # CHLORINATED DIOXINS AND FURANS is canonical - removed alias
    "DIOXINS (CHLORINATED DIBENZODIOXINS)": "CHLORINATED DIOXINS",
    "DIOXINS AND DIBENZOFURANS": "DIOXINS AND FURANS",
    "1,2,3,4,6,7,8,9-OCTACHLORODIBENZOFURAN": "OCDF",
    "OCTACHLORODIBENZOFURAN": "OCDF",
    "1,2,3,4,6,7,8,9-OCTACHLORODIBENZO[B,E][1,4]DIOXIN (OCDD)": "OCDD",
    "OCTACHLORODIBENZODIOXIN": "OCDD",
    "1,2,3,4,6,7,8-HEPTACHLORODIBENZO[B,E][1,4]DIOXIN (HPCDD)": "1,2,3,4,6,7,8-HPCDD",
    "HPCDD": "1,2,3,4,6,7,8-HPCDD",
    "HEPTACHLORODIBENZO[B,E][1,4]DIOXIN (HPCDD) (MIXED ISOMERS)": "HPCDD (MIXED)",
    "1,2,3,4,7,8,9-HEPTACHLORODIBENZOFURAN": "1,2,3,4,7,8,9-HPCDF",
    "1,2,3,4,6,7,8-HEPTACHLORODIBENZOFURAN": "1,2,3,4,6,7,8-HPCDF",
    "HEPTACHLORODIBENZOFURAN": "HPCDF (MIXED)",
    "1,2,3,4,7,8-HEXACHLORODIBENZOFURAN (HXCDF)": "1,2,3,4,7,8-HXCDF",
    "1,2,3,4,7,8-HEXACHLORODIBENZO[B,E][1,4]DIOXIN (HXCDD)": "1,2,3,4,7,8-HXCDD",
    "1,2,3,6,7,8-HEXACHLORODIBENZOFURAN (HXCDF)": "1,2,3,6,7,8-HXCDF",
    "1,2,3,6,7,8-HEXACHLORODIBENZO[B,E][1,4]DIOXIN (HXCDD)": "1,2,3,6,7,8-HXCDD",
    "1,2,3,7,8,9-HEXACHLORODIBENZO-P-DIOXIN (HXCDD)": "1,2,3,7,8,9-HXCDD",
    "1,2,3,7,8,9-HEXACHLORODIBENZOFURAN (HXCDF)": "1,2,3,7,8,9-HXCDF",
    "2,3,4,6,7,8-HEXACHLORODIBENZOFURAN": "2,3,4,6,7,8-HXCDF",
    "HEXACHLORODIBENZO[B,E][1,4]DIOXIN (HXCDD) (MIXED ISOMERS)": "HXCDD (MIXED)",
    "HXCDD": "HXCDD (MIXED)",
    "HXCDF": "HXCDF (MIXED)",
    "1,2,3,7,8-PENTACHLORODIBENZOFURAN": "1,2,3,7,8-PECDF",
    "1,2,3,7,8-PENTACHLORODIBENZO[B,E][1,4]DIOXIN (PECDD)": "1,2,3,7,8-PECDD",
    "2,3,4,7,8-PENTACHLORODIBENZOFURAN (PECDF)": "2,3,4,7,8-PECDF",
    "PECDD": "1,2,3,7,8-PECDD",
    "PECDF": "2,3,4,7,8-PECDF",
    "PENTACHLORODIBENZOFURAN (PECDF)": "PECDF (MIXED)",
    "PENTACHLORODIBENZO[B,E][1,4]DIOXIN (PECDD) (MIXED ISOMERS)": "PECDD (MIXED)",

    # Pesticide variations
    "4,4'-DDT": "DDT",
    "P,P'-DDT": "DDT",
    "4,4'-DDE": "DDE",
    "P,P'-DDE": "DDE",
    "4,4'-DDD": "DDD",
    "P,P'-DDD": "DDD",
    "GAMMA-HEXACHLOROCYCLOHEXANE": "LINDANE",
    "GAMMA-HEXACHLOROCYCLOHEXANE (LINDANE)": "LINDANE",
    "ALPHA-HEXACHLOROCYCLOHEXANE": "ALPHA-HCH",
    "BETA-HEXACHLOROCYCLOHEXANE": "BETA-HCH",
    "DELTA-HEXACHLOROCYCLOHEXANE": "DELTA-HCH",
    "ENDOSULFAN (I OR II)": "ENDOSULFAN",
    "PCP": "PENTACHLOROPHENOL",
    "2,4-DICHLOROPHENOXYACETIC ACID": "2,4-D",
    "(4-CHLORO-2-METHYLPHENOXY)ACETIC ACID": "MCPA",
    "4-(2,4-DICHLOROPHENOXY)BUTANOIC ACID": "2,4-DB",
    "2,4,5-TRICHLOROPHENOXYACETIC ACID": "2,4,5-T",
    "2-(2,4,5-TRICHLOROPHENOXY)PROPANOIC ACID": "SILVEX",
    "2,4,5-TP": "SILVEX",
    "3,6-DICHLORO-2-METHOXYBENZOIC ACID": "DICAMBA",
    "3-(3,4-DICHLOROPHENYL)-1,1-DIMETHYLUREA (DIURON)": "DIURON",
    "3-(4-CHLOROPHENYL)-1,1-DIMETHYLUREA": "MONURON",
    "2-(1-METHYLPROPYL)-4,6-DINITROPHENOL (DINOSEB)": "DINOSEB",
    "GUTHION": "AZINPHOS-METHYL",
    "FENCHLORPHOS": "RONNEL",
    "O-ETHYL O-(4-NITROPHENYL) PHENYLPHOSPHONOTHIOATE": "EPN",

    # N-Nitrosamine variations
    "N,N-DIBUTYLNITROUS AMIDE": "N-NITROSODIBUTYLAMINE",
    "N,N-DIPHENYLNITROUS AMIDE": "N-NITROSODIPHENYLAMINE",
    "N,N-DIPROPYLNITROUS AMIDE": "N-NITROSODIPROPYLAMINE",
    "1-NITROSOPYRROLIDINE": "N-NITROSOPYRROLIDINE",
    "N-NITROSODIMETHYLAMINE": "NDMA",
    "N,N-DIETHYLNITROUS AMIDE": "N-NITROSODIETHYLAMINE",

    # BTEX/xylene variations
    "XYLENE": "XYLENES (MIXED)",
    "XYLENES": "XYLENES (MIXED)",
    "XYLENES (TOTAL)": "XYLENES (MIXED)",
    "XYLENE (MIXED ISOMERS)": "XYLENES (MIXED)",
    "1,3 (OR 1,4)-DIMETHYLBENZENE (M (OR P)-XYLENE)": "XYLENES (MIXED)",
    "1,2-DIMETHYLBENZENE": "O-XYLENE",
    "1,2-DIMETHYLBENZENE (O-XYLENE)": "O-XYLENE",
    "1,3-DIMETHYLBENZENE": "M-XYLENE",
    "1,3-DIMETHYLBENZENE (M-XYLENE)": "M-XYLENE",
    "1,4-DIMETHYLBENZENE": "P-XYLENE",
    "1,4-DIMETHYLBENZENE (P-XYLENE)": "P-XYLENE",
    "TRIMETHYLBENZENE (MIXED ISOMERS)": "TRIMETHYLBENZENE (MIXED)",

    # Cresol variations
    "CRESOL": "CRESOLS (MIXED)",
    "METHYLPHENOL (CRESOL MIXED ISOMERS)": "CRESOLS (MIXED)",
    "2-METHYLPHENOL": "O-CRESOL",
    "2-METHYLPHENOL (O-CRESOL)": "O-CRESOL",
    "3-METHYLPHENOL": "M-CRESOL",
    "3-METHYLPHENOL (M-CRESOL)": "M-CRESOL",
    "4-METHYLPHENOL": "P-CRESOL",
    "4-METHYLPHENOL (P-CRESOL)": "P-CRESOL",
    "2-METHYL-4,6-DINITROPHENOL (4,6-DINITRO-O-CRESOL)": "DINITRO-O-CRESOL",

    # Ketone variations
    "METHYL ETHYL KETONE": "2-BUTANONE",
    "2-BUTANONE (METHYL ETHYL KETONE)": "2-BUTANONE",
    "4-METHYL-2-PENTANONE (METHYL ISOBUTYL KETONE)": "METHYL ISOBUTYL KETONE",
    "3,5,5-TRIMETHYLCYCLOHEX-2-EN-1-ONE": "ISOPHORONE",

    # MTBE variations
    "METHYL TERT-BUTYL ETHER": "MTBE",
    "2-METHOXY-2-METHYLPROPANE (MTBE)": "MTBE",

    # Misc organic variations
    "2-PROPENENITRILE (ACRYLONITRILE)": "ACRYLONITRILE",
    "4-(4-AMINO-3-METHYLPHENYL)-2-METHYLANILINE": "3,3'-DIMETHYLBENZIDINE",
    "1-PHENYLETHANONE": "ACETOPHENONE",
    "9H-CARBAZOLE": "CARBAZOLE",
    "METHYL 2-METHYLPROP-2-ENOATE": "METHYL METHACRYLATE",
    "METHYL PROP-2-ENOATE": "METHYL ACRYLATE",
    "ETHYL PROP-2-ENOATE": "ETHYL ACRYLATE",
    "2-METHYLOXIRANE": "PROPYLENE OXIDE",
    "2-METHYL-1,3-BUTADIENE": "ISOPRENE",
    "BENZOYL BENZENECARBOPEROXOATE": "BENZOYL PEROXIDE",
    "2,2',2''-NITRILOTRIETHANOL": "TRIETHANOLAMINE",
    "2-CHLORO-1-PHENYLETHANONE": "CHLOROACETOPHENONE",
    "2-PROPANOL": "ISOPROPANOL",
    "1-BUTANOL (N-BUTANOL)": "N-BUTANOL",
    "1-BUTANOL": "N-BUTANOL",
    "10H-PHENOTHIAZINE": "PHENOTHIAZINE",
    "CHLOROBENZOIC ACID": "2-CHLOROBENZOIC ACID",
    "BETA-NAPHTHYLAMINE": "2-NAPHTHALENAMINE",
    "4-PHENYLANILINE": "DIPHENYLAMINE",
    "2,2'-OXYDIETHANOL": "DIETHYLENE GLYCOL",
    "AZEPAN-2-ONE": "CAPROLACTAM",
    "ETHYL MERCAPTAN": "ETHANETHIOL",
    "ETHYL CARBONOCHLORIDATE": "ETHYL CHLOROFORMATE",
    "1,1'-BIPHENYL": "BIPHENYL",
    "1,2-PROPANEDIOL": "PROPYLENE GLYCOL",

    # TPH variations
    "TOTAL PETROLEUM HYDROCARBONS": "TPH",
    "TOTAL PETROLEUM HYDROCARBONS (TPH)": "TPH",
    "TOTAL RECOVERABLE PETROLEUM HYDROCARBONS": "TPH",
    "TOTAL RECOVERABLE PETROLEUM HYDROCARBONS (TRPH)": "TPH",
    "TRPH": "TPH",
    "TOTAL EXTRACTABLE PETROLEUM HYDROCARBONS (TEPH)": "TPH",
    "TEPH": "TPH",
    "TOTAL PETROLEUM HYDROCARBON -DIESEL": "DIESEL",
    "DIESEL FUEL": "DIESEL",
    "DIESEL FUEL NO. 2": "DIESEL",
    "DIESEL RANGE ORGANICS": "DRO",
    "DIESEL RANGE ORGANICS (DRO)": "DRO",
    "TOTAL PETROLEUM HYDROCARBON -GASOLINE": "GASOLINE",
    "AUTOMOTIVE GASOLINE": "GASOLINE",
    "GASOLINE RANGE ORGANICS": "GRO",
    "GASOLINE RANGE ORGANICS (GRO)": "GRO",
    "KEROSENE (FUEL OIL NO. 1)": "KEROSENE",
    "HEATING OIL": "FUEL OIL NO. 2",
    "MINERAL OILS": "MINERAL OIL",
    "RESIDUAL RANGE ORGANICS": "RRO",
    "RESIDUAL RANGE ORGANICS (RRO)": "RRO",
    # TPH fraction case variations
    "C5-C8 ALIPHATIC HYDROCARBONS": "C5-C8 ALIPHATICS",
    "C5-C8 Aliphatic Hydrocarbons": "C5-C8 ALIPHATICS",
    "C9-C10 AROMATIC HYDROCARBONS": "C9-C10 AROMATICS",
    "C9-C10 Aromatic Hydrocarbons": "C9-C10 AROMATICS",
    "C9-C12 ALIPHATIC HYDROCARBONS": "C9-C12 ALIPHATICS",
    "C9-C12 Aliphatic Hydrocarbons": "C9-C12 ALIPHATICS",
    "C9-C18 ALIPHATIC HYDROCARBONS": "C9-C18 ALIPHATICS",
    "C11-C22 AROMATIC HYDROCARBONS": "C11-C22 AROMATICS",
    "C11-C22 Aromatic Hydrocarbons": "C11-C22 AROMATICS",
    "C13-C18 ALIPHATIC HYDROCARBONS": "C13-C18 ALIPHATICS",
    "C13-C18 Aliphatic Hydrocarbons": "C13-C18 ALIPHATICS",
    "C19-C36 ALIPHATIC HYDROCARBONS": "C19-C36 ALIPHATICS",
    "C19-C36 Aliphatic Hydrocarbons": "C19-C36 ALIPHATICS",

    # CFC variations
    "DICHLORODIFLUOROMETHANE": "CFC-12",
    "TRICHLOROFLUOROMETHANE": "CFC-11",
    "CHLORODIFLUOROMETHANE": "HCFC-22",
    "1,1,2-TRICHLORO-1,2,2-TRIFLUOROETHANE": "CFC-113",
    "1,1,2,2-TETRACHLORO-1,2-DIFLUOROETHANE": "CFC-112",
    "1,2-DICHLORO-1,1,2,2-TETRAFLUOROETHANE": "CFC-114",

    # Alkylbenzene variations
    "BUTAN-2-YLBENZENE": "SEC-BUTYLBENZENE",
    "PROPYLBENZENE": "N-PROPYLBENZENE",
    "ISOPROPYLBENZENE": "CUMENE",
    "BUTYLBENZENE": "N-BUTYLBENZENE",
    "(2-METHYL-2-PROPANYL)BENZENE": "TERT-BUTYLBENZENE",
    "[(E)-PROP-1-ENYL]BENZENE": "TRANS-1-PROPENYLBENZENE",
    "[(Z)-PROP-1-ENYL]BENZENE": "CIS-1-PROPENYLBENZENE",
    "PHENYLMETHANOL": "BENZYL ALCOHOL",
    "CHLOROMETHYLBENZENE": "BENZYL CHLORIDE",
    "ETHYL METHYL BENZENE (MIXED ISOMERS)": "ETHYL METHYL BENZENE (MIXED)",

    # Alkane variations
    "HEXANE": "N-HEXANE",
    "HEPTANE": "N-HEPTANE",
    "2,2,4-TRIMETHYLPENTANE": "ISOOCTANE",
    "1-PROPENE": "PROPYLENE",
    "PROPENE": "PROPYLENE",
    "OCTANE": "N-OCTANE",
    "PENTANE": "N-PENTANE",
    "NONANE": "N-NONANE",
    "METHYLCYCLOHEXANOL (MIXED ISOMERS)": "METHYLCYCLOHEXANOL (MIXED)",
    "TRIBUTYLSTANNANYLIUM": "TRIBUTYLTIN",
    "TETRABUTYL ORTHOSILICATE": "TETRABUTYL SILICATE",

    # Nitrotoluene variations
    "1-METHYL-2-NITROBENZENE": "2-NITROTOLUENE",
    "1-METHYL-3-NITROBENZENE": "3-NITROTOLUENE",
    "1-METHYL-4-NITROBENZENE": "4-NITROTOLUENE",
    "PICRIC ACID": "2,4,6-TRINITROPHENOL",
    "2,4,6-TRINITROTOLUENE": "TNT",
    "CYCLOTRIMETHYLENETRINITRAMINE": "RDX",
    "HEXAHYDRO-1,3,5-TRINITRO-1,3,5-TRIAZINE (RDX)": "RDX",
    "CYCLOTETRAMETHYLENETETRANITRAMINE": "HMX",
    "1,3,5,7-TETRANITRO-1,3,5,7-TETRAZOCANE (HMX)": "HMX",
    "N-METHYL-N,2,4,6-TETRANITROANILINE (TETRYL)": "TETRYL",

    # PFAS variations
    "PERFLUOROOCTANOIC ACID": "PFOA",
    "PERFLUOROOCTANOIC ACID (PFOA)": "PFOA",
    "PERFLUOROOCTANESULFONIC ACID": "PFOS",
    "PERFLUOROOCTANE SULFONIC ACID (PFOS)": "PFOS",

    # Chemical warfare variations
    "1-CHLORO-2-[(2-CHLOROETHYL)SULFANYL]ETHANE": "MUSTARD GAS",
    "DICHLORO-[(E)-2-CHLOROETHENYL]ARSANE (LEWISITE)": "LEWISITE",

    # Generic category variations
    "VOCS": "VOC",
    "VOLATILE ORGANIC COMPOUNDS": "VOC",
    "SVOCS": "SVOC",
    "SEMIVOLATILE ORGANIC COMPOUNDS": "SVOC",
    "UNEXPLODED ORDNANCE (UXO)": "UXO",
    "UNEXPLODED ORDNANCE": "UXO",
    "3-METHYLPHENOL (MIXED MONOCHLORINATED ISOMERS)": "CHLOROCRESOL (MIXED)",
    "BUTYLTIN TOXICITY EQUIVALENTS (TEQ)": "BUTYLTIN TEQ",
    "DICHLOROPROPANE (MIXED ISOMERS)": "DICHLOROPROPANE (MIXED)",

    # Inorganic variations
    "HYDROGEN (H2)": "HYDROGEN",
    "PHOSPHORUS (P4)": "PHOSPHORUS",
    "IODINE (I2)": "IODINE",
    "BROMINE (BR2)": "BROMINE",
    "URANIUM-234/235/238": "URANIUM (COMBINED)",
}


def _build_lookup() -> dict[str, tuple[str, str | None] | tuple[str, str | None, str]]:
    """Build the full lookup table from canonical entries and aliases.

    Returns a dict where:
    - All canonical names map to their (CAS, ATSDR, PUBCHEM) tuple
    - All alias names map to their canonical entry's tuple
    """
    lookup: dict[str, tuple[str, str | None] | tuple[str, str | None, str]] = {}

    # Add all canonical entries
    lookup.update(_CANONICAL)

    # Add all aliases, mapping to their canonical entry
    for alias, canonical in _ALIASES.items():
        if canonical in _CANONICAL:
            lookup[alias] = _CANONICAL[canonical]
        # else: alias points to unknown canonical - skip silently

    return lookup


# The exported lookup table
SUPERFUND_CAS_LOOKUP = _build_lookup()
