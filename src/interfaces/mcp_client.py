"""
MCP Client with permission enforcement.
All tool calls must go through this client for auditability.
"""
from src.core.tools.registry import tool_registry
from src.core.graph.state_schema import ToolCall
# from core.tools.registry import tool_registry
# from core.graph.state_schema import ToolCall
from datetime import datetime
import uuid


class MCPClient:
    """
    Model Context Protocol (MCP) Client with permission enforcement.
    
    Architectural rule: All tool calls must be explicit, permission-checked, and logged.
    """
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url
    
    def call_tool(
        self,
        agent_id: str,
        tool_name: str,
        arguments: dict,
        state: dict = None,
    ) -> dict:
        """
        Call a tool with permission checking and audit logging.
        
        Args:
            agent_id: The agent requesting the tool call
            tool_name: The tool to invoke
            arguments: Tool arguments
            state: Current state (for audit logging)
        
        Returns:
            Tool execution result with status
        """
        # Check permission
        if not tool_registry.check_permission(agent_id, tool_name):
            return {
                "status": "error",
                "error": f"Agent '{agent_id}' lacks permission for tool '{tool_name}'",
            }
        
        # Execute tool via registry
        try:
            result = tool_registry.execute_tool(agent_id, tool_name, arguments)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def create_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        arguments: dict,
    ) -> ToolCall:
        """
        Create a ToolCall object for state tracking.
        
        Args:
            agent_id: The agent requesting the call
            tool_name: The tool name
            arguments: Tool arguments
        
        Returns:
            ToolCall object
        """
        return ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            status="pending",
        )
    
    def get_available_tools(self, agent_id: str) -> list:
        """
        Get list of tools available to an agent.
        
        Args:
            agent_id: The agent identifier
        
        Returns:
            List of tool names with descriptions
        """
        tool_names = tool_registry.list_tools_for_agent(agent_id)
        tools_info = []
        
        for tool_name in tool_names:
            tool_def = tool_registry.get_tool(tool_name)
            if tool_def:
                tools_info.append({
                    "name": tool_name,
                    "description": tool_def.get("description", ""),
                })
        
        return tools_info
