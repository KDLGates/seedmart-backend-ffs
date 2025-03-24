from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
import psycopg2
import os

# Configure the PostgreSQL connection URL with SSL parameters included in the URI
SQLALCHEMY_DATABASE_URI = "postgresql://kdlgates:vM6B8tG4uZO7Eu5WyNEauGapBtJ1g6J1@dpg-cvgiol3tq21c73e4d3fg-a/seedmart_xie3?sslmode=require"

# Create engine with specific configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,         # Set connection pool size
    max_overflow=10      # Allow up to 10 extra connections
)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def close_session(session):
    session.close()

def get_db_connection():
    """Get a raw psycopg2 connection"""
    try:
        # Use the connection string directly - don't add additional parameters
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URI)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None