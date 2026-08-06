"""ATSDR ToxFAQs URL lookup by substance category.

Single-responsibility module: Maps chemical category names to their ATSDR ToxFAQs URLs.
Extracted from superfund_cas_lookup.py per SRP.

Source: CDC/ATSDR Toxic Substances Portal (scraped 2024 via scripts/scrape_atsdr_toxfaqs.py)
Verified against: scripts/atsdr_toxid_map.csv

URL format: https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=XXX&toxid=YY
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════
# ATSDR ToxFAQs URLs (verified from scripts/atsdr_toxid_map.csv)
# Format: https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=XXX&toxid=YY
# ═══════════════════════════════════════════════════════════════════════════════
ATSDR_URLS: dict[str, str] = {
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

# Backwards compatibility alias for existing imports
_ATSDR = ATSDR_URLS
