"""
Vector Processor Module.
Uses Sentence Transformers to generate embeddings and cluster articles semantically.
"""
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger('news_tracker')

class VectorProcessor:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        try:
            logger.info(f"Loading Sentence Transformer: {model_name}")
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def generate_embedding(self, text):
        """Generate vector embedding for a text string."""
        if not text:
            return None
        try:
            return self.model.encode(text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def cluster_articles(self, articles, threshold=0.75):
        """
        Cluster a list of articles based on semantic similarity using Agglomerative Clustering.
        
        Args:
            articles (list): List of article dicts. Must have 'title' and/or 'summary'.
            threshold (float): Similarity threshold (converted to distance) to consider items as one cluster.
            
        Returns:
            list: List of clusters, where each cluster is a list of article dicts.
        """
        if not articles:
            return []
            
        # 1. Prepare texts for embedding (Title + Summary for better context)
        texts = [f"{art.get('title', '')} {art.get('summary', '')}" for art in articles]
        
        # 2. Generate embeddings
        embeddings = self.model.encode(texts)
        
        if len(embeddings) == 0:
            return []

        # 3. Normalize embeddings for cosine similarity
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # 4. Clustering using Agglomerative Clustering
        # distance_threshold = 1 - similarity_threshold
        clustering_model = AgglomerativeClustering(
            n_clusters=None,
            metric='cosine', 
            linkage='average',
            distance_threshold=1 - threshold
        )
        
        # If only 1 article, it's a single cluster
        if len(articles) == 1:
            return [articles]
            
        try:
            cluster_labels = clustering_model.fit_predict(embeddings)
        except ValueError:
            # Fallback for very small datasets or errors
            return [[art] for art in articles]

        # 5. Group articles by label
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(articles[idx])
            
        return list(clusters.values())
