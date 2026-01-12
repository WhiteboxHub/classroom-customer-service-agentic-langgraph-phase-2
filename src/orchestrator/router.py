from typing import Dict, Any, Literal
from langchain_core.messages import AIMessage
from src.core.graph.state_schema import AgentState
from .schema import RoutingDecision

class Router:
    """
    Intent Classification logic acting as a node.
    """
    def route_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyze the state and route to the appropriate agent.
        Updates 'next_step' in the state.
        """
        print("--- ROUTER ---")
        messages = state['messages']
        last_msg = messages[-1].content.lower() if messages else ""
        
        target = "claims" # Default
        confidence = 0.5
        reasoning = "Default fallback"

        if "bill" in last_msg or "invoice" in last_msg:
            target = "billing"
            confidence = 0.9
            reasoning = "Keywords: bill/invoice"
        elif "schedule" in last_msg or "appoint" in last_msg:
            target = "scheduling"
            confidence = 0.9
            reasoning = "Keywords: schedule/appoint"
        elif "claim" in last_msg:
            target = "claims"
            confidence = 0.9
            reasoning = "Keywords: claim"
            
        print(f"Routing to: {target} (Confidence: {confidence})")
        return {"next_step": target}

    def should_continue(self, state: AgentState) -> Literal["claims", "billing", "scheduling", "__end__"]:
        """
        Conditional edge function.
        """
        next_step = state.get("next_step")
        if next_step in ["claims", "billing", "scheduling"]:
            return next_step
        return "__end__"
