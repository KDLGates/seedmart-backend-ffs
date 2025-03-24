import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from data_retention import cleanup_old_seed_prices
from flask import Flask, current_app
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_scheduler(app: Flask):
    """
    Configure and start background tasks for the application using APScheduler.
    Optimized for running in AWS ECS/Fargate environment.
    """
    scheduler = BackgroundScheduler(daemon=True)
    
    # Register data retention job to run at 2 AM daily
    # This is a good time when server load is typically low
    scheduler.add_job(
        func=lambda: _run_with_app_context(app, cleanup_old_seed_prices),
        trigger=CronTrigger(hour=2, minute=0),
        id="data_retention_job",
        name="Remove old seed price records",
        max_instances=1,
        replace_existing=True,
        coalesce=True,  # Combine multiple executions into one if system was down
    )
    
    # Only add resource-intensive jobs if we have enough system resources
    # or if explicitly enabled through environment variables
    if os.environ.get('ENABLE_INTENSIVE_JOBS') == 'true':
        logger.info("Scheduling intensive maintenance jobs")
        # Add any resource-intensive maintenance jobs here
    
    # Start the scheduler
    scheduler.start()
    logger.info("Background scheduler started")
    
    # Register shutdown with Flask
    app.scheduler = scheduler  # Store reference to shut it down later
    
    return scheduler

def _run_with_app_context(app, func, *args, **kwargs):
    """
    Execute the given function within the Flask application context.
    This ensures that database models and other Flask extensions are accessible.
    """
    with app.app_context():
        try:
            logger.info(f"Running scheduled task: {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"Completed scheduled task: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in scheduled task {func.__name__}: {str(e)}")
            # In production, you might want to send an alert here

# This allows the scheduler to be tested independently
if __name__ == "__main__":
    # Create a test app just for demonstration
    test_app = Flask(__name__)
    configure_scheduler(test_app)
    
    # Keep the script running to test the scheduler
    try:
        logger.info("Scheduler running, press Ctrl+C to exit")
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        if hasattr(test_app, 'scheduler'):
            test_app.scheduler.shutdown()
        logger.info("Scheduler shut down successfully")