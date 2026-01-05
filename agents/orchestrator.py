def orchestrator_node(state):
    text = state["request_text"].lower()

    if "claim" in text:
        intent = "claims"
    elif "bill" in text:
        intent = "billing"
    else:
        intent = "unknown"

    state["intent"] = intent
    state["audit_log"].append(f"Intent classified as {intent}")
    return state
