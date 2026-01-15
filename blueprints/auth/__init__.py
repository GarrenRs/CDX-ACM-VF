"""
Auth Blueprint - Authentication and authorization
Handles: Login, Logout, Password management
"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='')

from . import routes
