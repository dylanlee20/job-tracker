from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models.database import db
from models.user import User
import secrets
import string

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function


def generate_password(length=10):
    """Generate a random password"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users"""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'

        if not username:
            flash('Username is required', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        else:
            # Generate password if not provided
            if not password:
                password = generate_password()

            user = User(username=username, is_admin=is_admin)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash(f'User "{username}" created with password: {password}', 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/add_user.html')


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Enable/disable user"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Cannot disable yourself', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'enabled' if user.is_active else 'disabled'
        flash(f'User "{user.username}" has been {status}', 'success')

    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """Reset user password"""
    user = User.query.get_or_404(user_id)
    new_password = generate_password()
    user.set_password(new_password)
    db.session.commit()

    flash(f'Password for "{user.username}" reset to: {new_password}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Cannot delete yourself', 'error')
    else:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{username}" deleted', 'success')

    return redirect(url_for('admin.users'))
