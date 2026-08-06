"""
Database migration script to add enhancement fields
Adds: industry, application tracking, and sponsorship fields to jobs table
"""
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.job import Job
from industries import get_industry_for_company
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Run database migration to add enhancement fields"""
    app, _ = create_app()

    with app.app_context():
        logger.info("Starting database migration...")

        try:
            # SQLite doesn't support adding columns with complex constraints easily
            # We'll add columns one by one

            # Check if columns already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('jobs')]

            columns_to_add = []

            if 'industry' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN industry VARCHAR(100)")

            if 'application_submitted' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN application_submitted BOOLEAN DEFAULT 0 NOT NULL")

            if 'application_date' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN application_date DATETIME")

            if 'application_result' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN application_result VARCHAR(20)")

            if 'result_date' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN result_date DATETIME")

            if 'result_notes' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN result_notes TEXT")

            if 'sponsorship_required' not in existing_columns:
                columns_to_add.append("ALTER TABLE jobs ADD COLUMN sponsorship_required BOOLEAN")

            # Execute ALTER TABLE statements
            for sql in columns_to_add:
                logger.info(f"Executing: {sql}")
                db.session.execute(text(sql))
                db.session.commit()

            if columns_to_add:
                logger.info(f"Added {len(columns_to_add)} new columns to jobs table")
            else:
                logger.info("All columns already exist, skipping column addition")

            # Backfill industry based on company
            logger.info("Backfilling industry data...")
            jobs = Job.query.all()
            updated_count = 0

            for job in jobs:
                if not job.industry:  # Only update if industry is not set
                    industry = get_industry_for_company(job.company)
                    job.industry = industry
                    updated_count += 1

            db.session.commit()
            logger.info(f"Updated industry for {updated_count} jobs")

            # Create indexes if they don't exist
            logger.info("Creating indexes...")
            try:
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_industry ON jobs(industry)"))
                db.session.commit()
                logger.info("Index created successfully")
            except Exception as e:
                logger.warning(f"Index creation skipped (may already exist): {e}")

            logger.info("Migration completed successfully!")

            # Print summary
            total_jobs = Job.query.count()
            jobs_with_industry = Job.query.filter(Job.industry.isnot(None)).count()

            logger.info(f"\nMigration Summary:")
            logger.info(f"  Total jobs: {total_jobs}")
            logger.info(f"  Jobs with industry: {jobs_with_industry}")
            logger.info(f"  Jobs without industry: {total_jobs - jobs_with_industry}")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
