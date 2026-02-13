"""
NewsCatcher V3 API Client with clustering support.
"""
import time
import logging
import requests
from config import Config

logger = logging.getLogger('news_tracker')


class NewsCatcherClient:
    def __init__(self):
        self.api_key = Config.API_KEY
        self.base_url = Config.API_BASE_URL
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

    def search(self, query, retry_count=3, clustering=True):
        """
        Search articles with V3 API + clustering.
        When clustering=True, returns {'clusters': [...], 'articles': [...]}
        """
        payload = {
            "q": query,
            "countries": Config.COUNTRY,
            "lang": Config.LANGUAGES,
            "sort_by": "date",
            "page_size": 100,
            "clustering_enabled": clustering,
            "clustering_variable": "title",
            "clustering_threshold": 0.6,
            "include_nlp_data": True,
        }

        for attempt in range(retry_count):
            try:
                logger.info(f"V3 API: Searching for '{query}' (Attempt {attempt+1}/{retry_count})")
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit hit. Waiting {wait_time}s.")
                    time.sleep(wait_time)
                    continue

                if response.status_code == 401:
                    logger.error("Invalid API Key. Check NEWSCATCHER_API_KEY in .env")
                    return None

                if response.status_code == 403:
                    logger.warning("V3 clustering may require NLP plan. Retrying without clustering...")
                    payload['clustering_enabled'] = False
                    payload.pop('clustering_variable', None)
                    payload.pop('clustering_threshold', None)
                    payload.pop('include_nlp_data', None)
                    continue

                response.raise_for_status()
                data = response.json()

                # V3 returns either clustered or flat response
                clusters = data.get('clusters', [])
                articles = data.get('articles', [])

                if clusters:
                    logger.info(f"V3 API: Found {len(clusters)} clusters for '{query}'")
                    return {'clusters': clusters, 'articles': articles, 'clustered': True}
                elif articles:
                    logger.info(f"V3 API: Found {len(articles)} articles (unclustered) for '{query}'")
                    return {'clusters': [], 'articles': articles, 'clustered': False}
                else:
                    logger.warning(f"V3 API: No results for '{query}'")
                    return {'clusters': [], 'articles': [], 'clustered': False}

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt+1}")
                time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                time.sleep(2 ** attempt)

            except Exception as e:
                logger.exception(f"Unexpected error during search: {e}")
                break

        logger.error(f"Failed to fetch articles for '{query}' after {retry_count} attempts")
        return None
