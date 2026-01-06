"""
Shared Blackboard State Schema for Agentic Execution.
This is the single source of truth for all agent state transitions.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Literal
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
import operator
from datetime import datetime


class ToolCall(BaseModel):
    """Represents a tool invocation request."""
    tool_name: str
    arguments: Dict[str, Any]
    agent_id: str
    timestamp: str
    status: Literal["pending", "approved", "rejected", "executed", "failed"] = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


class PlanStep(BaseModel):
    """A single step in the execution plan."""
    step_id: str
    agent_id: str
    action: str
    reasoning: str
    required_tools: List[str]
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = "pending"


class ExecutionPlan(BaseModel):
    """LLM-generated execution plan."""
    intent: str
    confidence: float
    steps: List[PlanStep]
    created_at: str


class ApprovalRequest(BaseModel):
    """Human approval request for sensitive operations."""
    request_id: str
    operation: str
    agent_id: str
    details: Dict[str, Any]
    status: Literal["pending", "approved", "rejected"] = "pending"
    timestamp: str


class AuditEvent(BaseModel):
    """Audit log entry for state transitions."""
    event_id: str
    timestamp: str
    node_name: str
    event_type: str
    details: Dict[str, Any]
    state_snapshot: Optional[Dict[str, Any]] = None


class AgentState(TypedDict):
    """
    The 'Blackboard' Shared State - single source of truth for all agent execution.
    
    Architectural rules:
    - State is immutable; nodes return updates (dict merge)
    - All transitions are explicit and auditable
    - LLMs read state but never mutate it directly
    - Tools are invoked via explicit tool_calls list
    """
    # Messages: Conversation history (append-only)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Execution plan: LLM-generated plan with steps
    plan: Optional[ExecutionPlan]
    
    # Current execution step
    current_step: Optional[str]
    
    # Next node to execute (determined by graph routing)
    next_step: Optional[str]
    
    # Shared scratchpad: Agent-to-agent communication
    scratchpad: Dict[str, Any]
    
    # User context: Verified member ID, session info, auth context
    user_info: Dict[str, Any]
    
    # Tool calls: All tool invocations (pending, approved, executed)
    tool_calls: Annotated[List[ToolCall], operator.add]
    
    # Approval requests: Human-in-the-loop approvals
    approval_requests: Annotated[List[ApprovalRequest], operator.add]
    
    # Audit trail: All state transitions for replayability
    audit_trail: Annotated[List[AuditEvent], operator.add]
    
    # Sentinel veto: Safety agent can block execution
    sentinel_veto: Optional[Dict[str, Any]]
    
    # Execution metadata
    execution_metadata: Dict[str, Any]
