import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database Settings
    _database_url = os.environ.get('DATABASE_URL')
    if not _database_url:
        # Check for individual Replit DB secrets if DATABASE_URL is missing
        pg_user = os.environ.get('PGUSER')
        pg_pass = os.environ.get('PGPASSWORD')
        pg_host = os.environ.get('PGHOST')
        pg_port = os.environ.get('PGPORT')
        pg_db = os.environ.get('PGDATABASE')
        if all([pg_user, pg_pass, pg_host, pg_port, pg_db]):
            _database_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = _database_url or 'sqlite:///codexx.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/assets/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # JSON Settings
    JSON_AS_ASCII = False
    
    # Admin Settings
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # For in-memory SQLite during tests, keep engine options empty to avoid
    # passing invalid pool settings like pool_size to SQLite's StaticPool.
    SQLALCHEMY_ENGINE_OPTIONS = {}


# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
