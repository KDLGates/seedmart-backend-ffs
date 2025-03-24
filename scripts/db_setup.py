import os
import ssl
import pg8000
from dotenv import load_dotenv
from config import Config

load_dotenv()

# Set up SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Parse the database URL to get connection parameters
url = Config.SQLALCHEMY_DATABASE_URI
if url.startswith('postgresql://'):
    url = url.replace('postgresql://', '')

# Split URL into components
auth, rest = url.split('@')
user_pass, host_port_db = auth, rest
user, password = user_pass.split(':')
host_port, db = host_port_db.split('/')
host, port = host_port.split(':') if ':' in host_port else (host_port, '5432')

# Remove query parameters from database name if present
db = db.split('?')[0]

# Connect to default postgres database first
conn = pg8000.connect(
    host=host,
    database='postgres',  # Connect to postgres database initially
    user=user,
    password=password,
    port=int(port),
    ssl_context=ssl_context
)

conn.autocommit = True
cursor = conn.cursor()

# Create database if it doesn't exist
cursor.execute("SELECT 1 FROM pg_database WHERE datname=?", (db,))
if not cursor.fetchone():
    cursor.execute(f"CREATE DATABASE {db}")
    print(f"Database {db} created.")
else:
    print(f"Database {db} already exists.")

# Close connection
cursor.close()
conn.close()