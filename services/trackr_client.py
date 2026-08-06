"""HTTP client for the-trackr.com's public programmes API.

Pure requests, no browser. One GET per tracker:

    GET https://api.the-trackr.com/programmes
        ?region=<Hong Kong|US|UK>&industry=Finance&season=2027&type=summer-internships

Returns the raw programme list; `normalize_programme` flattens each record
into the fields the megasheet and the daily stage email care about.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.the-trackr.com/programmes"
REQUEST_TIMEOUT = 30

# The three trackers the megasheet mirrors, in display order.
TRACKERS = [
    {"region": "Hong Kong", "season": "2027", "slug": "hong-kong-finance"},
    {"region": "US", "season": "2027", "slug": "us-finance-2027"},
    {"region": "UK", "season": "2027", "slug": "uk-finance"},
]

_UTM_RE = re.compile(r"(&|\?)(utm_[a-z]+|gh_src)=[^&]*")


def _strip_tracking(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    cleaned = _UTM_RE.sub("", url)
    # If the query string lost its leading "?", restore it.
    if "?" not in cleaned and "&" in cleaned:
        cleaned = cleaned.replace("&", "?", 1)
    return cleaned.rstrip("?&")


def _parse_iso_date(raw: Optional[str]) -> Optional[str]:
    """'2026-01-04T00:00:00.000Z' -> '2026-01-04' (None-safe)."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        logger.warning("trackr: unparseable date %r", raw)
        return None


def fetch_tracker(region: str, season: str) -> List[Dict]:
    """Fetch every programme for one tracker. Raises on HTTP errors."""
    params = {
        "region": region,
        "industry": "Finance",
        "season": season,
        "type": "summer-internships",
    }
    resp = requests.get(
        API_URL,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0 (megasheet-sync)"},
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError(f"trackr: unexpected payload for {region}: {type(data)}")
    logger.info("trackr: %s -> %d programmes", region, len(data))
    return data


def normalize_programme(raw: Dict, region: str) -> Optional[Dict]:
    """Flatten one raw API record into megasheet fields. Returns None if the
    record is missing the essentials (id, name, company)."""
    company = (raw.get("company") or {})
    company_name = (company.get("name") or "").strip()
    name = (raw.get("name") or "").strip()
    ext_id = (raw.get("id") or "").strip()
    if not (ext_id and name and company_name):
        logger.warning("trackr: skipping incomplete record %r", raw.get("id"))
        return None

    cities = [c for c in (raw.get("locations") or []) if c]
    return {
        "external_id": ext_id,
        "company": company_name,
        "position": name,
        "region": region,
        "cities": cities,
        "categories": [c for c in (raw.get("categories") or []) if c],
        "opening_date": _parse_iso_date(raw.get("openingDate")),
        "closing_date": _parse_iso_date(raw.get("closingDate")),
        "is_rolling": bool(raw.get("rolling")),
        "process": (raw.get("process") or "").strip() or None,
        "current_stage": (raw.get("currentStage") or "").strip() or None,
        "apply_url": _strip_tracking(raw.get("url")),
        "careers_site": _strip_tracking(company.get("careersSite")),
        "notes": (raw.get("notes") or "").strip() or None,
    }


def fetch_all() -> List[Dict]:
    """Fetch and normalize all three trackers, in display order."""
    out: List[Dict] = []
    for t in TRACKERS:
        for raw in fetch_tracker(t["region"], t["season"]):
            p = normalize_programme(raw, t["region"])
            if p:
                out.append(p)
    return out
