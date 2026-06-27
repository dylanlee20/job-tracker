"""Import the curated megasheet (firms.json + roles.csv) into the jobs table.

The megasheet is a hand-curated list of full-time analyst / graduate programs
(2026–2027 classes) from a trusted source. It carries data the automated CSV
scraper cannot: real application deadlines, a stable source role id, the firm's
organic careers URL, and the firm's annual recruiting window.

These firms (Citadel, Jane Street, Point72, Apollo, Warburg Pincus, ...) are
mostly robots-blocked or have no scrapable ATS, so they are maintained here as
data rather than scraped. Refresh by editing the two files and re-running:

    python3 -m services.megasheet_import_service        # or import_all()

Idempotent: rows are matched by job_hash (company + position + location).
User state (application_submitted, is_important, notes, result) is preserved
on update; only megasheet-managed fields are refreshed.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models.database import db
from models.job import Job

logger = logging.getLogger(__name__)

MEGASHEET_DIR = Path(__file__).resolve().parent.parent / "data" / "megasheet"
FIRMS_PATH = MEGASHEET_DIR / "firms.json"
ROLES_PATH = MEGASHEET_DIR / "roles.csv"

SOURCE_TAG = "megasheet"


def _parse_date(raw: str) -> Optional[datetime]:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        logger.warning("megasheet: unparseable date %r — ignoring", raw)
        return None


def _parse_bool(raw: str) -> bool:
    return (raw or "").strip().lower() in ("true", "1", "yes", "y")


def load_firms() -> Dict[str, Dict]:
    with open(FIRMS_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_roles() -> List[Dict]:
    rows: List[Dict] = []
    with open(ROLES_PATH, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            company = (row.get("company") or "").strip()
            position = (row.get("position") or "").strip()
            if not company or not position:
                continue
            rows.append(row)
    return rows


def import_all() -> Dict[str, int]:
    """Upsert every megasheet role into the jobs table. Returns counts."""
    firms = load_firms()
    roles = load_roles()

    created = updated = skipped = 0
    now = datetime.utcnow()

    for row in roles:
        company = row["company"].strip()
        position = row["position"].strip()
        location = (row.get("location") or "").strip() or "Various"
        firm = firms.get(company, {})
        if not firm:
            logger.warning("megasheet: firm %r missing from firms.json — using fallbacks", company)

        job_hash = Job.generate_job_hash(company, position, location)
        deadline = _parse_date(row.get("deadline", ""))
        is_rolling = _parse_bool(row.get("is_rolling", ""))
        post_date = _parse_date(row.get("date_added", ""))
        careers_url = firm.get("careers_url") or "https://www.google.com/search?q=" + \
            "+".join(f"{company} {position} careers".split())
        recruiting_window = firm.get("recruiting_window")
        industry = firm.get("sector") or "Other"
        external_id = (row.get("external_id") or "").strip() or None

        existing = Job.query.filter_by(job_hash=job_hash).first()
        if existing:
            # Refresh megasheet-managed fields only; keep user application state.
            existing.title = position
            existing.location = location
            existing.deadline = deadline
            existing.is_rolling = is_rolling
            existing.external_id = external_id
            existing.recruiting_window = recruiting_window
            existing.post_date = post_date
            existing.job_url = careers_url
            existing.source_website = SOURCE_TAG
            existing.industry = industry
            existing.status = "active"
            existing.last_seen = now
            existing.last_updated = now
            updated += 1
        else:
            db.session.add(Job(
                job_hash=job_hash,
                company=company,
                title=position,
                location=location,
                category="Other",
                industry=industry,
                description="",
                post_date=post_date,
                deadline=deadline,
                is_rolling=is_rolling,
                external_id=external_id,
                recruiting_window=recruiting_window,
                source_website=SOURCE_TAG,
                job_url=careers_url,
                status="active",
                first_seen=post_date or now,
                last_seen=now,
                last_updated=now,
            ))
            created += 1

    db.session.commit()
    logger.info("megasheet import: %d created, %d updated, %d skipped",
                created, updated, skipped)
    return {"created": created, "updated": updated, "skipped": skipped,
            "total": len(roles)}


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logging.basicConfig(level=logging.INFO)
    from app import create_app

    app, _ = create_app()
    with app.app_context():
        result = import_all()
        print(f"Megasheet import: {result}")
