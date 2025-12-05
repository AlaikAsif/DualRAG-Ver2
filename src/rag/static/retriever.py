"""Document retrieval and MMR reranker helper.

This module provides a minimal Retriever with an MMR reranker.

It expects a FAISS index file at `data/vectors/static/index/faiss_index.bin` and
uses the project's `VectorStore` embedding model to compute vectors.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

import numpy as np

from src.rag.static.vector_store import VectorStore
from langchain_community.vectorstores import FAISS
import faiss


def _cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = np.linalg.norm(b, axis=1, keepdims=True)
    a_norm[a_norm == 0] = 1e-12
    b_norm[b_norm == 0] = 1e-12
    sim = (a @ b.T) / (a_norm * b_norm.T)
    return sim


def mmr_select(query_vec: np.ndarray, candidate_vecs: np.ndarray, candidate_ids: List[Any], k: int = 5, lambda_param: float = 0.5) -> List[int]:
    """Select `k` items from candidates using Maximal Marginal Relevance (MMR).

    Returns list of indices from candidate_ids in selected order.
    """
    n_candidates = candidate_vecs.shape[0]
    if n_candidates == 0:
        return []
    if k <= 0:
        return []

    # compute similarities
    sims_to_query = _cosine_similarity_matrix(candidate_vecs, query_vec.reshape(1, -1)).flatten()
    sims_between = _cosine_similarity_matrix(candidate_vecs, candidate_vecs)

    selected = []
    remaining = list(range(n_candidates))

    first = int(np.argmax(sims_to_query))
    selected.append(first)
    remaining.remove(first)

    while len(selected) < min(k, n_candidates):
        best_score = None
        best_idx = None
        for i in remaining:
            rel = sims_to_query[i]
            max_sim_to_selected = max(sims_between[i, j] for j in selected) if selected else 0.0
            score = lambda_param * rel - (1 - lambda_param) * max_sim_to_selected
            if (best_score is None) or (score > best_score):
                best_score = score
                best_idx = i
        if best_idx is None:
            break
        selected.append(best_idx)
        remaining.remove(best_idx)

    return [candidate_ids[i] for i in selected]


class Retriever:
    """Minimal retriever wrapper providing similarity search + MMR rerank.

    Notes:
    - This is intentionally small and defensive: it will try to use the LangChain
      FAISS adapter methods when available, and fall back to reading the raw index
      and computing embeddings with the project's `VectorStore` embedding model.
    """

    def __init__(self, vector_store: Optional[FAISS] = None, embedding_model: Optional[Any] = None):
        self.vector_store = vector_store
        self.embedding_model = embedding_model or VectorStore().embedding_model

    @classmethod
    def load_local(cls, index_path: Optional[str] = None) -> "Retriever":
        vs = VectorStore()
        index_path = index_path or os.path.join("data", "vectors", "static", "index")

        if os.path.isdir(index_path):
            candidates = [
                os.path.join(index_path, "faiss_index.bin"),
                os.path.join(index_path, "index.faiss"),
                os.path.join(index_path, "index")
            ]
            found = None
            for cand in candidates:
                if os.path.exists(cand):
                    found = cand
                    break
            if found is None:
                raise FileNotFoundError(f"No FAISS index file found in directory {index_path}")
            index_path = found

        if not os.path.exists(index_path):
            parent = os.path.dirname(index_path)
            if parent and os.path.isdir(parent):
                for fn in ("faiss_index.bin", "index.faiss", "index"):
                    cand = os.path.join(parent, fn)
                    if os.path.exists(cand):
                        index_path = cand
                        break

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Vector store index not found at {index_path}")

        index = faiss.read_index(index_path)

        index_to_docstore_id = {}
        try:
            persist_dir = os.path.dirname(index_path)
            docs_fp = os.path.join(persist_dir, "documents.jsonl")
            if os.path.exists(docs_fp):
                with open(docs_fp, "r", encoding="utf-8") as fh:
                    for i, line in enumerate(fh):
                        if not line.strip():
                            continue
                        obj = __import__("json").loads(line)
                        doc_id = str(i)
                        try:
                            vs.docstore._dict[doc_id] = {"text": obj.get("text"), "metadata": obj.get("metadata")}
                        except Exception:
                            try:
                                vs.docstore.store[doc_id] = {"text": obj.get("text"), "metadata": obj.get("metadata")}
                            except Exception:
                                pass
                        index_to_docstore_id[i] = doc_id
        except Exception:
            index_to_docstore_id = {}

        # Construct FAISS adapter; pass embedding function for compatibility when needed
        try:
            fc = FAISS(embedding_function=getattr(vs.embedding_model, "embed", vs.embedding_model), index=index, docstore=vs.docstore, index_to_docstore_id=index_to_docstore_id)
        except TypeError:
            # adapter signature may differ across versions; try without index_to_docstore_id
            fc = FAISS(embedding_function=getattr(vs.embedding_model, "embed", vs.embedding_model), index=index, docstore=vs.docstore)

        return cls(vector_store=fc, embedding_model=vs.embedding_model)

    def similarity_search_documents(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Return top-k documents for `query` using underlying vector store.

        Returns list of dicts: {'id', 'text', 'metadata', 'score' (if available)}
        """
        if self.vector_store is None:
            raise RuntimeError("Vector store not loaded. Call `load_local()` first or pass a vector_store instance.")

        # Prefer adapter method that returns scores
        docs = []
        try:
            items = self.vector_store.similarity_search_with_score(query, k=k)
            for doc, score in items:
                docs.append({
                    "id": doc.metadata.get("id") if doc.metadata else None,
                    "text": getattr(doc, "page_content", str(doc)),
                    "metadata": doc.metadata,
                    "score": float(score),
                })
            return docs
        except Exception:
            # Try adapter's similarity_search first (may not provide scores)
            try:
                items = self.vector_store.similarity_search(query, k=k)
                for doc in items:
                    docs.append({
                        "id": doc.metadata.get("id") if doc.metadata else None,
                        "text": getattr(doc, "page_content", str(doc)),
                        "metadata": doc.metadata,
                        "score": None,
                    })
                return docs
            except Exception:
                # Final fallback: perform a raw FAISS search using the underlying index
                try:
                    # compute query vector via embedding model
                    qvec = np.asarray(self.embedding_model.embed([query]))
                    if qvec.ndim == 2 and qvec.shape[0] == 1:
                        q = qvec[0]
                    else:
                        q = np.asarray(qvec).flatten()
                    # normalize
                    q = q.astype(np.float32)
                    nrm = np.linalg.norm(q)
                    if nrm == 0:
                        nrm = 1e-12
                    q = (q / nrm).reshape(1, -1).astype(np.float32)

                    index = getattr(self.vector_store, "index", None)
                    if index is None:
                        # try to load from default persisted location
                        idx_dir = os.path.join("data", "vectors", "static", "index")
                        for fn in ("faiss_index.bin", "index.faiss", "index"):
                            p = os.path.join(idx_dir, fn)
                            if os.path.exists(p):
                                index = faiss.read_index(p)
                                break

                    if index is None:
                        return []

                    scores, ids = index.search(q, k)
                    ids = ids.flatten().tolist()
                    scores = scores.flatten().tolist()

                    # try to map ids to documents using docstore and adapter mapping
                    index_to_docstore_id = getattr(self.vector_store, "index_to_docstore_id", None)
                    ds = getattr(self.vector_store, "docstore", None)

                    for iid, score in zip(ids, scores):
                        if iid < 0:
                            continue
                        doc_id = None
                        if index_to_docstore_id:
                            doc_id = index_to_docstore_id.get(int(iid))
                        if ds is not None:
                            # try common docstore backing maps
                            backing = getattr(ds, "_dict", None) or getattr(ds, "store", None)
                            if doc_id is None:
                                doc_id = str(int(iid))
                            try:
                                entry = backing.get(doc_id) if backing else None
                                text = entry.get("text") if entry else None
                                meta = entry.get("metadata") if entry else None
                            except Exception:
                                text = None
                                meta = None
                        else:
                            text = None
                            meta = None

                        docs.append({
                            "id": doc_id,
                            "text": text or "",
                            "metadata": meta,
                            "score": float(score),
                        })
                    return docs
                except Exception:
                    return []

    def mmr_rerank(self, query: str, initial_k: int = 50, top_k: int = 5, lambda_param: float = 0.5) -> List[Dict[str, Any]]:
        """Perform MMR reranking: get `initial_k` candidates then select `top_k` diverse & relevant ones.

        Returns list of selected candidate dicts in MMR-selected order.
        """
        # 1) get initial candidates
        candidates = self.similarity_search_documents(query, k=initial_k)
        if not candidates:
            return []

        texts = [c["text"] for c in candidates]

        # 2) compute vectors for query and candidates
        # embedding_model.embed should accept list[str] and return numpy array-like
        try:
            cand_vecs = np.asarray(self.embedding_model.embed(texts))
            query_vec = np.asarray(self.embedding_model.embed([query]))[0]
        except Exception:
            # if embeddings fail, return top-k by original score (best-effort)
            return candidates[:top_k]

        # 3) run MMR selection
        candidate_ids = list(range(len(candidates)))
        selected_indices = mmr_select(query_vec, cand_vecs, candidate_ids, k=top_k, lambda_param=lambda_param)

        # map selected indices back to candidate dicts preserving order
        selected = [candidates[i] for i in selected_indices]
        return selected


__all__ = ["Retriever", "mmr_select"]

