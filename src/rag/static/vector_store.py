# faiss vector store management

from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from src.rag.static.embeddings import StaticEmbeddings
import faiss
import os
import json
import numpy as np
from filelock import FileLock


class VectorStore:
    """Helper around FAISS vector store for static RAG.

    Usage:
        vs = VectorStore()
        store = vs.create_vector_store(texts, metadatas=metas)
    """

    def __init__(self, embedding_model: Any = None, indexer: Any = None):
        self.embedding_model = embedding_model or StaticEmbeddings()
        self.indexer = indexer
        self.docstore = InMemoryDocstore()

    def create_vector_store(self, texts: list, metadatas: list = None, embeddings: object = None):
        """Create a FAISS-backed vector store from texts."""
        metadatas = metadatas or [None] * len(texts)

        if embeddings is None:
            embed_fn = None
            if hasattr(self.embedding_model, "embed"):
                embed_fn = self.embedding_model.embed
            elif callable(self.embedding_model):
                embed_fn = self.embedding_model

            if embed_fn is None:
                raise ValueError("No embedding function available to create vector store")

            embeddings = embed_fn(texts)

        out_dir = os.path.join("data", "vectors", "static", "index")
        out_path = os.path.join(out_dir, "faiss_index.bin")
        os.makedirs(out_dir, exist_ok=True)

        # If a previous index exists, remove it so we overwrite cleanly
        # Use FileLock to avoid races between processes writing files
        try:
            lock = FileLock(os.path.join(out_dir, ".lock"))
            with lock:
                try:
                    if os.path.exists(out_path):
                        os.remove(out_path)
                    for fn in os.listdir(out_dir):
                        fp = os.path.join(out_dir, fn)
                        if os.path.isfile(fp):
                            os.remove(fp)
                except Exception:
                    pass
        except Exception:
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception:
                pass

        def _write_exports(texts_out, metas_out, embs_out, out_dir_local):
            try:
                docs_fp = os.path.join(out_dir_local, "documents.jsonl")
                with open(docs_fp, "w", encoding="utf-8") as fh:
                    for t, m in zip(texts_out, metas_out):
                        fh.write(json.dumps({"text": t, "metadata": m}, ensure_ascii=False) + "\n")
            except Exception:
                pass
            try:
                if embs_out is not None:
                    np.save(os.path.join(out_dir_local, "embeddings.npy"), embs_out)
            except Exception:
                pass

        # Prefer convenience constructor if available
        # If embeddings were provided by the caller, prefer manual construction
        # to ensure we use these exact embeddings and export them.
        if embeddings is not None:
            # Manual construction using provided embeddings
            index_to_docstore_id = {}
            for i, (txt, meta) in enumerate(zip(texts, metadatas)):
                doc_id = str(i)
                try:
                    self.docstore._dict[doc_id] = {"text": txt, "metadata": meta}
                except Exception:
                    try:
                        self.docstore.store[doc_id] = {"text": txt, "metadata": meta}
                    except Exception:
                        pass
                index_to_docstore_id[i] = doc_id

            try:
                emb_arr = np.asarray(embeddings).astype(np.float32)
                if emb_arr.ndim == 1:
                    emb_arr = emb_arr.reshape(-1, 1)
                norms = np.linalg.norm(emb_arr, axis=1, keepdims=True)
                norms[norms == 0] = 1e-12
                emb_norm = emb_arr / norms
                d = emb_norm.shape[1]
                faiss_index = faiss.IndexFlatIP(d)
                faiss_index.add(emb_norm)
                vector_store = FAISS(embedding_function=(getattr(self.embedding_model, 'embed', None) if hasattr(self.embedding_model, 'embed') else None), index=faiss_index, docstore=self.docstore, index_to_docstore_id=index_to_docstore_id)
            except Exception:
                vector_store = None

            # Persist: write vector_store via save_local if possible, else write raw index
            try:
                if vector_store is not None and hasattr(vector_store, 'save_local'):
                    try:
                        lock = FileLock(os.path.join(out_dir, '.lock'))
                        with lock:
                            vector_store.save_local(out_dir)
                            _write_exports(texts, metadatas, embeddings, out_dir)
                            return out_dir
                    except Exception:
                        try:
                            vector_store.save_local(out_dir)
                        except Exception:
                            pass
                        try:
                            _write_exports(texts, metadatas, embeddings, out_dir)
                        except Exception:
                            pass
                        return out_dir
                # fallback: write raw faiss index
                lock = FileLock(os.path.join(out_dir, '.lock'))
                with lock:
                    faiss.write_index(faiss_index, out_path)
                    _write_exports(texts, metadatas, embeddings, out_dir)
                    return out_dir
            except Exception:
                try:
                    faiss.write_index(faiss_index, out_path)
                except Exception:
                    pass
                try:
                    _write_exports(texts, metadatas, embeddings, out_dir)
                except Exception:
                    pass
                return out_dir

        if hasattr(FAISS, "from_texts"):
            try:
                vs = FAISS.from_texts(texts, self.embedding_model if hasattr(self.embedding_model, "embed") else self.embedding_model, metadatas=metadatas)
                # try to persist using adapter helper if present
                try:
                    if hasattr(vs, "save_local"):
                        # persist under lock
                        try:
                            lock = FileLock(os.path.join(out_dir, ".lock"))
                            with lock:
                                vs.save_local(out_dir)
                                # try to save exported docs/embeddings for incremental updates
                                try:
                                    # compute embeddings if we don't have them
                                    if embeddings is None:
                                        embed_fn = getattr(self.embedding_model, "embed", None)
                                        if callable(embed_fn):
                                            embeddings_local = embed_fn(texts)
                                        else:
                                            embeddings_local = None
                                    else:
                                        embeddings_local = embeddings
                                except Exception:
                                    embeddings_local = None
                                _write_exports(texts, metadatas, embeddings_local, out_dir)
                                return out_dir
                        except Exception:
                            # if lock acquisition fails, try to save without lock
                            try:
                                vs.save_local(out_dir)
                            except Exception:
                                pass
                            try:
                                _write_exports(texts, metadatas, embeddings, out_dir)
                            except Exception:
                                pass
                            return out_dir
                except Exception:
                    pass
                # fallback to writing underlying faiss index
                if hasattr(vs, "index"):
                    try:
                        lock = FileLock(os.path.join(out_dir, ".lock"))
                        with lock:
                            faiss.write_index(vs.index, out_path)
                            # write exports
                            try:
                                _write_exports(texts, metadatas, embeddings, out_dir)
                            except Exception:
                                pass
                            return out_dir
                    except Exception:
                        # fallback to write without lock
                        try:
                            faiss.write_index(vs.index, out_path)
                        except Exception:
                            pass
                        try:
                            _write_exports(texts, metadatas, embeddings, out_dir)
                        except Exception:
                            pass
                        return out_dir
                # if no index available, return the vs object path hint
                try:
                    _write_exports(texts, metadatas, embeddings, out_dir)
                except Exception:
                    pass
                return out_dir
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

        # Build a raw FAISS index from precomputed embeddings and attach docstore
        try:
            emb_arr = np.asarray(embeddings).astype(np.float32)
            if emb_arr.ndim == 1:
                emb_arr = emb_arr.reshape(-1, 1)
            # normalize for cosine-like inner-product search
            norms = np.linalg.norm(emb_arr, axis=1, keepdims=True)
            norms[norms == 0] = 1e-12
            emb_norm = emb_arr / norms
            d = emb_norm.shape[1]
            faiss_index = faiss.IndexFlatIP(d)
            faiss_index.add(emb_norm)
            vector_store = FAISS(embedding_function=(getattr(self.embedding_model, 'embed', None) if hasattr(self.embedding_model, 'embed') else None), index=faiss_index, docstore=self.docstore, index_to_docstore_id=index_to_docstore_id)
        except Exception:
            # If constructing via adapter fails, try to fall back to a minimal adapter
            vector_store = None

        # Persist FAISS index to the project's data folder (fallback)
        try:
            if hasattr(vector_store, "save_local"):
                try:
                    lock = FileLock(os.path.join(out_dir, ".lock"))
                    with lock:
                        vector_store.save_local(out_dir)
                        try:
                            _write_exports(texts, metadatas, embeddings, out_dir)
                        except Exception:
                            pass
                        return out_dir
                except Exception:
                    try:
                        vector_store.save_local(out_dir)
                    except Exception:
                        pass
                    try:
                        _write_exports(texts, metadatas, embeddings, out_dir)
                    except Exception:
                        pass
                    return out_dir
        except Exception:
            pass

        # final fallback: write raw faiss index
        try:
            lock = FileLock(os.path.join(out_dir, ".lock"))
            with lock:
                faiss.write_index(vector_store.index, out_path)
                try:
                    _write_exports(texts, metadatas, embeddings, out_dir)
                except Exception:
                    pass
                return out_dir
        except Exception:
            try:
                faiss.write_index(vector_store.index, out_path)
            except Exception:
                pass
            try:
                _write_exports(texts, metadatas, embeddings, out_dir)
            except Exception:
                pass
            return out_dir
    

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

    @staticmethod
    def from_export_files(chunks_path: str, embeddings_path: str, persist_dir: str | None = None):
        """Build a FAISS vector store from exported `chunks.jsonl` and `embeddings.npy`.

        Returns tuple `(out_path, faiss_adapter)` where `out_path` is the saved index path
        and `faiss_adapter` is the LangChain FAISS adapter instance.
        """
        persist_dir = persist_dir or os.path.join("data", "vectors", "static", "index")
        os.makedirs(persist_dir, exist_ok=True)

        # Load chunks
        texts = []
        metadatas = []
        with open(chunks_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                obj = json.loads(line)
                texts.append(obj.get("text") or obj.get("content") or obj.get("page_content") or obj.get("chunk") )
                metadatas.append(obj.get("metadata") or {})

        # Load embeddings
        emb = np.load(embeddings_path)
        if emb.shape[0] != len(texts):
            raise ValueError("Embeddings length does not match number of chunks")

        # Build InMemoryDocstore mapping
        docstore = InMemoryDocstore()
        index_to_docstore_id = {}
        for i, (t, m) in enumerate(zip(texts, metadatas)):
            doc_id = str(i)
            # store conservative fields
            try:
                docstore._dict[doc_id] = {"text": t, "metadata": m}
            except Exception:
                try:
                    docstore.store[doc_id] = {"text": t, "metadata": m}
                except Exception:
                    pass
            index_to_docstore_id[i] = doc_id

        # Construct FAISS adapter with precomputed embeddings
        faiss_adapter = FAISS(embeddings=emb, docstore=docstore, index_to_docstore_id=index_to_docstore_id)

        # Persist using adapter save_local if available
        try:
            if hasattr(faiss_adapter, "save_local"):
                faiss_adapter.save_local(persist_dir)
                out_path = os.path.join(persist_dir, "faiss_index.bin")
                return out_path, faiss_adapter
        except Exception:
            pass

        # Fallback to write raw faiss index
        out_path = os.path.join(persist_dir, "faiss_index.bin")
        faiss.write_index(faiss_adapter.index, out_path)
        return out_path, faiss_adapter
    
    def add_documents(self, texts: list, metadatas: list = None, embeddings: object = None, persist_dir: str | None = None):
        """Add documents to the persisted vector store.

        Implementation note: to keep the code robust without relying on the
        LangChain adapter's append API, this method will load any previously
        persisted `documents.jsonl` (if present), append the new documents,
        and rebuild/persist the FAISS index. This is less efficient than an
        in-place append but is deterministic and simple.
        """
        persist_dir = persist_dir or os.path.join("data", "vectors", "static", "index")
        os.makedirs(persist_dir, exist_ok=True)

        # Try efficient adapter-backed append first when possible
        try:
            # Attempt to load existing adapter saved via save_local
            if os.path.isdir(persist_dir) and hasattr(FAISS, "load_local"):
                try:
                    faiss_adapter = FAISS.load_local(persist_dir)
                except Exception:
                    faiss_adapter = None
            else:
                faiss_adapter = None

            # If we have an adapter and it exposes an add API, use it
            if faiss_adapter is not None:
                appended = False
                # Prefer add_texts API if available
                try:
                    if hasattr(faiss_adapter, "add_texts"):
                        faiss_adapter.add_texts(texts, metadatas=metadatas)
                        appended = True
                    elif hasattr(faiss_adapter, "add_documents"):
                        # some adapters use add_documents(documents)
                        docs = []
                        for t, m in zip(texts, metadatas or [None] * len(texts)):
                            docs.append({"page_content": t, "metadata": m})
                        faiss_adapter.add_documents(docs)
                        appended = True
                    elif embeddings is not None and hasattr(faiss_adapter, "add_embeddings"):
                        faiss_adapter.add_embeddings(embeddings, metadatas)
                        appended = True
                except Exception:
                    appended = False

                if appended:
                    # persist adapter if possible (under lock)
                    try:
                        if hasattr(faiss_adapter, "save_local"):
                            try:
                                lock = FileLock(os.path.join(persist_dir, ".lock"))
                                with lock:
                                    faiss_adapter.save_local(persist_dir)
                            except Exception:
                                try:
                                    faiss_adapter.save_local(persist_dir)
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    # append to documents.jsonl for rebuild fallback (under lock)
                    docs_fp = os.path.join(persist_dir, "documents.jsonl")
                    try:
                        lock = FileLock(os.path.join(persist_dir, ".lock"))
                        with lock:
                            with open(docs_fp, "a", encoding="utf-8") as fh:
                                for t, m in zip(texts, metadatas or [None] * len(texts)):
                                    fh.write(json.dumps({"text": t, "metadata": m}, ensure_ascii=False) + "\n")
                    except Exception:
                        try:
                            with open(docs_fp, "a", encoding="utf-8") as fh:
                                for t, m in zip(texts, metadatas or [None] * len(texts)):
                                    fh.write(json.dumps({"text": t, "metadata": m}, ensure_ascii=False) + "\n")
                        except Exception:
                            pass

                    # efficient append succeeded; return the index directory
                    return persist_dir
        except Exception:
            # fall through to rebuild path
            pass

        # Fallback: rebuild by reading existing exported docs (if any) and reindexing
        existing_texts = []
        existing_metas = []
        docs_fp = os.path.join(persist_dir, "documents.jsonl")
        if os.path.exists(docs_fp):
            try:
                with open(docs_fp, "r", encoding="utf-8") as fh:
                    for line in fh:
                        if not line.strip():
                            continue
                        obj = json.loads(line)
                        existing_texts.append(obj.get("text"))
                        existing_metas.append(obj.get("metadata") or {})
            except Exception:
                existing_texts = []
                existing_metas = []

        metadatas = metadatas or [None] * len(texts)

        combined_texts = existing_texts + texts
        combined_metas = existing_metas + metadatas

        # Rebuild index from combined texts (safer fallback)
        return self.create_vector_store(combined_texts, metadatas=combined_metas, embeddings=None)
    

__all__ = ["VectorStore"]