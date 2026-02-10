#!/usr/bin/env python3
"""
Test script for JPMorgan Australia scraper
"""

from scrapers.jpmorgan_australia_scraper import JPMorganAustraliaScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 60)
    print("Testing JPMorgan Australia Scraper")
    print("=" * 60)
    print()

    # Create scraper instance
    scraper = JPMorganAustraliaScraper()

    print(f"Company: {scraper.company_name}")
    print(f"URL: {scraper.source_url}")
    print()

    # Run scraper with retry
    print("Starting scrape...")
    jobs = scraper.scrape_with_retry()

    print()
    print("=" * 60)
    print(f"Scraping Results")
    print("=" * 60)
    print(f"Total jobs found: {len(jobs)}")
    print()

    if jobs:
        print("Sample jobs:")
        for i, job in enumerate(jobs[:5], 1):  # Show first 5 jobs
            print(f"\n{i}. {job['title']}")
            print(f"   Location: {job['location']}")
            print(f"   URL: {job['job_url'][:80]}...")
    else:
        print("No jobs found!")

    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == '__main__':
    main()
