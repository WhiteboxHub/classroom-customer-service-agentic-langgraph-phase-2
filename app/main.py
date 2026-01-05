from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.graph import build_graph
from app.state import AgenticState

app = FastAPI()
graph = build_graph()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    state: AgenticState = {
        "conversation_id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "user_role": None,
        "request_text": req.message,
        "intent": "unknown",

        "execution_status": "not_started",
        "current_step": None,

        "plan": None,
        "agent_results": {},

        "tool_calls": [],
        "approvals": {},

        "sentinel_findings": [],
        "sentinel_blocked": False,

        "audit_log": [],
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    final = graph.invoke(state)
    return final
