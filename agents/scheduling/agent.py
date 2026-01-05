def scheduling_agent(state):
    """
    Handles appointment-related workflows:
    - Availability lookup
    - Provider matching
    - Appointment status
    """

    state["agent_results"]["scheduling"] = {
        "status": "checked",
        "available_slots": ["2026-01-10 10:00", "2026-01-11 14:00"]
    }

    state["audit_log"].append("Scheduling agent executed")
    return state
