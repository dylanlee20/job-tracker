"""Pure helpers for the release-radar feature.

Derives region / sector / role / front-office tags from raw text fields so
the WhaleStreet pipeline can filter scraped CSV rows by the same dimensions
as the curated `data/release_radar.json` entries.

No DB / Flask dependencies — safe to import from anywhere.
"""

from __future__ import annotations

from typing import Optional


REGION_US_KEYWORDS = (
    "new york", "ny-", "ny,", " ny ", "nyc", "manhattan",
    "san francisco", "sf-", "sf,", "sf bay", "palo alto", "mountain view",
    "chicago", "chi-", "chi,",
    "houston", "boston", "los angeles", "seattle", "atlanta", "dallas",
    "washington dc", "washington, dc", "d.c.", "miami", "charlotte",
    "philadelphia", "san jose", "menlo park", "cupertino", "redmond",
    "united states", "usa", "u.s.", "us-", " us,",
)
REGION_UK_KEYWORDS = (
    "london", "uk", "u.k.", "united kingdom", "england",
    "canary wharf", "city of london", "edinburgh", "manchester",
)
REGION_HK_KEYWORDS = (
    "hong kong", "hong-kong", "hongkong", "hksar", "hk sar",
    " hk,", " hk-", "hk ", "kowloon", "central, hk",
)
REGION_MULTI_HINTS = (
    "multiple", "various", "4 locations", "3 locations",
    "2 locations", "5 locations", "remote", "anywhere",
)


def derive_region(location: Optional[str], url: Optional[str] = None) -> str:
    """Return one of: 'US', 'UK', 'HK', 'MULTI', 'OTHER'.

    Precedence: explicit HK > explicit UK > explicit US > multi > other.
    HK first so 'Hong Kong' beats a stray 'kong' substring elsewhere; UK
    before US so 'London, United Kingdom' is not stolen by the 'United' in
    'United States' (it isn't — 'united states' is the keyword — but defense
    in depth is cheap).
    """
    haystack = " ".join(filter(None, [location or "", url or ""])).lower()
    if not haystack.strip():
        return "OTHER"

    if any(k in haystack for k in REGION_HK_KEYWORDS):
        return "HK"
    if any(k in haystack for k in REGION_UK_KEYWORDS):
        return "UK"
    if any(k in haystack for k in REGION_US_KEYWORDS):
        return "US"
    if any(k in haystack for k in REGION_MULTI_HINTS):
        return "MULTI"
    return "OTHER"


# Firm -> (sector, subsector). Keep finance-leaning since most scraped CSV
# rows are banks; consulting + tech enter via the curated JSON file.
SECTOR_MAP = {
    # Bulge brackets
    "goldman sachs": ("Finance", "Bulge Bracket"),
    "jpmorgan": ("Finance", "Bulge Bracket"),
    "jp morgan": ("Finance", "Bulge Bracket"),
    "morgan stanley": ("Finance", "Bulge Bracket"),
    "bank of america": ("Finance", "Bulge Bracket"),
    "bofa": ("Finance", "Bulge Bracket"),
    "citi": ("Finance", "Bulge Bracket"),
    "citigroup": ("Finance", "Bulge Bracket"),
    "barclays": ("Finance", "Bulge Bracket"),
    "ubs": ("Finance", "Bulge Bracket"),
    "deutsche bank": ("Finance", "Bulge Bracket"),
    "hsbc": ("Finance", "Bulge Bracket"),
    "wells fargo": ("Finance", "Bulge Bracket"),
    "mizuho": ("Finance", "Bulge Bracket"),
    "nomura": ("Finance", "Bulge Bracket"),
    "bnp paribas": ("Finance", "Bulge Bracket"),
    "socgen": ("Finance", "Bulge Bracket"),
    "mufg": ("Finance", "Bulge Bracket"),
    "smbc": ("Finance", "Bulge Bracket"),
    "rbc": ("Finance", "Bulge Bracket"),
    "bmo": ("Finance", "Bulge Bracket"),
    "macquarie": ("Finance", "Bulge Bracket"),
    # EBs
    "evercore": ("Finance", "Elite Boutique"),
    "lazard": ("Finance", "Elite Boutique"),
    "centerview": ("Finance", "Elite Boutique"),
    "moelis": ("Finance", "Elite Boutique"),
    "pjt partners": ("Finance", "Elite Boutique"),
    "guggenheim": ("Finance", "Elite Boutique"),
    "perella weinberg": ("Finance", "Elite Boutique"),
    "houlihan lokey": ("Finance", "Elite Boutique"),
    "greenhill": ("Finance", "Elite Boutique"),
    "rothschild": ("Finance", "Elite Boutique"),
    "qatalyst": ("Finance", "Elite Boutique"),
    # Middle market
    "jefferies": ("Finance", "Middle Market"),
    "piper sandler": ("Finance", "Middle Market"),
    "stifel": ("Finance", "Middle Market"),
    "raymond james": ("Finance", "Middle Market"),
    "william blair": ("Finance", "Middle Market"),
    "td cowen": ("Finance", "Middle Market"),
    "baird": ("Finance", "Middle Market"),
    "lincoln international": ("Finance", "Middle Market"),
    "harris williams": ("Finance", "Middle Market"),
    # PE
    "blackstone": ("Finance", "PE"),
    "kkr": ("Finance", "PE"),
    "carlyle": ("Finance", "PE"),
    "apollo": ("Finance", "PE"),
    "tpg": ("Finance", "PE"),
    "bain capital": ("Finance", "PE"),
    "warburg pincus": ("Finance", "PE"),
    "vista": ("Finance", "PE"),
    "silver lake": ("Finance", "PE"),
    "thoma bravo": ("Finance", "PE"),
    "h&f": ("Finance", "PE"),
    "permira": ("Finance", "PE"),
    "cvc": ("Finance", "PE"),
    "eqt": ("Finance", "PE"),
    "brookfield": ("Finance", "PE"),
    "ares": ("Finance", "PE"),
    # HF
    "citadel": ("Finance", "HF"),
    "millennium": ("Finance", "HF"),
    "point72": ("Finance", "HF"),
    "de shaw": ("Finance", "HF"),
    "two sigma": ("Finance", "HF"),
    "renaissance": ("Finance", "HF"),
    "bridgewater": ("Finance", "HF"),
    "aqr": ("Finance", "HF"),
    "balyasny": ("Finance", "HF"),
    "exoduspoint": ("Finance", "HF"),
    "brevan howard": ("Finance", "HF"),
    "marshall wace": ("Finance", "HF"),
    "schonfeld": ("Finance", "HF"),
    # Quant
    "jane street": ("Finance", "Quant"),
    "hudson river": ("Finance", "Quant"),
    "hrt": ("Finance", "Quant"),
    "jump trading": ("Finance", "Quant"),
    "tower research": ("Finance", "Quant"),
    "optiver": ("Finance", "Quant"),
    "imc": ("Finance", "Quant"),
    "sig": ("Finance", "Quant"),
    "drw": ("Finance", "Quant"),
    "flow traders": ("Finance", "Quant"),
    "akuna": ("Finance", "Quant"),
    "five rings": ("Finance", "Quant"),
    "citadel securities": ("Finance", "Quant"),
    # AM
    "blackrock": ("Finance", "Asset Management"),
    "vanguard": ("Finance", "Asset Management"),
    "fidelity": ("Finance", "Asset Management"),
    "capital group": ("Finance", "Asset Management"),
    "t. rowe price": ("Finance", "Asset Management"),
    "pimco": ("Finance", "Asset Management"),
    "wellington": ("Finance", "Asset Management"),
    "invesco": ("Finance", "Asset Management"),
    # Consulting
    "mckinsey": ("Consulting", "MBB"),
    "bain": ("Consulting", "MBB"),
    "bcg": ("Consulting", "MBB"),
    "boston consulting group": ("Consulting", "MBB"),
    "deloitte": ("Consulting", "Big 4"),
    "pwc": ("Consulting", "Big 4"),
    "ey ": ("Consulting", "Big 4"),
    "ernst & young": ("Consulting", "Big 4"),
    "kpmg": ("Consulting", "Big 4"),
    "oliver wyman": ("Consulting", "Tier 2 Strategy"),
    "roland berger": ("Consulting", "Tier 2 Strategy"),
    "strategy&": ("Consulting", "Tier 2 Strategy"),
    "kearney": ("Consulting", "Tier 2 Strategy"),
    "l.e.k.": ("Consulting", "Tier 2 Strategy"),
    "parthenon": ("Consulting", "Tier 2 Strategy"),
    "accenture": ("Consulting", "Tier 2 Strategy"),
    # Tech
    "google": ("Tech", "FAANG"),
    "meta": ("Tech", "FAANG"),
    "facebook": ("Tech", "FAANG"),
    "apple": ("Tech", "FAANG"),
    "amazon": ("Tech", "FAANG"),
    "microsoft": ("Tech", "FAANG"),
    "netflix": ("Tech", "FAANG"),
    "stripe": ("Tech", "Top Tech"),
    "openai": ("Tech", "Top Tech"),
    "anthropic": ("Tech", "Top Tech"),
    "databricks": ("Tech", "Top Tech"),
    "snowflake": ("Tech", "Top Tech"),
    "nvidia": ("Tech", "Top Tech"),
    "tesla": ("Tech", "Top Tech"),
    "uber": ("Tech", "Top Tech"),
    "airbnb": ("Tech", "Top Tech"),
}


def derive_sector(company: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Return (sector, subsector) tuple, or (None, None) if no match."""
    if not company:
        return (None, None)
    lc = company.lower().strip()
    for key, val in SECTOR_MAP.items():
        if key in lc:
            return val
    return (None, None)


SUMMER_KEYWORDS = (
    "summer analyst", "summer associate", "summer intern",
    "summer consultant", "summer program", "summer placement",
    "sa20", "sa26", "sa27", "sa28",
    "intern,", "intern -", "internship",
    "industrial placement",
)


def is_summer_internship(title: Optional[str]) -> bool:
    if not title:
        return False
    t = title.lower()
    return any(k in t for k in SUMMER_KEYWORDS)


FRONT_OFFICE_KEYWORDS = {
    "Finance": (
        "investment banking", "ibd", "m&a", "mergers",
        "sales & trading", "sales and trading", "s&t",
        "equity research", "fixed income research", "credit research",
        "private equity", "growth equity", "buyout",
        "hedge fund", "investment associate", "investment analyst",
        "quant", "quantitative", "trading", "trader",
        "portfolio", "structuring", "derivatives",
        "capital markets", "ecm", "dcm", "lev fin",
    ),
    "Consulting": (
        "consulting", "consultant", "associate consultant", "business analyst",
        "strategy", "management consultant",
    ),
    "Tech": (
        "software engineer", "swe", "software developer",
        "product manager", "pm,", "pm -",
        "data scientist", "machine learning", "ml engineer", "mle",
        "research engineer", "research scientist",
        "applied scientist", "research intern",
        "hardware engineer", "ios", "android",
        "infrastructure engineer", "platform engineer",
    ),
}

BACK_OFFICE_HINTS = (
    "operations", "ops -", "compliance", "audit", "risk",
    "human resources", "hr ", "marketing", "communications",
    "legal", "tax", "internal audit", "facilities",
)


def is_front_office(title: Optional[str], sector: Optional[str]) -> bool:
    if not title:
        return False
    t = title.lower()
    if any(k in t for k in BACK_OFFICE_HINTS):
        return False
    if not sector:
        # Sector unknown: treat as front-office if title has any of the
        # finance/tech/consulting positive keywords.
        all_kw = (
            FRONT_OFFICE_KEYWORDS["Finance"]
            + FRONT_OFFICE_KEYWORDS["Consulting"]
            + FRONT_OFFICE_KEYWORDS["Tech"]
        )
        return any(k in t for k in all_kw)
    return any(k in t for k in FRONT_OFFICE_KEYWORDS.get(sector, ()))
