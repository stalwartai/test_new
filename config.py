import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    API_KEY = os.getenv('NEWSCATCHER_API_KEY')
    NEWSDATA_API_KEY = os.getenv('NEWSDATA_API_KEY', 'pub_6b98b1d8e5664e1bb95762fde5f2507d')
    API_BASE_URL = "https://v3-api.newscatcherapi.com/api/search"
    COUNTRY = 'IN'
    LANGUAGES = 'en,hi'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///news_tracker.db')
    SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR', 8))
    SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', 0))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'output')
    DAYS_TO_KEEP = int(os.getenv('DAYS_TO_KEEP', 90))

    @staticmethod
    def validate():
        if not Config.API_KEY:
            raise ValueError("NEWSCATCHER_API_KEY not found in environment variables")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(Config.OUTPUT_FOLDER):
            os.makedirs(Config.OUTPUT_FOLDER)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
