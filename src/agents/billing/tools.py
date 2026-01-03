class BillingTools:
    """
    Ledger & Payment Gateway tools
    """
    @staticmethod
    def check_balance(account_id: str):
        return {"account_id": account_id, "balance": 150.00}

    @staticmethod
    def process_payment(account_id: str, amount: float):
        return {"status": "Success", "amount": amount}
