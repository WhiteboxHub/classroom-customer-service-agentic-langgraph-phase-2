"""
Tool initialization - register all tools with the registry.
"""
# from src.core.tools.registry import tool_registry, ToolPermission
# from src.agents.claims.tools import ClaimsTools
# from src.agents.billing.tools import BillingTools
# from src.mcp_server import MCPServer
from core.tools.registry import tool_registry, ToolPermission
from agents.claims.tools import ClaimsTools
from agents.billing.tools import BillingTools
from mcp_server import MCPServer
import asyncio


# Synchronous wrappers for async MCP tools
# Note: In production, these would be properly async-aware
# For now, we use a simple approach that works in most cases

def sync_get_claim_status(claim_id: str):
    """
    Synchronous wrapper for claim status lookup.
    Note: This is a simplified version. In production, tools should be async-aware.
    """
    try:
        # Try to get running event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we can't use asyncio.run()
            # Return a placeholder that indicates async is needed
            # In production, the tool registry would handle async tools
            return {"error": "Async tool requires async context - use async tool execution"}
    except RuntimeError:
        # No event loop, safe to use asyncio.run
        pass
    
    # Fallback: use the sync ClaimsTools method instead
    from src.agents.claims.tools import ClaimsTools
    return ClaimsTools.lookup_claim_status(claim_id)


def sync_check_eligibility(member_id: str):
    """
    Synchronous wrapper for eligibility check.
    Note: This is a simplified version. In production, tools should be async-aware.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return {"error": "Async tool requires async context"}
    except RuntimeError:
        pass
    
    # For now, return a simple response
    # In production, this would properly call the async MCP server
    return {"member_id": member_id, "eligible": True, "note": "Simplified sync wrapper"}


def initialize_tools():
    """
    Register all tools with the registry.
    This must be called before graph execution.
    """
    # Claims tools
    tool_registry.register(
        "lookup_claim_status",
        ClaimsTools.lookup_claim_status,
        ToolPermission.CLAIMS_READ,
        "Look up the status of a claim by claim ID",
    )
    tool_registry.register(
        "lookup_policy_code",
        ClaimsTools.lookup_policy_code,
        ToolPermission.CLAIMS_READ,
        "Look up policy code details",
    )
    tool_registry.register(
        "mcp_get_claim_status",
        sync_get_claim_status,
        ToolPermission.CLAIMS_READ,
        "MCP: Get detailed claim status from database",
    )
    
    # Billing tools
    tool_registry.register(
        "check_balance",
        BillingTools.check_balance,
        ToolPermission.BILLING_READ,
        "Check account balance",
    )
    tool_registry.register(
        "process_payment",
        BillingTools.process_payment,
        ToolPermission.BILLING_WRITE,
        "Process a payment (requires approval)",
    )
    
    # Member/eligibility tools
    tool_registry.register(
        "check_eligibility",
        sync_check_eligibility,
        ToolPermission.MEMBER_READ,
        "Check member eligibility status",
    )

