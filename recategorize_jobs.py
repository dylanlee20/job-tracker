"""
Recategorize all existing jobs with improved categorization
and normalize locations to City, Country format
"""

from app import create_app
from models.database import db
from models.job import Job
from utils.job_utils import categorize_job, normalize_location
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def recategorize_all_jobs():
    """Recategorize all jobs with the improved categorization logic"""
    app_tuple = create_app()
    app = app_tuple[0] if isinstance(app_tuple, tuple) else app_tuple

    with app.app_context():
        logger.info("Starting job recategorization and location normalization...")

        # Get all jobs
        all_jobs = Job.query.all()
        total = len(all_jobs)

        logger.info(f"Found {total} jobs to process")

        updated_count = 0
        category_changes = {}
        location_changes = {}

        for idx, job in enumerate(all_jobs):
            # Recategorize
            new_category = categorize_job(job.title, job.description)
            old_category = job.category

            if new_category != old_category:
                job.category = new_category
                updated_count += 1

                # Track category changes
                change_key = f"{old_category} → {new_category}"
                category_changes[change_key] = category_changes.get(change_key, 0) + 1

            # Normalize location
            new_location = normalize_location(job.location)
            old_location = job.location

            if new_location != old_location:
                job.location = new_location

                # Track location changes
                loc_key = f"{old_location} → {new_location}"
                location_changes[loc_key] = location_changes.get(loc_key, 0) + 1

            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1}/{total} jobs...")

        # Commit all changes
        db.session.commit()

        logger.info(f"\nRecategorization complete!")
        logger.info(f"Total jobs processed: {total}")
        logger.info(f"Jobs with category changes: {updated_count}")

        logger.info(f"\nCategory changes:")
        for change, count in sorted(category_changes.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {change}: {count} jobs")

        logger.info(f"\nTop 20 location normalizations:")
        for change, count in sorted(location_changes.items(), key=lambda x: x[1], reverse=True)[:20]:
            logger.info(f"  {change}: {count} jobs")

        # Show final category distribution
        logger.info(f"\nFinal category distribution:")
        from sqlalchemy import func
        category_dist = db.session.query(
            Job.category,
            func.count(Job.id)
        ).filter_by(status='active').group_by(Job.category).all()

        for category, count in sorted(category_dist, key=lambda x: x[1], reverse=True):
            logger.info(f"  {category}: {count} jobs")

        logger.info(f"\nLocation distribution (top 15):")
        location_dist = db.session.query(
            Job.location,
            func.count(Job.id)
        ).filter_by(status='active').group_by(Job.location).order_by(func.count(Job.id).desc()).limit(15).all()

        for location, count in location_dist:
            logger.info(f"  {location}: {count} jobs")


if __name__ == '__main__':
    recategorize_all_jobs()
