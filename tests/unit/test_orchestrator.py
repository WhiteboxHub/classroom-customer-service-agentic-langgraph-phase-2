import pytest
from src.agents.orchestrator import orchestrator_node
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_orchestrator_routes_to_claims():
    state = {
        "messages": [HumanMessage(content="My claim was denied")],
        "plan": None,
        "current_step": None,
        "next_step": None,
        "scratchpad": {},
        "user_info": {},
        "tool_calls": [],
        "approval_requests": [],
        "audit_trail": [],
        "sentinel_veto": None,
        "execution_metadata": {},
    }

    delta = await orchestrator_node(state)

    assert delta["next_step"] == "claims"
    assert delta["plan"] is not None
