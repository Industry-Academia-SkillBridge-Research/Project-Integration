import requests
import numpy as np
from app.core.config import settings


class OllamaClient:
    """Client for interacting with Ollama API for chat and embeddings."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    def chat(self, model: str, messages: list[dict], options: dict = None) -> dict:
        """Send chat completion request to Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        if options:
            payload["options"] = options
            
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def embed(self, texts: list[str], model: str = None) -> np.ndarray:
        """Generate embeddings for texts using Ollama."""
        model = model or settings.OLLAMA_EMBEDDING_MODEL
        embeddings = []
        
        for text in texts:
            payload = {
                "model": model,
                "prompt": text
            }
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
        
        return np.array(embeddings, dtype="float32")


def get_client() -> OllamaClient:
    """Returns an Ollama client instance."""
    return OllamaClient()







# from ollama import Client
# from app.core.config import settings

# def get_client() -> Client:
#     """Returns an Ollama client instance"""
#     return Client(host=settings.OLLAMA_BASE_URL)
