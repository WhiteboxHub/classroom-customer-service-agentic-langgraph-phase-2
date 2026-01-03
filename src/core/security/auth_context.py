from typing import Optional

class AuthContext:
    """
    Layer 2: Identity Propagation (User Token Handling) [cite: 1012]
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.user_id = None
        self.scopes = []

    def validate(self) -> bool:
        """
        Validate the token and populate user context.
        """
        if not self.token:
            return False
            
        # Mock validation logic
        if self.token.startswith("valid_"):
            self.user_id = "user_123"
            self.scopes = ["read", "write"]
            return True
        return False
        
    def get_user_id(self) -> str:
        return self.user_id
