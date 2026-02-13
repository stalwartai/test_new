"""
Data Processor — handles both clustered and unclustered article data.
Processes responses from NewsCatcher V3 and Google News RSS.
"""
import hashlib
import logging
from datetime import datetime
from .entity_recognizer import EntityRecognizer
from .vector_processor import VectorProcessor

logger = logging.getLogger('news_tracker')

# Category keywords for auto-classification
CATEGORY_KEYWORDS = {
    'Politics': ['election', 'parliament', 'bjp', 'congress', 'party', 'vote', 'campaign', 'political', 'minister', 'opposition', 'lok sabha', 'rajya sabha'],
    'Governance': ['policy', 'scheme', 'government', 'cabinet', 'ordinance', 'bill', 'reform', 'administration', 'governance', 'ministry'],
    'Economy': ['gdp', 'economy', 'budget', 'tax', 'finance', 'trade', 'investment', 'fiscal', 'inflation', 'rbi', 'market'],
    'Infrastructure': ['road', 'highway', 'bridge', 'railway', 'metro', 'airport', 'port', 'construction', 'inaugurate', 'project', 'smart city'],
    'Diplomacy': ['summit', 'bilateral', 'foreign', 'ambassador', 'diplomatic', 'treaty', 'g20', 'un', 'nato', 'brics', 'quad'],
    'Defence': ['army', 'navy', 'airforce', 'military', 'defence', 'defense', 'weapon', 'border', 'security', 'soldier'],
    'Technology': ['digital', 'tech', 'startup', 'innovation', 'ai', 'cyber', 'space', 'isro', 'satellite', 'internet'],
    'Social': ['education', 'health', 'hospital', 'school', 'university', 'poverty', 'welfare', 'women', 'farmer', 'rural'],
    'Event': ['rally', 'speech', 'conference', 'visit', 'inauguration', 'ceremony', 'meeting', 'address', 'function'],
}


class DataProcessor:
    """Processes API responses into database-ready format."""
    
    def __init__(self):
        self.ner = EntityRecognizer()
        try:
            self.vp = VectorProcessor()
        except Exception:
            self.vp = None
            logger.warning("VectorProcessor not loaded. Semantic clustering will be disabled.")

    def process_google_articles_clustered(self, articles, person_name, language='en'):
        """
        Process Google News RSS articles and cluster them.
        Returns: list of cluster dicts (same format as V3 response processing).
        """
        # 1. First cleanup and NER filter all articles
        clean_articles = []
        for art in articles:
            processed = self._process_single_article(art, person_name, 'google_rss')
            if processed:
                clean_articles.append(processed)

        if not clean_articles:
            return []

        results = []
        
        # 2. Cluster them
        if self.vp:
            clusters = self.vp.cluster_articles(clean_articles, threshold=0.4)
        else:
            # Fallback: treat each as separate cluster
            clusters = [[art] for art in clean_articles]

        # 3. Format for DB
        for cluster_group in clusters:
            if not cluster_group:
                continue
                
            # Representative is the first one (or longest title?)
            rep_art = cluster_group[0]
            cluster_id = hashlib.md5(f"{person_name}_{rep_art['title']}".encode()).hexdigest()
            
            cluster_data = {
                'id': cluster_id,
                'representative_title': rep_art['title'],
                'person_tracked': person_name,
                'category': rep_art['category'],
                'source_count': len(cluster_group),
                'first_published': rep_art['published_date'],
            }
            
            results.append({
                'cluster_data': cluster_data,
                'articles_data': cluster_group
            })
            
        return results

    def process_newscatcher_response(self, api_response, person_name):
        """
        Process NewsCatcher V3 response (clustered or unclustered).
        Returns: list of cluster dicts, each with cluster_data + articles_data
        """
        if not api_response:
            return []

        results = []

        if api_response.get('clustered') and api_response.get('clusters'):
            # Clustered response
            for cluster in api_response['clusters']:
                try:
                    cluster_id = cluster.get('cluster_id', hashlib.md5(str(cluster).encode()).hexdigest())
                    cluster_articles = cluster.get('articles', [])

                    if not cluster_articles:
                        continue

                    # Use first article's title as representative
                    rep_title = cluster_articles[0].get('title', 'Unknown Story')[:500]
                    first_date = self._parse_date(cluster_articles[0].get('published_date'))

                    # Process each article in the cluster
                    articles_data = []
                    for art in cluster_articles:
                        processed = self._process_single_article(art, person_name, 'newscatcher')
                        if processed:
                            articles_data.append(processed)

                    category = self._categorize_text(rep_title)

                    results.append({
                        'cluster_data': {
                            'id': cluster_id,
                            'representative_title': rep_title,
                            'person_tracked': person_name,
                            'category': category,
                            'source_count': len(articles_data),
                            'first_published': first_date,
                        },
                        'articles_data': articles_data
                    })
                except Exception as e:
                    logger.error(f"Error processing cluster: {e}")
                    continue
        else:
            # Unclustered response — each article is its own "cluster"
            articles = api_response.get('articles', [])
            for art in articles:
                try:
                    processed = self._process_single_article(art, person_name, 'newscatcher')
                    if processed:
                        results.append({
                            'cluster_data': None,  # No cluster
                            'articles_data': [processed]
                        })
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue

        return results

    def process_google_articles(self, articles, person_name, language='en'):
        """
        Process Google News RSS articles.
        Returns list of article dicts ready for database.
        """
        processed = []
        for art in articles:
            try:
                url = art.get('link', '')
                if not url:
                    continue

                article_id = hashlib.md5(url.encode()).hexdigest()
                pub_date = art.get('parsed_date', datetime.utcnow())

                processed.append({
                    'id': article_id,
                    'title': art.get('title', '')[:500],
                    'content': art.get('summary', '')[:5000],
                    'source_name': art.get('source', 'Unknown'),
                    'url': url,
                    'published_date': pub_date,
                    'person_tracked': person_name,
                    'language': language,
                    'sentiment_score': 0.0,
                    'category': self._categorize_text(art.get('title', '')),
                    'data_source': 'google_rss',
                })
            except Exception as e:
                logger.error(f"Error processing Google article: {e}")
                continue
        return processed

    def process_newsdata_articles(self, articles, person_name, language='en'):
        """
        Process NewsData.io articles.
        Returns list of article dicts ready for database.
        """
        processed = []
        for art in articles:
            try:
                url = art.get('link', '')
                if not url:
                    continue
                
                # Check duplication ID
                article_id = hashlib.md5(url.encode()).hexdigest()
                
                # Normalize date
                pub_date_str = art.get('pubDate', '')
                pub_date = self._parse_date(pub_date_str)

                processed.append({
                    'id': article_id,
                    'title': art.get('title', '')[:500],
                    'content': (art.get('description', '') or art.get('content', '') or '')[:5000],
                    'source_name': art.get('source_id', 'Unknown'), # newsdata returns source_id (e.g. 'ndtv')
                    'url': url,
                    'published_date': pub_date,
                    'person_tracked': person_name,
                    'language': language,
                    'sentiment_score': 0.0, # calculate later if needed
                    'category': self._categorize_text(art.get('title', '')),
                    'data_source': 'newsdata_io',
                    'image_url': art.get('image_url')
                })
            except Exception as e:
                logger.error(f"Error processing NewsData article: {e}")
                continue
        return processed

    def _process_single_article(self, article, person_name, data_source='newscatcher'):
        """Process a single article dict from any source."""
        try:
            # Verify if the person is actually in the text using NER
            # Combine title and description for better context
            text_to_check = f"{article.get('title', '')} {article.get('summary') or article.get('description', '')}"
            
            if not self.ner.verify_person(text_to_check, person_name):
                logger.debug(f"NER Filter: Skipping article for '{person_name}' - Entity not found.")
                return None

            url = article.get('link', '')
            if not url:
                return None

            article_id = hashlib.md5(url.encode()).hexdigest()

            return {
                'id': article_id,
                'title': article.get('title', '')[:500],
                'content': (article.get('summary') or article.get('description') or article.get('excerpt') or '')[:5000],
                'source_name': self._extract_source(article),
                'url': url,
                'published_date': self._parse_date(article.get('published_date')),
                'person_tracked': person_name,
                'language': article.get('language', 'unknown'),
                'sentiment_score': article.get('sentiment_score', 0.0),
                'category': self._categorize_text(article.get('title', '')),
                'data_source': data_source,
            }
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None

    @staticmethod
    def _extract_source(article):
        """Extract clean source name from article data."""
        # V3 may return source as dict or string
        source = article.get('source')
        if isinstance(source, dict):
            return source.get('domain') or source.get('name') or 'Unknown'

        # String source
        if isinstance(source, str) and source:
            return source

        # Fallback fields
        source_str = article.get('clean_url') or article.get('rights') or ''
        if source_str:
            return source_str.replace('www.', '').replace('.com', '').replace('.in', '').capitalize()
        return 'Unknown'

    @staticmethod
    def _parse_date(date_str):
        """Parse date from various formats."""
        if not date_str:
            return datetime.utcnow()
        if isinstance(date_str, datetime):
            return date_str

        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S %z',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.utcnow()

    @staticmethod
    def _categorize_text(text):
        """Auto-categorize based on keywords in text."""
        if not text:
            return 'Other'
        text_lower = text.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        return 'Other'
