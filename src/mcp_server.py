from src.database import database
# from database import database


class MCPServer:
    """
    Local Model Context Protocol (MCP) server
    """
    @staticmethod
    async def get_claim_status(claim_id: str):
        query = "SELECT * FROM claims WHERE claim_id = :claim_id"
        result = await database.fetch_one(query=query, values={"claim_id": claim_id})
        if result:
            return dict(result)
        return {"error": "Claim not found"}

    @staticmethod
    async def check_eligibility(member_id: str):
        query = "SELECT * FROM members WHERE member_id = :member_id"
        result = await database.fetch_one(query=query, values={"member_id": member_id})
        if result:
            return dict(result)
        return {"error": "Member not found"}
