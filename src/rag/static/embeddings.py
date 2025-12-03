# Embedding model initialization and management
from src.preprocessing import Chunker
from sentence_transformers import SentenceTransformer
class StaticEmbeddings:


    @staticmethod
    def embed(self, text: str):
        text_chunks = Chunker.select_chunking_strategy(0)
        # call embedding model on text_chunks
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embeddings = model.encode(text_chunks)
        return embeddings
    
    # Manage embedding cache
    @staticmethod
    def cache_embeddings(embeddings, cache_path: str):
        import pickle
        with open(cache_path, 'wb') as f:
            pickle.dump(embeddings, f)

    @staticmethod
    def load_cached_embeddings(cache_path: str):
        import pickle
        with open(cache_path, 'rb') as f:
            embeddings = pickle.load(f)
        return embeddings
    
__all__ = ["StaticEmbeddings"]
    

        
