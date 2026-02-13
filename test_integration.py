"""
Integration test for DataProcessor with NER.
"""
from src.data_processor import DataProcessor
import logging

# Configure logger to see debug messages from NER
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('news_tracker')
logger.setLevel(logging.DEBUG)

def test_integration():
    print("Initializing DataProcessor (loads NER model)...")
    dp = DataProcessor()
    
    print("\n--- Testing Integration ---")

    # Mock articles
    valid_article = {
        'title': 'PM Modi inaugurates new bridge',
        'link': 'http://example.com/1',
        'summary': 'Prime Minister Narendra Modi was present.',
        'published_date': '2025-01-01'
    }
    
    invalid_article = {
        'title': 'Rahul Gandhi visits Europe',
        'link': 'http://example.com/2',
        'summary': 'He spoke about policies.',
        'published_date': '2025-01-01'
    }

    ambiguous_article = {
        'title': 'Modi Toys launches new collection',
        'link': 'http://example.com/3',
        'summary': 'The toy company is growing fast.',
        'published_date': '2025-01-01'
    }
    
    # Test valid
    print(f"\nTesting Valid Article: '{valid_article['title']}'")
    res1 = dp._process_single_article(valid_article, 'Narendra Modi')
    print(f"Result: {'✅ Accepted' if res1 else '❌ Rejected (Failure)'}")
    
    # Test invalid
    print(f"\nTesting Invalid Article: '{invalid_article['title']}'")
    res2 = dp._process_single_article(invalid_article, 'Narendra Modi')
    print(f"Result: {'✅ Rejected' if not res2 else '❌ Accepted (Failure)'}")

    # Test ambiguous
    print(f"\nTesting Ambiguous Article (Toys): '{ambiguous_article['title']}'")
    res3 = dp._process_single_article(ambiguous_article, 'Narendra Modi')
    # Use generic result based on earlier NER test (it might accept it if ruler is aggressive)
    print(f"Result: {'Accepted' if res3 else 'Rejected'}")

if __name__ == "__main__":
    test_integration()
