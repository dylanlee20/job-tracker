"""Barclays scraper — pure-HTTP sitemap parse.

search.jobs.barclays is a TalentBrew site. The legacy Selenium scraper
tried to click country-filter checkboxes and parse `li.sr-job-item`
cards, but (a) the cards are injected by AJAX after the page loads so
the HTML returned by the Chrome driver at time-of-scrape had none, and
(b) the fallback "any /job/ link" path returned 146 jobs polluted with
duplicates and a hardcoded `location='United States'` even for Singapore
and Mumbai listings.

Barclays publishes a complete sitemap at /sitemap.xml listing every live
job URL. The URL format is deterministic:
    /job/<city-slug>/<title-slug>/<tenant-id>/<req-id>
so we can extract location (city-slug → title-cased) and title
(title-slug → title-cased, underscores stripped) directly from the URL.
No Selenium, no AJAX, no filter-click fragility.

Historical scope: US + Singapore + Hong Kong. Implemented as a city-slug
allowlist so the output matches the original intent.
"""
import re
import time
import requests
import xml.etree.ElementTree as ET

from scrapers.base_scraper import BaseScraper
from config import Config


_SITEMAP_URL = "https://search.jobs.barclays/sitemap.xml"
_JOB_PATH_RE = re.compile(
    r"^https://search\.jobs\.barclays/job/(?P<city>[^/]+)/(?P<slug>[^/]+)/(?P<tenant>\d+)/(?P<req>\d+)/?$"
)

# City slugs we count as "US + Singapore + Hong Kong" campus/banking hubs.
# Grouped so operator can adjust scope by edit, not config.
_TARGET_CITY_SLUGS = {
    # United States
    "new-york", "whippany", "wilmington", "jersey-city", "hoboken",
    "san-francisco", "chicago", "plano", "lake-mary", "florham-park",
    # Asia
    "singapore", "hong-kong",
}

_SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
}

_CITY_DISPLAY_OVERRIDES = {
    "new-york": "New York",
    "jersey-city": "Jersey City",
    "hong-kong": "Hong Kong",
    "san-francisco": "San Francisco",
    "florham-park": "Florham Park",
    "lake-mary": "Lake Mary",
}


def _slug_to_title(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-"))


def _city_display(slug: str) -> str:
    return _CITY_DISPLAY_OVERRIDES.get(slug, _slug_to_title(slug))


class BarclaysScraper(BaseScraper):
    """Barclays — US + Singapore + Hong Kong jobs from sitemap."""

    def __init__(self):
        super().__init__(
            company_name="Barclays",
            source_url="https://search.jobs.barclays/search-jobs",
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
        resp = self.session.get(_SITEMAP_URL, timeout=Config.SCRAPER_TIMEOUT)
        resp.raise_for_status()

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            self.logger.error(f"Barclays sitemap XML parse failed: {e}")
            return []

        urls = [
            (loc.text or "").strip()
            for loc in root.findall("s:url/s:loc", _SITEMAP_NS)
            if loc is not None and loc.text
        ]
        self.logger.info(f"Barclays sitemap: {len(urls)} total URLs")

        seen_req_ids = set()
        jobs = []
        for url in urls:
            m = _JOB_PATH_RE.match(url)
            if not m:
                continue
            city = m.group("city")
            if city not in _TARGET_CITY_SLUGS:
                continue
            req_id = m.group("req")
            if req_id in seen_req_ids:
                continue
            seen_req_ids.add(req_id)

            title = _slug_to_title(m.group("slug"))
            location = _city_display(city)

            jobs.append({
                "company": self.company_name,
                "title": title,
                "location": location,
                "description": "US + Singapore + Hong Kong (Barclays sitemap)",
                "post_date": None,
                "deadline": None,
                "source_website": self.source_url,
                "job_url": url,
            })

        self.logger.info(
            f"Completed scraping {len(jobs)} Barclays jobs "
            f"(US + Singapore + Hong Kong cities)"
        )
        return jobs
