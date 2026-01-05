def sentinel_node(state):
    for result in state["agent_results"].values():
        if "credit card" in str(result).lower():
            state["sentinel_blocked"] = True
            state["sentinel_findings"].append({
                "severity": "high",
                "reason": "PII detected",
                "blocked": True
            })
    return state
