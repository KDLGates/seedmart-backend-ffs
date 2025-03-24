from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

# Use the main Config class for database connection
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    connect_args={
        "ssl": True,
        "ssl_cert_reqs": "NONE"
    }
)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def close_session(session):
    session.close()