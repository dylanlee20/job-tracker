"""
CSRF utilities for API endpoints

For JSON APIs, CSRF tokens should be sent via X-CSRFToken header
For web forms, Flask-WTF handles CSRF automatically
"""
from functools import wraps
from flask import request, jsonify
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest
import logging

logger = logging.getLogger(__name__)


def csrf_exempt_if_api_key(f):
    """
    Decorator to exempt API endpoints from CSRF if they use API key authentication

    For now, this just logs the exemption. In production, you should:
    1. Implement API key authentication
    2. Only exempt endpoints that use API keys
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For programmatic API access, you could check for API key here
        # api_key = request.headers.get('X-API-Key')
        # if api_key and validate_api_key(api_key):
        #     return f(*args, **kwargs)

        # Otherwise, CSRF protection is enforced by Flask-WTF
        return f(*args, **kwargs)

    return decorated_function


def get_csrf_token():
    """Generate and return a CSRF token for the current session"""
    return generate_csrf()
