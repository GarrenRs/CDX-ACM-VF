"""
Portfolio Blueprint - Public portfolio views
Handles: Portfolio display, project details, CV, contact forms
"""

from flask import Blueprint

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='')

from . import routes
