"""
Notifications Module - Email and Telegram notifications
"""

import os
import smtplib
import json
import requests
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from .data import load_data


def get_admin_notifications_config():
    """Load admin-specific notification settings from environment variables"""
    return {
        'telegram': {
            'bot_token': current_app.config.get('ADMIN_TELEGRAM_BOT_TOKEN', ''),
            'chat_id': current_app.config.get('ADMIN_TELEGRAM_CHAT_ID', '')
        },
        'smtp': {
            'host': current_app.config.get('ADMIN_SMTP_HOST', ''),
            'port': current_app.config.get('ADMIN_SMTP_PORT', '587'),
            'email': current_app.config.get('ADMIN_SMTP_EMAIL', ''),
            'password': current_app.config.get('ADMIN_SMTP_PASSWORD', '')
        }
    }


def load_smtp_config(username=None):
    """
    Load SMTP configuration - user-specific ONLY (never admin config)
    
    IMPORTANT: This function NEVER returns admin SMTP config.
    Admin config is only accessible via get_admin_notifications_config()
    
    Args:
        username (str, optional): Username for user-specific config
        
    Returns:
        dict: SMTP configuration (user-specific or global user config, never admin)
    """
    # Try to load user-specific config first
    if username:
        try:
            user_data = load_data(username=username)
            if 'notifications' in user_data and 'smtp' in user_data['notifications']:
                smtp_cfg = user_data['notifications']['smtp']
                if all([
                    smtp_cfg.get('host'),
                    smtp_cfg.get('email'),
                    smtp_cfg.get('password')
                ]):
                    current_app.logger.debug(f"Loaded user-specific SMTP config for {username}")
                    return smtp_cfg
        except Exception as e:
            current_app.logger.debug(f"Could not load user SMTP config for {username}: {str(e)}")

    # Fall back to global user SMTP config (NOT admin config)
    # This is for backward compatibility with old smtp_config.json
    try:
        if os.path.exists('smtp_config.json'):
            with open('smtp_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Verify this is NOT admin config by checking if it matches admin env vars
                admin_config = get_admin_notifications_config()['smtp']
                if (config.get('host') == admin_config.get('host') and 
                    config.get('email') == admin_config.get('email')):
                    current_app.logger.warning("smtp_config.json matches admin config - ignoring to prevent mix-up")
                    return {}
                current_app.logger.debug("Loaded global user SMTP config from smtp_config.json")
                return config
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        current_app.logger.debug(f"Could not load global SMTP config: {str(e)}")
    return {}


def save_smtp_config(config):
    """Save SMTP configuration to file"""
    try:
        with open('smtp_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        current_app.logger.error(f"Error saving SMTP config: {str(e)}")
        return False


def send_email(recipient, subject, body, html=False, username=None):
    """
    Send email using SMTP - user-specific config ONLY (never admin config)
    
    IMPORTANT: This function ONLY uses user-specific SMTP credentials.
    It NEVER uses admin SMTP credentials.
    
    Args:
        recipient (str): Email recipient
        subject (str): Email subject
        body (str): Email body
        html (bool): Whether body is HTML
        username (str, optional): Username for user-specific config
        
    Returns:
        bool: Success status
    """
    try:
        smtp_config = load_smtp_config(username=username)
        if not all([
            smtp_config.get('host'),
            smtp_config.get('port'),
            smtp_config.get('email'),
            smtp_config.get('password')
        ]):
            current_app.logger.debug(f"SMTP config incomplete for user {username or 'global'}")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_config.get('email')
        msg['To'] = recipient

        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_config.get('host'),
                         int(smtp_config.get('port'))) as server:
            server.starttls()
            server.login(smtp_config.get('email'), smtp_config.get('password'))
            server.send_message(msg)

        current_app.logger.info(f"Email sent to {recipient} using user {username or 'global'} SMTP config")
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email to {recipient}: {str(e)}")
        return False


def send_admin_notification(subject, message_text, html_body=None):
    """
    Send notification to admin via Telegram and SMTP
    
    IMPORTANT: This function ONLY uses admin credentials from environment variables.
    It NEVER uses user credentials, even if admin config is missing.
    
    Args:
        subject (str): Notification subject
        message_text (str): Notification message
        html_body (str, optional): HTML version of the message
    """
    config = get_admin_notifications_config()
    
    # 1. Telegram Admin Notification (admin credentials only)
    tg_token = config['telegram']['bot_token']
    tg_chat = config['telegram']['chat_id']
    if tg_token and tg_chat:
        try:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {
                'chat_id': tg_chat,
                'text': f"🛡️ <b>[Academy Admin System]</b>\n📌 <b>{subject}</b>\n\n{message_text}",
                'parse_mode': 'HTML'
            }
            threading.Thread(target=lambda: requests.post(url, json=payload, timeout=10)).start()
            current_app.logger.info("Admin Telegram notification sent")
        except Exception as e:
            current_app.logger.error(f"Admin Telegram Error: {str(e)}")
    else:
        current_app.logger.debug("Admin Telegram credentials not configured")

    # 2. SMTP Admin Notification (admin credentials only)
    smtp_cfg = config['smtp']
    if all([smtp_cfg.get('host'), smtp_cfg.get('email'), smtp_cfg.get('password')]):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🛡️ [Academy Admin] {subject}"
            msg['From'] = smtp_cfg['email']
            msg['To'] = os.environ.get('ADMIN_RECIPIENT_EMAIL', smtp_cfg['email'])
            
            content = html_body if html_body else f"<h3>🛡️ Administrative Notification</h3><p>{message_text}</p>"
            msg.attach(MIMEText(content, 'html'))
            
            def _send():
                try:
                    with smtplib.SMTP(smtp_cfg['host'], int(smtp_cfg.get('port', 587))) as server:
                        server.starttls()
                        server.login(smtp_cfg['email'], smtp_cfg['password'])
                        server.send_message(msg)
                    current_app.logger.info("Admin SMTP notification sent")
                except Exception as e:
                    current_app.logger.error(f"Admin SMTP send error: {str(e)}")
            
            threading.Thread(target=_send).start()
        except Exception as e:
            current_app.logger.error(f"Admin SMTP Error: {str(e)}")
    else:
        current_app.logger.debug("Admin SMTP credentials not configured")


def send_user_notification(username, subject, message_text, html_body=None):
    """
    Send notification to specific user via their Telegram and SMTP settings
    
    IMPORTANT: This function ONLY uses user-specific credentials.
    It NEVER uses admin credentials, even if user config is missing.
    
    Args:
        username (str): Username of the recipient user
        subject (str): Notification subject
        message_text (str): Notification message
        html_body (str, optional): HTML version of the message
    """
    if not username:
        current_app.logger.error("send_user_notification called without username")
        return
    
    # 1. Telegram User Notification (user-specific only)
    tg_token, tg_chat = get_telegram_credentials(username=username)
    
    if tg_token and tg_chat:
        try:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {
                'chat_id': tg_chat,
                'text': f"💼 <b>[Your Professional Portfolio]</b>\n🔔 <b>{subject}</b>\n\n{message_text}",
                'parse_mode': 'HTML'
            }
            threading.Thread(target=lambda: requests.post(url, json=payload, timeout=10)).start()
            current_app.logger.info(f"User Telegram notification sent to {username}")
        except Exception as e:
            current_app.logger.error(f"User Telegram Error ({username}): {str(e)}")
    else:
        current_app.logger.debug(f"No Telegram credentials configured for user {username}")

    # 2. SMTP User Notification (user-specific only)
    smtp_cfg = load_smtp_config(username=username)
    user_email = smtp_cfg.get('email') or load_data(username=username).get('contact', {}).get('email')
    
    if user_email and smtp_cfg.get('host'):
        try:
            send_email(
                recipient=user_email,
                subject=f"💼 [Portfolio Notification] {subject}",
                body=message_text,
                html=bool(html_body),
                username=username
            )
            current_app.logger.info(f"User SMTP notification sent to {username} at {user_email}")
        except Exception as e:
            current_app.logger.error(f"User SMTP Error ({username}): {str(e)}")
    else:
        current_app.logger.debug(f"No SMTP configuration for user {username}")


def get_telegram_credentials(username=None):
    """
    Get Telegram credentials - user-specific ONLY (never admin config)
    
    IMPORTANT: This function NEVER returns admin Telegram credentials.
    Admin credentials are only accessible via get_admin_notifications_config()
    
    Args:
        username (str, optional): Username for user-specific credentials
        
    Returns:
        tuple: (bot_token, chat_id) or (None, None) if not found
    """
    if username:
        # Get user-specific credentials from their data
        try:
            user_data = load_data(username=username)
            
            if 'notifications' in user_data and 'telegram' in user_data['notifications']:
                telegram_cfg = user_data['notifications']['telegram']
                bot_token = telegram_cfg.get('bot_token', '')
                chat_id = telegram_cfg.get('chat_id', '')
                
                if bot_token and chat_id:
                    # Verify this is NOT admin config
                    admin_config = get_admin_notifications_config()['telegram']
                    if (bot_token == admin_config.get('bot_token') and 
                        chat_id == admin_config.get('chat_id')):
                        current_app.logger.warning(f"User {username} Telegram config matches admin config - ignoring to prevent mix-up")
                        return None, None
                    current_app.logger.debug(f"Loaded user-specific Telegram credentials for {username}")
                    return bot_token, chat_id
        except Exception as e:
            current_app.logger.debug(f"Could not load Telegram credentials for {username}: {str(e)}")

    # For user notifications, we MUST NOT fall back to admin or global
    return None, None


def send_telegram_notification(message_text, username=None):
    """
    Send Telegram notification to user (user credentials only)
    
    IMPORTANT: This function ONLY uses user-specific credentials.
    It NEVER uses admin credentials.
    
    Args:
        message_text (str): Message to send
        username (str, optional): Username for user-specific credentials
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not username:
        current_app.logger.warning("send_telegram_notification called without username - cannot send")
        return False
    
    bot_token, chat_id = get_telegram_credentials(username=username)
    
    if not (bot_token and chat_id):
        current_app.logger.debug(f"No Telegram credentials found for user {username}")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message_text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            current_app.logger.info(f"Telegram notification sent to user {username}")
            return True
        else:
            current_app.logger.error(f"Telegram API error for user {username}: {response.status_code}")
            return False
    except Exception as e:
        current_app.logger.error(f"Telegram notification error for user {username}: {str(e)}")
        return False


def send_telegram_event_notification(event_type, details=None, username=None):
    """Send event notification via Telegram"""
    if not details:
        details = f"Event: {event_type}"
    
    message = f"🔔 <b>Event Notification</b>\n\n<b>Type:</b> {event_type}\n<b>Details:</b> {details}"
    send_telegram_notification(message, username=username)


def send_event_notification_async(event_type, details=None, username=None):
    """Send event notification asynchronously - per-user"""
    thread = threading.Thread(target=send_telegram_event_notification, args=(event_type, details, username))
    thread.daemon = True
    thread.start()