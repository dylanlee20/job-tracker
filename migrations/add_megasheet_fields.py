"""
Database migration: add megasheet (curated full-time-program list) fields.

Adds to the `jobs` table:
  - external_id        VARCHAR(30)  : source megasheet role id (e.g. "24764")
  - is_rolling         BOOLEAN      : "Rolling ASAP" deadline flag
  - recruiting_window  VARCHAR(120) : when this firm's role typically opens each year

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
        logger.info("Starting megasheet-fields migration...")

        inspector = db.inspect(db.engine)
        existing = {col['name'] for col in inspector.get_columns('jobs')}

        statements = []
        if 'external_id' not in existing:
            statements.append("ALTER TABLE jobs ADD COLUMN external_id VARCHAR(30)")
        if 'is_rolling' not in existing:
            statements.append("ALTER TABLE jobs ADD COLUMN is_rolling BOOLEAN DEFAULT 0 NOT NULL")
        if 'recruiting_window' not in existing:
            statements.append("ALTER TABLE jobs ADD COLUMN recruiting_window VARCHAR(120)")

        if not statements:
            logger.info("Nothing to do — all megasheet columns already present.")
            return

        for sql in statements:
            logger.info(f"Running: {sql}")
            db.session.execute(text(sql))
        db.session.commit()
        logger.info(f"Migration complete — added {len(statements)} column(s).")


if __name__ == '__main__':
    migrate()
