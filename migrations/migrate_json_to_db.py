"""
Migration Script: JSON to PostgreSQL
Migrates all data from data.json to PostgreSQL database

Usage:
    python migrations/migrate_json_to_db.py
"""

import os
import sys
import json
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_new import create_app
from extensions import db
from models import (
    Workspace, User, Project, Skill, Client, Message, 
    VisitorLog, Service, NotificationSettings
)


def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    try:
        # Try different date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except:
        return None


def migrate_users(data):
    """Migrate users from JSON to database"""
    users_data = data.get('users', [])
    print(f"Migrating {len(users_data)} users...")
    
    for user_json in users_data:
        username = user_json.get('username')
        if not username:
            continue
            
        # Find or create workspace for this user
        workspace = Workspace.query.filter_by(slug=username).first()
        if not workspace:
            workspace = Workspace(
                name=user_json.get('name', username),
                slug=username,
                description='',
                plan='pro'
            )
            db.session.add(workspace)
            db.session.flush()
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"  User {username} already exists, skipping...")
            continue
        
        # Check if email already exists, generate unique email if needed
        email = user_json.get('email', f'{username}@example.com')
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            email = f'{username}_{workspace.id[:8]}@example.com'
            print(f"  Warning: Email conflict for {username}, using {email}")
        
        # Create user
        user = User(
            workspace_id=workspace.id,
            username=username,
            email=email,
            password_hash=user_json.get('password_hash', generate_password_hash('password')),
            role=user_json.get('role', 'user'),
            is_active=True,
            is_verified=user_json.get('is_verified', False),
            is_demo=user_json.get('is_demo', False),
            must_change_password=user_json.get('must_change_password', False),
            created_at=parse_date(user_json.get('created_at'))
        )
        db.session.add(user)
        print(f"  [OK] Migrated user: {username}")
    
    db.session.commit()


def migrate_portfolio(portfolio_data, username):
    """Migrate a single portfolio to database"""
    workspace = Workspace.query.filter_by(slug=username).first()
    if not workspace:
        print(f"  Workspace not found for {username}, skipping portfolio...")
        return
    
    # Update workspace with portfolio data
    workspace.name = portfolio_data.get('name', username)
    workspace.title = portfolio_data.get('title', '')
    workspace.description = portfolio_data.get('description', '')
    workspace.photo = portfolio_data.get('photo', '')
    workspace.about = portfolio_data.get('about', '')
    workspace.contact = portfolio_data.get('contact', {})
    workspace.social = portfolio_data.get('social', {})
    workspace.settings = portfolio_data.get('settings', {'theme': 'luxury-gold'})
    
    # Migrate skills
    skills_data = portfolio_data.get('skills', [])
    print(f"  Migrating {len(skills_data)} skills...")
    for skill_json in skills_data:
        skill = Skill(
            workspace_id=workspace.id,
            name=skill_json.get('name', ''),
            level=skill_json.get('level', 50),
            created_at=datetime.utcnow()
        )
        db.session.add(skill)
    
    # Migrate projects
    projects_data = portfolio_data.get('projects', [])
    print(f"  Migrating {len(projects_data)} projects...")
    for project_json in projects_data:
        project = Project(
            workspace_id=workspace.id,
            title=project_json.get('title', ''),
            description=project_json.get('description', ''),
            short_description=project_json.get('short_description', ''),
            content=project_json.get('content', ''),
            image=project_json.get('image', ''),
            demo_url=project_json.get('demo_url', ''),
            github_url=project_json.get('github_url', ''),
            technologies=project_json.get('technologies', []),
            gallery=project_json.get('gallery', []),
            skill_related=project_json.get('skill_related', []),
            project_type=project_json.get('project_type', 'portfolio'),
            badge=project_json.get('badge', ''),
            request_budget_min=project_json.get('request_budget_min'),
            request_budget_max=project_json.get('request_budget_max'),
            request_deadline=parse_date(project_json.get('request_deadline')),
            request_status=project_json.get('request_status'),
            created_at=parse_date(project_json.get('created_at')) or datetime.utcnow()
        )
        db.session.add(project)
    
    # Migrate clients
    clients_data = portfolio_data.get('clients', [])
    print(f"  Migrating {len(clients_data)} clients...")
    for client_json in clients_data:
        client = Client(
            workspace_id=workspace.id,
            name=client_json.get('name', ''),
            email=client_json.get('email', ''),
            phone=client_json.get('phone', ''),
            company=client_json.get('company', ''),
            project_title=client_json.get('project_title', ''),
            project_description=client_json.get('project_description', ''),
            status=client_json.get('status', 'lead'),
            price=client_json.get('price', ''),
            deadline=parse_date(client_json.get('deadline')),
            start_date=parse_date(client_json.get('start_date')),
            notes=client_json.get('notes', ''),
            created_at=parse_date(client_json.get('created_at')) or datetime.utcnow(),
            status_updated_at=parse_date(client_json.get('status_updated_at'))
        )
        db.session.add(client)
    
    # Migrate messages
    messages_data = portfolio_data.get('messages', [])
    print(f"  Migrating {len(messages_data)} messages...")
    for msg_json in messages_data:
        message = Message(
            workspace_id=workspace.id,
            name=msg_json.get('name', ''),
            email=msg_json.get('email', ''),
            message=msg_json.get('message', ''),
            is_read=msg_json.get('read', False),
            category=msg_json.get('category', 'portfolio'),
            sender_id=msg_json.get('sender_id'),
            receiver_id=msg_json.get('receiver_id'),
            is_internal=(msg_json.get('category') == 'internal'),
            created_at=parse_date(msg_json.get('date')) or datetime.utcnow()
        )
        db.session.add(message)
    
    # Migrate visitor logs
    visitors_data = portfolio_data.get('visitors', {})
    today_visits = visitors_data.get('today', [])
    print(f"  Migrating {len(today_visits)} visitor logs...")
    for visit_json in today_visits:
        ip = visit_json.get('ip', visit_json.get('ip_address', ''))
        if ip:
            visit = VisitorLog(
                workspace_id=workspace.id,
                ip_address=ip,
                created_at=parse_date(visit_json.get('timestamp') or visit_json.get('date'))
            )
            db.session.add(visit)
    
    # Migrate services
    services_data = portfolio_data.get('services', [])
    print(f"  Migrating {len(services_data)} services...")
    for service_json in services_data:
        service = Service(
            workspace_id=workspace.id,
            title=service_json.get('title', ''),
            description=service_json.get('description', ''),
            short_description=service_json.get('short_description', ''),
            category=service_json.get('category', ''),
            pricing_type=service_json.get('pricing_type', 'custom'),
            price_min=service_json.get('price_min'),
            price_max=service_json.get('price_max'),
            currency=service_json.get('currency', 'USD'),
            deliverables=service_json.get('deliverables', []),
            duration=service_json.get('duration', ''),
            skills_required=service_json.get('skills_required', []),
            image=service_json.get('image', ''),
            gallery=service_json.get('gallery', []),
            is_active=service_json.get('is_active', True),
            is_featured=service_json.get('is_featured', False),
            created_at=parse_date(service_json.get('created_at')) or datetime.utcnow()
        )
        db.session.add(service)
    
    # Migrate notification settings
    notifications = portfolio_data.get('notifications', {})
    telegram = notifications.get('telegram', {})
    if telegram.get('bot_token'):
        notif_settings = NotificationSettings.query.filter_by(workspace_id=workspace.id).first()
        if not notif_settings:
            notif_settings = NotificationSettings(workspace_id=workspace.id)
        notif_settings.telegram_bot_token = telegram.get('bot_token')
        notif_settings.telegram_chat_id = telegram.get('chat_id')
        notif_settings.telegram_configured_at = parse_date(telegram.get('configured_at'))
        db.session.add(notif_settings)
    
    db.session.commit()
    print(f"  [OK] Completed migration for portfolio: {username}")


def main():
    """Main migration function"""
    print("=" * 60)
    print("JSON to PostgreSQL Migration Script")
    print("=" * 60)
    
    # Create app and context
    app = create_app()
    with app.app_context():
        # Create all tables
        print("\nCreating database tables...")
        db.create_all()
        print("[OK] Database tables created")
        
        # Load JSON data
        json_file = 'data.json'
        if not os.path.exists(json_file):
            print(f"Error: {json_file} not found!")
            return
        
        print(f"\nLoading data from {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Migrate users first
        print("\n" + "=" * 60)
        print("STEP 1: Migrating Users")
        print("=" * 60)
        migrate_users(data)
        
        # Migrate portfolios
        print("\n" + "=" * 60)
        print("STEP 2: Migrating Portfolios")
        print("=" * 60)
        portfolios = data.get('portfolios', {})
        for username, portfolio_data in portfolios.items():
            print(f"\nMigrating portfolio: {username}")
            migrate_portfolio(portfolio_data, username)
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Verify data in database")
        print("2. Update utils/data.py to use database instead of JSON")
        print("3. Test the application")
        print("4. Backup data.json before removing JSON dependency")


if __name__ == '__main__':
    main()
