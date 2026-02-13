"""
Test script for VectorProcessor clustering.
"""
from src.vector_processor import VectorProcessor
import logging

logging.basicConfig(level=logging.INFO)

def test_clustering():
    print("Initializing VectorProcessor (loading MiniLM model)...")
    vp = VectorProcessor()

    articles = [
        {"id": 1, "title": "PM Modi inaugurates Sudarshan Setu", "summary": "Prime Minister Narendra Modi dedicated Sudarshan Setu to the nation."},
        {"id": 2, "title": "Modi opens new bridge in Gujarat", "summary": "PM Modi inaugurated India's longest cable-stayed bridge, Sudarshan Setu."},
        {"id": 3, "title": "CR Patil addresses farmers rally", "summary": "BJP state president CR Patil spoke about new agricultural policies."},
        {"id": 4, "title": "Gujarat BJP Chief meets farmers", "summary": "C.R. Patil held a meeting with local farmers today."},
        {"id": 5, "title": "Stock market hits new high", "summary": "Sensex and Nifty touched lifetime highs on Monday."}
    ]

    print(f"\nClustering {len(articles)} articles...")
    
    # Debug: print similarities
    texts = [f"{art['title']} {art['summary']}" for art in articles]
    embeddings = vp.generate_embedding(texts)
    from sklearn.metrics.pairwise import cosine_similarity
    sim_matrix = cosine_similarity(embeddings)
    print("Similarity Matrix:")
    print(sim_matrix)
    print(f"Similarity 1 vs 2: {sim_matrix[0][1]}")
    
    # Threshold 0.4 = Distance 0.6. Similarity > 0.4 should merge.
    clusters = vp.cluster_articles(articles, threshold=0.4) 

    print(f"\nFound {len(clusters)} clusters:\n")
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i+1} ({len(cluster)} articles):")
        for art in cluster:
            print(f"  - [{art['id']}] {art['title']}")
            
    # Verification
    # Cluster 1: Modi bridge (Articles 1, 2)
    # Cluster 2: Patil rally (Articles 3, 4)
    # Cluster 3: Stock market (Article 5)
    
    # Simple check based on titles
    print("\nVerification:")
    
    modi_cluster = [c for c in clusters if any("Modi" in a['title'] for a in c)]
    patil_cluster = [c for c in clusters if any("Patil" in a['title'] for a in c)]
    
    if len(modi_cluster) >= 1 and len(modi_cluster[0]) >= 2:
        print("✅ Modi articles clustered correctly.")
    else:
        print("❌ Modi articles NOT clustered correctly.")

    if len(patil_cluster) >= 1 and len(patil_cluster[0]) >= 2:
        print("✅ Patil articles clustered correctly.")
    else:
        print("❌ Patil articles NOT clustered correctly.")

if __name__ == "__main__":
    test_clustering()
