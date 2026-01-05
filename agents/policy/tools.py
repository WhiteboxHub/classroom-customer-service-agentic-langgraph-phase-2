def lookup_policy(policy_id: str):
    """
    Mock policy lookup.
    """
    return {
        "policy_id": policy_id,
        "coverage": "Covered after deductible",
        "requires_auth": True
    }
