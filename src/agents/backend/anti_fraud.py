from src.core.graph.state_schema import AgentState
# from core.graph.state_schema import AgentState


class AntiFraudAgent:
    """
    Anti-Fraud Agent (The 'Auditor') [cite: 580]
    """
    async def check_fraud(self, state: AgentState):
        print("[AntiFraud] Analyzing patterns...")
        # Fraud detection logic
        return False
