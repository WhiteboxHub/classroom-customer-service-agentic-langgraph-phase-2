from src.rag import RagEngine
from src.mcp_server import MCPServer
from langchain_core.messages import AIMessage

rag = RagEngine()

async def claims_agent_node(state):
    print("--- CLAIMS SPECIALIST ---")
    messages = state['messages']
    last_msg = messages[-1].content
    
    # 1. RAG Lookup
    context_docs = rag.search(last_msg)
    context_str = "\n".join(context_docs)
    
    # 2. Tool Usage (Naive extraction)
    response_text = ""
    
    if "CLM-" in last_msg:
        import re
        match = re.search(r"CLM-\d{4}", last_msg)
        if match:
            claim_id = match.group(0)
            print(f"Looking up claim {claim_id}...")
            claim_info = await MCPServer.get_claim_status(claim_id)
            response_text += f"\nClaim Status: {claim_info}"
    
    # 3. Synthesize Response (Mock LLM)
    response_text = f"Based on our policy:\n{context_str}\n\n{response_text}"
    
    # In a real app, we'd feed context + tool output to an LLM here.
    
    return {
        "messages": [AIMessage(content=response_text)],
        "next_step": "__end__"
    }
