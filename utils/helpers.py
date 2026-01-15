"""
Helpers Module - Utility functions for common operations
"""

import os
import json
import shutil
from datetime import datetime
from flask import current_app
from .data import load_data


def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def create_backup(manual=True):
    """Create a backup of data.json to backups folder"""
    try:
        if not os.path.exists('data.json'):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f'backup_{timestamp}.json'
        backup_path = os.path.join('backups', backup_filename)

        os.makedirs('backups', exist_ok=True)

        with open('data.json', 'r', encoding='utf-8') as original:
            backup_content = original.read()
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(backup_content)

        file_size = os.path.getsize(backup_path) / 1024

        backup_info = {
            'filename': backup_filename,
            'timestamp': datetime.now().isoformat(),
            'size_kb': round(file_size, 2),
            'type': 'manual' if manual else 'automatic'
        }

        save_backup_metadata(backup_info)
        keep_recent_backups(max_backups=20)

        return backup_info
    except Exception as e:
        current_app.logger.error(f"Error creating backup: {str(e)}")
        return None


def save_backup_metadata(backup_info):
    """Save backup metadata to JSON file"""
    try:
        os.makedirs('backups', exist_ok=True)
        metadata_file = 'backups/backups.json'
        backups_list = []

        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backups_list = json.load(f)

        backups_list.append(backup_info)

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(backups_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        current_app.logger.error(f"Error saving backup metadata: {str(e)}")


def get_backups_list():
    """Get list of all backups with metadata"""
    try:
        metadata_file = 'backups/backups.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backups = json.load(f)
                return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        return []
    except Exception as e:
        current_app.logger.error(f"Error reading backups list: {str(e)}")
        return []


def keep_recent_backups(max_backups=20):
    """Keep only the most recent backups"""
    try:
        backups = get_backups_list()
        if len(backups) > max_backups:
            to_delete = backups[max_backups:]
            for backup in to_delete:
                backup_path = os.path.join('backups', backup['filename'])
                if os.path.exists(backup_path):
                    os.remove(backup_path)

            updated_backups = backups[:max_backups]
            with open('backups/backups.json', 'w', encoding='utf-8') as f:
                json.dump(updated_backups, f, ensure_ascii=False, indent=2)
    except Exception as e:
        current_app.logger.error(f"Error cleaning old backups: {str(e)}")


def get_unread_messages_count():
    """Get count of unread messages for current user or admin"""
    try:
        from flask import session
        from models import Message, User
        from extensions import db
        
        username = session.get('username')
        is_admin = session.get('is_admin', False)
        
        if not username:
            return 0
        
        if is_admin:
            # Admin sees platform messages and internal messages to admin
            unread_count = Message.query.filter(
                Message.is_read == False,
                db.or_(
                    Message.workspace_id.is_(None),  # Platform messages
                    Message.receiver_id == 'admin',  # Messages to admin
                    Message.category == 'platform'
                )
            ).count()
        else:
            # Get user from database
            user = User.query.filter_by(username=username).first()
            if not user:
                return 0
            
            # Count unread messages TO user (portfolio from visitors + internal from admin)
            unread_count = Message.query.filter(
                Message.is_read == False,
                Message.parent_id.is_(None),  # Only main messages
                db.or_(
                    # Portfolio messages from visitors
                    db.and_(
                        Message.workspace_id == user.workspace_id,
                        Message.category == 'portfolio',
                        db.or_(
                            Message.sender_id.is_(None),  # Visitor
                            Message.sender_id != str(user.id)
                        )
                    ),
                    # Internal from admin
                    db.and_(
                        Message.category == 'internal',
                        Message.sender_role == 'admin',
                        Message.receiver_id == str(user.id)
                    )
                )
            ).count()
        
        return unread_count
    except Exception as e:
        current_app.logger.error(f"Error getting unread messages count: {str(e)}")
        return 0


def get_visitor_count():
    """Get visitor count for current user's portfolio"""
    try:
        from flask import session
        username = session.get('username')
        if not username:
            return 0
        
        user_data = load_data(username=username)
        visitors = user_data.get('visitors', {})
        return visitors.get('total', 0)
    except Exception as e:
        current_app.logger.error(f"Error getting visitor count: {str(e)}")
        return 0


def get_clients_stats(username=None):
    """Get client statistics for user"""
    try:
        if not username:
            from flask import session
            username = session.get('username')
        
        if not username:
            return {'total': 0, 'active': 0, 'pending': 0, 'revenue': 0.0, 'recent': []}
        
        user_data = load_data(username=username)
        clients = user_data.get('clients', [])
        
        total_clients = len(clients)
        active_clients = len([c for c in clients if c.get('status') in ['in-progress', 'negotiation']])
        pending_clients = len([c for c in clients if c.get('status') == 'lead'])
        
        # Calculate total revenue from clients with prices
        total_revenue = 0.0
        for c in clients:
            price = c.get('price', '')
            if price:
                try:
                    # Remove any non-numeric characters except decimal point
                    price_clean = ''.join(ch for ch in str(price) if ch.isdigit() or ch == '.')
                    if price_clean:
                        total_revenue += float(price_clean)
                except (ValueError, TypeError):
                    pass
        
        return {
            'total': total_clients,
            'active': active_clients,
            'pending': pending_clients,
            'revenue': total_revenue,
            'recent': clients[-5:] if clients else []
        }
    except Exception as e:
        current_app.logger.error(f"Error getting client stats: {str(e)}")
        return {'total': 0, 'active': 0, 'pending': 0, 'revenue': 0.0, 'recent': []}


def track_visitor(username=None):
    """Track visitor to user's portfolio"""
    try:
        from flask import session
        from .security import get_client_ip
        
        if not username:
            username = session.get('username')
        
        if not username:
            return

        user_data = load_data(username=username)
        from .data import save_data
        
        if 'visitors' not in user_data:
            user_data['visitors'] = {
                'total': 0,
                'today': [],
                'unique_ips': []
            }

        client_ip = get_client_ip()
        
        # Track unique IPs
        if client_ip not in user_data['visitors']['unique_ips']:
            user_data['visitors']['unique_ips'].append(client_ip)

        # Increment total
        user_data['visitors']['total'] += 1

        # Track today's visits
        today = datetime.now().strftime('%Y-%m-%d')
        today_record = {
            'date': today,
            'ip': client_ip,
            'time': datetime.now().strftime('%H:%M:%S')
        }
        user_data['visitors']['today'].append(today_record)

        # Keep only last 1000 visitors
        if len(user_data['visitors']['today']) > 1000:
            user_data['visitors']['today'] = user_data['visitors']['today'][-1000:]

        save_data(user_data, username=username)
    except Exception as e:
        current_app.logger.error(f"Error tracking visitor: {str(e)}")


def sanitize_about(text: str) -> str:
    """Sanitize and normalize the 'about' field for safe rendering in the portfolio.

    - Removes <script> and <style> blocks
    - Preserves a small set of safe tags (p, br, strong, em, ul, ol, li, span)
    - Keeps `class` attribute only on <span> elements to allow badges
    - If input contains no HTML, converts double-newlines into paragraphs and single newlines into <br>
    """
    try:
        import re
        if not text:
            return ''

        # Normalize newlines, collapse multiple blank lines, and trim whitespace
        txt = text.replace('\r\n', '\n').replace('\r', '\n')
        txt = re.sub(r'\n\s*\n+', '\n\n', txt)
        txt = txt.strip()

        # Remove script/style blocks entirely
        txt = re.sub(r'<(script|style).*?>.*?</\1>', '', txt, flags=re.I | re.S)

        # If there's no HTML-like content, convert plain text to paragraphs
        if '<' not in txt and '>' not in txt:
            # Escape HTML-sensitive characters
            from markupsafe import escape
            escaped = escape(txt).strip()
            # Convert paragraphs and filter out empty ones
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', escaped) if p.strip()]
            paragraphs = [p.replace('\n', '<br>\n') for p in paragraphs]
            wrapped = ''.join(f'<p>{p}</p>' for p in paragraphs)
            return wrapped

        # For content that contains HTML, remove disallowed tags but preserve allowed ones
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'span', 'b', 'i', 'u']

        # Remove all tags that are not allowed, keep their inner text
        txt = re.sub(r'</?(?!(' + '|'.join(allowed_tags) + r')\b)[^>]*>', '', txt, flags=re.I)

        # For allowed tags, strip attributes except class on span
        # Remove attributes generally
        def _strip_attrs(match):
            tag = match.group(1).lower()
            attrs = match.group(2) or ''
            if tag == 'span':
                # preserve only class attribute and sanitize its value
                m = re.search(r'class\s*=\s*"([^"]+)"', attrs)
                cls = ''
                if m:
                    # keep only safe characters in class
                    cls_val = re.sub(r'[^a-zA-Z0-9_\-\s]', '', m.group(1))
                    cls = f' class="{cls_val}"'
                return f'<{tag}{cls}>'
            # other tags: no attrs
            return f'<{tag}>'

        txt = re.sub(r'<(\w+)([^>]*)>', _strip_attrs, txt, flags=re.I)

        # Collapse multiple <br> into a single <br>
        txt = re.sub(r'(?:(?:<br\s*/?>)\s*){2,}', '<br>\n', txt, flags=re.I)

        # Collapse multiple blank lines into paragraph breaks
        blocks = [b.strip() for b in re.split(r'\n\s*\n', txt) if b.strip()]
        normalized_blocks = []
        for block in blocks:
            if '<p' in block.lower():
                normalized_blocks.append(block)
            else:
                # replace single newlines with <br>
                b_html = block.replace('\n', '<br>\n')
                normalized_blocks.append(f'<p>{b_html}</p>')
        txt = ''.join(normalized_blocks)

        # Trim leading/trailing whitespace and remove leading/trailing <br> and empty <p> tags
        txt = txt.strip()
        txt = re.sub(r'^(?:\s|(?:<br\s*/?>))+', '', txt, flags=re.I)
        txt = re.sub(r'(?:\s|(?:<br\s*/?>))+$', '', txt, flags=re.I)
        # remove empty paragraphs at start/end
        txt = re.sub(r'^(?:<p>\s*</p>)+', '', txt, flags=re.I)
        txt = re.sub(r'(?:<p>\s*</p>)+$', '', txt, flags=re.I)

        return txt
    except Exception as e:
        current_app.logger.error(f"Error sanitizing about text: {str(e)}")
        return ''


__all__ = [
    'allowed_file',
    'create_backup',
    'save_backup_metadata',
    'get_backups_list',
    'keep_recent_backups',
    'get_unread_messages_count',
    'get_visitor_count',
    'get_clients_stats',
    'track_visitor',
    'sanitize_about'
]
