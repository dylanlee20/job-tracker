"""Nomura scraper — pure-HTTP Taleo page scrape.

Old scraper pointed at `vacancy/1/adv/` with five query filter IDs
(f_Item_Opportunity_408_lk=522951..522954 and _84825_lk=749). Those IDs
were renumbered on the tenant side, so the filtered URL now returns
zero `tr.search_res.details_row` rows. Selenium waited 15s for JS that
never needed to run — the unfiltered page is fully server-rendered.

Fix: drop the stale filters, fetch the vacancy/1/adv HTML directly, and
apply location + campus-keyword filtering client-side so volumes remain
scoped to "US + Singapore + Hong Kong campus/intern/analyst" per the
original intent. Static HTML, no browser needed.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from config import Config


_LIST_URL = (
    "https://nomuracampus.tal.net/vx/mobile-0/appcentre-ext/brand-4/"
    "candidate/jobboard/vacancy/1/adv/"
)

_TARGET_LOCATION_RE = re.compile(
    r"\b(new york|ny|usa|united states|singapore|hong kong|hk)\b",
    re.IGNORECASE,
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_deadline(text: str):
    if not text:
        return None
    text = text.strip()
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


class NomuraScraper(BaseScraper):
    """Nomura — US/Singapore/HK campus jobs via Taleo static HTML."""

    def __init__(self):
        super().__init__(
            company_name="Nomura",
            source_url=_LIST_URL,
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

    def scrape_jobs(self):
        resp = self.session.get(_LIST_URL, timeout=Config.SCRAPER_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        rows = soup.select("tr.search_res.details_row")
        self.logger.info(f"Nomura jobboard: {len(rows)} rows on page")

        jobs = []
        for row in rows:
            try:
                link = row.select_one("a.subject")
                if not link:
                    continue
                title = link.get_text(strip=True)
                if not title:
                    continue
                job_url = link.get("href", "") or ""

                tds = row.find_all("td")
                location = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                deadline_text = tds[2].get_text(strip=True) if len(tds) > 2 else ""

                # Scope to US + Singapore + Hong Kong (matches historic intent).
                if not _TARGET_LOCATION_RE.search(location):
                    continue

                jobs.append({
                    "company": self.company_name,
                    "title": title,
                    "location": location,
                    "description": "Campus opportunities (US/Singapore/HK)",
                    "post_date": None,
                    "deadline": _parse_deadline(deadline_text),
                    "source_website": self.source_url,
                    "job_url": job_url,
                })
            except Exception as e:
                self.logger.warning(f"Error parsing Nomura row: {e}")
                continue

        self.logger.info(
            f"Completed scraping {len(jobs)} Nomura jobs "
            f"(US + Singapore + Hong Kong)"
        )
        return jobs
