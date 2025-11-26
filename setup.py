from setuptools import setup, find_packages

setup(
    name="chatbot-revamp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-community",
        "langchain-ollama",
        "ollama",
        "chroma-db",
        "sentence-transformers",
        "pydantic",
        "pydantic-settings",
        "fastapi",
        "uvicorn",
    ],
)
