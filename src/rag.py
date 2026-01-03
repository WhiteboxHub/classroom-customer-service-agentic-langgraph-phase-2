import os
import chromadb
from chromadb.utils import embedding_functions

class RagEngine:
    def __init__(self):
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        try:
            self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        except:
             self.client = chromadb.PersistentClient(path="./chroma_data_local")
             
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="healthcare_docs", 
            embedding_function=self.ef
        )

    def search(self, query: str, k: int = 3):
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return results['documents'][0] if results['documents'] else []
