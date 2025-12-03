"""Text cleaning and normalization

Note: import of Loader is deferred inside `comprehensive_clean()` to avoid
module-level circular imports between `loaders` and `cleaning`.
"""
from langdetect import detect, LangDetectException

class TextCleaner:
    @staticmethod
    def normalize(text: str) -> str:
        if not isinstance(text, str):
            raise ValueError("No text provided for cleaning")
        normalized_text = text.lower().strip()
        return normalized_text
    
    @staticmethod
    def special_char_removal(text: str) -> str:
        if not isinstance(text, str):
            raise ValueError("No text provided for cleaning")
        cleaned_text = ''.join(e for e in text if e.isalnum() or e.isspace())
        return cleaned_text
    
    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        if not isinstance(text, str):
            raise ValueError("No text provided for cleaning")
        cleaned_text = ' '.join(text.split())
        return cleaned_text
    
    @staticmethod
    def language_detection(text: str, target_language: str = "en") -> bool:
        """Detect if text matches target language. Default is English."""
        if not isinstance(text, str):
            raise ValueError("No text provided for cleaning")
        try:
            detected_lang = detect(text)
            return detected_lang == target_language
        except LangDetectException:
            return False
    
    @staticmethod
    def filter_english_only(text: str) -> str:
        """Return text if English, otherwise return empty string."""
        if TextCleaner.language_detection(text, "en"):
            return text
        return ""
    
    @staticmethod
    def comprehensive_clean():
        """Apply all cleaning steps to documents."""
        # Import Loader here to avoid circular import at module import time
        from .loaders import Loader
        documents = Loader.loop_file_paths()
        cleaned_documents = []

        for doc in documents:
            text = doc.page_content
            text = TextCleaner.normalize(text)
            text = TextCleaner.special_char_removal(text)
            text = TextCleaner.remove_extra_whitespace(text)
            text = TextCleaner.filter_english_only(text)
            if text:
                doc.page_content = text
                cleaned_documents.append(doc)
 
        return cleaned_documents
    
    __all__ = ["TextCleaner"]