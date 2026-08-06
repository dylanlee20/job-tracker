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
    """Upsert every megasheet role into the jobs table, then clear DB rows
    that dropped out of the CSV (their user state migrates to the matching
    new row by external_id when possible). Returns counts."""
    firms = load_firms()
    roles = load_roles()

    created = updated = skipped = 0
    now = datetime.utcnow()
    seen_hashes = set()

    for row in roles:
        company = row["company"].strip()
        position = row["position"].strip()
        location = (row.get("location") or "").strip() or "Various"
        region = (row.get("region") or "").strip() or "Other"
        process = (row.get("process") or "").strip() or None
        current_stage = (row.get("current_stage") or "").strip() or None
        apply_url = (row.get("apply_url") or "").strip() or None
        firm = firms.get(company, {})
        if not firm:
            logger.warning("megasheet: firm %r missing from firms.json — using fallbacks", company)

        job_hash = Job.generate_job_hash(company, position, location)
        seen_hashes.add(job_hash)
        deadline = _parse_date(row.get("deadline", ""))
        is_rolling = _parse_bool(row.get("is_rolling", ""))
        post_date = _parse_date(row.get("date_added", ""))
        job_url = apply_url or firm.get("careers_url") or \
            "https://www.google.com/search?q=" + \
            "+".join(f"{company} {position} careers".split())
        recruiting_window = firm.get("recruiting_window")
        industry = firm.get("sector") or "Other"
        external_id = (row.get("external_id") or "").strip() or None

        existing = Job.query.filter_by(job_hash=job_hash).first()
        if existing:
            # Refresh megasheet-managed fields only; keep user application state.
            existing.title = position
            existing.location = location
            existing.region = region
            existing.process = process
            existing.current_stage = current_stage
            existing.deadline = deadline
            existing.is_rolling = is_rolling
            existing.external_id = external_id
            existing.recruiting_window = recruiting_window
            existing.post_date = post_date
            existing.job_url = job_url
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
                region=region,
                process=process,
                current_stage=current_stage,
                category="Other",
                industry=industry,
                description="",
                post_date=post_date,
                deadline=deadline,
                is_rolling=is_rolling,
                external_id=external_id,
                recruiting_window=recruiting_window,
                source_website=SOURCE_TAG,
                job_url=job_url,
                status="active",
                first_seen=post_date or now,
                last_seen=now,
                last_updated=now,
            ))
            created += 1

    db.session.flush()
    removed = _clear_dropped_rows(seen_hashes)

    db.session.commit()
    logger.info("megasheet import: %d created, %d updated, %d skipped, %d cleared",
                created, updated, skipped, removed)
    return {"created": created, "updated": updated, "skipped": skipped,
            "removed": removed, "total": len(roles)}


def _clear_dropped_rows(seen_hashes: set) -> int:
    """Delete megasheet DB rows no longer present in the CSV. Before deleting,
    migrate any user application state to the replacement row that shares the
    same external_id (location/title edits on trackr change the job_hash)."""
    import re

    def norm(s):
        return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

    live = [j for j in Job.query.filter_by(source_website=SOURCE_TAG).all()
            if j.job_hash in seen_hashes]
    stale = [j for j in Job.query.filter_by(source_website=SOURCE_TAG).all()
             if j.job_hash not in seen_hashes]
    by_key = {(norm(j.company), norm(j.title)): j for j in live}
    removed = 0
    for old in stale:
        heir = None
        if old.external_id:
            heir = next((j for j in live if j.external_id == old.external_id), None)
        if heir is None:
            heir = by_key.get((norm(old.company), norm(old.title)))
        if heir is not None:
            if old.application_submitted and not heir.application_submitted:
                heir.application_submitted = True
                heir.application_date = old.application_date
                heir.application_result = old.application_result
                heir.result_date = old.result_date
                heir.result_notes = old.result_notes
                heir.is_important = heir.is_important or old.is_important
                heir.user_notes = heir.user_notes or old.user_notes
        logger.info("megasheet: clearing dropped row %s - %s (%s)",
                    old.company, old.title, old.location)
        db.session.delete(old)
        removed += 1
    return removed


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
