"""
Google News RSS Feed Client.
Free secondary source for news aggregation.
Uses Google News RSS feeds to fetch articles about tracked persons.
"""
import re
import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus

import requests

logger = logging.getLogger('news_tracker')


class GoogleNewsClient:
    """Fetches articles from Google News RSS feed (free, no API key needed)."""

    BASE_URL = "https://news.google.com/rss/search"

    def search(self, query, language='en', country='IN', max_results=50):
        """
        Search Google News RSS for articles.

        Args:
            query: Search query string
            language: Language code (en, hi)
            country: Country code (IN)
            max_results: Max articles to return

        Returns:
            List of article dicts or empty list
        """
        try:
            encoded_query = quote_plus(query)
            url = f"{self.BASE_URL}?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"

            logger.info(f"Google RSS: Searching for '{query}' (lang={language})")
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            articles = self._parse_rss(response.text, max_results)
            logger.info(f"Google RSS: Found {len(articles)} articles for '{query}'")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Google RSS request failed: {e}")
            return []
        except Exception as e:
            logger.exception(f"Google RSS unexpected error: {e}")
            return []

    def _parse_rss(self, xml_text, max_results):
        """Parse RSS XML and extract articles."""
        articles = []
        try:
            root = ET.fromstring(xml_text)
            channel = root.find('channel')
            if channel is None:
                return articles

            items = channel.findall('item')
            for item in items[:max_results]:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                description = item.findtext('description', '')

                # Extract source from title (Google News adds " - SourceName" at end)
                source_name = 'Unknown'
                if ' - ' in title:
                    parts = title.rsplit(' - ', 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()

                # Clean HTML from description
                clean_desc = re.sub(r'<[^>]+>', '', description).strip()

                # Parse date
                parsed_date = self._parse_date(pub_date)

                articles.append({
                    'title': title[:500],
                    'link': link,
                    'summary': clean_desc[:5000] if clean_desc else '',
                    'source': source_name,
                    'published_date': pub_date,
                    'parsed_date': parsed_date,
                    'language': 'en',  # Will be set by caller
                })

            return articles
        except ET.ParseError as e:
            logger.error(f"Google RSS XML parse error: {e}")
            return []

    @staticmethod
    def _parse_date(date_str):
        """Parse RSS date format."""
        if not date_str:
            return datetime.utcnow()
        # RSS format: "Thu, 06 Feb 2025 12:00:00 GMT"
        formats = [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S %z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.utcnow()
