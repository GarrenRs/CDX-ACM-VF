"""
Data Management Module - Handles loading and saving portfolio data
Unified database layer using SQLAlchemy with backward compatibility for JSON
"""

import json
import os
from flask import current_app
from datetime import datetime
from extensions import db
from models import (
    Workspace, User, Project, Skill, Client, Message,
    VisitorLog, Service, NotificationSettings
)


def get_workspace_by_username(username):
    """Get workspace by username slug"""
    return Workspace.query.filter_by(slug=username).first()


def get_or_create_workspace(username, name=None):
    """Get or create workspace for a user"""
    workspace = get_workspace_by_username(username)
    if not workspace:
        workspace = Workspace(
            name=name or username,
            slug=username,
            description='',
            plan='pro'
        )
        db.session.add(workspace)
        db.session.commit()
    return workspace


def load_data(username=None):
    """
    Load portfolio data for a specific user or global data
    Uses database first, falls back to JSON for backward compatibility
    
    Args:
        username (str, optional): Username to load data for
        
    Returns:
        dict: User portfolio data or global data
    """
    try:
        # If username provided, load from database
        if username:
            workspace = get_workspace_by_username(username)
            if workspace:
                return workspace_to_dict(workspace)
            else:
                # Fallback to JSON for backward compatibility
                return load_data_from_json(username=username)
        
        # Global data - return users list and portfolios dict
        users = User.query.all()
        workspaces = Workspace.query.all()
        
        # Build portfolios dict for landing page
        portfolios = {}
        for ws in workspaces:
            portfolios[ws.slug] = {
                'name': ws.name,
                'title': ws.title or '',
                'description': ws.description or '',
                'about': ws.about or '',
                'photo': ws.photo or '',
                'username': ws.slug,
                'is_verified': False  # Will be updated from users
            }
        
        return {
            'users': [user_to_dict(u) for u in users],
            'portfolios': portfolios
        }
    except Exception as e:
        current_app.logger.error(f"Error loading data: {str(e)}")
        # Fallback to JSON
        return load_data_from_json(username=username)


def workspace_to_dict(workspace):
    """Convert workspace model to dictionary"""
    if not workspace:
        return get_default_portfolio_data()
    
    # Get all related data
    skills = [{'name': s.name, 'level': s.level} for s in workspace.skills]
    projects = [project_to_dict(p) for p in workspace.projects]
    clients = [client_to_dict(c) for c in workspace.clients]
    messages = [message_to_dict(m) for m in workspace.messages]
    services = [service_to_dict(s) for s in workspace.services]
    
    # Get visitor logs
    visitor_logs = VisitorLog.query.filter_by(workspace_id=workspace.id).all()
    today_visits = []
    unique_ips = set()
    for log in visitor_logs:
        if log.created_at.date() == datetime.utcnow().date():
            today_visits.append({
                'ip': log.ip_address,
                'timestamp': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'date': log.created_at.strftime('%Y-%m-%d')
            })
        unique_ips.add(log.ip_address)
    
    # Get notification settings
    notifications = {}
    notif_settings = NotificationSettings.query.filter_by(workspace_id=workspace.id).first()
    if notif_settings and notif_settings.telegram_bot_token:
        notifications['telegram'] = {
            'bot_token': notif_settings.telegram_bot_token,
            'chat_id': notif_settings.telegram_chat_id,
            'configured_at': notif_settings.telegram_configured_at.strftime('%Y-%m-%d %H:%M:%S') if notif_settings.telegram_configured_at else None
        }
    
    return {
        'username': workspace.slug,
        'name': workspace.name,
        'title': workspace.title or '',
        'description': workspace.description or '',
        'about': workspace.about or '',
        'photo': workspace.photo or '',
        'skills': skills,
        'projects': projects,
        'clients': clients,
        'messages': messages,
        'services': services,
        'contact': workspace.contact or {},
        'social': workspace.social or {},
        'settings': workspace.settings or {'theme': 'luxury-gold'},
        'visitors': {
            'total': len(visitor_logs),
            'today': today_visits,
            'unique_ips': list(unique_ips)
        },
        'notifications': notifications
    }


def project_to_dict(project):
    """Convert project model to dictionary"""
    result = {
        'id': project.id,
        'title': project.title,
        'description': project.description or '',
        'short_description': project.short_description or '',
        'content': project.content or '',
        'image': project.image or '',
        'demo_url': project.demo_url or '',
        'github_url': project.github_url or '',
        'technologies': project.technologies or [],
        'gallery': project.gallery or [],
        'skill_related': project.skill_related or [],
        'project_type': project.project_type or 'portfolio',
        'badge': project.badge or '',
        'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else None
    }
    
    if project.project_type == 'request':
        result.update({
            'request_budget_min': project.request_budget_min,
            'request_budget_max': project.request_budget_max,
            'request_deadline': project.request_deadline.strftime('%Y-%m-%d') if project.request_deadline else None,
            'request_status': project.request_status or 'open'
        })
    
    return result


def client_to_dict(client):
    """Convert client model to dictionary"""
    return {
        'id': client.id,
        'name': client.name,
        'email': client.email or '',
        'phone': client.phone or '',
        'company': client.company or '',
        'project_title': client.project_title or '',
        'project_description': client.project_description or '',
        'status': client.status or 'lead',
        'price': client.price or '',
        'deadline': client.deadline.strftime('%Y-%m-%d') if client.deadline else None,
        'start_date': client.start_date.strftime('%Y-%m-%d') if client.start_date else None,
        'notes': client.notes or '',
        'created_at': client.created_at.strftime('%Y-%m-%d %H:%M:%S') if client.created_at else None,
        'status_updated_at': client.status_updated_at.strftime('%Y-%m-%d %H:%M:%S') if client.status_updated_at else None
    }


def message_to_dict(message):
    """Convert message model to dictionary"""
    return {
        'id': message.id,
        'name': message.name,
        'email': message.email,
        'message': message.message,
        'read': message.is_read,
        'category': message.category or 'portfolio',
        'sender_id': message.sender_id,
        'receiver_id': message.receiver_id,
        'date': message.created_at.strftime('%Y-%m-%d %H:%M:%S') if message.created_at else None
    }


def service_to_dict(service):
    """Convert service model to dictionary"""
    return {
        'id': service.id,
        'title': service.title,
        'description': service.description or '',
        'short_description': service.short_description or '',
        'category': service.category or '',
        'pricing_type': service.pricing_type or 'custom',
        'price_min': service.price_min,
        'price_max': service.price_max,
        'currency': service.currency or 'USD',
        'deliverables': service.deliverables or [],
        'duration': service.duration or '',
        'skills_required': service.skills_required or [],
        'image': service.image or '',
        'gallery': service.gallery or [],
        'is_active': service.is_active,
        'is_featured': service.is_featured,
        'created_at': service.created_at.isoformat() if service.created_at else None,
        'updated_at': service.updated_at.isoformat() if service.updated_at else None
    }


def user_to_dict(user):
    """Convert user model to dictionary"""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'password_hash': user.password_hash,
        'role': user.role,
        'is_demo': user.is_demo,
        'is_verified': user.is_verified,
        'must_change_password': user.must_change_password,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
    }


def get_default_portfolio_data():
    """Return default portfolio template"""
    return {
        'name': '',
        'title': 'Web Developer & Designer',
        'description': 'Welcome to my professional portfolio.',
        'skills': [],
        'projects': [],
        'services': [],
        'messages': [],
        'clients': [],
        'settings': {
            'theme': 'luxury-gold'
        },
        'visitors': {
            'total': 0,
            'today': [],
            'unique_ips': []
        }
    }


def save_data(user_data, username=None, auto_backup=True):
    """
    Save portfolio data to database
    Uses database first, falls back to JSON for backward compatibility
    
    Args:
        user_data (dict): Data to save
        username (str, optional): Username for data isolation
        auto_backup (bool): Create automatic backup before saving (default: True)
    """
    try:
        if not username:
            current_app.logger.warning("save_data called without username, falling back to JSON")
            return save_data_to_json(user_data, username, auto_backup)
        
        workspace = get_or_create_workspace(username, user_data.get('name'))
        
        # Update workspace fields
        workspace.name = user_data.get('name', workspace.name)
        workspace.title = user_data.get('title', '')
        workspace.description = user_data.get('description', '')
        workspace.photo = user_data.get('photo', '')
        workspace.about = user_data.get('about', '')
        workspace.contact = user_data.get('contact', {})
        workspace.social = user_data.get('social', {})
        workspace.settings = user_data.get('settings', {'theme': 'luxury-gold'})
        
        # Update skills
        if 'skills' in user_data:
            # Delete existing skills
            Skill.query.filter_by(workspace_id=workspace.id).delete()
            # Add new skills
            for skill_data in user_data.get('skills', []):
                skill = Skill(
                    workspace_id=workspace.id,
                    name=skill_data.get('name', ''),
                    level=skill_data.get('level', 50)
                )
                db.session.add(skill)
        
        # Projects, clients, messages, services are managed through their own routes
        # This function only saves portfolio-level data
        
        db.session.commit()
        current_app.logger.info(f"Saved data for workspace: {username}")
        
    except Exception as e:
        current_app.logger.error(f"Error saving data to database: {str(e)}")
        db.session.rollback()
        # Fallback to JSON
        return save_data_to_json(user_data, username, auto_backup)


# Backward compatibility functions for JSON
def load_data_from_json(username=None):
    """Load data from JSON file (backward compatibility)"""
    try:
        data = {}
        if os.path.exists('data.json'):
            with open('data.json', 'r', encoding='utf-8') as file:
                data = json.load(file)

        if username:
            portfolios = data.get('portfolios', {})
            if username in portfolios:
                user_data = portfolios[username]
                # Backward compatibility: Add project_type and badge to old projects
                if 'projects' in user_data:
                    from .badges import determine_badge
                    for project in user_data['projects']:
                        if 'project_type' not in project:
                            project['project_type'] = 'portfolio'
                        if 'badge' not in project:
                            project['badge'] = determine_badge(project.get('project_type', 'portfolio'))
                return user_data
            else:
                return get_default_portfolio_data()
        return data
    except Exception as e:
        current_app.logger.error(f"Error loading data from JSON: {str(e)}")
        return {}


def save_data_to_json(user_data, username=None, auto_backup=True):
    """Save data to JSON file (backward compatibility)"""
    try:
        if auto_backup and os.path.exists('data.json'):
            try:
                from .helpers import create_backup
                create_backup(manual=False)
            except Exception as backup_error:
                current_app.logger.warning(f"Auto-backup failed: {str(backup_error)}")
        
        all_data = {}
        if os.path.exists('data.json'):
            with open('data.json', 'r', encoding='utf-8') as file:
                all_data = json.load(file)

        if username:
            if 'portfolios' not in all_data:
                all_data['portfolios'] = {}
            all_data['portfolios'][username] = user_data
        else:
            all_data.update(user_data)

        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        current_app.logger.error(f"Error saving data to JSON: {str(e)}")


def get_current_theme(session_obj):
    """
    Get current user's theme for dashboard
    
    Args:
        session_obj: Flask session object
        
    Returns:
        str: Theme name
    """
    username = session_obj.get('username')
    if not username:
        return 'luxury-gold'
    user_data = load_data(username=username)
    return user_data.get('settings', {}).get('theme', 'luxury-gold')


def get_global_meta():
    """Get default SEO meta tags"""
    return {
        'title': 'Codexx Academy | Elite Proof-of-Work Ecosystem',
        'description': 'The premier ecosystem for verified professionals. Build in silence, show in public.',
        'keywords': 'Codexx Academy, Proof of Work, Elite Professionals, Portfolio Ecosystem'
    }
