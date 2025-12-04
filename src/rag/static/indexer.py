"""Document indexing pipeline for FAISS vector store.

Simple batch indexer that computes embeddings and builds FAISS indexes.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from src.rag.static.vector_store import VectorStore
from src.rag.static.embeddings import StaticEmbeddings


class Indexer:
    """Simple batch document indexer for FAISS vector store."""

    def __init__(self, embedding_model: Optional[Any] = None):

        # Default to StaticEmbeddings if none provided
        self.embedding_model = embedding_model or StaticEmbeddings()

    def index_embeddings(
        self,
        documents: List[str],
        embeddings_fn: Optional[callable] = None,
        metadatas: Optional[List[Dict]] = None
    ) -> List[Tuple[str, np.ndarray, Optional[Dict]]]:
        """Index documents by computing embeddings.
        
        Args:
            documents: List of document texts
            embeddings_fn: Optional custom embedding function. Defaults to self.embedding_model.embed
            metadatas: Optional list of metadata dicts (one per document)
            
        Returns:
            List of (text, embedding, metadata) tuples
        """
        # Determine embedding function. Accept any of:
        # - a plain callable that accepts List[str] -> np.ndarray
        # - a callable that accepts a single str
        # - a staticmethod wrapper (unwrap via __func__)
        def _unwrap(fn):
            if fn is None:
                return None
            # staticmethod objects may be passed directly
            if hasattr(fn, "__func__"):
                return fn.__func__
            return fn

        embed_fn = _unwrap(embeddings_fn)
        if embed_fn is None:
            # Prefer the instance embed method when available. This avoids
            # unwrapping bound methods into raw functions which lose the
            # `self` binding and causes failures during batch calls.
            embed_fn = getattr(self.embedding_model, "embed", None)
            if embed_fn is None:
                # try lazy import of StaticEmbeddings as a last resort
                try:
                    from src.rag.static.embeddings import StaticEmbeddings as _SE

                    embed_fn = getattr(_SE(), "embed", None) or getattr(_SE, "embed", None)
                except Exception:
                    embed_fn = None
        metadatas = metadatas or [None] * len(documents)

        # Compute embeddings in batch for efficiency
        if embed_fn is None:
            # fallback to the instance embed method
            embed_fn = getattr(self.embedding_model, "embed", None)

        if embed_fn is None:
            raise RuntimeError("No embedding function available. Pass `embeddings_fn` or provide an embedding_model.")

        # Try batch call first (many embedder APIs accept list[str])
        try:
            embeddings = np.asarray(embed_fn(documents))
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(len(documents), -1)
        except Exception:
            # Fallback to calling embed per document
            embeddings_list = []
            for doc in documents:
                try:
                    out = embed_fn(doc)
                    arr = np.asarray(out)
                    if arr.ndim == 2 and arr.shape[0] == 1:
                        arr = arr[0]
                    embeddings_list.append(arr)
                except Exception:
                    try:
                        out = embed_fn([doc])
                        arr = np.asarray(out)
                        if arr.ndim == 2 and arr.shape[0] == 1:
                            arr = arr[0]
                        embeddings_list.append(arr)
                    except Exception:
                        embeddings_list.append(np.zeros(384))
            embeddings = np.vstack(embeddings_list)

        indexed_data = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            indexed_data.append((doc, embeddings[i], meta))

        return indexed_data

    def build_and_persist_index(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        embeddings_fn: Optional[callable] = None
    ) -> str:
        """Build and persist a FAISS index from documents.
        
        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            embeddings_fn: Optional custom embedding function
            
        Returns:
            Path to saved FAISS index file
        """
        # Index the documents
        indexed_data = self.index_embeddings(documents, embeddings_fn=embeddings_fn, metadatas=metadatas)
        
        # Extract texts and embeddings
        texts = [item[0] for item in indexed_data]
        embeddings = np.asarray([item[1] for item in indexed_data])
        meta_list = [item[2] for item in indexed_data]
        
        # Create and persist vector store
        vs = VectorStore()
        saved_path = vs.create_vector_store(texts, metadatas=meta_list, embeddings=embeddings)
        
        return saved_path


__all__ = ["Indexer"]
