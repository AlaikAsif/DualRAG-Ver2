# Document indexing into Chroma
from src.rag.static.embeddings import StaticEmbeddings

class Indexer:
    @staticmethod
    def index_embeddings(documents, embeddings=staticmethod(StaticEmbeddings.embed)):
        # Index documents using embeddings
        indexed_data = []
        for doc in documents:
            emb = embeddings(doc)
            indexed_data.append((doc, emb))
        return indexed_data
    
__all__ = ["Indexer"]
