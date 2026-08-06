from models.database import db
from models.job import Job
from datetime import datetime
from sqlalchemy import and_, or_
import logging

logger = logging.getLogger(__name__)


class SavedJobsService:
    """Service for tracking saved/starred jobs"""

    @staticmethod
    def get_disappeared_saved_jobs():
        """
        Get all starred jobs that have become inactive

        Returns:
            list: List of job dictionaries with disappearance date
        """
        disappeared_jobs = Job.query.filter(
            and_(
                Job.is_important == True,
                Job.status == 'inactive'
            )
        ).order_by(Job.last_seen.desc()).all()

        return [
            {
                **job.to_dict(),
                'disappeared_date': job.last_seen
            }
            for job in disappeared_jobs
        ]

    @staticmethod
    def get_similar_jobs(job_id, limit=5):
        """
        Find similar jobs based on a given job

        Args:
            job_id: ID of the reference job
            limit: Maximum number of similar jobs to return

        Returns:
            list: List of similar job dictionaries
        """
        reference_job = Job.query.get(job_id)
        if not reference_job:
            return []

        # Find similar jobs based on:
        # 1. Same category
        # 2. Same company (different position)
        # 3. Same location
        # Priority: Category match > Company match > Location match

        similar_jobs = Job.query.filter(
            and_(
                Job.id != job_id,
                Job.status == 'active',
                or_(
                    Job.category == reference_job.category,
                    Job.company == reference_job.company,
                    Job.location == reference_job.location
                )
            )
        ).limit(limit * 2).all()  # Get more than needed for scoring

        # Score and sort jobs by similarity
        scored_jobs = []
        for job in similar_jobs:
            score = 0
            # Category match is most important
            if job.category == reference_job.category:
                score += 3
            # Same company
            if job.company == reference_job.company:
                score += 2
            # Same location
            if job.location == reference_job.location:
                score += 1
            # Same industry
            if job.industry == reference_job.industry:
                score += 1

            scored_jobs.append((score, job))

        # Sort by score (descending) and take top N
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        return [job.to_dict() for score, job in scored_jobs[:limit]]

    @staticmethod
    def get_all_saved_jobs_summary():
        """
        Get summary of all saved jobs

        Returns:
            dict: Summary statistics
        """
        total_saved = Job.query.filter_by(is_important=True).count()
        active_saved = Job.query.filter_by(is_important=True, status='active').count()
        disappeared_saved = Job.query.filter_by(is_important=True, status='inactive').count()

        return {
            'total_saved': total_saved,
            'active': active_saved,
            'disappeared': disappeared_saved,
            'disappearance_rate': round((disappeared_saved / total_saved * 100), 1) if total_saved > 0 else 0
        }

    @staticmethod
    def get_recommendations_for_all_saved():
        """
        Get job recommendations based on all saved jobs

        Returns:
            list: List of recommended jobs with reasoning
        """
        # Get all active saved jobs
        saved_jobs = Job.query.filter_by(is_important=True, status='active').all()

        if not saved_jobs:
            return []

        # Aggregate preferences from saved jobs
        category_counts = {}
        company_counts = {}
        location_counts = {}

        for job in saved_jobs:
            category_counts[job.category] = category_counts.get(job.category, 0) + 1
            company_counts[job.company] = company_counts.get(job.company, 0) + 1
            location_counts[job.location] = location_counts.get(job.location, 0) + 1

        # Get top preferences
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Find jobs matching preferences that aren't already saved
        saved_job_ids = {job.id for job in saved_jobs}

        recommended_jobs = Job.query.filter(
            and_(
                Job.status == 'active',
                Job.is_important == False,
                or_(
                    Job.category.in_([cat[0] for cat in top_categories]),
                    Job.company.in_([comp[0] for comp in top_companies]),
                    Job.location.in_([loc[0] for loc in top_locations])
                )
            )
        ).limit(20).all()

        # Score and annotate recommendations
        scored_recommendations = []
        for job in recommended_jobs:
            if job.id in saved_job_ids:
                continue

            score = 0
            reasons = []

            # Check category match
            for cat, count in top_categories:
                if job.category == cat:
                    score += 3
                    reasons.append(f"Matches your interest in {cat}")
                    break

            # Check company match
            for comp, count in top_companies:
                if job.company == comp:
                    score += 2
                    reasons.append(f"Same company as your saved jobs ({comp})")
                    break

            # Check location match
            for loc, count in top_locations:
                if job.location == loc:
                    score += 1
                    reasons.append(f"In your preferred location ({loc})")
                    break

            if score > 0:
                scored_recommendations.append({
                    **job.to_dict(),
                    'recommendation_score': score,
                    'recommendation_reasons': reasons
                })

        # Sort by score and return top 10
        scored_recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return scored_recommendations[:10]
