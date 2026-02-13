"""
Standalone script to run the News Scheduler.
Used by Docker entrypoint.
"""
import time
import signal
import sys
from src.scheduler import NewsScheduler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('news_tracker')

def handle_sigterm(*args):
    logger.info("Received SIGTERM, stopping scheduler...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    logger.info("Starting News Scheduler Service...")
    scheduler = NewsScheduler()
    scheduler.start()
    
    # Run a manual collection on startup
    logger.info("Running initial collection...")
    try:
        scheduler.run_news_collection()
    except Exception as e:
        logger.error(f"Error in initial collection: {e}")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("Scheduler stopped by user.")
