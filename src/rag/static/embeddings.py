"""Embedding helpers for Static RAG.

Provides a simple wrapper around sentence-transformers with a stable
`StaticEmbeddings` class exposing `.embed()` and cache helpers.

The `.embed()` method accepts either a single string or a list of strings
and always returns a numpy array of shape (n, d).
"""
from __future__ import annotations

from typing import Iterable, List, Union, Optional

import numpy as np


class StaticEmbeddings:
    """Wrapper around sentence-transformers for local embeddings.

    Notes:
    - The implementation defers importing heavy dependencies until `.embed()`
      is called to avoid import-time failures in environments without
      the transformers/accelerate stack available.
    - Default model: `sentence-transformers/all-MiniLM-L6-v2`.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            self._model = False
            return self._model
        self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: Union[str, Iterable[str]]) -> np.ndarray:
        """Return embeddings for `texts` (single str or iterable of str).

        Returns:
            np.ndarray of shape (n, d)
        """
        # Normalize to list
        if isinstance(texts, str):
            inputs = [texts]
        else:
            inputs = list(texts)

        model = self._load_model()
        if model is False:
            return self._stub_embed(inputs)

        embs = model.encode(inputs, show_progress_bar=False)
        arr = np.asarray(embs)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        return arr

    def _stub_embed(self, inputs: List[str], dim: int = 384) -> np.ndarray:
        """Deterministic fallback embedding for testing when models unavailable."""
        out = []
        for text in inputs:
            b = text.encode("utf-8", errors="ignore")
            vec = np.zeros(dim, dtype=np.float32)
            if len(b) == 0:
                vec[0] = 1.0
            else:
                for i, val in enumerate(b):
                    vec[i % dim] += (val + 1)
            norm = np.linalg.norm(vec)
            if norm == 0:
                norm = 1.0
            vec = vec / norm
            out.append(vec)
        return np.vstack(out)

    @staticmethod
    def cache_embeddings(embeddings: np.ndarray, cache_path: str) -> None:
        import pickle

        with open(cache_path, "wb") as f:
            pickle.dump(embeddings, f)

    @staticmethod
    def load_cached_embeddings(cache_path: str) -> np.ndarray:
        import pickle

        with open(cache_path, "rb") as f:
            return pickle.load(f)


__all__ = ["StaticEmbeddings"]



