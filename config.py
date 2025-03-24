import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret key from environment or use a secure default
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    DB_URL = os.environ.get('DB_URL')
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_PORT = os.environ.get('DB_PORT') or '5432'
    DB_NAME = os.environ.get('DB_NAME') or 'seedmart'
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # Disable SQL track modifications for performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application settings
    THREADS_PER_PAGE = 2
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = SECRET_KEY
    
    # AWS specific settings
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'
    
    # Redis cache config (if available)
    REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_TYPE = 'redis' if REDIS_URL else 'simple'