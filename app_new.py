"""
Codexx Academy - Main Application Entry Point
Refactored using Application Factory Pattern for modular architecture

This module initializes the Flask application with all necessary extensions,
configurations, and middleware. All actual route handling is delegated to blueprints.
"""

import os
import uuid
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify, send_file
from config import get_config
from extensions import db
from utils.data import load_data, save_data
from utils.decorators import login_required, admin_required, disable_in_demo
from utils.security import get_admin_credentials, get_client_ip, log_ip_activity, check_rate_limit
from utils.helpers import allowed_file, get_clients_stats
from utils.notifications import send_telegram_notification, get_telegram_credentials, load_smtp_config, save_smtp_config
from models import User, Message

# Import all blueprints
from blueprints.auth import auth_bp
from blueprints.pages import pages_bp
from blueprints.dashboard import dashboard_bp
from blueprints.portfolio import portfolio_bp
from blueprints.services import services_bp


def create_app(config_name=None):
    """
    Application Factory Pattern
    Creates and configures Flask application instance
    
    Args:
        config_name (str): Configuration environment name (optional)
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    app = Flask(__name__)
    
    # Load configuration
    conf = get_config()
    app.config.from_object(conf)
    
    # Fix PostgreSQL URL if needed
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_url and db_url.startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
            "postgres://", "postgresql://", 1)
    
    # Initialize extensions with app
    initialize_extensions(app)
    
    # Register Jinja filters
    try:
        from utils.helpers import sanitize_about
        app.jinja_env.filters['sanitize_about'] = sanitize_about
        app.logger.info('✓ Registered Jinja filter: sanitize_about')
    except Exception as e:
        app.logger.warning(f'Could not register sanitize_about filter: {str(e)}')
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register request/response hooks
    register_hooks(app)
    
    # Health check route
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Codexx Academy Application is running'}, 200
    
    return app


def initialize_extensions(app):
    """Initialize Flask extensions with the app instance"""
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        try:
            from sqlalchemy import text
            db.create_all()
            # Verify connection
            db.session.execute(text('SELECT 1'))
            app.logger.info("✓ Database initialized successfully")
        except Exception as e:
            app.logger.error(f"✗ Database initialization failed: {str(e)}")


def register_blueprints(app):
    """Register all application blueprints"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(services_bp)


def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(400)
    def bad_request(e):
        from flask import render_template
        return render_template('400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('403.html'), 403
    
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        app.logger.error(f"Server Error: {str(e)}")
        return render_template('500.html'), 500
    
    @app.errorhandler(503)
    def service_unavailable(e):
        from flask import render_template
        return render_template('503.html'), 503
    
    @app.errorhandler(413)
    def file_too_large(e):
        from flask import flash, redirect, request
        flash('File is too large. Maximum size is 16MB.', 'error')
        return redirect(request.url), 413


def register_hooks(app):
    """Register request/response hooks and context processors"""
    
    @app.before_request
    def before_request():
        """Initialize request context"""
        # This will be used for session validation, rate limiting, etc.
        # Implementation will be in blueprints
        pass
    
    @app.context_processor
    def inject_global_vars():
        """Consolidated professional context processor for all templates"""
        from utils.helpers import get_unread_messages_count, get_visitor_count, get_clients_stats
        from utils.ui_helpers import inject_blueprint_assets, get_page_specific_class
        
        username = session.get('username')
        
        # Get current theme
        if username:
            user_data = load_data(username=username)
            current_theme = user_data.get('settings', {}).get('theme', 'luxury-gold')
        else:
            current_theme = 'luxury-gold'
        
        is_demo_mode = session.get('is_demo_mode', True)
        is_admin = session.get('is_admin', False)
        
        # Load admin social links strictly for the main platform footer
        admin_data = load_data(username='admin')
        admin_social = admin_data.get('social', {})

        # Default Meta Tags for SEO
        default_meta = {
            'title': 'Codexx Academy | Elite Proof-of-Work Ecosystem',
            'description': 'The premier ecosystem for verified professionals. Build in silence, show in public.',
            'keywords': 'Codexx Academy, Proof of Work, Elite Professionals, Portfolio Ecosystem'
        }
        
        # Get Blueprint-specific assets
        blueprint_assets = inject_blueprint_assets()
        
        # Get page-specific CSS class
        page_class = get_page_specific_class(
            blueprint_assets.get('current_blueprint'),
            request.endpoint.split('.')[-1] if request.endpoint else None
        )

        return {
            'current_theme': current_theme,
            'is_demo_mode': is_demo_mode,
            'is_admin': is_admin,
            'username': username,
            'current_year': datetime.now().year,
            'admin_social': admin_social,
            'default_meta': default_meta,
            'get_unread_messages_count': get_unread_messages_count,
            'get_visitor_count': get_visitor_count,
            'get_clients_stats': lambda: get_clients_stats(username),
            # Blueprint Assets
            'blueprint_styles': blueprint_assets.get('blueprint_styles', []),
            'blueprint_scripts': blueprint_assets.get('blueprint_scripts', []),
            'current_blueprint': blueprint_assets.get('current_blueprint'),
            'page_class': page_class
        }
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers['Content-Security-Policy'] = (
            "default-src *; "
            "script-src * 'unsafe-inline' 'unsafe-eval'; "
            "style-src * 'unsafe-inline'; "
            "font-src *; "
            "img-src * data: blob:; "
            "connect-src *; "
            "frame-ancestors *;"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


if __name__ == '__main__':
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Create app
    app = create_app(env)
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(env == 'development')
    )
