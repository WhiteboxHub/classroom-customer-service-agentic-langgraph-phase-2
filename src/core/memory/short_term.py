"""
Short-term memory: Conversation summaries after each step.
Used for grounding, not for control decisions.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.database import database


class ShortTermMemory:
    """
    Conversation State Store (Postgres) for short-term summaries.
    
    Architectural rule: Memory is for grounding only, not control flow.
    """
    
    def __init__(self):
        self.conn_url = os.getenv("POSTGRES_URL")
    
    async def save_summary(
        self,
        session_id: str,
        step_id: str,
        node_name: str,
        summary: str,
        metadata: Dict[str, Any] = None,
    ):
        """
        Save a summary after each execution step.
        
        Args:
            session_id: Conversation/session identifier
            step_id: Execution step identifier
            node_name: Name of the node that executed
            summary: Text summary of the step
            metadata: Additional metadata
        """
        try:
            query = """
                INSERT INTO conversation_summaries 
                (session_id, step_id, node_name, summary, metadata, created_at)
                VALUES (:session_id, :step_id, :node_name, :summary, :metadata, :created_at)
            """
            await database.execute(
                query=query,
                values={
                    "session_id": session_id,
                    "step_id": step_id,
                    "node_name": node_name,
                    "summary": summary,
                    "metadata": metadata or {},
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            print(f"[ShortTermMemory] Saved summary for {session_id}/{step_id}")
        except Exception as e:
            # Graceful degradation: log but don't fail
            print(f"[ShortTermMemory] Error saving summary: {e}")
    
    async def get_recent_summaries(
        self, session_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent summaries for a session (for grounding).
        
        Args:
            session_id: Conversation identifier
            limit: Maximum number of summaries to retrieve
        
        Returns:
            List of summary dictionaries
        """
        try:
            query = """
                SELECT step_id, node_name, summary, metadata, created_at
                FROM conversation_summaries
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT :limit
            """
            results = await database.fetch_all(
                query=query,
                values={"session_id": session_id, "limit": limit},
            )
            return [dict(row) for row in results]
        except Exception as e:
            print(f"[ShortTermMemory] Error retrieving summaries: {e}")
            return []
    
    async def create_step_summary(
        self,
        session_id: str,
        node_name: str,
        state: Dict[str, Any],
    ) -> str:
        """
        Create a summary of the current step for storage.
        
        Args:
            session_id: Session identifier
            node_name: Name of the executing node
            state: Current state snapshot
        
        Returns:
            Text summary
        """
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        summary_parts = [f"Node: {node_name}"]
        if last_message:
            content = last_message.content if hasattr(last_message, "content") else str(last_message)
            summary_parts.append(f"Last message: {content[:100]}...")
        
        tool_calls = state.get("tool_calls", [])
        if tool_calls:
            summary_parts.append(f"Tools called: {[tc.tool_name for tc in tool_calls[-3:]]}")
        
        return " | ".join(summary_parts)


# Global instance
short_term_memory = ShortTermMemory()
