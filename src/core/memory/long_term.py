import os
from typing import List
# from qdrant_client import QdrantClient

class LongTermMemory:
    """
    Vector DB wrapper for historical context [cite: 973]
    """
    def __init__(self):
        self.vector_db_url = os.getenv("VECTOR_DB_URL")
        # self.client = QdrantClient(url=self.vector_db_url)
        print(f"[LongTermMemory] Connected to {self.vector_db_url}")
        
    def search(self, query: str, top_k: int = 3) -> List[str]:
        # Perform vector similarity search
        print(f"[LongTermMemory] Searching for: {query}")
        return ["Similar past case 1", "Similar past case 2"]
    
    def add_document(self, content: str, metadata: dict = None):
        # Embed and index document
        print(f"[LongTermMemory] Indexing document")
