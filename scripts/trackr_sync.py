"""Sync the megasheet data files from the-trackr.com.

Rebuilds data/megasheet/roles.csv from the three live trackers
(Hong Kong / US / UK finance summer internships), keeps legacy hand-curated
rows that do not overlap a trackr programme, and merges any new firms into
data/megasheet/firms.json.

    python3 scripts/trackr_sync.py               # rewrite the CSV + firms.json
    python3 scripts/trackr_sync.py --import-db   # ...then upsert into jobs.db

CSV schema (superset of the original; the importer reads both):
    external_id, company, position, region, location,
    date_added, deadline, is_rolling, process, current_stage, apply_url
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.trackr_client import fetch_all  # noqa: E402

logger = logging.getLogger(__name__)

MEGASHEET_DIR = Path(__file__).resolve().parent.parent / "data" / "megasheet"
ROLES_PATH = MEGASHEET_DIR / "roles.csv"
FIRMS_PATH = MEGASHEET_DIR / "firms.json"

FIELDNAMES = [
    "external_id", "company", "position", "region", "location",
    "date_added", "deadline", "is_rolling", "process", "current_stage",
    "apply_url",
]

# Map a programme's first trackr category to a firms.json sector label.
CATEGORY_SECTOR = {
    "Bulge Bracket": "Bank - Bulge Bracket",
    "Elite Boutique": "Bank - Elite Boutique",
    "Middle Market": "Bank - Middle Market",
    "Buy-Side": "Buy-Side",
    "Asset Management": "Asset Management",
    "Trading and Quant": "Trading / Quant",
    "Big 4": "Big 4",
    "Consulting": "Consulting",
    "Real Estate": "Real Estate",
    "Pensions and Insurance": "Pensions / Insurance",
    "Accounting and Audit": "Accounting / Audit",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _load_existing_rows() -> List[Dict]:
    if not ROLES_PATH.exists():
        return []
    with open(ROLES_PATH, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _programme_location(p: Dict) -> str:
    """Region-first location string, e.g. 'US - Chicago / New York'."""
    if p["cities"]:
        return f"{p['region']} - " + " / ".join(p["cities"][:4])
    return p["region"]


def build_rows(programmes: List[Dict]) -> List[Dict]:
    rows = []
    for p in programmes:
        rows.append({
            "external_id": p["external_id"],
            "company": p["company"],
            "position": p["position"],
            "region": p["region"],
            "location": _programme_location(p),
            "date_added": p["opening_date"] or "",
            "deadline": p["closing_date"] or "",
            "is_rolling": "true" if p["is_rolling"] else "false",
            "process": p["process"] or "",
            "current_stage": p["current_stage"] or "",
            "apply_url": p["apply_url"] or "",
        })
    return rows


def keep_legacy_rows(existing: List[Dict], programmes: List[Dict]) -> List[Dict]:
    """Legacy hand-curated rows survive unless a trackr programme overlaps
    them (same normalized company + position). Overlapping ones are cleared,
    since the trackr version supersedes them."""
    trackr_keys = {(_norm(p["company"]), _norm(p["position"])) for p in programmes}
    trackr_ids = {p["external_id"] for p in programmes}

    kept, cleared = [], []
    for row in existing:
        ext = (row.get("external_id") or "").strip()
        key = (_norm(row.get("company", "")), _norm(row.get("position", "")))
        if ext in trackr_ids or key in trackr_keys:
            cleared.append(row)
            continue
        kept.append({
            "external_id": ext,
            "company": row.get("company", "").strip(),
            "position": row.get("position", "").strip(),
            "region": (row.get("region") or "Other").strip() or "Other",
            "location": (row.get("location") or "Various").strip(),
            "date_added": row.get("date_added", ""),
            "deadline": row.get("deadline", ""),
            "is_rolling": row.get("is_rolling", "false"),
            "process": row.get("process", ""),
            "current_stage": row.get("current_stage", ""),
            "apply_url": row.get("apply_url", ""),
        })
    for row in cleared:
        logger.info("cleared overlapping legacy row: %s - %s",
                    row.get("company"), row.get("position"))
    logger.info("legacy rows: %d kept, %d cleared as overlapping",
                len(kept), len(cleared))
    return kept


def merge_firms(programmes: List[Dict]) -> Dict[str, int]:
    """Add any firm the trackers mention that firms.json does not know yet.
    Existing entries are never modified (they may be hand-tuned)."""
    with open(FIRMS_PATH, "r", encoding="utf-8") as fh:
        firms = json.load(fh)

    added = 0
    for p in programmes:
        if p["company"] in firms:
            continue
        sector = "Other"
        for cat in p["categories"]:
            if cat in CATEGORY_SECTOR:
                sector = CATEGORY_SECTOR[cat]
                break
        window = None
        if p["opening_date"]:
            from datetime import datetime
            opened = datetime.strptime(p["opening_date"], "%Y-%m-%d")
            window = f"Opened {opened.strftime('%b %Y')} (2027 cycle)"
        firms[p["company"]] = {
            "careers_url": p["careers_site"] or p["apply_url"] or "",
            "sector": sector,
            "recruiting_window": window,
        }
        added += 1

    new_firms = {"_README": firms.pop("_README", "")}
    new_firms.update(dict(sorted(firms.items())))
    with open(FIRMS_PATH, "w", encoding="utf-8") as fh:
        json.dump(new_firms, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    logger.info("firms.json: %d new firms added (total %d)", added, len(firms))
    return {"added": added, "total": len(firms)}


def sync() -> Dict[str, int]:
    programmes = fetch_all()
    if len(programmes) < 100:
        raise RuntimeError(
            f"trackr returned only {len(programmes)} programmes across all "
            "trackers; refusing to overwrite roles.csv with a suspicious "
            "payload")

    existing = _load_existing_rows()
    legacy = keep_legacy_rows(existing, programmes)
    rows = build_rows(programmes) + legacy

    with open(ROLES_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    firm_stats = merge_firms(programmes)
    logger.info("roles.csv rewritten: %d trackr rows + %d legacy rows",
                len(programmes), len(legacy))
    return {"trackr": len(programmes), "legacy": len(legacy),
            "firms_added": firm_stats["added"]}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-db", action="store_true",
                        help="also upsert the refreshed CSV into jobs.db")
    args = parser.parse_args()

    stats = sync()
    print(f"Sync complete: {stats}")

    if args.import_db:
        from app import create_app
        from services.megasheet_import_service import import_all

        app, _ = create_app()
        with app.app_context():
            result = import_all()
            print(f"DB import: {result}")
