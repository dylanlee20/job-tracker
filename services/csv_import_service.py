"""Import jobs from the WhaleStreet job-scraper CSV into the local SQLite.

Replaces the 21 in-process bank scrapers. The WhaleStreet pipeline runs
on GitHub Actions, scrapes 349 firms daily, and writes
`services/job-scraper/jobs_finance.csv` to disk. This service reads
that CSV, groups rows by company, and calls the existing
`JobService.process_scraped_jobs(jobs, company)` so all the dedupe,
hash, and inactive-marking logic stays unchanged.

CSV path resolution order:
  1. JOBS_CSV_PATH env var
  2. ~/whalestreet/services/job-scraper/jobs_finance.csv
"""

from __future__ import annotations

import csv
import logging
import os
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from services.job_service import JobService

logger = logging.getLogger(__name__)


DEFAULT_CSV_PATH = Path.home() / "whalestreet" / "services" / "job-scraper" / "jobs_finance.csv"


def resolve_csv_path() -> Path:
    env = os.environ.get("JOBS_CSV_PATH")
    if env:
        return Path(env).expanduser()
    return DEFAULT_CSV_PATH


def _parse_post_date(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _row_to_job_dict(row: Dict[str, str]) -> Optional[Dict]:
    company = (row.get("company_name") or "").strip()
    title = (row.get("job_title") or "").strip()
    job_url = (row.get("job_url") or "").strip()
    if not company or not title or not job_url:
        return None
    if (row.get("scrape_status") or "").strip().lower() not in ("", "success"):
        return None
    return {
        "company": company,
        "title": title,
        "location": (row.get("location") or "").strip() or "Unknown",
        "description": "",
        "post_date": _parse_post_date(row.get("date_posted", "")),
        "deadline": None,
        "source_website": (row.get("source_url") or "").strip() or "whalestreet.ai",
        "job_url": job_url,
    }


class CSVImportService:
    """Singleton-style state mirrored from the old ScraperService API."""

    _progress = {
        "is_running": False,
        "current_company": None,
        "current_index": 0,
        "total_companies": 0,
        "completed_companies": [],
        "failed_companies": [],
        "start_time": None,
        "results": None,
    }
    _lock = threading.Lock()

    @classmethod
    def get_progress(cls):
        with cls._lock:
            return {
                "is_running": cls._progress["is_running"],
                "current_company": cls._progress["current_company"],
                "current_index": cls._progress["current_index"],
                "total_companies": cls._progress["total_companies"],
                "completed_companies": list(cls._progress["completed_companies"]),
                "failed_companies": list(cls._progress["failed_companies"]),
                "start_time": cls._progress["start_time"],
                "results": cls._progress["results"],
            }

    @classmethod
    def is_running(cls) -> bool:
        with cls._lock:
            return cls._progress["is_running"]

    @classmethod
    def _set(cls, **kwargs):
        with cls._lock:
            cls._progress.update(kwargs)

    @classmethod
    def _reset(cls):
        with cls._lock:
            cls._progress.update({
                "is_running": False,
                "current_company": None,
                "current_index": 0,
                "total_companies": 0,
                "completed_companies": [],
                "failed_companies": [],
                "start_time": None,
                "results": None,
            })

    @classmethod
    def _read_csv(cls, csv_path: Path) -> Dict[str, List[Dict]]:
        if not csv_path.is_file():
            raise FileNotFoundError(f"WhaleStreet CSV not found at {csv_path}")
        by_company: Dict[str, List[Dict]] = defaultdict(list)
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                job = _row_to_job_dict(row)
                if job is None:
                    continue
                by_company[job["company"]].append(job)
        return by_company

    @classmethod
    def get_available_companies(cls) -> List[str]:
        try:
            csv_path = resolve_csv_path()
            return sorted(cls._read_csv(csv_path).keys())
        except FileNotFoundError:
            return []

    @classmethod
    def import_all(cls, with_progress: bool = False) -> Dict:
        """Import every company's jobs from the CSV."""
        csv_path = resolve_csv_path()
        logger.info(f"Importing jobs from CSV: {csv_path}")
        by_company = cls._read_csv(csv_path)

        results = {"companies": {}, "summary": {
            "total_new": 0, "total_updated": 0, "total_inactive": 0,
            "successful_companies": 0,
        }}

        if with_progress:
            cls._set(
                is_running=True,
                current_company=None,
                current_index=0,
                total_companies=len(by_company),
                completed_companies=[],
                failed_companies=[],
                start_time=datetime.utcnow().isoformat(),
                results=None,
            )

        for index, (company, jobs) in enumerate(sorted(by_company.items()), start=1):
            if with_progress:
                cls._set(current_company=company, current_index=index)
            try:
                stats = JobService.process_scraped_jobs(jobs, company)
                results["companies"][company] = {"success": True, "stats": stats}
                results["summary"]["total_new"] += stats.get("new_jobs", 0)
                results["summary"]["total_updated"] += stats.get("updated_jobs", 0)
                results["summary"]["total_inactive"] += stats.get("inactive_jobs", 0)
                results["summary"]["successful_companies"] += 1
                if with_progress:
                    with cls._lock:
                        cls._progress["completed_companies"].append(company)
            except Exception as exc:
                logger.exception(f"Failed importing {company}: {exc}")
                results["companies"][company] = {"success": False, "error": str(exc)}
                if with_progress:
                    with cls._lock:
                        cls._progress["failed_companies"].append(company)

        if with_progress:
            cls._set(is_running=False, results=results)

        logger.info(
            f"CSV import complete. "
            f"new={results['summary']['total_new']} "
            f"updated={results['summary']['total_updated']} "
            f"inactive={results['summary']['total_inactive']} "
            f"firms={results['summary']['successful_companies']}/{len(by_company)}"
        )
        return results

    @classmethod
    def import_single_company(cls, company: str) -> Dict:
        csv_path = resolve_csv_path()
        by_company = cls._read_csv(csv_path)
        if company not in by_company:
            return {"success": False, "error": f"Company '{company}' not found in CSV"}
        try:
            stats = JobService.process_scraped_jobs(by_company[company], company)
            return {"success": True, "stats": stats}
        except Exception as exc:
            logger.exception(f"Failed importing {company}")
            return {"success": False, "error": str(exc)}

    @classmethod
    def run_async(cls, app=None) -> bool:
        """Kick off an import in a background thread; returns False if already running."""
        if cls.is_running():
            return False

        def worker():
            if app is not None:
                with app.app_context():
                    try:
                        cls.import_all(with_progress=True)
                    except Exception:
                        logger.exception("Async CSV import failed")
                        cls._set(is_running=False)
            else:
                try:
                    cls.import_all(with_progress=True)
                except Exception:
                    logger.exception("Async CSV import failed")
                    cls._set(is_running=False)

        thread = threading.Thread(target=worker, daemon=True, name="csv-import")
        thread.start()
        return True
