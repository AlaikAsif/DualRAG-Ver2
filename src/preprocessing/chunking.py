# Text chunking strategies
from .cleaning import TextCleaner
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import re

class Chunker:
    @staticmethod
    def overlapping_chunk_text(text: str, chunk_size: int = 400, chunk_overlap: int = 100,length_function = len) -> list:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function
        )
        chunks = text_splitter.split_text(text)
        return chunks
    @staticmethod
    def context_aware_chunk_text(text: str, chunk_size: int = 400, chunk_overlap: int = 100,length_function = len) -> list:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", "", ". "],
        )
        chunks = splitter.split_text(text)
        return chunks

    @staticmethod
    def semantic_chunk_text(text: str, chunk_size: int = 400, similarity_threshold: float = 0.7) -> list:
        """Split text into semantic chunks based on sentence similarity using embeddings."""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        # Get embeddings for all sentences
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(sentences)
        
        chunks = []
        current_chunk = [sentences[0]]
        
        for i in range(1, len(sentences)):
            # Compare current sentence with previous
            similarity = cosine_similarity(
                [embeddings[i-1]], 
                [embeddings[i]]
            )[0][0]
            
            if similarity >= similarity_threshold:
                # Similar topics → same chunk
                current_chunk.append(sentences[i])
            else:
                # Topic changed → new chunk
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i]]
            
            # If chunk reaches size limit, save it
            if len(" ".join(current_chunk)) >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        
        # Add last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    @staticmethod
    def select_chunking_strategy(selection: int, text: str):
        """Select and apply chunking strategy."""
        if selection == 0:
            return Chunker.overlapping_chunk_text(text)
        elif selection == 1:
            return Chunker.context_aware_chunk_text(text)
        elif selection == 2:
            return Chunker.semantic_chunk_text(text)
        else:
            raise ValueError("Invalid chunking strategy selection")


__all__ = ["Chunker"]