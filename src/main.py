import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.database import database
from src.core.graph.engine import Engine
from src.core.graph.state_schema import AgentState
from src.agents.orchestrator import orchestrator_node
from src.agents.claims.agent import claims_agent_node
from langchain_core.messages import HumanMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    session_id: str

# Build Graph
engine = Engine()
engine.add_node("orchestrator", orchestrator_node)
engine.add_node("claims", claims_agent_node)
engine.set_entry_point("orchestrator")

def router_logic(state):
    if state["next_step"] == "claims":
        return "claims"
    return "__end__"

engine.add_conditional_edges("orchestrator", router_logic)
engine.add_edge("claims", "__end__")

compiled_app = engine.compile()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"Received message: {request.message}")
    
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_info": {"session_id": request.session_id},
        "scratchpad": {},
        "next_step": None
    }
    
    result = await compiled_app.ainvoke(initial_state)
    
    last_message = result['messages'][-1]
    return {"response": last_message.content, "agent_path": result.get("next_step")}

@app.get("/health")
def health():
    return {"status": "ok"}
