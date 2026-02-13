"""
NewsData.io Client
Fetches news articles using the NewsData.io API.
"""
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('news_tracker')

class NewsDataClient:
    BASE_URL = "https://newsdata.io/api/1/news"
    
    def __init__(self, api_key):
        self.api_key = api_key
        
    def fetch_articles(self, query, language='en', country='in'):
        """
        Fetch articles from NewsData.io.
        
        Args:
            query (str): Search query (e.g., "Narendra Modi").
            language (str): Language code (default 'en').
            country (str): Country code (default 'in').
            
        Returns:
            dict: Raw API response.
        """
        params = {
            'apikey': self.api_key,
            'q': query,
            'language': language,
            'country': country,
            'image': 1, # Request images if available
        }
        
        try:
            logger.info(f"NewsData: Fetching for '{query}'...")
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            total_results = data.get('totalResults', 0)
            logger.info(f"NewsData: Found {total_results} results for '{query}'")
            
            return data
        except Exception as e:
            logger.error(f"NewsData API Error: {e}")
            return None
