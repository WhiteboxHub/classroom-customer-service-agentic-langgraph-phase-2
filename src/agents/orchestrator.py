async def orchestrator_node(state):
    print("--- ORCHESTRATOR ---")
    messages = state['messages']
    last_msg = messages[-1].content.lower()
    
    if "claim" in last_msg or "denied" in last_msg or "coverage" in last_msg:
        return {"next_step": "claims"}
    
    return {"next_step": "__end__"}
