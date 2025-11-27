# LLM initialization module
from langchain.llms import Ollama
import logging

"""
For Ollama (default):
            model="granite", url="http://localhost:11434

"""
class LLM:
    def __init__(self,url="http://localhost:11434",model="granite3-dense:8b"):
        self.url = url
        self.model = model
        self.endpoint = f"{url}/api/generate"
        self.llm = None
        self.initialize_connection()

    def initialize_connection_ollama(self):
        try:
            self.llm = Ollama(model=self.model, url=self.url)
            logging.info(f"Connected to Ollama model: {self.model} at {self.url}")
        except Exception as e:
            logging.error(f"Failed to connect to Ollama model: {e}")
            raise e
    def generate_ollama(self, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
        if not self.llm:
            raise ValueError("LLM not initialized.")
        try:
            response = self.llm(prompt,temperature=temperature)
            return response
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            raise e
    def health_check_ollama(self) -> bool:
        try:
            response = self.llm("test")
            return True if response else False
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False