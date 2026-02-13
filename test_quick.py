"""Quick test to verify Google News RSS and Dashboard work."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.google_news import GoogleNewsClient
from src.database import Database

# Test Google News RSS
print("=== Testing Google News RSS ===")
g = GoogleNewsClient()
articles = g.search('"Narendra Modi"', language='en', country='IN', max_results=5)
print(f"Found {len(articles)} articles from Google News RSS")
for a in articles[:5]:
    print(f"  [{a['source']}] {a['title'][:80]}")

# Test DB
print("\n=== Testing Database ===")
db = Database()
stats = db.get_statistics()
print(f"DB Stats: {stats}")

print("\n=== All modules working! ===")
print("Run 'python main.py' to start the full system.")
