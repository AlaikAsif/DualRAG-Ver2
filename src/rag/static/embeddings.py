# Embedding model initialization and management
from FlagEmbeddings import FlagModel

class StaticEmbeddings:
    def __init__(self, model_name: str):
        self.model = FlagModel(model_name)

    def embed(self, text)
