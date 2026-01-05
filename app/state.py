from typing import TypedDict, List, Dict, Optional, Literal
from datetime import datetime

Intent = Literal["claims", "billing", "scheduling", "policy", "multi", "unknown"]
ExecStatus = Literal["not_started", "running", "blocked", "completed", "failed"]
ApprovalStatus = Literal["pending", "approved", "rejected"]

class PlanStep(TypedDict):
    step_id: str
    agent: str
    description: str
    requires_approval: bool
    status: ExecStatus

class ExecutionPlan(TypedDict):
    intent: Intent
    steps: List[PlanStep]

class ToolCall(TypedDict):
    tool: str
    agent: str
    input: dict
    output: Optional[dict]
    success: bool

class Approval(TypedDict):
    step_id: str
    status: ApprovalStatus
    reviewer: Optional[str]

class SentinelFinding(TypedDict):
    severity: Literal["low", "high"]
    reason: str
    blocked: bool

class AgenticState(TypedDict):
    conversation_id: str
    user_id: str
    user_role: Optional[str]
    request_text: str
    intent: Intent

    execution_status: ExecStatus
    current_step: Optional[str]

    plan: Optional[ExecutionPlan]
    agent_results: Dict[str, dict]

    tool_calls: List[ToolCall]
    approvals: Dict[str, Approval]

    sentinel_findings: List[SentinelFinding]
    sentinel_blocked: bool

    audit_log: List[str]
    started_at: datetime
    updated_at: datetime
