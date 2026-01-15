"""
Security Module - Security utilities including IP tracking, rate limiting, and credentials
"""

import os
import json
import time
from datetime import datetime
from flask import request, current_app
from werkzeug.security import generate_password_hash, check_password_hash


# Rate Limiting
RATE_LIMIT_REQUESTS = {}  # {ip: [(timestamp, endpoint), ...]}
RATE_LIMIT_MAX_REQUESTS = 10  # Max 10 requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds
IP_LOG_FILE = 'security/ip_log.json'
AUDIT_LOG_FILE = 'security/audit_log.json'


def log_audit_event(event_type, username=None, details=''):
    """Log high-level audit events for administrative review"""
    try:
        log_data = {
            'event': event_type,
            'username': username,
            'details': details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(log_data)
        logs = logs[-1000:]

        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        current_app.logger.error(f"Error logging audit event: {str(e)}")


def get_client_ip():
    """Get real client IP address"""
    return request.environ.get('HTTP_X_FORWARDED_FOR',
                              request.environ.get('REMOTE_ADDR', 'unknown'))


def check_rate_limit(endpoint='contact'):
    """Check if IP is within rate limit"""
    client_ip = get_client_ip()
    current_time = time.time()

    if client_ip not in RATE_LIMIT_REQUESTS:
        RATE_LIMIT_REQUESTS[client_ip] = []

    # Clean old requests outside the window
    RATE_LIMIT_REQUESTS[client_ip] = [
        (ts, ep) for ts, ep in RATE_LIMIT_REQUESTS[client_ip]
        if current_time - ts < RATE_LIMIT_WINDOW
    ]

    # Check if limit exceeded
    endpoint_requests = [
        ep for ts, ep in RATE_LIMIT_REQUESTS[client_ip] if ep == endpoint
    ]
    if len(endpoint_requests) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Add current request
    RATE_LIMIT_REQUESTS[client_ip].append((current_time, endpoint))
    return True


def log_ip_activity(activity_type, details=''):
    """Log IP activity for security tracking"""
    try:
        client_ip = get_client_ip()
        log_data = {
            'ip': client_ip,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'activity': activity_type,
            'details': details,
            'user_agent': request.headers.get('User-Agent', 'Unknown')[:100]
        }

        # Load existing logs
        try:
            with open(IP_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(log_data)

        # Keep only last 1000 logs
        logs = logs[-1000:]

        os.makedirs(os.path.dirname(IP_LOG_FILE), exist_ok=True)
        with open(IP_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        current_app.logger.error(f"Error logging IP activity: {str(e)}")


def get_admin_credentials():
    """Load admin credentials from environment variables safely"""
    username = os.environ.get('ADMIN_USERNAME')
    password = os.environ.get('ADMIN_PASSWORD')
    if not username or not password:
        return {'username': None, 'password_hash': None}
    return {
        'username': username,
        'password_hash': generate_password_hash(password)
    }


def verify_password(password, password_hash):
    """Verify password against hash"""
    return check_password_hash(password_hash, password)


# Demo credentials
DEMO_USER_CREDENTIALS = {
    'username': 'demo_codexx',
    'password_hash': generate_password_hash('Demo_2026!'),
    'is_demo': True
}


__all__ = [
    'get_client_ip',
    'check_rate_limit',
    'log_ip_activity',
    'get_admin_credentials',
    'verify_password',
    'log_audit_event',
    'DEMO_USER_CREDENTIALS'
]
