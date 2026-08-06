"""
Database migration: add trackr (summer-internship tracker) fields.

Adds to the `jobs` table:
  - region         VARCHAR(40)  : tracker region (Hong Kong / US / UK / Other)
  - process        VARCHAR(200) : interview process, e.g. "HV > VI > AC"
  - current_stage  VARCHAR(100) : latest recruiting stage, e.g. "Offers Out"

Idempotent: checks existing columns first. SQLite-safe (ADD COLUMN only).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    app, _ = create_app()

    with app.app_context():
        logger.info("Starting trackr-fields migration...")

        inspector = db.inspect(db.engine)
        existing = {col['name'] for col in inspector.get_columns('jobs')}

        statements = []
        if 'region' not in existing:
            statements.append("ALTER TABLE jobs ADD COLUMN region VARCHAR(40)")
        if 'process' not in existing:
            statements.append("ALTER TABLE jobs ADD COLUMN process VARCHAR(200)")
        if 'current_stage' not in existing:
            statements.append("ALTER TABLE jobs ADD COLUMN current_stage VARCHAR(100)")

        if not statements:
            logger.info("Nothing to do - all trackr columns already present.")
            return

        for sql in statements:
            logger.info(f"Running: {sql}")
            db.session.execute(text(sql))
        db.session.commit()
        logger.info(f"Migration complete - added {len(statements)} column(s).")


if __name__ == '__main__':
    migrate()
