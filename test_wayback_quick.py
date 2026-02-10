"""
Quick test of Wayback Machine availability
Checks which companies have archived data
"""

from services.wayback_service import WaybackService

def main():
    print("="*70)
    print("NewWhale Job Tracker - Wayback Machine Quick Test")
    print("="*70)
    print("\nChecking Wayback Machine snapshot availability...")
    print("This will help determine if we can backfill historical data")
    print("="*70 + "\n")

    recommendations = WaybackService.get_recommendations()

    # Display results
    print(f"{'Company':<25} {'Snapshots':<15} {'Likelihood':<15} {'URL':<30}")
    print("-"*85)

    for rec in recommendations:
        url_short = rec['url'][:27] + "..." if len(rec['url']) > 30 else rec['url']
        print(f"{rec['company']:<25} {rec['snapshots_last_month']:<15} {rec['likely_success']:<15} {url_short}")

    # Summary
    high_count = sum(1 for r in recommendations if r['likely_success'] == 'High')
    medium_count = sum(1 for r in recommendations if r['likely_success'] == 'Medium')
    low_count = sum(1 for r in recommendations if r['likely_success'] == 'Low')

    print("\n" + "="*70)
    print("Summary:")
    print(f"  High Likelihood:   {high_count} companies - Good candidates for backfill")
    print(f"  Medium Likelihood: {medium_count} companies - May have partial data")
    print(f"  Low Likelihood:    {low_count} companies - Unlikely to have useful data")
    print("="*70)

    if high_count > 0:
        print("\n✓ Good news! Some companies have archived data available.")
        print("  Run 'python3 backfill_historical_data.py' to start backfilling.")
    else:
        print("\n✗ Unfortunately, no companies have strong Wayback Machine coverage.")
        print("  This means career sites aren't regularly archived, likely because:")
        print("  - They use JavaScript to load job listings (WM doesn't execute JS)")
        print("  - The sites change URLs/structure frequently")
        print("  - They block archiving robots")

    print("\nNote: Even with 'Low' likelihood, we'll continue collecting live data")
    print("      and build valuable historical trends going forward.")
    print("="*70)


if __name__ == '__main__':
    main()
