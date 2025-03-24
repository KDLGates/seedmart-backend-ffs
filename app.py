from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from config import Config
from models.models import db
from routes.api import api
from routes.auth import auth
from seed_db import seed_database
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.market import MarketService
from database import SQLALCHEMY_DATABASE_URI, engine
import atexit
import os

app = Flask(__name__)
app.config.from_object(Config)

# Use the database URL directly from database.py
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine.dialect.create_connect_args(engine.url)[1]

# JWT Configuration
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# IMPORTANT: Configure JWT to not block requests without JWT tokens
# This allows market data to be accessed without authentication
app.config['JWT_OPTIONAL'] = True

# CORS Configuration - Properly handle both development and production
# Get allowed origins - default to wildcard to ensure frontend can connect
origins = [os.environ.get('ALLOWED_ORIGINS', '*')]

# Add production domain automatically if on same hostname
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    # Add both http and https versions to be safe
    origins.append(f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}")
    origins.append(f"http://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}")

# Add ALB DNS if available (for AWS deployments)
alb_dns_name = os.environ.get('ALB_DNS_NAME')
if alb_dns_name:
    origins.append(f"http://{alb_dns_name}")
    origins.append(f"https://{alb_dns_name}")

print(f"CORS Origins: {origins}")

# Configure CORS with credentials support
CORS(app, 
     resources={r"/api/*": {"origins": origins}},
     supports_credentials=True)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Handle invalid tokens to prevent 500 errors - return 401 instead
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({
        'status': 'error',
        'message': 'Invalid token provided',
        'error': error_string
    }), 401

# Handle expired tokens
@jwt.expired_token_loader
def expired_token_callback(header, payload):
    return jsonify({
        'status': 'error',
        'message': 'Token has expired',
    }), 401

# Handle missing tokens for optional endpoints
@jwt.unauthorized_loader
def missing_token_callback(error_string):
    # This will allow endpoints without @jwt_required() to proceed
    # while providing proper error responses to endpoints that do require auth
    return jsonify({
        'status': 'error',
        'message': 'Authorization token is missing',
        'error': error_string
    }), 401

# Register blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(auth, url_prefix='/api/auth')

# Initialize scheduler with proper settings for production
scheduler = BackgroundScheduler(daemon=True)

# Function to wrap update_seed_prices with app context
def update_prices_with_context():
    with app.app_context():
        MarketService.update_seed_prices()

# Add market update job - runs every 30 seconds
scheduler.add_job(
    func=update_prices_with_context,
    trigger=IntervalTrigger(seconds=30),  # Increased to reduce database load
    id='update_market_prices',
    name='Update seed market prices',
    replace_existing=True,
    max_instances=1,
    coalesce=True  # Combine multiple pending runs into one
)

# Start the scheduler
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Health check endpoint for AWS ELB/ECS
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "SeedMart API is running"})

# Health check endpoint for API monitoring with database check
@app.route('/api/health', methods=['GET'])
def api_health_check():
    db_status = "Unknown"
    try:
        # Try a simple query to verify database connectivity
        db.session.execute("SELECT 1")
        db_status = "Connected"
    except Exception as e:
        db_status = f"Not Connected: {str(e)}"
    status = "OK" if db_status == "Connected" else "WARNING"
    return jsonify({
         "status": status,
         "message": "SeedMart API is running",
         "database": db_status
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
        
        # Only seed in development or if explicitly requested
        if os.environ.get('SEED_DATABASE') == 'true' or os.environ.get('FLASK_ENV') != 'production':
            seed_database()  # Seed the database if it's empty
    
    # Use production settings when deployed
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', debug=debug, threaded=True)