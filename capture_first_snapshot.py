"""
Capture the first weekly snapshot for historical tracking
Run this once to initialize the historical tracking system
"""

from app import create_app
from services.snapshot_service import SnapshotService

def main():
    print("="*70)
    print("NewWhale Job Tracker - Initial Snapshot Capture")
    print("="*70)

    app, scheduler = create_app()
    scheduler.stop()

    with app.app_context():
        print("\nCapturing baseline snapshot of current job market...")

        try:
            snapshot = SnapshotService.capture_weekly_snapshot()

            print(f"\n✓ Snapshot captured successfully!")
            print(f"\nSnapshot Details:")
            print(f"  Week: {snapshot.year}-W{snapshot.week_number:02d}")
            print(f"  Date: {snapshot.snapshot_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Total Active Jobs: {snapshot.total_active_jobs}")
            print(f"  Total Companies: {snapshot.total_companies}")
            print(f"  Total Locations: {snapshot.total_locations}")
            print(f"  New Jobs This Week: {snapshot.new_jobs_this_week}")
            print(f"  Closed Jobs This Week: {snapshot.closed_jobs_this_week}")

            import json
            if snapshot.category_breakdown:
                category_data = json.loads(snapshot.category_breakdown)
                print(f"\n  Category Breakdown:")
                for cat, count in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {cat}: {count} jobs")

            print("\n" + "="*70)
            print("Historical tracking initialized!")
            print("="*70)
            print("\nFuture snapshots will be captured automatically every Sunday at 2:00 AM.")
            print("This will enable year-over-year comparisons and trend analysis.")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
