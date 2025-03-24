from datetime import datetime, timedelta
from sqlalchemy import text
from models.models import SeedPrice
from database import SessionLocal
import os
import logging

# Configure logging for better AWS CloudWatch integration
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def cleanup_old_seed_prices():
    """
    Deletes SeedPrice records older than one year by using efficient SQL
    for better performance with large datasets.
    """
    # Use retention days from environment or default to 365
    retention_days = int(os.environ.get('DATA_RETENTION_DAYS', 365))
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    db = SessionLocal()
    try:
        # Use raw SQL for more efficient bulk deletion, especially important in production
        if os.environ.get('FLASK_ENV') == 'production':
            # More efficient batch deletion for production
            batch_size = 10000
            total_deleted = 0
            
            while True:
                # Get IDs of records to delete in batches
                stmt = text(
                    "DELETE FROM seed_prices WHERE id IN "
                    "(SELECT id FROM seed_prices WHERE recorded_at < :cutoff_date LIMIT :batch_size) "
                    "RETURNING id"
                )
                result = db.execute(stmt, {"cutoff_date": cutoff_date, "batch_size": batch_size})
                deleted_count = result.rowcount
                db.commit()
                
                total_deleted += deleted_count
                logger.info(f"Deleted batch of {deleted_count} records")
                
                if deleted_count < batch_size:
                    break
                    
            logger.info(f"Total deleted: {total_deleted} old seed price records")
        else:
            # Simpler approach for development
            deleted = db.query(SeedPrice).filter(SeedPrice.recorded_at < cutoff_date).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Deleted {deleted} old seed price records")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error during data cleanup: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Running manual data retention cleanup")
    cleanup_old_seed_prices()