"""
Tool Registry with Permission Enforcement.
Tools are the "hands" - deterministic execution with explicit permissions.
"""
from typing import Dict, Callable, Any, List, Optional
from enum import Enum


class ToolPermission(Enum):
    """Permission levels for tool access."""
    CLAIMS_READ = "claims:read"
    CLAIMS_WRITE = "claims:write"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    SCHEDULING_READ = "scheduling:read"
    SCHEDULING_WRITE = "scheduling:write"
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"


# Agent-to-permission mapping
AGENT_PERMISSIONS: Dict[str, List[ToolPermission]] = {
    "claims": [
        ToolPermission.CLAIMS_READ,
        ToolPermission.CLAIMS_WRITE,
        ToolPermission.MEMBER_READ,
    ],
    "billing": [
        ToolPermission.BILLING_READ,
        ToolPermission.BILLING_WRITE,
        ToolPermission.MEMBER_READ,
    ],
    "scheduling": [
        ToolPermission.SCHEDULING_READ,
        ToolPermission.SCHEDULING_WRITE,
        ToolPermission.MEMBER_READ,
    ],
    "orchestrator": [],  # Orchestrator doesn't call tools directly
    "sentinel": [
        ToolPermission.CLAIMS_READ,
        ToolPermission.BILLING_READ,
        ToolPermission.SCHEDULING_READ,
        ToolPermission.MEMBER_READ,
    ],
}


class ToolRegistry:
    """
    Central registry for all tools with permission checking.
    No agent may access tools outside its domain.
    """
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._tool_permissions: Dict[str, ToolPermission] = {}
    
    def register(
        self,
        tool_name: str,
        tool_func: Callable,
        required_permission: ToolPermission,
        description: str = "",
    ):
        """
        Register a tool with its required permission.
        
        Args:
            tool_name: Unique identifier for the tool
            tool_func: The callable tool function
            required_permission: Permission required to invoke this tool
            description: Human-readable description
        """
        self._tools[tool_name] = {
            "func": tool_func,
            "description": description,
            "permission": required_permission,
        }
        self._tool_permissions[tool_name] = required_permission
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool definition by name."""
        return self._tools.get(tool_name)
    
    def list_tools_for_agent(self, agent_id: str) -> List[str]:
        """
        List all tools an agent is permitted to use.
        
        Args:
            agent_id: The agent identifier
        
        Returns:
            List of tool names the agent can access
        """
        agent_perms = AGENT_PERMISSIONS.get(agent_id, [])
        available_tools = []
        
        for tool_name, tool_def in self._tools.items():
            required_perm = tool_def["permission"]
            if required_perm in agent_perms:
                available_tools.append(tool_name)
        
        return available_tools
    
    def check_permission(self, agent_id: str, tool_name: str) -> bool:
        """
        Check if an agent has permission to use a tool.
        
        Args:
            agent_id: The agent identifier
            tool_name: The tool name
        
        Returns:
            True if agent has permission, False otherwise
        """
        if tool_name not in self._tools:
            return False
        
        required_perm = self._tools[tool_name]["permission"]
        agent_perms = AGENT_PERMISSIONS.get(agent_id, [])
        
        return required_perm in agent_perms
    
    def execute_tool(
        self, agent_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool with permission checking.
        
        Args:
            agent_id: The agent requesting execution
            tool_name: The tool to execute
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        
        Raises:
            PermissionError: If agent lacks permission
            ValueError: If tool doesn't exist
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        
        if not self.check_permission(agent_id, tool_name):
            raise PermissionError(
                f"Agent '{agent_id}' lacks permission to use tool '{tool_name}'"
            )
        
        tool_func = self._tools[tool_name]["func"]
        try:
            result = tool_func(**arguments)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global tool registry instance
tool_registry = ToolRegistry()

