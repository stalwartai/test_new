"""
Scheduler — orchestrates news collection from multiple sources.
Fetches from NewsCatcher V3 + Google News RSS, processes clusters, stores in DB.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import time
from config import Config
from .api_client import NewsCatcherClient
from .google_news import GoogleNewsClient
from .newsdata_client import NewsDataClient
from .database import Database
from .data_processor import DataProcessor
from .reports import ReportGenerator

logger = logging.getLogger('news_tracker')


class NewsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.api_client = NewsCatcherClient()
        self.google_client = GoogleNewsClient()
        self.newsdata_client = NewsDataClient(api_key=Config.NEWSDATA_API_KEY)
        self.db = Database()
        self.processor = DataProcessor()
        self.reporter = ReportGenerator()

    def start(self):
        """Start the scheduler."""
        trigger = CronTrigger(
            hour=Config.SCHEDULE_HOUR,
            minute=Config.SCHEDULE_MINUTE,
            timezone='UTC'
        )
        self.scheduler.add_job(
            self.run_news_collection,
            trigger=trigger,
            id='news_collection_job',
            name='Daily News Collection',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info(f"Scheduler started. Next run at {Config.SCHEDULE_HOUR}:{Config.SCHEDULE_MINUTE:02d} UTC")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def run_now(self):
        """Run collection immediately."""
        logger.info("Manual run initiated")
        self.run_news_collection()

    def run_news_collection(self):
        """Main workflow: Fetch from multiple sources -> Process -> Store -> Report."""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting news collection")
        logger.info("=" * 60)

        people_to_track = [
            ("Narendra Modi", '"Narendra Modi"'),
            ("CR Patil", '"CR Patil" OR "C.R. Patil"')
        ]

        total_new = 0

        try:
            for person_name, query in people_to_track:
                logger.info(f"--- Collecting for: {person_name} ---")
                new_articles = 0

                # ── Source 1: NewsCatcher V3 API ──
                new_articles += self._collect_newscatcher(query, person_name)

                # ── Source 2: Google News RSS ──
                new_articles += self._collect_google_rss(query, person_name)

                # ── Source 3: NewsData.io API ──
                new_articles += self._collect_newsdata(query, person_name)
                
                total_new += new_articles
                logger.info(f"Total new articles for {person_name}: {new_articles}")

            # ── Cleanup old data ──
            self.db.cleanup_old_data(Config.DAYS_TO_KEEP)

            # ── Generate Report ──
            if total_new > 0:
                report_path = self.reporter.generate_daily_report()
                if report_path:
                    logger.info(f"Report generated: {report_path}")

            # ── Log Statistics ──
            stats = self.db.get_statistics()
            logger.info(f"Collection complete in {time.time() - start_time:.2f}s")
            logger.info(f"Stats: {stats}")

        except Exception as e:
            logger.exception(f"Error during news collection: {e}")

    def _collect_newscatcher(self, query, person_name):
        """Collect from NewsCatcher V3 with clustering."""
        try:
            result = self.api_client.search(query)
            if not result:
                logger.warning(f"NewsCatcher: No results for {person_name}")
                return 0

            processed = self.processor.process_newscatcher_response(result, person_name)
            new_count = 0

            for item in processed:
                cluster_data = item.get('cluster_data')
                articles_data = item.get('articles_data', [])

                if cluster_data:
                    # Clustered: save cluster + articles
                    count = self.db.add_cluster(cluster_data, articles_data)
                    new_count += count
                else:
                    # Unclustered: save individual articles
                    for art in articles_data:
                        if self.db.add_unclustered_article(art):
                            new_count += 1

            logger.info(f"NewsCatcher: {new_count} new articles for {person_name}")
            return new_count
        except Exception as e:
            logger.error(f"NewsCatcher collection error: {e}")
            return 0

    def _collect_google_rss(self, query, person_name):
        """Collect from Google News RSS (free source)."""
        try:
            new_count = 0
            # Collect in multiple languages
            for lang in ['en', 'hi']:
                articles = self.google_client.search(query, language=lang, country='IN')
                if not articles:
                    continue

                # Use clustered processing
                clustered_results = self.processor.process_google_articles_clustered(articles, person_name, language=lang)
                
                for item in clustered_results:
                    cluster_data = item.get('cluster_data')
                    articles_data = item.get('articles_data', [])
                    
                    if cluster_data:
                        count = self.db.add_cluster(cluster_data, articles_data)
                        new_count += count

            logger.info(f"Google RSS: {new_count} new articles for {person_name}")
            return new_count
        except Exception as e:
            logger.error(f"Google RSS collection error: {e}")
            return 0

    def _collect_newsdata(self, query, person_name):
        """Collect from NewsData.io API."""
        try:
            # NewsData.io sometimes needs simpler queries.
            # Convert "Narendra Modi" OR "Modi" -> "Narendra Modi"
            simplified_query = person_name 
            
            result = self.newsdata_client.fetch_articles(simplified_query, country='in')
            if not result:
                return 0
                
            articles = result.get('results', [])
            if not articles:
                return 0
                
            processed = self.processor.process_newsdata_articles(articles, person_name)
            new_count = 0
            
            for art in processed:
                # NewsData articles are not clustered by default, but we can try clustering them if needed.
                # For now, treat as unclustered to match Google RSS behavior if clustering fails
                if self.db.add_unclustered_article(art):
                    new_count += 1
                    
            logger.info(f"NewsData.io: {new_count} new articles for {person_name}")
            return new_count
        except Exception as e:
            logger.error(f"NewsData.io collection error: {e}")
            return 0
