"""
Database module with Cluster + Article models.
One NewsCluster has Many NewsArticles (grouped by story).
"""
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from config import Config

logger = logging.getLogger('news_tracker')
Base = declarative_base()


class NewsCluster(Base):
    """Represents a single news story covered by multiple sources."""
    __tablename__ = 'news_clusters'

    id = Column(String, primary_key=True)
    representative_title = Column(String(500), nullable=False)
    person_tracked = Column(String(100))
    category = Column(String(50), default='Other')
    source_count = Column(Integer, default=1)
    first_published = Column(DateTime)
    created_date = Column(DateTime, default=datetime.utcnow)

    # Relationship: one cluster -> many articles
    articles = relationship('NewsArticle', back_populates='cluster', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<NewsCluster(title='{self.representative_title[:40]}', sources={self.source_count})>"


class NewsArticle(Base):
    """Represents a single article from a specific source."""
    __tablename__ = 'news_articles'

    id = Column(String, primary_key=True)
    cluster_id = Column(String, ForeignKey('news_clusters.id'), nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source_name = Column(String(200))
    url = Column(String(1000), unique=True)
    published_date = Column(DateTime)
    collected_date = Column(DateTime, default=datetime.utcnow)
    person_tracked = Column(String(100))
    language = Column(String(10))
    sentiment_score = Column(Float, default=0.0)
    category = Column(String(50))
    is_duplicate = Column(Integer, default=0)
    data_source = Column(String(50), default='newscatcher')  # 'newscatcher' or 'google_rss'

    # Relationship back to cluster
    cluster = relationship('NewsCluster', back_populates='articles')

    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:40]}', source='{self.source_name}')>"


class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info("Database initialized")

    def get_session(self):
        return self.Session()

    # ── Cluster Operations ──────────────────────────────────────────

    def add_cluster(self, cluster_data, articles_data):
        """Add a cluster with its articles."""
        session = self.Session()
        try:
            # Check if cluster already exists
            existing = session.query(NewsCluster).filter_by(id=cluster_data['id']).first()
            if existing:
                # Merge new articles into existing cluster
                new_count = 0
                for art_data in articles_data:
                    if not session.query(NewsArticle).filter_by(url=art_data['url']).first():
                        article = NewsArticle(**art_data, cluster_id=existing.id)
                        session.add(article)
                        new_count += 1
                existing.source_count = len(existing.articles) + new_count
                session.commit()
                return new_count
            else:
                cluster = NewsCluster(**cluster_data)
                session.add(cluster)
                session.flush()  # Get cluster.id

                count = 0
                for art_data in articles_data:
                    if not session.query(NewsArticle).filter_by(url=art_data['url']).first():
                        article = NewsArticle(**art_data, cluster_id=cluster.id)
                        session.add(article)
                        count += 1

                cluster.source_count = count
                session.commit()
                logger.debug(f"Added cluster '{cluster_data['id']}' with {count} articles")
                return count
        except Exception as e:
            logger.error(f"Error adding cluster: {e}")
            session.rollback()
            return 0
        finally:
            session.close()

    def add_unclustered_article(self, article_data):
        """Add a standalone article (e.g. from Google RSS) without a cluster."""
        session = self.Session()
        try:
            if session.query(NewsArticle).filter_by(url=article_data['url']).first():
                return False
            article = NewsArticle(**article_data)
            session.add(article)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding unclustered article: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def bulk_add_articles(self, articles_data):
        """Add multiple standalone articles (backward compatible)."""
        session = self.Session()
        count = 0
        try:
            for data in articles_data:
                if not session.query(NewsArticle).filter_by(url=data['url']).first():
                    article = NewsArticle(**data)
                    session.add(article)
                    count += 1
            session.commit()
            logger.info(f"Added {count} new articles")
            return count
        except Exception as e:
            logger.error(f"Error in bulk add: {e}")
            session.rollback()
            return 0
        finally:
            session.close()

    # ── Query Operations ────────────────────────────────────────────

    def get_clusters(self, days=7, person=None):
        """Get recent clusters with their articles."""
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = session.query(NewsCluster).filter(NewsCluster.created_date >= cutoff)
            if person:
                query = query.filter(NewsCluster.person_tracked == person)
            return query.order_by(NewsCluster.first_published.desc()).all()
        finally:
            session.close()

    def get_recent_articles(self, days=7, person=None):
        """Get recent articles (flat view)."""
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = session.query(NewsArticle).filter(NewsArticle.collected_date >= cutoff)
            if person:
                query = query.filter(NewsArticle.person_tracked == person)
            return query.order_by(NewsArticle.published_date.desc()).all()
        finally:
            session.close()

    def get_stories_grouped(self, days=7, person=None):
        """
        Get stories grouped by cluster.
        Returns list of dicts with cluster info + list of source articles.
        """
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Get clustered stories
            cluster_q = session.query(NewsCluster).filter(NewsCluster.created_date >= cutoff)
            if person:
                cluster_q = cluster_q.filter(NewsCluster.person_tracked == person)
            clusters = cluster_q.order_by(NewsCluster.first_published.desc()).all()

            stories = []
            for c in clusters:
                sources = []
                languages = set()
                for art in c.articles:
                    sources.append({
                        'name': art.source_name,
                        'url': art.url,
                        'language': art.language,
                        'title': art.title
                    })
                    if art.language:
                        languages.add(art.language)
                stories.append({
                    'id': c.id,
                    'headline': c.representative_title,
                    'person': c.person_tracked,
                    'category': c.category,
                    'source_count': len(sources),
                    'source_names': ', '.join(sorted(set(s['name'] for s in sources))),
                    'sources': sources,
                    'languages': ', '.join(sorted(languages)),
                    'published': c.first_published.strftime('%Y-%m-%d %H:%M') if c.first_published else 'N/A'
                })

            # Also get unclustered articles (no cluster_id)
            unclustered_q = session.query(NewsArticle).filter(
                NewsArticle.collected_date >= cutoff,
                NewsArticle.cluster_id.is_(None)
            )
            if person:
                unclustered_q = unclustered_q.filter(NewsArticle.person_tracked == person)
            unclustered = unclustered_q.order_by(NewsArticle.published_date.desc()).all()

            for art in unclustered:
                stories.append({
                    'id': art.id,
                    'headline': art.title,
                    'person': art.person_tracked,
                    'category': art.category or 'Other',
                    'source_count': 1,
                    'source_names': art.source_name,
                    'sources': [{'name': art.source_name, 'url': art.url, 'language': art.language, 'title': art.title}],
                    'languages': art.language or '',
                    'published': art.published_date.strftime('%Y-%m-%d %H:%M') if art.published_date else 'N/A'
                })

            return stories
        finally:
            session.close()

    def get_statistics(self, days=7):
        """Get summary statistics."""
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            total = session.query(NewsArticle).filter(NewsArticle.collected_date >= cutoff).count()
            clusters = session.query(NewsCluster).filter(NewsCluster.created_date >= cutoff).count()

            modi_count = session.query(NewsArticle).filter(
                NewsArticle.collected_date >= cutoff,
                NewsArticle.person_tracked.ilike('%Modi%')
            ).count()

            patil_count = session.query(NewsArticle).filter(
                NewsArticle.collected_date >= cutoff,
                NewsArticle.person_tracked.ilike('%Patil%')
            ).count()

            channels = session.query(NewsArticle.source_name).filter(
                NewsArticle.collected_date >= cutoff
            ).distinct().count()

            languages = session.query(NewsArticle.language).filter(
                NewsArticle.collected_date >= cutoff
            ).distinct().all()

            return {
                'total_articles': total,
                'total_stories': clusters,
                'modi_count': modi_count,
                'patil_count': patil_count,
                'unique_channels': channels,
                'languages': [l[0] for l in languages if l[0]]
            }
        finally:
            session.close()

    def cleanup_old_data(self, days=90):
        """Delete old clusters and articles."""
        session = self.Session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            # Delete old articles first (cascade will handle cluster orphans)
            del_articles = session.query(NewsArticle).filter(NewsArticle.collected_date < cutoff).delete()
            del_clusters = session.query(NewsCluster).filter(NewsCluster.created_date < cutoff).delete()
            session.commit()
            logger.info(f"Cleaned up {del_articles} articles and {del_clusters} clusters")
            return del_articles
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
