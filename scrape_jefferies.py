#!/usr/bin/env python3
"""
Scrape Jefferies jobs and save to database
"""

from app import create_app
from services.scraper_service import ScraperService

def main():
    # Create Flask app context
    app, scheduler = create_app()

    with app.app_context():
        print("="*70)
        print("Scraping Jefferies...")
        print("="*70)

        result = ScraperService.run_single_scraper('Jefferies')

        print("\n" + "="*70)
        print("RESULT:")
        print(f"  Success: {result.get('success')}")

        if result.get('success'):
            stats = result.get('stats', {})
            print(f"  Total scraped: {stats.get('total_scraped', 0)}")
            print(f"  New jobs: {stats.get('new_jobs', 0)}")
            print(f"  Updated jobs: {stats.get('updated_jobs', 0)}")
            print(f"  Inactive jobs: {stats.get('inactive_jobs', 0)}")
        else:
            print(f"  Error: {result.get('error')}")

        print("="*70)

if __name__ == '__main__':
    main()
