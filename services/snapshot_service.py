"""
Job Snapshot Service - Historical Tracking
Captures and analyzes job market trends over time
"""

from models.database import db
from models.job import Job
from models.job_snapshot import JobSnapshot
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import json
import logging

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for managing job market snapshots"""

    @staticmethod
    def capture_weekly_snapshot():
        """
        Capture current job market state as a weekly snapshot
        Should be run once per week (e.g., every Sunday)
        """
        try:
            now = datetime.utcnow()
            week_number = now.isocalendar()[1]
            year = now.year

            # Check if snapshot for this week already exists
            existing = JobSnapshot.query.filter_by(
                year=year,
                week_number=week_number
            ).first()

            if existing:
                logger.info(f"Snapshot for {year}-W{week_number} already exists")
                return existing

            # Get active jobs
            active_jobs = Job.query.filter_by(status='active').all()
            total_active_jobs = len(active_jobs)

            # Get unique companies and locations
            total_companies = db.session.query(Job.company)\
                .filter_by(status='active')\
                .distinct()\
                .count()

            total_locations = db.session.query(Job.location)\
                .filter_by(status='active')\
                .distinct()\
                .count()

            # Category breakdown
            category_data = db.session.query(
                Job.category,
                func.count(Job.id)
            ).filter_by(status='active')\
             .group_by(Job.category)\
             .all()

            category_breakdown = {cat: count for cat, count in category_data if cat}

            # Company breakdown
            company_data = db.session.query(
                Job.company,
                func.count(Job.id)
            ).filter_by(status='active')\
             .group_by(Job.company)\
             .all()

            company_breakdown = {comp: count for comp, count in company_data}

            # Location breakdown (top 20)
            location_data = db.session.query(
                Job.location,
                func.count(Job.id)
            ).filter_by(status='active')\
             .group_by(Job.location)\
             .order_by(func.count(Job.id).desc())\
             .limit(20)\
             .all()

            location_breakdown = {loc: count for loc, count in location_data}

            # Calculate weekly changes
            week_ago = now - timedelta(days=7)
            new_jobs_this_week = Job.query.filter(
                and_(
                    Job.first_seen >= week_ago,
                    Job.status == 'active'
                )
            ).count()

            closed_jobs_this_week = Job.query.filter(
                and_(
                    Job.last_seen >= week_ago,
                    Job.last_seen < now,
                    Job.status == 'inactive'
                )
            ).count()

            # Create snapshot
            snapshot = JobSnapshot(
                snapshot_date=now,
                week_number=week_number,
                year=year,
                total_active_jobs=total_active_jobs,
                total_companies=total_companies,
                total_locations=total_locations,
                category_breakdown=json.dumps(category_breakdown),
                company_breakdown=json.dumps(company_breakdown),
                location_breakdown=json.dumps(location_breakdown),
                new_jobs_this_week=new_jobs_this_week,
                closed_jobs_this_week=closed_jobs_this_week
            )

            db.session.add(snapshot)
            db.session.commit()

            logger.info(f"Created snapshot for {year}-W{week_number}: {total_active_jobs} jobs")
            return snapshot

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error capturing snapshot: {e}")
            raise

    @staticmethod
    def get_year_over_year_comparison(category=None, company=None):
        """
        Compare current week with same week last year

        Args:
            category: Optional category filter
            company: Optional company filter

        Returns:
            dict with comparison data
        """
        try:
            now = datetime.utcnow()
            current_week = now.isocalendar()[1]
            current_year = now.year
            last_year = current_year - 1

            # Get current snapshot
            current_snapshot = JobSnapshot.query.filter_by(
                year=current_year,
                week_number=current_week
            ).first()

            # Get last year's snapshot (same week)
            last_year_snapshot = JobSnapshot.query.filter_by(
                year=last_year,
                week_number=current_week
            ).first()

            if not current_snapshot or not last_year_snapshot:
                return {
                    'available': False,
                    'message': 'Insufficient historical data'
                }

            # Parse JSON data
            current_categories = json.loads(current_snapshot.category_breakdown) if current_snapshot.category_breakdown else {}
            last_year_categories = json.loads(last_year_snapshot.category_breakdown) if last_year_snapshot.category_breakdown else {}

            current_companies = json.loads(current_snapshot.company_breakdown) if current_snapshot.company_breakdown else {}
            last_year_companies = json.loads(last_year_snapshot.company_breakdown) if last_year_snapshot.company_breakdown else {}

            # Calculate changes
            if category:
                current_count = current_categories.get(category, 0)
                last_year_count = last_year_categories.get(category, 0)

                return {
                    'available': True,
                    'category': category,
                    'current_year': current_year,
                    'current_count': current_count,
                    'last_year_count': last_year_count,
                    'change': current_count - last_year_count,
                    'change_percent': ((current_count - last_year_count) / last_year_count * 100) if last_year_count > 0 else None
                }

            if company:
                current_count = current_companies.get(company, 0)
                last_year_count = last_year_companies.get(company, 0)

                return {
                    'available': True,
                    'company': company,
                    'current_year': current_year,
                    'current_count': current_count,
                    'last_year_count': last_year_count,
                    'change': current_count - last_year_count,
                    'change_percent': ((current_count - last_year_count) / last_year_count * 100) if last_year_count > 0 else None
                }

            # Overall comparison
            return {
                'available': True,
                'current_year': current_year,
                'current_total': current_snapshot.total_active_jobs,
                'last_year_total': last_year_snapshot.total_active_jobs,
                'change': current_snapshot.total_active_jobs - last_year_snapshot.total_active_jobs,
                'change_percent': ((current_snapshot.total_active_jobs - last_year_snapshot.total_active_jobs) /
                                 last_year_snapshot.total_active_jobs * 100) if last_year_snapshot.total_active_jobs > 0 else None,
                'categories_comparison': {
                    cat: {
                        'current': current_categories.get(cat, 0),
                        'last_year': last_year_categories.get(cat, 0),
                        'change': current_categories.get(cat, 0) - last_year_categories.get(cat, 0)
                    }
                    for cat in set(list(current_categories.keys()) + list(last_year_categories.keys()))
                }
            }

        except Exception as e:
            logger.error(f"Error in year-over-year comparison: {e}")
            return {
                'available': False,
                'error': str(e)
            }

    @staticmethod
    def get_trend_data(weeks=12):
        """
        Get historical trend data for the past N weeks

        Args:
            weeks: Number of weeks to retrieve

        Returns:
            list of snapshot data
        """
        try:
            snapshots = JobSnapshot.query\
                .order_by(JobSnapshot.snapshot_date.desc())\
                .limit(weeks)\
                .all()

            trend_data = []
            for snapshot in reversed(snapshots):
                category_breakdown = json.loads(snapshot.category_breakdown) if snapshot.category_breakdown else {}

                trend_data.append({
                    'date': snapshot.snapshot_date.isoformat(),
                    'week': f"{snapshot.year}-W{snapshot.week_number:02d}",
                    'total_jobs': snapshot.total_active_jobs,
                    'new_jobs': snapshot.new_jobs_this_week,
                    'closed_jobs': snapshot.closed_jobs_this_week,
                    'categories': category_breakdown
                })

            return trend_data

        except Exception as e:
            logger.error(f"Error getting trend data: {e}")
            return []

    @staticmethod
    def get_all_snapshots():
        """Get all historical snapshots"""
        try:
            snapshots = JobSnapshot.query\
                .order_by(JobSnapshot.snapshot_date.desc())\
                .all()

            return [{
                'id': s.id,
                'date': s.snapshot_date.isoformat(),
                'week': f"{s.year}-W{s.week_number:02d}",
                'total_jobs': s.total_active_jobs,
                'total_companies': s.total_companies,
                'new_jobs': s.new_jobs_this_week,
                'closed_jobs': s.closed_jobs_this_week
            } for s in snapshots]

        except Exception as e:
            logger.error(f"Error getting snapshots: {e}")
            return []
