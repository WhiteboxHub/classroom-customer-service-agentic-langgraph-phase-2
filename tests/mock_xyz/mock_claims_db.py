import random
import json

class MockClaimsDB:
    """
    Simulated Claims Database
    """
    def __init__(self):
        self.claims = {
            "CLM-001": {"status": "Approved", "amount": 500.00, "description": "Windshield repair"},
            "CLM-002": {"status": "Denied", "reason": "Policy expired", "description": "Towing service"},
            "CLM-003": {"status": "Processing", "description": "Bumper replacement"}
        }

    def get_claim_status(self, claim_id: str) -> dict:
        """
        Returns hardcoded JSON data but occasionally raises a generic Exception 
        to test the agent's recovery loop.
        """
        # Chaos Monkey: 20% chance of failure
        if random.random() < 0.2:
            raise Exception("MockDB Connection Error: Timeout accessing Claims Table")

        claim = self.claims.get(claim_id)
        if not claim:
            return {"status": "Not Found", "error": "Claim ID does not exist"}
            
        return claim
