from models.database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import secrets
import string


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


def generate_secure_password(length=16):
    """Generate a cryptographically secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def create_admin_user(username=None, password=None):
    """
    Create default admin user if not exists

    SECURITY: Password must be provided via ADMIN_PASSWORD environment variable
    or will be auto-generated and displayed once.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Get username from environment or use default
    username = username or os.environ.get('ADMIN_USERNAME', 'admin')

    # Check if admin already exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        logger.info(f"Admin user '{username}' already exists")
        return existing

    # Get password from environment variable or generate secure one
    password = password or os.environ.get('ADMIN_PASSWORD')

    generated = False
    if not password:
        # Generate secure random password
        password = generate_secure_password(16)
        generated = True
        logger.warning("=" * 80)
        logger.warning("ADMIN PASSWORD WAS AUTO-GENERATED - SAVE THIS IMMEDIATELY!")
        logger.warning(f"Username: {username}")
        logger.warning(f"Password: {password}")
        logger.warning("This password will NOT be shown again. Please save it securely!")
        logger.warning("=" * 80)

    # Validate password strength
    if len(password) < 8:
        raise ValueError("Admin password must be at least 8 characters long")

    # Create admin user
    admin = User(username=username, is_admin=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    if not generated:
        logger.info(f"Admin user '{username}' created successfully with provided password")

    return admin
