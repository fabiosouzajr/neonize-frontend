import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    NEONIZE_SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sessions')
    NEONIZE_DB_PATH = os.path.join(NEONIZE_SESSION_DIR, 'neonize.db')
    
    # Ensure session directory exists
    os.makedirs(NEONIZE_SESSION_DIR, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}