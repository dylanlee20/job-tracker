from models.database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


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


def create_admin_user(username='admin', password='admin123'):
    """Create default admin user if not exists"""
    existing = User.query.filter_by(username=username).first()
    if not existing:
        admin = User(username=username, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user '{username}' created successfully!")
        return admin
    return existing
