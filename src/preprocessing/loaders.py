# PDF/DOCX document loaders
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import os
from pathlib import Path
from langdetect import detect

class Loader:
    @staticmethod
    def load(file_path: str):
        if file_path.endswith(".pdf"):
            Loader = PyPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            Loader = Docx2txtLoader(file_path)
        else:
            raise ValueError("Unsupported file format")
        return Loader.load()
    @staticmethod
    def loop_file_paths(directory_path: str = None):
        if directory_path is None:
            directories = [
                Path(__file__).parent.parent.parent / "data" / "documents" / "raw",
                Path(__file__).parent.parent.parent / "data" / "documents" / "processed",
                Path(__file__).parent.parent.parent / "data" / "documents" / "metadata"
            ]
        else:
            directories = [Path(directory_path)]

        documents = []
        for directory in directories:
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                if os.path.isfile(file_path):
                    loaded_docs = Loader.load(file_path)
                    # Add metadata to each document
                    for doc in loaded_docs:
                        doc.metadata['source'] = file_path
                        doc.metadata['filename'] = file_name
                    documents.extend(loaded_docs)
        return documents


__all__ = ["Loader"]