"""
Test script for NewsData.io integration.
"""
from src.newsdata_client import NewsDataClient
from src.data_processor import DataProcessor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)

def test_newsdata():
    print("Testing NewsData.io Integration...")
    
    # Initialize client
    api_key = Config.NEWSDATA_API_KEY
    if not api_key:
        print("❌ Error: NEWSDATA_API_KEY not found in Config.")
        return

    client = NewsDataClient(api_key)
    processor = DataProcessor()
    
    query = "Narendra Modi"
    print(f"Fetching articles for: {query}")
    
    response = client.fetch_articles(query, country='in')
    
    if not response or 'results' not in response:
        print("❌ Failed to fetch data or no results.")
        return

    articles = response['results']
    print(f"✅ Fetched {len(articles)} raw articles.")
    
    # Process
    print("Processing articles...")
    processed = processor.process_newsdata_articles(articles, "Narendra Modi")
    
    print(f"✅ Processed {len(processed)} articles.")
    
    if processed:
        print("\n--- Sample Article ---")
        art = processed[0]
        print(f"Title: {art['title']}")
        print(f"Source: {art['source_name']}")
        print(f"Date: {art['published_date']}")
        print(f"Data Source: {art['data_source']}")
        print("----------------------")

if __name__ == "__main__":
    test_newsdata()
