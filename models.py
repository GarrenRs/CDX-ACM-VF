from extensions import db
from datetime import datetime
from sqlalchemy import JSON
import uuid

# Custom JSON type that uses JSONB on PostgreSQL and JSON/Text on SQLite
class SafeJSON(db.TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    plan = db.Column(db.String(50), default='pro')
    # Portfolio fields
    title = db.Column(db.String(255))
    photo = db.Column(db.String(500))
    about = db.Column(db.Text)
    contact = db.Column(SafeJSON, default={})  # {email, phone, location}
    social = db.Column(SafeJSON, default={})  # {linkedin, github, twitter, facebook, etc}
    settings = db.Column(SafeJSON, default={'theme': 'luxury-gold'})
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='workspace', lazy=True, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='workspace', lazy=True, cascade='all, delete-orphan')
    skills = db.relationship('Skill', backref='workspace', lazy=True, cascade='all, delete-orphan')
    clients = db.relationship('Client', backref='workspace', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='workspace', lazy=True, cascade='all, delete-orphan')
    visitor_logs = db.relationship('VisitorLog', backref='workspace', lazy=True, cascade='all, delete-orphan')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_demo = db.Column(db.Boolean, default=False)
    badges = db.Column(SafeJSON, default=[]) # List of badges: ["verified", "top_expert", "master"]
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    content = db.Column(db.Text)
    image = db.Column(db.String(500))
    demo_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    technologies = db.Column(SafeJSON, default=[])
    gallery = db.Column(SafeJSON, default=[])
    skill_related = db.Column(SafeJSON, default=[])
    project_type = db.Column(db.String(50), default='portfolio')  # portfolio, training, request
    badge = db.Column(db.String(50))  # completed, training, request
    # Request-specific fields
    request_budget_min = db.Column(db.Float)
    request_budget_max = db.Column(db.Float)
    request_deadline = db.Column(db.Date)
    request_status = db.Column(db.String(50))  # open, closed, in-progress
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(255))
    project_title = db.Column(db.String(255))
    project_description = db.Column(db.Text)
    status = db.Column(db.String(50), default='lead')  # lead, in-progress, completed, cancelled
    price = db.Column(db.String(50))
    deadline = db.Column(db.Date)
    start_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_updated_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_internal = db.Column(db.Boolean, default=False) # True for chat/reply, False for public inquiry
    sender_id = db.Column(db.String(36)) # For internal messaging
    receiver_id = db.Column(db.String(36)) # For internal messaging
    parent_id = db.Column(db.String(36)) # To link replies to original message
    sender_role = db.Column(db.String(20), default='visitor')
    category = db.Column(db.String(30), default='portfolio') # 'platform', 'portfolio', 'internal'
    # Portfolio contact form fields
    request_type = db.Column(db.String(100))  # Type of request
    interest_area = db.Column(db.String(100))  # Area of interest
    seriousness = db.Column(db.String(50))  # Seriousness level
    contact_pref = db.Column(db.String(50))  # Preferred contact method
    company = db.Column(db.String(255))  # Company/Project name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VisitorLog(db.Model):
    __tablename__ = 'visitor_logs'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_visitor_workspace_date', 'workspace_id', 'created_at'),
    )


# Service Model for portfolio services
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    category = db.Column(db.String(100))  # web_dev, design, consulting, etc
    pricing_type = db.Column(db.String(50))  # fixed, hourly, custom
    price_min = db.Column(db.Float)
    price_max = db.Column(db.Float)
    currency = db.Column(db.String(10), default='USD')
    deliverables = db.Column(SafeJSON, default=[])
    duration = db.Column(db.String(100))
    skills_required = db.Column(SafeJSON, default=[])
    image = db.Column(db.String(500))
    gallery = db.Column(SafeJSON, default=[])
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    workspace_rel = db.relationship('Workspace', backref='services', lazy=True)


# Notification Settings Model
class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('workspaces.id'), nullable=False, unique=True)
    telegram_bot_token = db.Column(db.String(255))
    telegram_chat_id = db.Column(db.String(100))
    telegram_configured_at = db.Column(db.DateTime)
    smtp_config = db.Column(SafeJSON, default={})
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)