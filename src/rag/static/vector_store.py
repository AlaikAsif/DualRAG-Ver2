# faiss vector store management

from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from src.rag.static.embeddings import StaticEmbeddings
from src.rag.static.indexer import Indexer
import faiss
import os


class VectorStore:
    """Helper around FAISS vector store for static RAG.

    Usage:
        vs = VectorStore()
        store = vs.create_vector_store(texts, metadatas=metas)
    """

    def __init__(self, embedding_model: Any = None, indexer: Any = None):
        # embedding_model: either a callable embed(texts) -> np.ndarray or an instance with .embed()
        self.embedding_model = embedding_model or StaticEmbeddings()
        self.indexer = indexer or Indexer()
        self.docstore = InMemoryDocstore()

    def create_vector_store(self, texts: list, metadatas: list = None, embeddings: object = None):
        """Create a FAISS-backed vector store from texts.

        If `embeddings` is provided it will be used directly. Otherwise the
        configured `embedding_model` will be used to compute embeddings.
        """
        metadatas = metadatas or [None] * len(texts)

        # Compute embeddings if not provided
        if embeddings is None:
            embed_fn = None
            if hasattr(self.embedding_model, "embed"):
                embed_fn = self.embedding_model.embed
            elif callable(self.embedding_model):
                embed_fn = self.embedding_model

            if embed_fn is None:
                raise ValueError("No embedding function available to create vector store")

            embeddings = embed_fn(texts)

        # Prepare persistence path (always persist into this folder)
        out_dir = os.path.join("data", "vectors", "static", "index")
        out_path = os.path.join(out_dir, "faiss_index.bin")
        os.makedirs(out_dir, exist_ok=True)

        # If a previous index exists, remove it so we overwrite cleanly
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
            # also remove other files in the dir to avoid stale metadata
            for fn in os.listdir(out_dir):
                fp = os.path.join(out_dir, fn)
                if os.path.isfile(fp):
                    os.remove(fp)
        except Exception:
            # best-effort cleanup; ignore errors
            pass

        # Prefer convenience constructor if available
        if hasattr(FAISS, "from_texts"):
            try:
                vs = FAISS.from_texts(texts, self.embedding_model if hasattr(self.embedding_model, "embed") else self.embedding_model, metadatas=metadatas)
                # try to persist using adapter helper if present
                try:
                    if hasattr(vs, "save_local"):
                        vs.save_local(out_dir)
                        return out_path
                except Exception:
                    pass
                # fallback to writing underlying faiss index
                if hasattr(vs, "index"):
                    faiss.write_index(vs.index, out_path)
                    return out_path
                # if no index available, return the vs object path hint
                return out_path
            except Exception:
                # fallback to manual construction
                pass

        # Manual construction: create an empty docstore mapping and pass precomputed embeddings
        index_to_docstore_id = {}
        for i, (txt, meta) in enumerate(zip(texts, metadatas)):
            doc_id = str(i)
            # store document content in the docstore under doc_id
            try:
                # InMemoryDocstore expects a dict-like mapping
                self.docstore._dict[doc_id] = {"text": txt, "metadata": meta}
            except Exception:
                # best-effort: try attribute name used by implementation
                try:
                    self.docstore.store[doc_id] = {"text": txt, "metadata": meta}
                except Exception:
                    pass
            index_to_docstore_id[i] = doc_id

        vector_store = FAISS(embeddings=embeddings, docstore=self.docstore, index_to_docstore_id=index_to_docstore_id)

        # Persist FAISS index to the project's data folder (fallback)
        try:
            if hasattr(vector_store, "save_local"):
                vector_store.save_local(out_dir)
                return out_path
        except Exception:
            pass

        # final fallback: write raw faiss index
        faiss.write_index(vector_store.index, out_path)
        return out_path
    

    def load_vector_store(self, index_path: str):
        """Load a FAISS vector store from the given index path."""
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index file not found at: {index_path}")

        # Load the FAISS index
        faiss_index = faiss.read_index(index_path)

        # Create a FAISS vector store instance
        vector_store = FAISS(embedding_function=self.embedding_model, index=faiss_index, docstore=self.docstore)

        return vector_store
    
    def check_vector_store_exists(self, index_path: str) -> bool:
        return os.path.exists(index_path)
    

__all__ = ["VectorStore"]