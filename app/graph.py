from langgraph.graph import StateGraph, END
from app.state import AgenticState
from agents.orchestrator import orchestrator_node
from agents.claims.agent import claims_agent
from agents.billing.agent import billing_agent
from safety.sentinel import sentinel_node
from agents.scheduling.agent import scheduling_agent
from agents.policy.agent import policy_agent

def build_graph():
    graph = StateGraph(AgenticState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("claims", claims_agent)
    graph.add_node("billing", billing_agent)
    graph.add_node("sentinel", sentinel_node)

    graph.add_node("scheduling", scheduling_agent)
    graph.add_node("policy", policy_agent)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
   
        "orchestrator",
        lambda s: s["intent"],
        {
            "claims": "claims",
            "billing": "billing",
            "multi": "claims",
            "scheduling": "scheduling",
            "policy": "policy",
            "unknown": END,
        },
    )

    graph.add_edge("claims", "sentinel")
    graph.add_edge("billing", "sentinel")

    graph.add_conditional_edges(
        "sentinel",
        lambda s: "blocked" if s["sentinel_blocked"] else "ok",
        {
            "blocked": END,
            "ok": END,
        },
    )

    return graph.compile()
