ALLOWED_TOOLS = {
    "claims": ["claims_db"],
    "billing": ["billing_api"]
}

def validate_tool(agent: str, tool: str):
    if tool not in ALLOWED_TOOLS.get(agent, []):
        raise PermissionError("Tool not allowed")
