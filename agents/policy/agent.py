def policy_agent(state):
    """
    Handles coverage and benefits explanation.
    Read-only agent by design.
    """

    state["agent_results"]["policy"] = {
        "coverage": "Covered after deductible",
        "notes": "Pre-authorization required"
    }

    state["audit_log"].append("Policy agent executed")
    return state
