"""
Export preprocessing chunks and embeddings.

Usage:
    python scripts/export_chunks_to_embeddings.py [--out-dir data/embeddings] [--chunk-size 400] [--chunk-overlap 100]

By default the script will try to load documents using `Loader.loop_file_paths()`.
If no documents are found it will run a small self-test using sample text.

Outputs:
- <out_dir>/chunks.jsonl  (one JSON per chunk: {"text":..., "metadata": ...})
- <out_dir>/embeddings.npy (numpy array of shape (n_chunks, dim))

This script is safe to run during development; semantic embedding requires
`sentence-transformers` to be installed. If it's not available the script will
still produce chunks and a zero-length embeddings file.
"""

from pathlib import Path
import json
import argparse
import numpy as np
from typing import List, Dict, Any



def get_documents() -> List[Any]:
    try:
        from src.preprocessing.loaders import Loader
        docs = Loader.loop_file_paths()
        return docs
    except Exception:
        return []


def clean_doc(doc) -> Any:
    text = doc.page_content
    # import cleaner lazily to avoid module import side-effects
    try:
        from src.preprocessing.cleaning import TextCleaner
    except Exception:
        # if import fails, perform minimal local cleaning
        text = text.strip()
        doc.page_content = text
        return doc

    text = TextCleaner.normalize(text)
    text = TextCleaner.special_char_removal(text)
    text = TextCleaner.remove_extra_whitespace(text)
    text = TextCleaner.filter_english_only(text)
    doc.page_content = text
    return doc


def chunk_documents(docs, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
    records = []
    for doc in docs:
        if not getattr(doc, "page_content", None):
            continue
        try:
            from src.preprocessing.chunking import Chunker
            chunks = Chunker.overlapping_chunk_text(doc.page_content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        except Exception:
            # fallback: simple split by paragraphs
            chunks = [p.strip() for p in doc.page_content.split("\n\n") if p.strip()]
        for i, chunk_text in enumerate(chunks):
            meta = dict(getattr(doc, "metadata", {}) or {})
            meta.update({"chunk_index": i, "source": meta.get("source", "<unknown>")})
            records.append({"text": chunk_text, "metadata": meta})
    return records


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print("sentence-transformers not available; skipping embedding step.")
        return None

    model = SentenceTransformer(model_name)
    emb_list = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        emb = model.encode(batch, show_progress_bar=False)
        emb_list.append(emb)
    if emb_list:
        return np.vstack(emb_list)
    return np.zeros((0, model.get_sentence_embedding_dimension()))


def save_outputs(records: List[Dict[str, Any]], embeddings: np.ndarray, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks_file = out_dir / "chunks.jsonl"
    with open(chunks_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    emb_file = out_dir / "embeddings.npy"
    if embeddings is None:
        # write empty array
        np.save(emb_file, np.zeros((0,)))
    else:
        np.save(emb_file, embeddings)

    print(f"Saved {len(records)} chunks to {chunks_file}")
    print(f"Saved embeddings to {emb_file} (shape: {None if embeddings is None else embeddings.shape})")


def main(args):
    out_dir = Path(args.out_dir)
    chunk_size = args.chunk_size
    chunk_overlap = args.chunk_overlap

    docs = get_documents()
    if not docs:
        print("No documents found in configured directories — running self-test with sample text.")
        # create a fake doc-like object
        class Doc:
            def __init__(self, text):
                self.page_content = text
                self.metadata = {"source": "sample"}
        sample_text = (
            "This is a sample document. It contains a few sentences about a single topic. "
            "We will chunk this and embed.\n\n" 
            "Here is a second paragraph that changes topic. It should likely become a new chunk."
        )
        docs = [Doc(sample_text)]

    # Clean documents
    cleaned = []
    for doc in docs:
        try:
            d = clean_doc(doc)
            if d.page_content:
                cleaned.append(d)
        except Exception:
            continue

    # Chunk
    records = chunk_documents(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = [r["text"] for r in records]

    # Embed
    embeddings = None
    if texts:
        embeddings = embed_texts(texts, model_name=args.model_name, batch_size=args.batch_size)

    save_outputs(records, embeddings, out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/embeddings", help="Output directory")
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument("--model-name", default="all-MiniLM-L6-v2")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    main(args)
