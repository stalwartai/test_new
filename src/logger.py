import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name='news_tracker', log_level=logging.INFO):
    """Setup logger with console and file handlers with rotation"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Check if handlers specific to this logger are already added to avoid duplication
    if not logger.handlers:
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File Handler (10MB max, 5 backups)
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger
