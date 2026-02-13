import re
from urllib.parse import urlparse

class ArticleValidator:
    @staticmethod
    def validate(article_data):
        """Validate article data"""
        if not article_data.get('title') or len(article_data['title']) < 5:
            return False, "Title must be at least 5 characters long and cannot be empty"
        
        url = article_data.get('url')
        if not url:
            return False, "URL is required"
            
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                 return False, "Invalid URL format"
        except:
             return False, "Invalid URL"
             
        return True, "Valid"

class QueryValidator:
    @staticmethod
    def validate(query):
        """Validate search query"""
        if not query:
            return False, "Query cannot be empty"
            
        if len(query) < 3:
            return False, "Query must be at least 3 characters long"
            
        if len(query) > 500:
             return False, "Query too long (max 500 characters)"
             
        return True, "Valid"
