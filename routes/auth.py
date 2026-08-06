from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db
from models.user import User
from datetime import datetime
from urllib.parse import urlparse, urljoin

auth_bp = Blueprint('auth', __name__)


def is_safe_url(target):
    """
    Validate that a redirect URL is safe (prevents open redirect attacks)

    Returns True only if the URL is relative or points to the same host
    """
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    # Only allow http/https schemes
    if test_url.scheme not in ('http', 'https', ''):
        return False

    # Must be same host or no host (relative URL)
    return test_url.netloc == ref_url.netloc or test_url.netloc == ''


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been disabled. Contact admin.', 'error')
                return render_template('login.html')

            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Validate redirect URL to prevent open redirect attacks
            next_page = request.args.get('next')
            if next_page and not is_safe_url(next_page):
                # Log potential attack attempt
                flash('Invalid redirect URL detected', 'error')
                next_page = None

            return redirect(next_page or url_for('web.index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
        elif len(new_password) < 6:
            flash('New password must be at least 6 characters', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'error')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('web.index'))

    return render_template('change_password.html')
