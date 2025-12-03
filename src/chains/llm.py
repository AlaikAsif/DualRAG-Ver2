# LLM initialization module
from langchain_ollama import OllamaLLM
import logging
from typing import Optional

"""
Ollama LLM wrapper.

This wrapper attempts to be resilient to different client APIs and
keeps a simple `generate()` method for downstream code.
"""

logger = logging.getLogger(__name__)


class LLM:
    def __init__(self, url: str = "http://localhost:11434", model: str = "granite3-dense:8b", connect: bool = True):
        """Initialize the wrapper.

        Args:
            url: base URL for Ollama server
            model: model name to load
            connect: if False, skip creating the client (useful for tests)
        """
        self.url = url
        self.model = model
        self.llm: Optional[object] = None
        if connect:
            self.initialize_connection()

    def initialize_connection(self):
        """Create the underlying Ollama client.

        Tries common constructor argument names for compatibility across
        versions: `base_url` then `url`.
        """
        try:
            try:
                # Preferred new class name and parameter
                self.llm = OllamaLLM(model=self.model, base_url=self.url)
            except TypeError:
                # Older constructor name
                self.llm = OllamaLLM(model=self.model, url=self.url)
            logger.info("Connected to Ollama model: %s at %s", self.model, self.url)
        except Exception as e:
            logger.error("Failed to connect to Ollama model: %s", e)
            raise

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
        """Generate text from the underlying LLM.

        This method supports different client APIs (invoke, generate, callable)
        and normalizes the returned value to a string.
        """
        if not self.llm:
            raise ValueError("LLM not initialized.")

        try:
            # Prepare a small kwargs dict we'll try to pass; some clients
            # don't accept these and will raise TypeError. We'll retry
            # without them if needed.
            call_kwargs = {"temperature": temperature, "max_tokens": max_tokens}

            def _call_with_fallback(callable_fn, prompt_arg):
                try:
                    return callable_fn(prompt_arg, **call_kwargs)
                except TypeError:
                    # Retry without the additional kwargs
                    return callable_fn(prompt_arg)

            # Prefer `invoke` if available
            if hasattr(self.llm, "invoke"):
                resp = _call_with_fallback(self.llm.invoke, prompt)
            elif hasattr(self.llm, "generate"):
                # Some generate APIs accept a list or single string
                try:
                    resp = _call_with_fallback(self.llm.generate, prompt)
                except TypeError:
                    resp = _call_with_fallback(self.llm.generate, [prompt])
            elif callable(self.llm):
                try:
                    resp = _call_with_fallback(self.llm, prompt)
                except TypeError:
                    resp = self.llm(prompt)
            else:
                raise RuntimeError("Underlying LLM client does not expose a supported call interface.")

            # Normalize common LangChain-like result shapes
            if isinstance(resp, str):
                return resp
            if hasattr(resp, "generations"):
                try:
                    return str(resp.generations[0][0].text)
                except Exception:
                    return str(resp)
            return str(resp)
        except Exception as e:
            logger.error("Error generating text: %s", e)
            raise

    def health_check(self) -> bool:
        """Simple health check that sends a tiny prompt."""
        try:
            out = self.generate("ping", temperature=0.0, max_tokens=10)
            return bool(out)
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return False