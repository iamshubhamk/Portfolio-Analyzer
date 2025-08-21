import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

class NewsRAGEngine:
    def __init__(self, news_file_path):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Make path absolute relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.join(base_dir, '..', news_file_path)
        print("Loading news data from:", abs_path)
        self.news_data = self.load_news_data(abs_path)
        self.index, self.news_vectors = self.build_faiss_index()

    def load_news_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def build_faiss_index(self):
        embeddings = []
        for news in self.news_data:
            # Combine title and summary for better semantic search
            text_content = f"{news.get('title', '')} {news.get('summary', '')}".strip()
            if text_content:  # Only process if there's content
                embedding = self.model.encode(text_content)
                embeddings.append(embedding)
            else:
                # If no content, use a zero vector (will be filtered out)
                embedding = self.model.encode("")
                embeddings.append(embedding)
        
        embeddings = np.array(embeddings).astype('float32')
        dim = len(embeddings[0])
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        return index, embeddings

    def search_relevant_news(self, query, top_k=5, threshold=2.0):
        """
        Search for relevant news articles based on a query.
        
        Args:
            query (str): The search query
            top_k (int): Number of top results to return
            threshold (float): Distance threshold for relevance (lower = more relevant)
        
        Returns:
            list: List of complete news article dictionaries
        """
        query_vector = self.model.encode(query)
        query_vector = np.array([query_vector]).astype('float32')
        
        # Search the FAISS index
        D, I = self.index.search(query_vector, top_k)
        
        results = []
        for idx, distance in zip(I[0], D[0]):
            if distance < threshold:  # Lower distance = more relevant
                # Return the complete dictionary of the news article
                results.append(self.news_data[idx])
        
        return results
    
    def search_by_company(self, company_name, top_k=5):
        """
        Search for news articles related to a specific company.
        
        Args:
            company_name (str): Name of the company to search for
            top_k (int): Number of top results to return
        
        Returns:
            list: List of complete news article dictionaries
        """
        return self.search_relevant_news(company_name, top_k=top_k)
    
    def search_by_topic(self, topic, top_k=5):
        """
        Search for news articles related to a specific topic.
        
        Args:
            topic (str): Topic to search for (e.g., 'market', 'earnings', 'dividend')
            top_k (int): Number of top results to return
        
        Returns:
            list: List of complete news article dictionaries
        """
        return self.search_relevant_news(topic, top_k=top_k)

if __name__ == "__main__":
    # Test the improved NewsRAGEngine
    news_engine = NewsRAGEngine('data/news_articles.json')
    
    # Test queries
    test_queries = [
        "What is the news about Adani Green Energy?",
        "market performance today",
        "earnings reports",
        "dividend announcements",
        "Reliance Industries"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = news_engine.search_relevant_news(query, top_k=3)
        print("--------------------------------")
        print(results)

