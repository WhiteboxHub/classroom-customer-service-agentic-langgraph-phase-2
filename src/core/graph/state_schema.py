from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The 'Blackboard' Shared State definition using LangGraph's TypedDict format.
    """
    # Messages: List of conversation history, appended to by nodes
    messages: Annotated[List[BaseMessage], operator.add]
    
    # The next node to execute
    next_step: Optional[str]
    
    # A dictionary for the "Shared Scratchpad" plan
    scratchpad: Dict[str, Any]
    
    # Verified member ID and context
    user_info: Dict[str, Any]
