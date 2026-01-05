def billing_agent(state):
    state["agent_results"]["billing"] = {
        "balance": "$120"
    }
    state["audit_log"].append("Billing agent executed")
    return state
