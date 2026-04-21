"""Deutsche Bank scraper — pure-HTTP against Workday CXS API.

Old scraper used `wait_for_element('.job, .vacancy, .position')` on the
students-graduates SPA landing page; those CSS classes never existed in the
live DOM, so every run returned 0 jobs since ~Feb 2026.

Real DB career data lives at db.wd3.myworkdayjobs.com. The public CXS
endpoint `/wday/cxs/db/DBWebsite/jobs` accepts POST JSON with facet filters
and returns paginated JSON. workerSubType facets let us narrow to
campus-track roles (Interns / Graduate Trainees / Apprentices) directly.
"""
import time
import requests

from scrapers.base_scraper import BaseScraper
from config import Config


_CXS_URL = "https://db.wd3.myworkdayjobs.com/wday/cxs/db/DBWebsite/jobs"
_SITE_BASE = "https://db.wd3.myworkdayjobs.com/DBWebsite"

# worker sub-type facet IDs from the DB Workday tenant.
# Interns / Practical Work Exp. / Graduate Trainees / Apprentices.
_CAMPUS_WORKER_SUBTYPES = [
    "645e861bc53a01f8c083feaefb3a1c09",
    "645e861bc53a0145cdb4feaefb3a1d09",
    "645e861bc53a018fc2809ac3fb3a9444",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://db.wd3.myworkdayjobs.com",
    "Referer": _SITE_BASE + "/en-US/DBWebsite",
}


class DeutscheBankScraper(BaseScraper):
    """Deutsche Bank — global campus/intern/graduate jobs via Workday CXS."""

    def __init__(self):
        super().__init__(
            company_name="Deutsche Bank",
            source_url=_SITE_BASE + "/en-US/DBWebsite",
        )
        self.session = requests.Session()
        self.session.headers.update(_HEADERS)

    def scrape_with_retry(self, max_retries=None):
        if max_retries is None:
            max_retries = Config.SCRAPER_RETRY_COUNT
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Starting scrape for {self.company_name} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                jobs = self.scrape_jobs()
                self.logger.info(
                    f"Successfully scraped {len(jobs)} jobs from {self.company_name}"
                )
                return jobs
            except Exception as e:
                self.logger.error(
                    f"Scrape failed for {self.company_name} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(5)
        return []

    def _post_query(self, offset: int, limit: int = 20) -> dict:
        payload = {
            "appliedFacets": {"workerSubType": _CAMPUS_WORKER_SUBTYPES},
            "limit": limit,
            "offset": offset,
            "searchText": "",
        }
        resp = self.session.post(_CXS_URL, json=payload, timeout=Config.SCRAPER_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def scrape_jobs(self):
        all_jobs = []
        limit = 20
        offset = 0
        total = None
        # cap pagination to avoid infinite loops on unexpected API behavior
        max_offset = 500

        while offset <= max_offset:
            data = self._post_query(offset=offset, limit=limit)

            if total is None:
                total = int(data.get("total", 0))
                self.logger.info(f"DB Workday reports {total} campus-track jobs")
                if total == 0:
                    break

            postings = data.get("jobPostings", []) or []
            if not postings:
                break

            for p in postings:
                try:
                    title = (p.get("title") or "").strip()
                    if not title:
                        continue
                    location = (p.get("locationsText") or "").strip()
                    ext_path = p.get("externalPath") or ""
                    job_url = _SITE_BASE + ext_path if ext_path else ""
                    post_date = p.get("postedOn") or None

                    all_jobs.append({
                        "company": self.company_name,
                        "title": title,
                        "location": location,
                        "description": "Campus track: Intern / Graduate / Apprentice",
                        "post_date": post_date,
                        "deadline": None,
                        "source_website": self.source_url,
                        "job_url": job_url,
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing DB job posting: {e}")
                    continue

            offset += limit
            if offset >= total:
                break
            time.sleep(0.5)

        self.logger.info(
            f"Completed scraping {len(all_jobs)} DB campus-track jobs "
            f"(reported total {total})"
        )
        return all_jobs
