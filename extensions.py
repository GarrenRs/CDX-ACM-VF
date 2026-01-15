"""
Extensions Module - Centralized initialization of Flask extensions
Decouples extensions from the main app.py to avoid circular imports
and enable better testing.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions without binding to app
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

__all__ = ['db', 'login_manager']
