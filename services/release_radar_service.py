"""Release Radar service.

Builds the two lists the WhaleStreet 公众号 pipeline consumes:

  - Freshly Opened: SA / Summer Intern postings published in the last N days
    (default 3). The "申请通道刚开" news bulletin.

  - Interview Wave: front-office SA / Summer Intern postings whose application
    window opened 10+ days ago (default min=10, max=60). At this point firms
    are typically sending OAs / first-round invites, so this is the "OA + 面经"
    bulletin.

Sources merged into both lists:
  1. `data/release_radar.json` — curated, hand-maintained entries (top 50-80
     brand-name firms). Always authoritative when present.
  2. The `jobs` SQLite table populated by the WhaleStreet CSV ingestion. Used
     as a long-tail discovery channel — title/company/location are run through
     `utils/release_radar_utils` to derive sector + region + role + FO tags.

The service returns plain Python dicts ready for Jinja rendering; routes layer
adds filtering and grouping for the template.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from models.database import db
from models.job import Job
from utils.release_radar_utils import (
    derive_region,
    derive_sector,
    is_front_office,
    is_summer_internship,
)

logger = logging.getLogger(__name__)

RADAR_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "release_radar.json"


def _today() -> datetime:
    return datetime.utcnow()


def _load_curated() -> list[dict]:
    if not RADAR_JSON_PATH.exists():
        logger.warning("release_radar.json missing at %s", RADAR_JSON_PATH)
        return []
    try:
        with RADAR_JSON_PATH.open() as f:
            data = json.load(f)
        return data.get("events", [])
    except Exception:
        logger.exception("Failed to parse release_radar.json")
        return []


def _curated_to_event(raw: dict, source: str) -> dict:
    """Normalize a curated JSON row into the unified event shape."""
    return {
        "source": source,                                 # 'curated' or 'scraped'
        "firm": raw.get("firm"),
        "firm_cn": raw.get("firm_cn") or raw.get("firm"),
        "sector": raw.get("sector"),
        "subsector": raw.get("subsector"),
        "region": raw.get("region"),
        "role": raw.get("role"),
        "program_name": raw.get("program_name"),
        "front_office": bool(raw.get("front_office", False)),
        "post_date": raw.get("post_date"),
        "application_url": raw.get("application_url"),
        "source_url": raw.get("source_url"),
        "confidence": raw.get("confidence", "needs_verification"),
        "verified_date": raw.get("verified_date"),
        "notes": raw.get("notes"),
    }


def _scraped_to_event(job: Job) -> dict:
    sector, subsector = derive_sector(job.company)
    region = derive_region(job.location, job.job_url)
    return {
        "source": "scraped",
        "firm": job.company,
        "firm_cn": job.company,
        "sector": sector,
        "subsector": subsector,
        "region": region,
        "role": "SA" if "analyst" in (job.title or "").lower() else "SI",
        "program_name": job.title,
        "front_office": is_front_office(job.title, sector),
        "post_date": (job.post_date or job.first_seen).strftime("%Y-%m-%d")
        if (job.post_date or job.first_seen)
        else None,
        "application_url": job.job_url,
        "source_url": job.source_website,
        "confidence": "verified",
        "verified_date": job.last_seen.strftime("%Y-%m-%d") if job.last_seen else None,
        "notes": None,
    }


def _post_date_dt(event: dict) -> Optional[datetime]:
    raw = event.get("post_date")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _apply_filters(
    events: list[dict],
    region: Optional[str],
    sector: Optional[str],
) -> list[dict]:
    out = events
    if region and region != "ALL":
        out = [e for e in out if e.get("region") == region]
    if sector and sector != "ALL":
        out = [e for e in out if e.get("sector") == sector]
    return out


def get_freshly_opened(
    days: int = 3,
    region: Optional[str] = None,
    sector: Optional[str] = None,
) -> list[dict]:
    """Postings whose application window opened in the last `days` days.

    Includes both curated entries and scraped DB rows that pass the
    summer-internship filter.
    """
    cutoff = _today() - timedelta(days=days)
    curated = [_curated_to_event(r, "curated") for r in _load_curated()]
    curated_fresh = [e for e in curated if (_post_date_dt(e) or _today()) >= cutoff]

    # Scraped rows: filter to summer/intern titles, post_date or first_seen in window.
    try:
        rows = (
            Job.query.filter(
                Job.status == "active",
                Job.first_seen >= cutoff,
            )
            .all()
        )
        scraped = [_scraped_to_event(j) for j in rows if is_summer_internship(j.title)]
    except Exception:
        logger.exception("DB query failed in get_freshly_opened")
        scraped = []

    events = _apply_filters(curated_fresh + scraped, region, sector)
    events.sort(key=lambda e: e.get("post_date") or "", reverse=True)
    return events


def get_interview_wave(
    min_days: int = 10,
    max_days: int = 60,
    region: Optional[str] = None,
    sector: Optional[str] = None,
) -> list[dict]:
    """Front-office summer postings posted 10-60 days ago. Interview invites
    are likely being sent now, so this is the 'OA + 面试' bulletin.
    """
    now = _today()
    earliest = now - timedelta(days=max_days)
    latest = now - timedelta(days=min_days)

    curated = [_curated_to_event(r, "curated") for r in _load_curated()]
    curated_wave = []
    for e in curated:
        if not e.get("front_office"):
            continue
        pd = _post_date_dt(e)
        if pd and earliest <= pd <= latest:
            curated_wave.append(e)

    try:
        rows = (
            Job.query.filter(
                Job.status == "active",
                Job.first_seen >= earliest,
                Job.first_seen <= latest,
            )
            .all()
        )
        scraped = []
        for j in rows:
            if not is_summer_internship(j.title):
                continue
            ev = _scraped_to_event(j)
            if ev["front_office"]:
                scraped.append(ev)
    except Exception:
        logger.exception("DB query failed in get_interview_wave")
        scraped = []

    events = _apply_filters(curated_wave + scraped, region, sector)
    events.sort(key=lambda e: e.get("post_date") or "")
    return events


def group_by_sector_then_region(events: list[dict]) -> dict:
    """Convenience grouping for the template: { sector: { region: [events] } }."""
    out: dict[str, dict[str, list[dict]]] = {}
    for e in events:
        sec = e.get("sector") or "Other"
        reg = e.get("region") or "Other"
        out.setdefault(sec, {}).setdefault(reg, []).append(e)
    # stable ordering: Finance, Consulting, Tech, then alphabetical
    sector_order = ["Finance", "Consulting", "Tech"]
    return {
        sec: out[sec]
        for sec in sector_order + sorted(s for s in out if s not in sector_order)
        if sec in out
    }
