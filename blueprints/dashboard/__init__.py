"""
Dashboard Blueprint - User dashboard management
Handles: All dashboard routes for managing portfolio, projects, clients, messages, etc.
"""

from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from . import routes
