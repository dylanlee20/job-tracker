"""
Historical Data Backfill Tool
Attempts to retrieve historical job data from Wayback Machine
"""

from services.wayback_service import WaybackService
from services.snapshot_service import SnapshotService
from models.database import db
from models.job_snapshot import JobSnapshot
from app import create_app
import json
from datetime import datetime

def check_wayback_availability():
    """Check which companies have good Wayback Machine coverage"""
    print("="*70)
    print("Checking Wayback Machine Availability")
    print("="*70)

    recommendations = WaybackService.get_recommendations()

    print(f"\n{'Company':<20} {'Snapshots (Last 30d)':<20} {'Success Likelihood':<20}")
    print("-"*70)

    for rec in recommendations:
        print(f"{rec['company']:<20} {rec['snapshots_last_month']:<20} {rec['likely_success']:<20}")

    print("\n" + "="*70)
    print("Recommendation: Focus on companies with 'High' likelihood")
    print("="*70)

    return recommendations


def backfill_company_data(company_name, weeks_back=52):
    """Backfill historical data for a specific company"""
    print(f"\n{'='*70}")
    print(f"Backfilling Historical Data for {company_name}")
    print(f"{'='*70}")
    print(f"Target: {weeks_back} weeks of historical data")
    print(f"Note: This uses Wayback Machine and may take 10-15 minutes")
    print(f"{'='*70}\n")

    historical_data = WaybackService.backfill_historical_data(company_name, weeks_back)

    if not historical_data:
        print(f"\n✗ No historical data found for {company_name}")
        print("  This could mean:")
        print("  - The website wasn't archived by Wayback Machine")
        print("  - The site structure has changed significantly")
        print("  - Job listings are loaded via JavaScript (not captured by WM)")
        return None

    print(f"\n✓ Successfully retrieved {len(historical_data)} historical data points")
    print("\nSample data:")
    for i, data in enumerate(historical_data[:5]):
        print(f"  {data['date'].strftime('%Y-%m-%d')}: ~{data['estimated_jobs']} jobs")

    if len(historical_data) > 5:
        print(f"  ... and {len(historical_data) - 5} more data points")

    return historical_data


def create_historical_snapshots(historical_data_by_company):
    """
    Create historical snapshots in database from backfilled data

    WARNING: This is approximate data from Wayback Machine
    """
    print(f"\n{'='*70}")
    print("Creating Historical Snapshots in Database")
    print(f"{'='*70}")

    app, scheduler = create_app()
    scheduler.stop()

    with app.app_context():
        created_count = 0

        # Group data by week
        weekly_data = {}

        for company, data_points in historical_data_by_company.items():
            for point in data_points:
                week_key = (point['date'].year, point['date'].isocalendar()[1])

                if week_key not in weekly_data:
                    weekly_data[week_key] = {
                        'date': point['date'],
                        'companies': {}
                    }

                weekly_data[week_key]['companies'][company] = point['estimated_jobs']

        # Create snapshots for each week
        for (year, week_num), data in sorted(weekly_data.items()):
            # Check if snapshot already exists
            existing = JobSnapshot.query.filter_by(
                year=year,
                week_number=week_num
            ).first()

            if existing:
                print(f"  Skipping {year}-W{week_num:02d} (already exists)")
                continue

            # Calculate totals
            total_jobs = sum(data['companies'].values())
            company_breakdown = json.dumps(data['companies'])

            snapshot = JobSnapshot(
                snapshot_date=data['date'],
                week_number=week_num,
                year=year,
                total_active_jobs=total_jobs,
                total_companies=len(data['companies']),
                total_locations=0,  # Unknown from historical data
                category_breakdown=None,  # Unknown from historical data
                company_breakdown=company_breakdown,
                location_breakdown=None,
                new_jobs_this_week=None,  # Unknown
                closed_jobs_this_week=None  # Unknown
            )

            db.session.add(snapshot)
            created_count += 1
            print(f"  ✓ Created snapshot for {year}-W{week_num:02d}: {total_jobs} jobs across {len(data['companies'])} companies")

        db.session.commit()

        print(f"\n{'='*70}")
        print(f"Successfully created {created_count} historical snapshots")
        print(f"{'='*70}")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          NewWhale Job Tracker - Historical Data Backfill         ║
║                                                                  ║
║  This tool attempts to retrieve historical job data from the     ║
║  Wayback Machine (Internet Archive) to build year-over-year     ║
║  comparisons immediately instead of waiting a full year.         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    print("\nOptions:")
    print("1. Check Wayback Machine availability for all companies")
    print("2. Backfill data for a specific company (test)")
    print("3. Full backfill (all companies with good coverage)")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == '1':
        check_wayback_availability()

    elif choice == '2':
        print("\nAvailable companies:")
        for i, company in enumerate(WaybackService.CAREER_URLS.keys(), 1):
            print(f"{i}. {company}")

        company_choice = input("\nEnter company number: ").strip()
        try:
            company_idx = int(company_choice) - 1
            company_name = list(WaybackService.CAREER_URLS.keys())[company_idx]

            weeks = input("How many weeks back to check? (default 52): ").strip()
            weeks_back = int(weeks) if weeks else 52

            backfill_company_data(company_name, weeks_back)
        except (ValueError, IndexError):
            print("Invalid selection")

    elif choice == '3':
        print("\n⚠️  WARNING: Full backfill may take 1-2 hours and make many requests to Wayback Machine")
        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()

        if confirm == 'yes':
            recommendations = check_wayback_availability()

            # Only backfill companies with high likelihood
            high_likelihood_companies = [
                rec['company'] for rec in recommendations
                if rec['likely_success'] == 'High'
            ]

            if not high_likelihood_companies:
                print("\n✗ No companies with high success likelihood found")
                return

            print(f"\nBackfilling data for: {', '.join(high_likelihood_companies)}")

            all_historical_data = {}
            for company in high_likelihood_companies:
                data = backfill_company_data(company, weeks_back=52)
                if data:
                    all_historical_data[company] = data

            if all_historical_data:
                save = input("\nSave this data to database? (yes/no): ").strip().lower()
                if save == 'yes':
                    create_historical_snapshots(all_historical_data)
        else:
            print("Backfill cancelled")

    elif choice == '4':
        print("\nExiting...")

    else:
        print("Invalid choice")


if __name__ == '__main__':
    main()
