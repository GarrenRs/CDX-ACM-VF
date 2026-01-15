"""
Pages Blueprint - Public static pages
Handles: About, Terms, Privacy, Verification, etc.
"""

from flask import Blueprint

pages_bp = Blueprint('pages', __name__, url_prefix='')

from . import routes
