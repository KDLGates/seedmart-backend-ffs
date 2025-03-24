from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
import psycopg2
import os

# Configure the PostgreSQL connection URL
SQLALCHEMY_DATABASE_URI = "postgresql://kdlgates:vM6B8tG4uZO7Eu5WyNEauGapBtJ1g6J1@dpg-cvgiol3tq21c73e4d3fg-a/seedmart_xie3"

# Create engine with specific configuration and proper SSL settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,         # Set connection pool size
    max_overflow=10,     # Allow up to 10 extra connections
    connect_args={
        "sslmode": "require",  # Require SSL connection
        "sslrootcert": None    # Skip verification of SSL certificate
    }
)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def close_session(session):
    session.close()

def get_db_connection():
    """Get a raw psycopg2 connection"""
    try:
        conn = psycopg2.connect(
            SQLALCHEMY_DATABASE_URI,
            sslmode="require",
            sslrootcert=None
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None