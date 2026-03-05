import faiss
import numpy as np
from app.services.openai_client import OllamaClient
from app.core.config import settings


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks for better context retrieval.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


class JDVectorStore:
    """
    RAG Vector store for job description text using Ollama embeddings and FAISS.
    Provides semantic search capabilities for interview context retrieval.
    """

    def __init__(self, jd_text: str, client: OllamaClient):
        self.client = client
        self.chunks = chunk_text(jd_text)
        
        print(f"Creating embeddings for {len(self.chunks)} chunks...")
        self.embeddings = self.client.embed(self.chunks)

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)
        print(f"Vector store initialized with {len(self.chunks)} chunks, embedding dim: {dim}")

    def similarity_search(self, query: str, k: int = 3) -> list[dict]:
        query_embedding = self.client.embed([query]).astype("float32")
        _, indices = self.index.search(query_embedding, k)

        return [{"page_content": self.chunks[i]} for i in indices[0]]


    # def similarity_search(self, query: str, k: int = 3) -> list[dict]:
    #     """
    #     Retrieve top-k most similar chunks for a query.
    #     Returns list of dicts with page_content.
    #     """
    #     query_embedding = self.client.embed([query])
    #     distances, indices = self.index.search(query_embedding, k)
        
    #     results = []
    #     for idx in indices[0]:
    #         results.append({"page_content": self.chunks[idx]})
        
    #     return results











# import faiss
# import numpy as np
# from ollama import Client
# from app.core.config import settings

# client = Client(host=settings.OLLAMA_BASE_URL)


# def chunk_text(text: str, chunk_size=500, overlap=100):
#     chunks = []
#     start = 0

#     while start < len(text):
#         end = start + chunk_size
#         chunks.append(text[start:end])
#         start += chunk_size - overlap

#     return chunks


# def embed_texts(texts: list[str]) -> np.ndarray:
#     embeddings = []
#     for text in texts:
#         response = client.embeddings(
#             model=settings.OLLAMA_EMBEDDING_MODEL,
#             prompt=text
#         )
#         embeddings.append(response['embedding'])
    
#     return np.array(embeddings, dtype="float32")


# class JDVectorStore:
#     def __init__(self, jd_text: str):
#         self.chunks = chunk_text(jd_text)
#         self.embeddings = embed_texts(self.chunks)

#         dim = self.embeddings.shape[1]
#         self.index = faiss.IndexFlatL2(dim)
#         self.index.add(self.embeddings)

#     def retrieve(self, query: str, top_k: int = 3) -> str:
#         query_embedding = embed_texts([query])
#         _, indices = self.index.search(query_embedding, top_k)

#         return "\n".join(self.chunks[i] for i in indices[0])
