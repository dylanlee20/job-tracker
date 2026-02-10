from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db
from models.user import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


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

            next_page = request.args.get('next')
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
