"""Jefferies scraper — Atom feed (pure HTTP).

Old scraper opened the Taleo SPA URL in Selenium, waited 25s for JS to
render `tr.search_res` rows, then failed to find any. The URL also
embedded a stale `xf-5d566aeb2688` token; live links use `xf-db4aa60af11c`.
Result: "No jobs found" on every run since ~Feb 2026.

Taleo exposes an Atom feed at /vx/mobile-0/appcentre-1/brand-4/candidate/
jobboard/vacancy/2/feed titled "Campus Opportunities". Static XML, parses
cleanly, no browser needed.
"""
import time
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from config import Config


def _parse_atom_published(text):
    """Atom <published> is RFC3339: 2026-04-22T10:15:00Z or with offset.
    Strip timezone and parse; return None on any failure."""
    if not text:
        return None
    t = text.strip()
    if t.endswith("Z"):
        t = t[:-1]
    # drop a trailing timezone like +01:00 or -0500
    t = re.sub(r"[+-]\d{2}:?\d{2}$", "", t)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    return None


_FEED_URL = (
    "https://jefferies.tal.net/vx/mobile-0/appcentre-1/brand-4/"
    "candidate/jobboard/vacancy/2/feed"
)
_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _extract_location(title: str) -> str:
    """Jefferies titles end with ' - <Location>' (sometimes multi-segment).

    Conservative: take the last dash-separated segment, but only if it
    looks like a place (letters/spaces, no words like 'Analyst' or 'Program').
    """
    if " - " not in title:
        return ""
    tail = title.rsplit(" - ", 1)[-1].strip()
    # reject obviously non-location tails
    if re.search(r"\b(analyst|program|internship|intern|summer|off-cycle|full-time|associate)\b",
                 tail, re.IGNORECASE):
        return ""
    return tail


class JefferiesScraper(BaseScraper):
    """Jefferies — campus opportunities via Taleo Atom feed."""

    def __init__(self):
        super().__init__(
            company_name="Jefferies",
            source_url=(
                "https://jefferies.tal.net/vx/mobile-0/appcentre-1/brand-4/"
                "candidate/jobboard/vacancy/2"
            ),
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
        resp = self.session.get(_FEED_URL, timeout=Config.SCRAPER_TIMEOUT)
        resp.raise_for_status()

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            self.logger.error(f"Jefferies feed XML parse failed: {e}")
            return []

        entries = root.findall("a:entry", _ATOM_NS)
        self.logger.info(f"Jefferies feed: {len(entries)} entries")

        jobs = []
        for e in entries:
            try:
                title_elem = e.find("a:title", _ATOM_NS)
                title = (title_elem.text or "").strip() if title_elem is not None else ""
                if not title:
                    continue

                # Prefer the entry's html link (first alternate); fall back to id.
                job_url = ""
                for link in e.findall("a:link", _ATOM_NS):
                    href = link.get("href") or ""
                    if href and link.get("rel", "alternate") == "alternate":
                        job_url = href
                        break
                if not job_url:
                    id_elem = e.find("a:id", _ATOM_NS)
                    job_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""

                published_elem = e.find("a:published", _ATOM_NS)
                post_date = _parse_atom_published(
                    published_elem.text if published_elem is not None else None
                )

                location = _extract_location(title)

                jobs.append({
                    "company": self.company_name,
                    "title": title,
                    "location": location,
                    "description": "Campus Opportunities (Taleo feed)",
                    "post_date": post_date,
                    "deadline": None,
                    "source_website": self.source_url,
                    "job_url": job_url,
                })
            except Exception as ex:
                self.logger.warning(f"Error parsing Jefferies entry: {ex}")
                continue

        self.logger.info(f"Completed scraping {len(jobs)} Jefferies jobs")
        return jobs
