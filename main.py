"""
News Aggregator — Main Entry Point.
Runs both the news collector (scheduler) and the web dashboard (Flask).
"""
import os
import sys
import signal
import logging
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.logger import setup_logger
from src.scheduler import NewsScheduler
from src.dashboard import create_app

logger = setup_logger()


def main():
    try:
        logger.info("=" * 60)
        logger.info("Starting News Aggregator System")
        logger.info("=" * 60)

        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")

        # Initialize scheduler
        scheduler = NewsScheduler()

        # Run initial collection
        logger.info("Running initial data collection...")
        scheduler.run_now()

        # Start daily scheduler
        scheduler.start()

        # Start Flask dashboard in a separate thread
        app = create_app()
        dashboard_thread = threading.Thread(
            target=lambda: app.run(
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False
            ),
            daemon=True
        )
        dashboard_thread.start()
        logger.info("Dashboard running at http://localhost:5000")

        # Graceful shutdown
        def shutdown(signum, frame):
            logger.info("Shutting down...")
            scheduler.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        # Keep alive
        logger.info("System running. Press Ctrl+C to stop.")
        logger.info("Dashboard: http://localhost:5000")
        while True:
            signal.pause() if hasattr(signal, 'pause') else __import__('time').sleep(3600)

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        scheduler.stop()
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
