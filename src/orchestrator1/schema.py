from pydantic import BaseModel, Field
from typing import Literal

class RoutingDecision(BaseModel):
    """
    RoutingDecision Pydantic models
    """
    intent: Literal['claims', 'billing', 'scheduling', 'triage'] = Field(description="The classified intent of the user request")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score of the routing decision")
    target_agent_id: str = Field(description="The ID of the agent to route to")
    reasoning: str = Field(description="Explanation of why this agent was selected")
