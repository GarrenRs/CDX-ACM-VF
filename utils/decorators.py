"""
Decorators Module - Authentication and authorization decorators
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def disable_in_demo(f):
    """Decorator to disable actions in demo mode with specific endpoint rules"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import User
        from flask import request
        
        # Refresh session data from database if user is logged in
        if 'admin_logged_in' in session:
            username = session.get('username')
            if username:
                try:
                    user = User.query.filter_by(username=username).first()
                    if user:
                        # Update session with latest status from database
                        session['is_demo_mode'] = user.is_demo
                        session['is_admin'] = (user.role == 'admin')
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Error refreshing session: {str(e)}")

        if session.get('is_demo_mode'):
            # Endpoints whose pages can be viewed in demo mode,
            # but where write actions (POST / PUT / DELETE / PATCH)
            # must be blocked.
            read_only_pages = {
                'dashboard.social',
                'dashboard.clients',
                'dashboard.add_client',
                'dashboard.edit_client',
                'dashboard.view_client',
                'dashboard.settings',
            }

            # Endpoints that remain fully blocked in demo mode
            # (administrative / destructive actions only).
            fully_blocked_actions = {
                'dashboard.delete_client',
                'backups.list',
                'backups.create',
                'backups.download',
                'backups.delete',
                'users.toggle_demo',
            }

            endpoint = request.endpoint
            method = request.method.upper()

            # Always block critical action endpoints entirely
            if endpoint in fully_blocked_actions:
                flash('This action is not available in demo mode.', 'warning')
                return redirect(url_for('dashboard.index'))

            # For read-only pages: allow GET to show full interface,
            # but block any modifying HTTP methods.
            if endpoint in read_only_pages and method not in ('GET', 'HEAD', 'OPTIONS'):
                flash('This action is not available in demo mode.', 'warning')
                # Prefer returning to same page if possible
                return redirect(request.referrer or url_for('dashboard.index'))

        return f(*args, **kwargs)
    
    return decorated_function
