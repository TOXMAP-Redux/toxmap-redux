"""Supplementary CAS and ATSDR lookup for Superfund contaminants not in TRI chemicals table.

These include PAHs, PCBs, chlorinated solvents, metals, pesticides, radionuclides,
and other hazardous substances commonly found at Superfund sites but not TRI-reportable.

Format: {CHEMICAL_NAME_UPPER: (CAS_NUMBER, ATSDR_TOXFAQS_URL, PUBCHEM_URL)}
  - 2-tuple (legacy): (CAS, ATSDR) - PubChem URL auto-generated from CAS
  - 3-tuple: (CAS, ATSDR, PUBCHEM) - explicit PubChem URL for mixtures without CAS

CAS numbers verified against PubChem (https://pubchem.ncbi.nlm.nih.gov/).
ATSDR ToxFAQs URLs from CDC/ATSDR Toxic Substances Portal (scraped 2024).
Note: ATSDR only covers ~200 substances; many chemicals will have None for ATSDR.
"""
from __future__ import annotations

# ATSDR ToxFAQs URLs (verified from scripts/atsdr_toxid_map.csv)
# Format: https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=XXX&toxid=YY
_ATSDR = {
    # Metals
    "ALUMINUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=190&toxid=34",
    "AMMONIA": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=10&toxid=2",
    "ANTIMONY": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=331&toxid=58",
    "ARSENIC": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=19&toxid=3",
    "BARIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=326&toxid=57",
    "BERYLLIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=184&toxid=33",
    "BORON": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=452&toxid=80",
    "CADMIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=47&toxid=15",
    "CHROMIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=61&toxid=17",
    "COBALT": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=372&toxid=64",
    "COPPER": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=205&toxid=37",
    "LEAD": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=93&toxid=22",
    "MANGANESE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=101&toxid=23",
    "MERCURY": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1195&toxid=24",
    "NICKEL": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=244&toxid=44",
    "SELENIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=152&toxid=28",
    "SILVER": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=538&toxid=97",
    "THALLIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=308&toxid=49",
    "TIN": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=542&toxid=98",
    "VANADIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=275&toxid=50",
    "ZINC": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=301&toxid=54",
    # Solvents
    "ACETONE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=4&toxid=1",
    "BENZENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=38&toxid=14",
    "CARBON DISULFIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=473&toxid=84",
    "CARBON TETRACHLORIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=195&toxid=35",
    "CHLOROBENZENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=488&toxid=87",
    "CHLOROFORM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=52&toxid=16",
    "ETHYLBENZENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=382&toxid=66",
    "FORMALDEHYDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=219&toxid=39",
    "METHYLENE CHLORIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=233&toxid=42",
    "N-HEXANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=392&toxid=68",
    "NAPHTHALENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=239&toxid=43",
    "PHENOL": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=147&toxid=27",
    "STYRENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=420&toxid=74",
    "TETRACHLOROETHYLENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=264&toxid=48",
    "TOLUENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=160&toxid=29",
    "TRICHLOROETHYLENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=172&toxid=30",
    "VINYL CHLORIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=281&toxid=51",
    "XYLENES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=295&toxid=53",
    # Chlorinated compounds
    "1,1,1-TRICHLOROETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=431&toxid=76",
    "1,1,2,2-TETRACHLOROETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=800&toxid=156",
    "1,1,2-TRICHLOROETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=795&toxid=155",
    "1,1-DICHLOROETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=717&toxid=129",
    "1,1-DICHLOROETHENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=721&toxid=130",
    "1,2-DIBROMOETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=725&toxid=131",
    "1,2-DICHLOROETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=591&toxid=110",
    "1,2-DICHLOROETHENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=463&toxid=82",
    "1,2-DICHLOROPROPANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=830&toxid=162",
    "1,3-BUTADIENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=458&toxid=81",
    "1,4-DIOXANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=954&toxid=199",
    "BROMOMETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=821&toxid=160",
    "CHLOROMETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=586&toxid=109",
    "DICHLOROBENZENES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=703&toxid=126",
    "DICHLOROPROPENES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=835&toxid=163",
    "ETHYLENE OXIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=733&toxid=133",
    "HEXACHLOROBENZENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=626&toxid=115",
    "HEXACHLOROBUTADIENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=864&toxid=168",
    "HEXACHLOROETHANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=869&toxid=169",
    "TRICHLOROBENZENES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1169&toxid=255",
    # PAHs / PCBs / Dioxins
    "PAHS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=121&toxid=25",
    "PCBS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=140&toxid=26",
    "CDDS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=363&toxid=63",
    "CDFS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=937&toxid=194",
    "CREOSOTE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=65&toxid=18",
    # Pesticides
    "ALDRIN": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=316&toxid=56",
    "DIELDRIN": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=316&toxid=56",
    "ATRAZINE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=854&toxid=59",
    "CHLORDANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=354&toxid=62",
    "CHLORDECONE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1188&toxid=276",
    "CHLORPYRIFOS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=494&toxid=88",
    "DDT": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=80&toxid=20",
    "DDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=80&toxid=20",
    "DDD": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=80&toxid=20",
    "DIAZINON": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=506&toxid=90",
    "DICHLORVOS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=596&toxid=111",
    "ENDOSULFAN": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=608&toxid=113",
    "ENDRIN": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=616&toxid=114",
    "GLYPHOSATE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1489&toxid=293",
    "HEPTACHLOR": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=744&toxid=135",
    "HCH": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=753&toxid=138",
    "LINDANE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=753&toxid=138",
    "MALATHION": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=521&toxid=92",
    "METHOXYCHLOR": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=777&toxid=151",
    "MIREX": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1188&toxid=276",
    "PARATHION": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1426&toxid=246",
    "PENTACHLOROPHENOL": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=401&toxid=70",
    "PYRETHRINS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=786&toxid=153",
    "TOXAPHENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=547&toxid=99",
    "2,4-D": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1501&toxid=288",
    # Phthalates
    "DEHP": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=377&toxid=65",
    "DIETHYL PHTHALATE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=602&toxid=112",
    "DI-N-BUTYL PHTHALATE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=858&toxid=167",
    "DI-N-OCTYLPHTHALATE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=972&toxid=204",
    # Explosives
    "TNT": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=676&toxid=125",
    "RDX": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=411&toxid=72",
    "HMX": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=876&toxid=171",
    "DINITROTOLUENES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=846&toxid=165",
    # Radionuclides
    "AMERICIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=810&toxid=158",
    "CESIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=576&toxid=107",
    "PLUTONIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=647&toxid=119",
    "RADIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=790&toxid=154",
    "RADON": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=406&toxid=71",
    "STRONTIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=655&toxid=120",
    "THORIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=659&toxid=121",
    "URANIUM": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=439&toxid=77",
    # PFAS
    "PFAS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1116&toxid=237",
    "PERFLUOROALKYLS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1116&toxid=237",
    # TPH / Fuels
    "TPH": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=423&toxid=75",
    "FUEL OILS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=515&toxid=91",
    "GASOLINE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=467&toxid=83",
    "JET FUELS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=772&toxid=150",
    # Other
    "ACRYLONITRILE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=446&toxid=78",
    "ACROLEIN": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=555&toxid=102",
    "ASBESTOS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=29&toxid=4",
    "BENZIDINE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=568&toxid=105",
    "CRESOLS": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=945&toxid=196",
    "CYANIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=71&toxid=19",
    "ETHYLENE GLYCOL": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=85&toxid=21",
    "FLUORIDES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=211&toxid=38",
    "HYDRAZINES": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=500&toxid=89",
    "HYDROGEN SULFIDE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1429&toxid=67",
    "MTBE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=227&toxid=41",
    "NDMA": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=883&toxid=173",
    "NITRATE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=1186&toxid=258",
    "NITROBENZENE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=531&toxid=95",
    "PERCHLORATE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=893&toxid=181",
    "PYRIDINE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=534&toxid=96",
    "2-BUTANONE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=342&toxid=60",
    "2-HEXANONE": "https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=737&toxid=134",
}


def _get_atsdr(name: str) -> str | None:
    """Look up ATSDR ToxFAQs URL for a chemical name."""
    return _ATSDR.get(name)


# Lookup table: {CHEMICAL_NAME_UPPER: (CAS_NUMBER, ATSDR_URL or None)}
# CAS numbers from PubChem; ATSDR URLs from CDC/ATSDR scraped data
SUPERFUND_CAS_LOOKUP: dict[str, tuple[str, str | None]] = {
    # ─────────────────────────────────────────────────────────────────────────
    # Polycyclic Aromatic Hydrocarbons (PAHs)
    # ATSDR groups all PAHs under toxid=25
    # ─────────────────────────────────────────────────────────────────────────
    "BENZO(A)PYRENE": ("50-32-8", _ATSDR["PAHS"]),
    "BENZO[A]PYRENE": ("50-32-8", _ATSDR["PAHS"]),
    "BENZO(B)FLUORANTHENE": ("205-99-2", _ATSDR["PAHS"]),
    "BENZO(K)FLUORANTHENE": ("207-08-9", _ATSDR["PAHS"]),
    "BENZO[A]ANTHRACENE": ("56-55-3", _ATSDR["PAHS"]),
    "BENZO(A)ANTHRACENE": ("56-55-3", _ATSDR["PAHS"]),
    "DIBENZO(A,H)ANTHRACENE": ("53-70-3", _ATSDR["PAHS"]),
    "DIBENZ(A,H)ANTHRACENE": ("53-70-3", _ATSDR["PAHS"]),
    "INDENO(1,2,3-CD)PYRENE": ("193-39-5", _ATSDR["PAHS"]),
    "CHRYSENE": ("218-01-9", _ATSDR["PAHS"]),
    "FLUORANTHENE": ("206-44-0", _ATSDR["PAHS"]),
    "FLUORENE": ("86-73-7", _ATSDR["PAHS"]),
    "9H-FLUORENE": ("86-73-7", _ATSDR["PAHS"]),
    "PYRENE": ("129-00-0", _ATSDR["PAHS"]),
    "ANTHRACENE": ("120-12-7", _ATSDR["PAHS"]),
    "PHENANTHRENE": ("85-01-8", _ATSDR["PAHS"]),
    "ACENAPHTHENE": ("83-32-9", _ATSDR["PAHS"]),
    "1,2-DIHYDROACENAPHTHYLENE": ("83-32-9", _ATSDR["PAHS"]),  # IUPAC name for acenaphthene
    "ACENAPHTHYLENE": ("208-96-8", _ATSDR["PAHS"]),
    "NAPHTHALENE": ("91-20-3", _ATSDR["NAPHTHALENE"]),
    "1-METHYLNAPHTHALENE": ("90-12-0", _ATSDR["NAPHTHALENE"]),
    "2-METHYLNAPHTHALENE": ("91-57-6", _ATSDR["NAPHTHALENE"]),
    "BENZO[G,H,I]PERYLENE": ("191-24-2", _ATSDR["PAHS"]),
    "BENZO(GHI)PERYLENE": ("191-24-2", _ATSDR["PAHS"]),
    "POLYCYCLIC AROMATIC HYDROCARBONS": ("N/A", _ATSDR["PAHS"]),
    "POLYCYCLIC AROMATIC HYDROCARBONS (PAHS)": ("N/A", _ATSDR["PAHS"]),
    "PAHS": ("N/A", _ATSDR["PAHS"]),
    "CARCINOGENIC POLYCYCLIC AROMATIC HYDROCARBONS (CPAH)": ("N/A", _ATSDR["PAHS"]),
    "POLYCYCLIC AROMATIC HYDROCARBONS, HIGH MOLECULAR WEIGHT (HPAHS)": ("N/A", _ATSDR["PAHS"]),
    "BENZO[A]PYRENE EQUIVALENTS": ("N/A", _ATSDR["PAHS"]),
    "BENZO[A]PYRENE EQUIVALENTS (BAPEQ)": ("N/A", _ATSDR["PAHS"]),
    "BAPEQ": ("N/A", _ATSDR["PAHS"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Polychlorinated Biphenyls (PCBs) - Aroclors
    # ATSDR groups all PCBs under toxid=26
    # ─────────────────────────────────────────────────────────────────────────
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
    "POLYCHLORINATED BIPHENYLS (PCBS)": ("1336-36-3", _ATSDR["PCBS"]),
    "PCBS": ("1336-36-3", _ATSDR["PCBS"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Chlorinated solvents / VOCs
    # ─────────────────────────────────────────────────────────────────────────
    "1,1-DICHLOROETHENE": ("75-35-4", _ATSDR["1,1-DICHLOROETHENE"]),
    "1,1-DICHLOROETHYLENE": ("75-35-4", _ATSDR["1,1-DICHLOROETHENE"]),
    "CIS-1,2-DICHLOROETHENE": ("156-59-2", _ATSDR["1,2-DICHLOROETHENE"]),
    "CIS-1,2-DICHLOROETHYLENE": ("156-59-2", _ATSDR["1,2-DICHLOROETHENE"]),
    "TRANS-1,2-DICHLOROETHENE": ("156-60-5", _ATSDR["1,2-DICHLOROETHENE"]),
    "TRANS-1,2-DICHLOROETHYLENE": ("156-60-5", _ATSDR["1,2-DICHLOROETHENE"]),
    "TETRACHLOROETHENE": ("127-18-4", _ATSDR["TETRACHLOROETHYLENE"]),
    "TETRACHLOROETHYLENE": ("127-18-4", _ATSDR["TETRACHLOROETHYLENE"]),
    "PERCHLOROETHYLENE": ("127-18-4", _ATSDR["TETRACHLOROETHYLENE"]),
    "PCE": ("127-18-4", _ATSDR["TETRACHLOROETHYLENE"]),
    "TRICHLOROETHENE": ("79-01-6", _ATSDR["TRICHLOROETHYLENE"]),
    "TRICHLOROETHYLENE": ("79-01-6", _ATSDR["TRICHLOROETHYLENE"]),
    "TCE": ("79-01-6", _ATSDR["TRICHLOROETHYLENE"]),
    "DICHLOROMETHANE": ("75-09-2", _ATSDR["METHYLENE CHLORIDE"]),
    "DICHLOROMETHANE (METHYLENE CHLORIDE)": ("75-09-2", _ATSDR["METHYLENE CHLORIDE"]),
    "METHYLENE CHLORIDE": ("75-09-2", _ATSDR["METHYLENE CHLORIDE"]),
    "CHLOROETHENE (VINYL CHLORIDE)": ("75-01-4", _ATSDR["VINYL CHLORIDE"]),
    "VINYL CHLORIDE": ("75-01-4", _ATSDR["VINYL CHLORIDE"]),
    "1,1,1-TRICHLOROETHANE": ("71-55-6", _ATSDR["1,1,1-TRICHLOROETHANE"]),
    "1,1,2-TRICHLOROETHANE": ("79-00-5", _ATSDR["1,1,2-TRICHLOROETHANE"]),
    "1,1,2,2-TETRACHLOROETHANE": ("79-34-5", _ATSDR["1,1,2,2-TETRACHLOROETHANE"]),
    "1,1-DICHLOROETHANE": ("75-34-3", _ATSDR["1,1-DICHLOROETHANE"]),
    "1,2-DIBROMOETHANE": ("106-93-4", _ATSDR["1,2-DIBROMOETHANE"]),
    "ETHYLENE DIBROMIDE": ("106-93-4", _ATSDR["1,2-DIBROMOETHANE"]),
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
    "METHYL BROMIDE": ("74-83-9", _ATSDR["BROMOMETHANE"]),
    "1,3-DICHLOROPROPENE": ("542-75-6", _ATSDR["DICHLOROPROPENES"]),
    "1,3-DICHLOROPROPENE (EZ MIXTURE)": ("542-75-6", _ATSDR["DICHLOROPROPENES"]),
    "CIS-1,3-DICHLOROPROPENE": ("10061-01-5", _ATSDR["DICHLOROPROPENES"]),
    "TRANS-1,3-DICHLOROPROPENE": ("10061-02-6", _ATSDR["DICHLOROPROPENES"]),
    "1,2,3-TRICHLOROPROPANE": ("96-18-4", None),  # No ATSDR ToxFAQs
    "TRICHLOROETHANE (MIXED ISOMERS)": ("N/A", _ATSDR["1,1,1-TRICHLOROETHANE"], "https://pubchem.ncbi.nlm.nih.gov/compound/1,1,1-Trichloroethane"),
    # ─────────────────────────────────────────────────────────────────────────
    # Trihalomethanes (THMs)
    # ─────────────────────────────────────────────────────────────────────────
    "BROMODICHLOROMETHANE": ("75-27-4", None),
    "DIBROMOCHLOROMETHANE": ("124-48-1", None),
    "BROMOFORM": ("75-25-2", None),
    "TRIBROMOMETHANE": ("75-25-2", None),
    # ─────────────────────────────────────────────────────────────────────────
    # Ethers
    # ─────────────────────────────────────────────────────────────────────────
    "BIS(2-CHLOROETHYL)ETHER": ("111-44-4", None),
    "BIS(2-CHLOROISOPROPYL) ETHER": ("108-60-1", None),
    "1-CHLORO-2-ETHENOXYETHANE": ("110-75-8", None),  # 2-chloroethyl vinyl ether
    # ─────────────────────────────────────────────────────────────────────────
    # Phthalates
    # ─────────────────────────────────────────────────────────────────────────
    "BIS(2-ETHYLHEXYL)PHTHALATE": ("117-81-7", _ATSDR["DEHP"]),
    "DI(2-ETHYLHEXYL)PHTHALATE": ("117-81-7", _ATSDR["DEHP"]),
    "DEHP": ("117-81-7", _ATSDR["DEHP"]),
    "DIETHYL PHTHALATE": ("84-66-2", _ATSDR["DIETHYL PHTHALATE"]),
    "DIBUTYL PHTHALATE": ("84-74-2", _ATSDR["DI-N-BUTYL PHTHALATE"]),
    "DI-N-OCTYL PHTHALATE": ("117-84-0", _ATSDR["DI-N-OCTYLPHTHALATE"]),
    "BUTYL BENZYL PHTHALATE": ("85-68-7", None),
    # ─────────────────────────────────────────────────────────────────────────
    # Metals and metal compounds
    # ─────────────────────────────────────────────────────────────────────────
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
    "HEXAVALENT CHROMIUM": ("18540-29-9", _ATSDR["CHROMIUM"]),
    "COBALT": ("7440-48-4", _ATSDR["COBALT"]),
    "COPPER": ("7440-50-8", _ATSDR["COPPER"]),
    "LEAD": ("7439-92-1", _ATSDR["LEAD"]),
    "MANGANESE": ("7439-96-5", _ATSDR["MANGANESE"]),
    "MERCURY": ("7439-97-6", _ATSDR["MERCURY"]),
    "METHYL MERCURY": ("22967-92-6", _ATSDR["MERCURY"]),
    "METHYLMERCURY": ("22967-92-6", _ATSDR["MERCURY"]),
    "NICKEL": ("7440-02-0", _ATSDR["NICKEL"]),
    "SELENIUM": ("7782-49-2", _ATSDR["SELENIUM"]),
    "SILVER": ("7440-22-4", _ATSDR["SILVER"]),
    "THALLIUM": ("7440-28-0", _ATSDR["THALLIUM"]),
    "THALLIUM COMPOUNDS": ("N/A", _ATSDR["THALLIUM"]),
    "TIN": ("7440-31-5", _ATSDR["TIN"]),
    "VANADIUM": ("7440-62-2", _ATSDR["VANADIUM"]),
    "VANADIUM, METAL AND/OR ALLOY": ("7440-62-2", _ATSDR["VANADIUM"]),
    "ZINC": ("7440-66-6", _ATSDR["ZINC"]),
    # Chromium forms
    "CHROMIUM (III)": ("7440-47-3", _ATSDR["CHROMIUM"]),
    "CHROMIUM (VI)": ("18540-29-9", _ATSDR["CHROMIUM"]),
    "CHROMIUM COMPOUNDS": ("N/A", _ATSDR["CHROMIUM"]),
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
    # ─────────────────────────────────────────────────────────────────────────
    # Dioxins and Furans
    # Note: For compound classes without specific CAS, use PubChem search URLs
    # ─────────────────────────────────────────────────────────────────────────
    "2,3,7,8-TETRACHLORODIBENZO-P-DIOXIN": ("1746-01-6", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "2,3,7,8-TETRACHLORODIBENZO-P-DIOXIN (TCDD)": ("1746-01-6", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "2,3,7,8-TETRACHLORODIBENZO-p-DIOXIN (TCDD) TOXICITY EQUIVALENTS (TEq)": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "2,3,7,8-TCDD": ("1746-01-6", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "TCDD": ("1746-01-6", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/compound/15625"),
    "2,3,7,8-TETRACHLORODIBENZOFURAN": ("51207-31-9", _ATSDR["CDFS"], "https://pubchem.ncbi.nlm.nih.gov/compound/39227"),
    "CHLORINATED DIOXINS AND FURANS": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=chlorinated+dioxins"),
    "DIOXINS (CHLORINATED DIBENZODIOXINS)": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=chlorinated+dibenzodioxins"),
    "DIOXINS AND DIBENZOFURANS": ("N/A", _ATSDR["CDDS"], "https://pubchem.ncbi.nlm.nih.gov/#query=dioxins+dibenzofurans"),
    # ─────────────────────────────────────────────────────────────────────────
    # Pesticides
    # ─────────────────────────────────────────────────────────────────────────
    "DDT": ("50-29-3", _ATSDR["DDT"]),
    "4,4'-DDT": ("50-29-3", _ATSDR["DDT"]),
    "P,P'-DDT": ("50-29-3", _ATSDR["DDT"]),
    "DDE": ("72-55-9", _ATSDR["DDE"]),
    "4,4'-DDE": ("72-55-9", _ATSDR["DDE"]),
    "P,P'-DDE": ("72-55-9", _ATSDR["DDE"]),
    "DDD": ("72-54-8", _ATSDR["DDD"]),
    "4,4'-DDD": ("72-54-8", _ATSDR["DDD"]),
    "P,P'-DDD": ("72-54-8", _ATSDR["DDD"]),
    "ALDRIN": ("309-00-2", _ATSDR["ALDRIN"]),
    "DIELDRIN": ("60-57-1", _ATSDR["DIELDRIN"]),
    "ENDRIN": ("72-20-8", _ATSDR["ENDRIN"]),
    "HEPTACHLOR": ("76-44-8", _ATSDR["HEPTACHLOR"]),
    "HEPTACHLOR EPOXIDE": ("1024-57-3", _ATSDR["HEPTACHLOR"]),
    "CHLORDANE": ("57-74-9", _ATSDR["CHLORDANE"]),
    "ALPHA-CHLORDANE": ("5103-71-9", _ATSDR["CHLORDANE"]),
    "GAMMA-CHLORDANE": ("5103-74-2", _ATSDR["CHLORDANE"]),
    "TOXAPHENE": ("8001-35-2", _ATSDR["TOXAPHENE"]),
    "LINDANE": ("58-89-9", _ATSDR["LINDANE"]),
    "GAMMA-HEXACHLOROCYCLOHEXANE": ("58-89-9", _ATSDR["LINDANE"]),
    "GAMMA-HEXACHLOROCYCLOHEXANE (LINDANE)": ("58-89-9", _ATSDR["LINDANE"]),
    "ALPHA-HEXACHLOROCYCLOHEXANE": ("319-84-6", _ATSDR["HCH"]),
    "BETA-HEXACHLOROCYCLOHEXANE": ("319-85-7", _ATSDR["HCH"]),
    "METHOXYCHLOR": ("72-43-5", _ATSDR["METHOXYCHLOR"]),
    "MIREX": ("2385-85-5", _ATSDR["MIREX"]),
    "CHLORDECONE": ("143-50-0", _ATSDR["CHLORDECONE"]),
    "ENDOSULFAN": ("115-29-7", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN (I OR II)": ("115-29-7", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN I": ("959-98-8", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN II": ("33213-65-9", _ATSDR["ENDOSULFAN"]),
    "ENDOSULFAN SULFATE": ("1031-07-8", _ATSDR["ENDOSULFAN"]),
    "ATRAZINE": ("1912-24-9", _ATSDR["ATRAZINE"]),
    "DIAZINON": ("333-41-5", _ATSDR["DIAZINON"]),
    "DISULFOTON": ("298-04-4", None),  # Organophosphate insecticide; no ATSDR ToxFAQs
    "MALATHION": ("121-75-5", _ATSDR["MALATHION"]),
    "PARATHION": ("56-38-2", _ATSDR["PARATHION"]),
    "PENTACHLOROPHENOL": ("87-86-5", _ATSDR["PENTACHLOROPHENOL"]),
    "PCP": ("87-86-5", _ATSDR["PENTACHLOROPHENOL"]),
    "2,4-DICHLOROPHENOXYACETIC ACID": ("94-75-7", _ATSDR["2,4-D"]),
    "2,4-D": ("94-75-7", _ATSDR["2,4-D"]),
    # ─────────────────────────────────────────────────────────────────────────
    # N-Nitrosamines
    # ─────────────────────────────────────────────────────────────────────────
    "N,N-DIBUTYLNITROUS AMIDE": ("924-16-3", None),  # N-Nitrosodibutylamine
    "N-NITROSODIBUTYLAMINE": ("924-16-3", None),
    "N,N-DIPHENYLNITROUS AMIDE": ("86-30-6", None),  # N-Nitrosodiphenylamine
    "N-NITROSODIPHENYLAMINE": ("86-30-6", None),
    "N,N-DIPROPYLNITROUS AMIDE": ("621-64-7", None),  # N-Nitrosodipropylamine
    "N-NITROSODIPROPYLAMINE": ("621-64-7", None),
    "1-NITROSOPYRROLIDINE": ("930-55-2", None),
    "N-NITROSOPYRROLIDINE": ("930-55-2", None),
    # ─────────────────────────────────────────────────────────────────────────
    # BTEX compounds
    # ─────────────────────────────────────────────────────────────────────────
    "BENZENE": ("71-43-2", _ATSDR["BENZENE"]),
    "ETHYLBENZENE": ("100-41-4", _ATSDR["ETHYLBENZENE"]),
    "TOLUENE": ("108-88-3", _ATSDR["TOLUENE"]),
    "XYLENE": ("1330-20-7", _ATSDR["XYLENES"]),
    "XYLENES": ("1330-20-7", _ATSDR["XYLENES"]),
    "XYLENES (TOTAL)": ("1330-20-7", _ATSDR["XYLENES"]),
    "O-XYLENE": ("95-47-6", _ATSDR["XYLENES"]),
    "M-XYLENE": ("108-38-3", _ATSDR["XYLENES"]),
    "P-XYLENE": ("106-42-3", _ATSDR["XYLENES"]),
    "STYRENE": ("100-42-5", _ATSDR["STYRENE"]),
    "1,2,4-TRIMETHYLBENZENE": ("95-63-6", None),  # No ATSDR ToxFAQs
    "1,3,5-TRIMETHYLBENZENE": ("108-67-8", None),  # No ATSDR ToxFAQs
    # ─────────────────────────────────────────────────────────────────────────
    # Inorganic ions, acids, and compounds
    # ─────────────────────────────────────────────────────────────────────────
    "NITRATE": ("14797-55-8", _ATSDR["NITRATE"]),
    "NITRATE/NITRITE": ("N/A", _ATSDR["NITRATE"]),  # mixture
    "CYANIDE": ("57-12-5", _ATSDR["CYANIDE"]),
    "HYDROGEN CYANIDE": ("74-90-8", _ATSDR["CYANIDE"]),
    "FLUORIDE": ("16984-48-8", _ATSDR["FLUORIDES"]),
    "AMMONIA": ("7664-41-7", _ATSDR["AMMONIA"]),
    "ASBESTOS": ("1332-21-4", _ATSDR["ASBESTOS"]),
    "PERCHLORATE": ("14797-73-0", _ATSDR["PERCHLORATE"]),
    "CALCIUM CARBONATE": ("471-34-1", None),
    # Acids (no ATSDR ToxFAQs for most inorganic acids)
    "SULFURIC ACID": ("7664-93-9", None),
    "HYDROCHLORIC ACID": ("7647-01-0", None),
    "NITRIC ACID": ("7697-37-2", None),
    "PHOSPHORIC ACID": ("7664-38-2", None),
    "HYDROFLUORIC ACID": ("7664-39-3", _ATSDR["FLUORIDES"]),
    "CHROMIC ACID": ("7738-94-5", _ATSDR["CHROMIUM"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Radioactive materials
    # ─────────────────────────────────────────────────────────────────────────
    "RADIUM": ("7440-14-4", _ATSDR["RADIUM"]),
    "RADIUM-226": ("13982-63-3", _ATSDR["RADIUM"]),
    "RADIUM-228": ("15262-20-1", _ATSDR["RADIUM"]),
    "URANIUM": ("7440-61-1", _ATSDR["URANIUM"]),
    "URANIUM-234": ("13966-29-5", _ATSDR["URANIUM"]),
    "URANIUM-235": ("15117-96-1", _ATSDR["URANIUM"]),
    "URANIUM-238": ("7440-61-1", _ATSDR["URANIUM"]),
    "THORIUM": ("7440-29-1", _ATSDR["THORIUM"]),
    "THORIUM-230": ("14269-63-7", _ATSDR["THORIUM"]),
    "THORIUM-232": ("7440-29-1", _ATSDR["THORIUM"]),
    "RADON": ("10043-92-2", _ATSDR["RADON"]),
    "RADON-222": ("14859-67-7", _ATSDR["RADON"]),
    "CESIUM-137": ("10045-97-3", _ATSDR["CESIUM"]),
    "STRONTIUM-90": ("10098-97-2", _ATSDR["STRONTIUM"]),
    "PLUTONIUM": ("7440-07-5", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-238": ("13981-16-3", _ATSDR["PLUTONIUM"]),
    "PLUTONIUM-239": ("15117-48-3", _ATSDR["PLUTONIUM"]),
    "AMERICIUM-241": ("14596-10-2", _ATSDR["AMERICIUM"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Explosives
    # ─────────────────────────────────────────────────────────────────────────
    "2,4,6-TRINITROTOLUENE": ("118-96-7", _ATSDR["TNT"]),
    "TNT": ("118-96-7", _ATSDR["TNT"]),
    "RDX": ("121-82-4", _ATSDR["RDX"]),
    "CYCLOTRIMETHYLENETRINITRAMINE": ("121-82-4", _ATSDR["RDX"]),
    "HMX": ("2691-41-0", _ATSDR["HMX"]),
    "CYCLOTETRAMETHYLENETETRANITRAMINE": ("2691-41-0", _ATSDR["HMX"]),
    "2,4-DINITROTOLUENE": ("121-14-2", _ATSDR["DINITROTOLUENES"]),
    "2,6-DINITROTOLUENE": ("606-20-2", _ATSDR["DINITROTOLUENES"]),
    # ─────────────────────────────────────────────────────────────────────────
    # PFAS (Per- and polyfluoroalkyl substances)
    # ATSDR groups all PFAS under toxid=237
    # ─────────────────────────────────────────────────────────────────────────
    "PFOA": ("335-67-1", _ATSDR["PFAS"]),
    "PERFLUOROOCTANOIC ACID": ("335-67-1", _ATSDR["PFAS"]),
    "PFOS": ("1763-23-1", _ATSDR["PFAS"]),
    "PERFLUOROOCTANESULFONIC ACID": ("1763-23-1", _ATSDR["PFAS"]),
    "PFNA": ("375-95-1", _ATSDR["PFAS"]),
    "PFDA": ("335-76-2", _ATSDR["PFAS"]),
    "PFBS": ("375-73-5", _ATSDR["PFAS"]),
    "PFHXA": ("307-24-4", _ATSDR["PFAS"]),
    "PFHXS": ("355-46-4", _ATSDR["PFAS"]),
    "PERFLUOROOCTANOIC ACID (PFOA)": ("335-67-1", _ATSDR["PFAS"]),
    "PERFLUOROOCTANE SULFONIC ACID (PFOS)": ("1763-23-1", _ATSDR["PFAS"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Phenols and chlorophenols
    # ─────────────────────────────────────────────────────────────────────────
    "PHENOL": ("108-95-2", _ATSDR["PHENOL"]),
    "CRESOL": ("1319-77-3", _ATSDR["CRESOLS"]),
    "O-CRESOL": ("95-48-7", _ATSDR["CRESOLS"]),
    "M-CRESOL": ("108-39-4", _ATSDR["CRESOLS"]),
    "P-CRESOL": ("106-44-5", _ATSDR["CRESOLS"]),
    "2-METHYLPHENOL": ("95-48-7", _ATSDR["CRESOLS"]),
    "2-METHYLPHENOL (O-CRESOL)": ("95-48-7", _ATSDR["CRESOLS"]),
    "3-METHYLPHENOL": ("108-39-4", _ATSDR["CRESOLS"]),
    "4-METHYLPHENOL": ("106-44-5", _ATSDR["CRESOLS"]),
    "4-METHYLPHENOL (P-CRESOL)": ("106-44-5", _ATSDR["CRESOLS"]),
    "2-CHLOROPHENOL": ("95-57-8", None),
    "4-CHLOROPHENOL": ("106-48-9", None),
    "2,4-DICHLOROPHENOL": ("120-83-2", None),
    "2,4,5-TRICHLOROPHENOL": ("95-95-4", None),
    "2,4,6-TRICHLOROPHENOL": ("88-06-2", None),
    "4-CHLOROANILINE": ("106-47-8", None),
    "2-METHYLANILINE": ("95-53-4", None),  # o-toluidine
    "2-METHYL-4,6-DINITROPHENOL (4,6-DINITRO-O-CRESOL)": ("534-52-1", None),
    # ─────────────────────────────────────────────────────────────────────────
    # Other organic compounds
    # ─────────────────────────────────────────────────────────────────────────
    "CARBON DISULFIDE": ("75-15-0", _ATSDR["CARBON DISULFIDE"]),
    "ACETONE": ("67-64-1", _ATSDR["ACETONE"]),
    "METHYL ETHYL KETONE": ("78-93-3", _ATSDR["2-BUTANONE"]),
    "2-BUTANONE": ("78-93-3", _ATSDR["2-BUTANONE"]),
    "2-BUTANONE (METHYL ETHYL KETONE)": ("78-93-3", _ATSDR["2-BUTANONE"]),
    "2-HEXANONE": ("591-78-6", _ATSDR["2-HEXANONE"]),
    "4-METHYL-2-PENTANONE (METHYL ISOBUTYL KETONE)": ("108-10-1", None),
    "METHYL ISOBUTYL KETONE": ("108-10-1", None),
    "3,5,5-TRIMETHYLCYCLOHEX-2-EN-1-ONE": ("78-59-1", None),  # isophorone
    "ISOPHORONE": ("78-59-1", None),
    "METHYL TERT-BUTYL ETHER": ("1634-04-4", _ATSDR["MTBE"]),
    "MTBE": ("1634-04-4", _ATSDR["MTBE"]),
    "2-METHOXY-2-METHYLPROPANE (MTBE)": ("1634-04-4", _ATSDR["MTBE"]),
    "FORMALDEHYDE": ("50-00-0", _ATSDR["FORMALDEHYDE"]),
    "ACRYLONITRILE": ("107-13-1", _ATSDR["ACRYLONITRILE"]),
    "2-PROPENENITRILE (ACRYLONITRILE)": ("107-13-1", _ATSDR["ACRYLONITRILE"]),
    "ACROLEIN": ("107-02-8", _ATSDR["ACROLEIN"]),
    "ETHYLENE OXIDE": ("75-21-8", _ATSDR["ETHYLENE OXIDE"]),
    "HYDRAZINE": ("302-01-2", _ATSDR["HYDRAZINES"]),
    "ETHYLENE GLYCOL": ("107-21-1", _ATSDR["ETHYLENE GLYCOL"]),
    "N-NITROSODIMETHYLAMINE": ("62-75-9", _ATSDR["NDMA"]),
    "NDMA": ("62-75-9", _ATSDR["NDMA"]),
    "BENZIDINE": ("92-87-5", _ATSDR["BENZIDINE"]),
    "4-(4-AMINO-3-METHYLPHENYL)-2-METHYLANILINE": ("838-88-0", None),  # 3,3'-dimethylbenzidine
    "3,3'-DIMETHYLBENZIDINE": ("838-88-0", None),
    "PYRIDINE": ("110-86-1", _ATSDR["PYRIDINE"]),
    "NITROBENZENE": ("98-95-3", _ATSDR["NITROBENZENE"]),
    "1-PHENYLETHANONE": ("98-86-2", None),  # acetophenone
    "ACETOPHENONE": ("98-86-2", None),
    "9H-CARBAZOLE": ("86-74-8", None),
    "CARBAZOLE": ("86-74-8", None),
    "TETRAHYDROFURAN": ("109-99-9", None),
    "DIMETHYLFORMAMIDE": ("68-12-2", None),
    "DIMETHYL SULFIDE": ("75-18-3", None),
    "DIMETHYLMERCURY": ("593-74-8", _ATSDR["MERCURY"]),
    "BENZOIC ACID": ("65-85-0", None),
    "METHYL ACETATE": ("79-20-9", None),
    "METHYL 2-METHYLPROP-2-ENOATE": ("80-62-6", None),  # methyl methacrylate
    "METHYL METHACRYLATE": ("80-62-6", None),
    "ETHANOL": ("64-17-5", None),
    "2-PROPANOL": ("67-63-0", None),  # isopropanol
    "ISOPROPANOL": ("67-63-0", None),
    "METHANE": ("74-82-8", None),
    # ─────────────────────────────────────────────────────────────────────────
    # TPH and fuels - many are mixtures without discrete CAS; use PubChem name URLs
    # Note: Some use /compound/ (refchem entries), others use /substance/ (SID)
    # ─────────────────────────────────────────────────────────────────────────
    "TOTAL PETROLEUM HYDROCARBONS": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "TOTAL PETROLEUM HYDROCARBONS (TPH)": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "TOTAL RECOVERABLE PETROLEUM HYDROCARBONS": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "TOTAL RECOVERABLE PETROLEUM HYDROCARBONS (TRPH)": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "TPH": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "TRPH": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "GASOLINE": ("8006-61-9", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    "AUTOMOTIVE GASOLINE": ("8006-61-9", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    "DIESEL FUEL": ("68476-34-6", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "DIESEL": ("68476-34-6", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "DIESEL FUEL NO. 2": ("68476-34-6", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "DIESEL RANGE ORGANICS": ("N/A", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "DIESEL RANGE ORGANICS (DRO)": ("N/A", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "DRO": ("N/A", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Diesel-Fuel"),
    "KEROSENE": ("8008-20-6", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "KEROSENE (FUEL OIL NO. 1)": ("8008-20-6", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "FUEL OIL": ("N/A", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "FUEL OIL NO. 2": ("68476-30-2", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "FUEL OIL NO. 4": ("68476-31-3", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "FUEL OIL NO. 6": ("68553-00-4", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "HEATING OIL": ("68476-30-2", _ATSDR["FUEL OILS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Fuel-Oils"),
    "JET FUEL": ("N/A", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "JP-4": ("50815-00-4", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/compound/Kerosene"),
    "JP-5": ("N/A", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/substance/135356845"),  # Jet fuels JP-5
    "JP-8": ("N/A", _ATSDR["JET FUELS"], "https://pubchem.ncbi.nlm.nih.gov/substance/505788256"),  # Jet fuels JP-8
    "MINERAL OILS": ("8042-47-5", None, "https://pubchem.ncbi.nlm.nih.gov/compound/Mineral-oil"),
    "MINERAL OIL": ("8042-47-5", None, "https://pubchem.ncbi.nlm.nih.gov/compound/Mineral-oil"),
    "RESIDUAL RANGE ORGANICS": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "RESIDUAL RANGE ORGANICS (RRO)": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "RRO": ("N/A", _ATSDR["TPH"], "https://pubchem.ncbi.nlm.nih.gov/substance/135312467"),
    "GASOLINE RANGE ORGANICS": ("N/A", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    "GASOLINE RANGE ORGANICS (GRO)": ("N/A", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    "GRO": ("N/A", _ATSDR["GASOLINE"], "https://pubchem.ncbi.nlm.nih.gov/compound/Gasoline"),
    # ─────────────────────────────────────────────────────────────────────────
    # CFCs / Refrigerants / Freons (no ATSDR ToxFAQs available)
    # ─────────────────────────────────────────────────────────────────────────
    "DICHLORODIFLUOROMETHANE": ("75-71-8", None),  # Freon-12, CFC-12
    "TRICHLOROFLUOROMETHANE": ("75-69-4", None),  # Freon-11, CFC-11
    "CHLORODIFLUOROMETHANE": ("75-45-6", None),  # HCFC-22, R-22
    "1,1,2-TRICHLORO-1,2,2-TRIFLUOROETHANE": ("76-13-1", None),  # CFC-113
    # ─────────────────────────────────────────────────────────────────────────
    # Metal oxides and compounds (no specific ATSDR for oxide forms)
    # ─────────────────────────────────────────────────────────────────────────
    "ALUMINUM OXIDE": ("1344-28-1", None),  # Alumina
    "BERYLLIUM COMPOUNDS": ("N/A", _ATSDR["BERYLLIUM"]),  # Category; link to Be ToxFAQs
    "CHROMIUM COMPOUNDS": ("N/A", _ATSDR["CHROMIUM"]),  # Category
    "COPPER COMPOUNDS": ("N/A", _ATSDR["COPPER"]),  # Category
    "LEAD COMPOUNDS": ("N/A", _ATSDR["LEAD"]),  # Category
    "MERCURY COMPOUNDS": ("N/A", _ATSDR["MERCURY"]),  # Category
    "NICKEL COMPOUNDS": ("N/A", _ATSDR["NICKEL"]),  # Category
    "ZINC COMPOUNDS": ("N/A", _ATSDR["ZINC"]),  # Category
    # ─────────────────────────────────────────────────────────────────────────
    # Alkylbenzenes (no ATSDR ToxFAQs for these specific isomers)
    # ─────────────────────────────────────────────────────────────────────────
    "BUTAN-2-YLBENZENE": ("135-98-8", None),  # sec-butylbenzene
    "SEC-BUTYLBENZENE": ("135-98-8", None),
    "PROPYLBENZENE": ("103-65-1", None),  # n-propylbenzene
    "N-PROPYLBENZENE": ("103-65-1", None),
    "ISOPROPYLBENZENE": ("98-82-8", None),  # cumene
    "CUMENE": ("98-82-8", None),
    "P-CYMENE": ("99-87-6", None),  # 4-isopropyltoluene
    "BUTYLBENZENE": ("104-51-8", None),  # n-butylbenzene
    "N-BUTYLBENZENE": ("104-51-8", None),
    "TERT-BUTYLBENZENE": ("98-06-6", None),
    # ─────────────────────────────────────────────────────────────────────────
    # Xylenes (specific isomers and mixtures)
    # ─────────────────────────────────────────────────────────────────────────
    "XYLENE (MIXED ISOMERS)": ("1330-20-7", _ATSDR["XYLENES"]),
    "1,2-DIMETHYLBENZENE": ("95-47-6", _ATSDR["XYLENES"]),  # o-xylene
    "1,2-DIMETHYLBENZENE (O-XYLENE)": ("95-47-6", _ATSDR["XYLENES"]),  # o-xylene
    "1,3-DIMETHYLBENZENE": ("108-38-3", _ATSDR["XYLENES"]),  # m-xylene
    "1,3-DIMETHYLBENZENE (M-XYLENE)": ("108-38-3", _ATSDR["XYLENES"]),  # m-xylene
    "1,4-DIMETHYLBENZENE": ("106-42-3", _ATSDR["XYLENES"]),  # p-xylene
    "1,4-DIMETHYLBENZENE (P-XYLENE)": ("106-42-3", _ATSDR["XYLENES"]),  # p-xylene
    # ─────────────────────────────────────────────────────────────────────────
    # 1,2-Dichloroethene variants
    # ─────────────────────────────────────────────────────────────────────────
    "1,2-DICHLOROETHENE (CIS AND TRANS MIXTURE)": ("540-59-0", _ATSDR["1,2-DICHLOROETHENE"]),
    "1,2-DICHLOROETHENE (TOTAL)": ("540-59-0", _ATSDR["1,2-DICHLOROETHENE"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Inorganic ions
    # ─────────────────────────────────────────────────────────────────────────
    "SULFATE": ("14808-79-8", None),  # No ATSDR ToxFAQs
    "SULFIDE": ("18496-25-8", None),
    "CHLORIDE": ("16887-00-6", None),
    "PHOSPHATE": ("14265-44-2", None),
    # ─────────────────────────────────────────────────────────────────────────
    # Petroleum fractions (categories, no specific CAS)
    # ─────────────────────────────────────────────────────────────────────────
    "C5-C8 ALIPHATIC HYDROCARBONS": ("N/A", _ATSDR["TPH"]),
    "C5-C8 Aliphatic Hydrocarbons": ("N/A", _ATSDR["TPH"]),
    "C9-C10 AROMATIC HYDROCARBONS": ("N/A", _ATSDR["TPH"]),
    "C9-C10 Aromatic Hydrocarbons": ("N/A", _ATSDR["TPH"]),
    "C9-C12 ALIPHATIC HYDROCARBONS": ("N/A", _ATSDR["TPH"]),
    "C9-C12 Aliphatic Hydrocarbons": ("N/A", _ATSDR["TPH"]),
    "C9-C18 ALIPHATIC HYDROCARBONS": ("N/A", _ATSDR["TPH"]),
    "C11-C22 AROMATIC HYDROCARBONS": ("N/A", _ATSDR["TPH"]),
    "C11-C22 Aromatic Hydrocarbons": ("N/A", _ATSDR["TPH"]),
    # ─────────────────────────────────────────────────────────────────────────
    # Generic categories (no specific CAS)
    # ─────────────────────────────────────────────────────────────────────────
    "INORGANICS": ("N/A", None),
    "METALS": ("N/A", None),
    "VOC": ("N/A", None),
    "VOCS": ("N/A", None),
    "VOLATILE ORGANIC COMPOUNDS": ("N/A", None),
    "SEMIVOLATILE ORGANIC COMPOUNDS": ("N/A", None),
    "SVOCS": ("N/A", None),
    "PESTICIDES": ("N/A", None),
    "ORGANICS": ("N/A", None),
    "NOT PROVIDED": ("N/A", None),
    "UNEXPLODED ORDNANCE (UXO)": ("N/A", None),
    "UNEXPLODED ORDNANCE": ("N/A", None),
    "UXO": ("N/A", None),
    "RADIONUCLIDES": ("N/A", None),
    "BASE NEUTRAL ACIDS": ("N/A", None),
    "PHENAZOPYRIDINE": ("94-78-0", None),
    # ─────────────────────────────────────────────────────────────────────────
    # Generic category terms (no specific CAS; general information links)
    # ─────────────────────────────────────────────────────────────────────────
    "INORGANICS": ("N/A", None),  # Generic category; no single ATSDR
    "METALS": ("N/A", None),  # Generic category; individual metals have ATSDR
    "VOC": ("N/A", None),  # Volatile organic compounds category
    "VOCS": ("N/A", None),
    "VOLATILE ORGANIC COMPOUNDS": ("N/A", None),
    "SVOC": ("N/A", None),  # Semi-volatile organic compounds category
    "SVOCS": ("N/A", None),
    "SEMIVOLATILE ORGANIC COMPOUNDS": ("N/A", None),
    "PAH": ("N/A", _ATSDR["PAHS"]),  # Polycyclic aromatic hydrocarbons
    "PAHS": ("N/A", _ATSDR["PAHS"]),
    "ORGANICS": ("N/A", None),  # Generic category
    "PESTICIDES": ("N/A", None),  # Generic category
    "HERBICIDES": ("N/A", None),  # Generic category
}
