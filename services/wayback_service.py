"""
Wayback Machine Historical Data Service
Scrapes archived career pages to backfill historical job data
"""

import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)


class WaybackService:
    """Service for retrieving historical job data from Internet Archive"""

    WAYBACK_API = "https://web.archive.org/cdx/search/cdx"
    WAYBACK_URL = "https://web.archive.org/web/{timestamp}/{url}"

    # Career URLs we're tracking
    CAREER_URLS = {
        'Goldman Sachs': 'https://higher.gs.com/results',
        'JPMorgan': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001',
        'Citi': 'https://jobs.citi.com/search-jobs',
        'UBS': 'https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad',
        'Blackstone': 'https://blackstone.wd1.myworkdayjobs.com/Blackstone_Campus_Careers',
        'BNP Paribas': 'https://bnpparibasfortis.simplyapply.com/jobboard',
        'Nomura': 'https://nomuracampus.tal.net/vx/lang-en-GB/mobile-0/appcentre-ext/brand-4/candidate/jobboard/vacancy',
        'Evercore': 'https://evercore.tal.net/vx/lang-en-GB/mobile-0/channel-1/appcentre-ext/brand-6/candidate/jobboard/vacancy'
    }

    @staticmethod
    def get_available_snapshots(url, from_date, to_date):
        """
        Get available Wayback Machine snapshots for a URL within date range

        Args:
            url: URL to check
            from_date: Start date (datetime)
            to_date: End date (datetime)

        Returns:
            List of snapshot timestamps
        """
        try:
            params = {
                'url': url,
                'from': from_date.strftime('%Y%m%d'),
                'to': to_date.strftime('%Y%m%d'),
                'output': 'json',
                'fl': 'timestamp,statuscode',
                'filter': 'statuscode:200',
                'collapse': 'timestamp:8'  # One snapshot per day
            }

            response = requests.get(WaybackService.WAYBACK_API, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if len(data) <= 1:  # Header only
                return []

            # Skip header, extract timestamps
            snapshots = [row[0] for row in data[1:] if len(row) >= 1]

            logger.info(f"Found {len(snapshots)} snapshots for {url}")
            return snapshots

        except Exception as e:
            logger.error(f"Error getting snapshots for {url}: {e}")
            return []

    @staticmethod
    def get_archived_page_content(url, timestamp):
        """
        Retrieve archived page content from Wayback Machine

        Args:
            url: Original URL
            timestamp: Wayback timestamp (YYYYMMDDhhmmss)

        Returns:
            HTML content or None
        """
        try:
            wayback_url = WaybackService.WAYBACK_URL.format(timestamp=timestamp, url=url)

            response = requests.get(wayback_url, timeout=30)
            response.raise_for_status()

            return response.text

        except Exception as e:
            logger.error(f"Error fetching archived page {timestamp}: {e}")
            return None

    @staticmethod
    def extract_job_count_from_html(html, company):
        """
        Extract approximate job count from archived HTML
        (This is a best-effort estimation since we can't run JavaScript)

        Args:
            html: HTML content
            company: Company name

        Returns:
            Estimated job count or None
        """
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Look for common patterns that indicate job counts
            count_patterns = [
                r'(\d+)\s+(?:jobs?|positions?|openings?|results?)',
                r'(?:showing|found|total)[\s:]+(\d+)',
                r'(\d+)\s+(?:job|position|opening)',
            ]

            # Search in text content
            text = soup.get_text()
            for pattern in count_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        count = int(matches[0])
                        if 1 <= count <= 10000:  # Sanity check
                            return count
                    except:
                        continue

            # Try to count job listings in HTML
            # Look for common job card patterns
            job_elements = (
                soup.find_all('div', class_=re.compile(r'job[-_]?(item|card|listing|result)', re.I)) or
                soup.find_all('tr', class_=re.compile(r'job[-_]?row', re.I)) or
                soup.find_all('a', href=re.compile(r'/job/|/careers/|/positions/', re.I))
            )

            if job_elements and len(job_elements) > 0:
                return len(job_elements)

            logger.debug(f"Could not extract job count for {company} from archived HTML")
            return None

        except Exception as e:
            logger.error(f"Error parsing HTML for {company}: {e}")
            return None

    @staticmethod
    def backfill_historical_data(company_name, weeks_back=52):
        """
        Attempt to backfill historical data for a company

        Args:
            company_name: Name of company
            weeks_back: How many weeks to go back

        Returns:
            List of estimated historical data points
        """
        if company_name not in WaybackService.CAREER_URLS:
            logger.warning(f"No career URL configured for {company_name}")
            return []

        url = WaybackService.CAREER_URLS[company_name]
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(weeks=weeks_back)

        logger.info(f"Searching for historical data for {company_name} from {from_date.date()} to {to_date.date()}")

        # Get available snapshots
        snapshots = WaybackService.get_available_snapshots(url, from_date, to_date)

        if not snapshots:
            logger.warning(f"No Wayback Machine snapshots found for {company_name}")
            return []

        historical_data = []

        # Sample snapshots (don't overload the Wayback Machine)
        # Take one snapshot per week
        sampled_snapshots = snapshots[::7] if len(snapshots) > 52 else snapshots

        for timestamp in sampled_snapshots[:52]:  # Limit to 52 weeks
            try:
                # Parse timestamp
                dt = datetime.strptime(timestamp[:8], '%Y%m%d')

                # Get archived content
                logger.info(f"Fetching snapshot from {dt.date()} for {company_name}...")
                html = WaybackService.get_archived_page_content(url, timestamp)

                if html:
                    # Extract job count
                    job_count = WaybackService.extract_job_count_from_html(html, company_name)

                    if job_count:
                        historical_data.append({
                            'date': dt,
                            'company': company_name,
                            'estimated_jobs': job_count,
                            'source': 'wayback_machine',
                            'timestamp': timestamp
                        })

                        logger.info(f"  ✓ Estimated {job_count} jobs on {dt.date()}")
                    else:
                        logger.info(f"  ✗ Could not extract job count")

                # Be nice to Wayback Machine
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing snapshot {timestamp}: {e}")
                continue

        logger.info(f"Backfill complete for {company_name}: found {len(historical_data)} data points")
        return historical_data

    @staticmethod
    def get_recommendations():
        """
        Provide recommendations on which companies are likely to have
        good Wayback Machine data
        """
        recommendations = []

        for company, url in WaybackService.CAREER_URLS.items():
            # Check if snapshots exist
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(days=30)  # Check last month

            snapshots = WaybackService.get_available_snapshots(url, from_date, to_date)

            recommendations.append({
                'company': company,
                'url': url,
                'snapshots_last_month': len(snapshots),
                'likely_success': 'High' if len(snapshots) > 5 else 'Medium' if len(snapshots) > 0 else 'Low'
            })

        return recommendations
