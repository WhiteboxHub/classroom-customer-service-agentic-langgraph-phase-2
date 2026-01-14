"""
Main FastAPI application with complete LangGraph execution.
"""
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime
import json
from src.database import database
from src.core.graph.engine import Engine
from src.core.graph.state_schema import AgentState
from src.agents.orchestrator import orchestrator_node
from src.agents.claims.agent import claims_agent_node
from src.agents.billing.agent import billing_agent_node
from src.agents.scheduling.agent import scheduling_agent_node
from src.agents.backend.sentinel import sentinel_node
from src.core.tools import initialize_tools
from src.core.memory.short_term import short_term_memory
from src.core.security.pii_scrubber import PIIScrubber
from langchain_core.messages import HumanMessage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect DB and initialize tools."""
    await database.connect()
    
    # Initialize tool registry
    initialize_tools()
    print("[Main] Tools initialized")
    
    yield
    
    await database.disconnect()


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    session_id: str


# Build complete LangGraph
engine = Engine()
engine.build_complete_graph(
    orchestrator_node=orchestrator_node,
    claims_node=claims_agent_node,
    billing_node=billing_agent_node,
    scheduling_node=scheduling_agent_node,
    sentinel_node=sentinel_node,
)

compiled_app = engine.compile()
print("[Main] LangGraph compiled and ready")


def create_initial_state(message: str, session_id: str) -> Dict[str, Any]:
    """
    Create initial agent state from user input.
    
    Args:
        message: User message (will be PII-scrubbed)
        session_id: Session identifier
    
    Returns:
        Initial AgentState dictionary
    """
    # PII scrubbing (Layer 1: Input Sandboxing)
    scrubbed_message = PIIScrubber.scrub(message)
    
    return {
        "messages": [HumanMessage(content=scrubbed_message)],
        "plan": None,
        "current_step": None,
        "next_step": None,
        "scratchpad": {},
        "user_info": {
            "session_id": session_id,
            "original_message_length": len(message),
            "scrubbed": message != scrubbed_message,
        },
        "tool_calls": [],
        "approval_requests": [],
        "audit_trail": [],
        "sentinel_veto": None,
        "execution_metadata": {
            "started_at": datetime.utcnow().isoformat(),
        },
    }


async def add_memory_summaries(state: AgentState, session_id: str):
    """
    Add short-term memory summaries after execution.
    This is for grounding only, not control decisions.
    
    Args:
        state: Final execution state
        session_id: Session identifier
    """
    try:
        # Create summary of execution
        summary = await short_term_memory.create_step_summary(
            session_id, "execution_complete", state
        )
        
        # Save summary (non-blocking)
        await short_term_memory.save_summary(
            session_id=session_id,
            step_id="execution_complete",
            node_name="system",
            summary=summary,
           metadata=json.dumps(
                    {
                        "plan": state.get("plan").dict() if state.get("plan") else None,
                        "tool_calls_count": len(state.get("tool_calls", [])),
                        "sentinel_veto": state.get("sentinel_veto") is not None,
                    },
                    default=str
                )
        )
    except Exception as e:
        # Graceful degradation: don't fail if memory fails
        print(f"[Main] Error saving memory summary: {e}")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint: Execute LangGraph with user input.
    
    Architectural flow:
    1. PII scrub input
    2. Create initial state
    3. Execute LangGraph (orchestrator -> domain agent -> sentinel -> end)
    4. Save memory summaries
    5. Return response
    """
    print(f"[Main] Received message for session: {request.session_id}")
    
    try:
        # Create initial state
        initial_state = create_initial_state(request.message, request.session_id)
        
        # Execute LangGraph
        result = await compiled_app.ainvoke(initial_state)
        
        # Add memory summaries (non-blocking)
        await add_memory_summaries(result, request.session_id)
        
        # Extract response
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message:
            response_content = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )
        else:
            response_content = "I apologize, but I couldn't generate a response."
        
        # Check for sentinel veto
        sentinel_veto = result.get("sentinel_veto")
        if sentinel_veto:
            response_content = (
                messages[-1].content
                if messages and hasattr(messages[-1], "content")
                else "Request blocked by safety checks."
            )
        
        # Extract execution metadata
        plan = result.get("plan")
        agent_path = []
        if plan:
            agent_path = [step.agent_id for step in plan.steps]
        
        return {
            "response": response_content,
            "agent_path": agent_path,
            "session_id": request.session_id,
            "sentinel_veto": sentinel_veto is not None,
            "tool_calls_count": len(result.get("tool_calls", [])),
        }
    
    except Exception as e:
        print(f"[Main] Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "graph_compiled": compiled_app is not None}
