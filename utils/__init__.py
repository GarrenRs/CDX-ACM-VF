"""
Utils Package - Centralized utility modules initialization
"""

from .decorators import login_required, admin_required, disable_in_demo
from .data import load_data, save_data, get_current_theme, get_global_meta
from .notifications import (
    send_email,
    send_admin_notification,
    send_user_notification,
    get_telegram_credentials,
    send_telegram_notification,
    load_smtp_config,
    save_smtp_config
)
from .security import (
    get_client_ip,
    check_rate_limit,
    log_ip_activity,
    get_admin_credentials,
    verify_password,
    DEMO_USER_CREDENTIALS
)
from .helpers import (
    allowed_file,
    create_backup,
    get_backups_list,
    get_unread_messages_count,
    get_visitor_count,
    get_clients_stats,
    track_visitor
)
from .ui_helpers import (
    get_blueprint_styles,
    get_blueprint_scripts,
    inject_blueprint_assets,
    get_page_specific_class,
    get_ui_config
)

__all__ = [
    # Decorators
    'login_required',
    'admin_required',
    'disable_in_demo',
    
    # Data
    'load_data',
    'save_data',
    'get_current_theme',
    'get_global_meta',
    
    # Notifications
    'send_email',
    'send_admin_notification',
    'send_user_notification',
    'get_telegram_credentials',
    'send_telegram_notification',
    'load_smtp_config',
    'save_smtp_config',
    
    # Security
    'get_client_ip',
    'check_rate_limit',
    'log_ip_activity',
    'get_admin_credentials',
    'verify_password',
    'DEMO_USER_CREDENTIALS',
    
    # Helpers
    'allowed_file',
    'create_backup',
    'get_backups_list',
    'get_unread_messages_count',
    'get_visitor_count',
    'get_clients_stats',
    'track_visitor',
    
    # UI Helpers
    'get_blueprint_styles',
    'get_blueprint_scripts',
    'inject_blueprint_assets',
    'get_page_specific_class',
    'get_ui_config'
]
