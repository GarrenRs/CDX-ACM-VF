"""
Auth Routes - Authentication and authorization
"""

from flask import render_template, session, redirect, url_for, request, flash
from utils.security import get_admin_credentials, get_client_ip, log_ip_activity, log_audit_event
from utils.data import load_data
from werkzeug.security import check_password_hash
from models import User
from extensions import db
from . import auth_bp


@auth_bp.route('/dashboard/login', methods=['GET', 'POST'])
def login():
    """Admin and User login"""
    ADMIN_CREDENTIALS = get_admin_credentials()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        client_ip = get_client_ip()

        # Check main Admin
        if username == ADMIN_CREDENTIALS.get('username') and ADMIN_CREDENTIALS.get('username'):
            if check_password_hash(ADMIN_CREDENTIALS['password_hash'], password):
                session['admin_logged_in'] = True
                session['is_admin'] = True
                session['is_demo_mode'] = False
                session['username'] = username
                flash('Admin Login Successful!', 'success')
                log_ip_activity('admin_login', f"User: {username}")
                return redirect(url_for('pages.index'))

        # Check users in database first
        db_user = User.query.filter_by(username=username).first()
        if db_user and check_password_hash(db_user.password_hash, password):
            session['admin_logged_in'] = True
            session['user_id'] = db_user.id
            session['username'] = db_user.username
            session['is_admin'] = (db_user.role == 'admin')
            # Set demo mode from database
            if db_user.role == 'admin':
                session['is_demo_mode'] = False
            else:
                session['is_demo_mode'] = db_user.is_demo

            # If the user must change their password on first login, force them to do so
            if db_user.must_change_password:
                session['force_change_password'] = True
                log_audit_event('force_password_required', username=db_user.username, details='First-login password change required')
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('dashboard.change_password'))

            flash(f'Welcome back, {username}!', 'success')
            log_ip_activity('user_login', f"User: {username}")
            return redirect(url_for('pages.index'))
        
        # Fallback: Check users in data.json for backward compatibility
        data = load_data()
        users = data.get('users', [])
        for user in users:
            if user['username'] == username and check_password_hash(
                    user['password_hash'], password):
                session['admin_logged_in'] = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = (user.get('role') == 'admin')
                session['is_demo_mode'] = user.get('is_demo', True)

                if user.get('must_change_password', False):
                    session['force_change_password'] = True
                    flash('You must change your password before continuing.', 'warning')
                    return redirect(url_for('dashboard.change_password'))

                flash(f'Welcome back, {username}!', 'success')
                log_ip_activity('user_login', f"User: {username}")
                return redirect(url_for('pages.index'))

        flash('Invalid credentials. Please try again.', 'error')
        log_ip_activity('failed_login', f"Username: {username}")

    return render_template('dashboard/login.html')


@auth_bp.route('/dashboard/logout')
def logout():
    """Logout current user"""
    from utils.decorators import login_required
    
    if 'admin_logged_in' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Disabled registration route"""
    flash('Registration is currently disabled. Please contact the administrator.', 'warning')
    return redirect(url_for('auth.login'))