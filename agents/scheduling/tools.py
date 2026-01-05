def fetch_provider_availability(provider_id: str):
    """
    Mock scheduling backend call.
    """
    return {
        "provider_id": provider_id,
        "slots": ["2026-01-10 10:00", "2026-01-11 14:00"]
    }
