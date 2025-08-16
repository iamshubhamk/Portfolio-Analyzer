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
        with open(path, 'r') as f:
            return json.load(f)

    def build_faiss_index(self):
        embeddings = []
        for news in self.news_data:
            embedding = self.model.encode(news['content'])
            embeddings.append(embedding)
        embeddings = np.array(embeddings).astype('float32')  # Convert to NumPy array
        dim = len(embeddings[0])
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        return index, embeddings

    def search_relevant_news(self, query, top_k=5, threshold=1):
        query_vector = self.model.encode(query)
        query_vector = np.array([query_vector]).astype('float32')  # Ensure correct shape and dtype
        D, I = self.index.search(query_vector, top_k)
        results = []
        for idx, distance in zip(I[0], D[0]):
            if distance < threshold:  # Lower distance = more relevant
                results.append(self.news_data[idx])
        return results

