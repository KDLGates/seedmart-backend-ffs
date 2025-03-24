import pg8000
import ssl
from config import Config

def get_db_connection():
    """
    Create and return a database connection using Config
    """
    try:
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

        conn = pg8000.connect(
            host=host,
            database=db,
            user=user,
            password=password,
            port=int(port),
            ssl_context=ssl_context
        )
        return conn
    except pg8000.Error as e:
        print(f"Database connection error: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    """Execute a query and optionally return results"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchall() if fetch else None
        conn.commit()
        return result
    finally:
        cursor.close()
        conn.close()
