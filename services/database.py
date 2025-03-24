from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import SQLALCHEMY_DATABASE_URI

# Use the main database connection URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
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