"""
Long-term memory: Vector DB for historical context retrieval.
Used for grounding only, not for control decisions.
"""
import os
from typing import List, Dict, Any
from src.rag import RagEngine


class LongTermMemory:
    """
    Vector DB wrapper for historical context retrieval.
    
    Architectural rule: Memory retrieval is for grounding only.
    LLMs use retrieved context but don't make control decisions based on it.
    """
    
    def __init__(self):
        self.vector_db_url = os.getenv("VECTOR_DB_URL")
        # Use existing RAG engine for vector search
        self.rag_engine = RagEngine()
        print(f"[LongTermMemory] Initialized (using RAG engine)")
    
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        Search long-term memory for similar past cases.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant context strings
        """
        try:
            results = self.rag_engine.search(query, k=top_k)
            print(f"[LongTermMemory] Found {len(results)} relevant contexts")
            return results if results else []
        except Exception as e:
            print(f"[LongTermMemory] Error searching: {e}")
            return []
    
    def add_document(self, content: str, metadata: dict = None):
        """
        Add a document to long-term memory (for future retrieval).
        
        Args:
            content: Document content
            metadata: Optional metadata
        """
        # In production, this would index the document in the vector DB
        print(f"[LongTermMemory] Would index document (not implemented in this POC)")


# Global instance
long_term_memory = LongTermMemory()
