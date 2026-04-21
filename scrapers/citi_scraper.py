"""Citi scraper — pure-HTTP implementation.

jobs.citi.com (iCIMS) is server-rendered, so we bypass Selenium entirely.
The URL path `/search-jobs/United%20States/287/1` resolves to US jobs;
pagination is `?p=N`. Instead of the old index-based selectors
(`country-filter-56`, `cfcareerlevel-filter-3`) which break whenever Citi
reshuffles filter order, we fetch all US jobs and keep titles matching
campus/intern/analyst/graduate keywords client-side.

Historical failure: the prior Selenium scraper clicked `#country-filter-56`
which no longer exists (US is now index 14); the whole scrape returned 0.
"""
import re
import time
import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from config import Config


_CAMPUS_KEYWORDS = re.compile(
    r"\b(intern|internship|analyst program|campus|new grad|new graduate|"
    r"student|summer|graduate program|early career|university|co-op|coop|"
    r"apprentice|rotational|associate program)\b",
    re.IGNORECASE,
)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class CitiScraper(BaseScraper):
    """Citi — US campus/intern/analyst jobs via pure HTTP."""

    def __init__(self):
        super().__init__(
            company_name="Citi",
            source_url="https://jobs.citi.com/search-jobs/United%20States/287/1",
        )
        self.session = requests.Session()
        self.session.headers.update(_DEFAULT_HEADERS)

    def scrape_with_retry(self, max_retries=None):
        """Override base retry loop to skip Selenium init."""
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
                    self.logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
        return []

    def scrape_jobs(self):
        all_jobs = []
        base = self.source_url
        page = 1
        total_pages = 1  # will be overwritten from page 1
        max_pages_cap = 150  # belt-and-suspenders against paginator bugs

        while page <= total_pages and page <= max_pages_cap:
            url = f"{base}?p={page}"
            self.logger.info(f"Fetching Citi page {page}/{total_pages}: {url}")

            resp = self.session.get(url, timeout=Config.SCRAPER_TIMEOUT)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            if page == 1:
                results_section = soup.find(id="search-results")
                if results_section:
                    try:
                        total_results = int(results_section.get("data-total-results", "0"))
                        total_pages = int(results_section.get("data-total-pages", "1"))
                        self.logger.info(
                            f"Citi reports {total_results} total US jobs "
                            f"across {total_pages} pages"
                        )
                    except (TypeError, ValueError):
                        self.logger.warning(
                            "Could not parse total pages/results from page 1"
                        )

            cards = soup.select("li.sr-job-item")
            if not cards:
                self.logger.info(f"No job cards on page {page}, stopping")
                break

            page_matches = 0
            for card in cards:
                try:
                    link = card.select_one("a.sr-job-item__link")
                    if not link:
                        continue
                    title = link.get_text(strip=True)
                    if not title:
                        continue
                    if not _CAMPUS_KEYWORDS.search(title):
                        continue

                    job_url = link.get("href", "") or ""
                    if job_url and not job_url.startswith("http"):
                        job_url = f"https://jobs.citi.com{job_url}"

                    loc_elem = card.select_one(".sr-job-location")
                    location = loc_elem.get_text(strip=True) if loc_elem else ""

                    all_jobs.append({
                        "company": self.company_name,
                        "title": title,
                        "location": location,
                        "description": "United States - campus/intern/analyst filter",
                        "post_date": None,
                        "deadline": None,
                        "source_website": self.source_url,
                        "job_url": job_url,
                    })
                    page_matches += 1
                except Exception as e:
                    self.logger.warning(f"Error parsing job card on page {page}: {e}")
                    continue

            self.logger.info(f"Page {page}: {page_matches} campus-relevant jobs kept")
            time.sleep(1.0)  # be polite
            page += 1

        self.logger.info(
            f"Completed scraping {len(all_jobs)} campus-relevant Citi jobs "
            f"from {page - 1} pages"
        )
        return all_jobs
