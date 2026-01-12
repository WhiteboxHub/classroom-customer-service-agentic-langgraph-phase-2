class MockLedger:
    """
    Simulated Billing Ledger
    """
    def __init__(self):
        self.accounts = {
            "ACC-123": {"balance": 100.00}
        }

    def get_balance(self, account_id):
        return self.accounts.get(account_id, {}).get("balance", 0.0)
