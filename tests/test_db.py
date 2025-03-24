# Script to create a new database
import pg8000
import os
import ssl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up SSL context (same as before)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Disables certificate verification

# Connect to the default 'postgres' database (or another existing database)
conn = pg8000.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database="postgres",  # Connect to postgres or another existing database
    user=os.getenv("DB_USER", "kdlgates"),
    password=os.getenv("DB_PASSWORD", ""),
    port=int(os.getenv("DB_PORT", "5432")),
    ssl_context=ssl_context
)

# Important: Set autocommit for creating database
conn.autocommit = True

# Create a cursor
cursor = conn.cursor()

# Check if database exists already
cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'seedmart'")
exists = cursor.fetchone()

if not exists:
    # Create the new database
    print("Creating database 'seedmart'...")
    cursor.execute("CREATE DATABASE seedmart")
    print("Database 'seedmart' created successfully!")
else:
    print("Database 'seedmart' already exists.")

# Close connection
cursor.close()
conn.close()