from langchain_core.messages import HumanMessage

from core.graph.engine import Engine
from core.graph.state_schema import AgentState

# Import agent node callables
from agents.orchestrator import orchestrator_node
from agents.claims.agent import claims_agent_node
from agents.billing.agent import billing_agent_node
from agents.scheduling.agent import scheduling_agent_node
from agents.backend.sentinel import sentinel_node


def run():
    # 1️⃣ Create engine
    engine = Engine()

    # 2️⃣ Build the graph explicitly
    engine.build_complete_graph(
        orchestrator_node=orchestrator_node,
        claims_node=claims_agent_node,
        billing_node=billing_agent_node,
        scheduling_node=scheduling_agent_node,
        sentinel_node=sentinel_node,
    )

    # 3️⃣ Compile the graph
    graph = engine.compile()

    # 4️⃣ Initial blackboard state
    initial_state: AgentState = {
        "messages": [HumanMessage(content="what is the claims status for my last accident?")],
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

    import asyncio

    final_state = asyncio.run(graph.ainvoke(initial_state))


    print("\n========== FINAL MESSAGE ==========")
    print(final_state["messages"][-1].content)

    print("\n========== FINAL STATE ==========")
    for k, v in final_state.items():
        if k != "messages":
            print(f"{k}: {v}")


if __name__ == "__main__":
    run()
