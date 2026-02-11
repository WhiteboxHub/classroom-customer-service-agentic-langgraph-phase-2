"""
Scheduling Agent Node: LLM-assisted tool selection for scheduling operations.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage
from src.core.llm import get_llm
from src.core.graph.state_schema import AgentState, ToolCall, AuditEvent
from src.core.security.audit_logger import AuditLogger
from src.interfaces.mcp_client import MCPClient
# from core.llm import get_llm
# from core.graph.state_schema import AgentState, ToolCall, AuditEvent
# from core.security.audit_logger import AuditLogger
# from interfaces.mcp_client import MCPClient

mcp_client = MCPClient()
audit_logger = AuditLogger()


async def scheduling_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Scheduling agent: LLM selects tools, graph executes them.
    
    Args:
        state: Current agent state
    
    Returns:
        State updates with tool calls and response
    """
    print("--- SCHEDULING AGENT NODE ---")
    
    messages = state.get("messages", [])
    if not messages:
        return {"next_step": "__end__"}
    
    last_message = messages[-1]
    user_query = last_message.content if hasattr(last_message, "content") else str(last_message)
    
    # Get available tools (scheduling tools would be registered here)
    available_tools = mcp_client.get_available_tools("scheduling")
    tools_list = [f"- {t['name']}: {t['description']}" for t in available_tools]
    tools_str = "\n".join(tools_list) if tools_list else "No tools available."
    
    # LLM decides which tools to use
    llm = get_llm("scheduling")
    
    system_prompt = """You are a Scheduling Coordinator for XYZ Corp.
        Your responsibility is to optimize appointment slots for technicians and customer support representatives.
        Prioritize urgent issues and minimize travel time for field techs.

        Available tools:
        {tools}

        Respond with JSON:
        {{
            "reasoning": "Why you need these tools",
            "tool_calls": [],
            "response_template": "Draft response"
        }}"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User query: {query}\n\nDetermine which tools to use."),
    ])
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        llm_response = await chain.ainvoke({
            "tools": tools_str,
            "query": user_query,
        })
        
        tool_calls_data = llm_response.get("tool_calls", [])
        response_template = llm_response.get("response_template", "I'll help you schedule an appointment.")
        
        new_tool_calls = []
        tool_results = {}
        
        for tool_call_data in tool_calls_data:
            tool_name = tool_call_data.get("tool_name")
            arguments = tool_call_data.get("arguments", {})
            
            tool_call = mcp_client.create_tool_call("scheduling", tool_name, arguments)
            tool_call.status = "approved"
            
            result = mcp_client.call_tool("scheduling", tool_name, arguments, state)
            tool_call.status = "executed" if result.get("status") == "success" else "failed"
            tool_call.result = result.get("result")
            tool_call.error = result.get("error")
            tool_results[tool_name] = result
            
            new_tool_calls.append(tool_call)
        
        # Generate response
        final_response = response_template
        for tool_name, result in tool_results.items():
            placeholder = "{{tool_result}}"
            if placeholder in final_response:
                result_str = json.dumps(result.get("result", {}), indent=2)
                final_response = final_response.replace(placeholder, result_str, 1)
        
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            node_name="scheduling",
            event_type="tool_execution",
            details={"tools_called": [tc.tool_name for tc in new_tool_calls]},
        )
        
        audit_logger.log_event(
            actor="scheduling",
            action="execute_tools",
            resource="scheduling_tools",
            status="success",
            details={"tools": [tc.tool_name for tc in new_tool_calls]},
        )
        
        print(f"Scheduling Agent: Executed {len(new_tool_calls)} tool(s)")
        
        return {
            "messages": [AIMessage(content=final_response)],
            "tool_calls": new_tool_calls,
            "audit_trail": [audit_event],
            "next_step": "__end__",
        }
    
    except Exception as e:
        print(f"Scheduling agent error: {e}")
        return {
            "messages": [AIMessage(content="I apologize, but I encountered an error. Please try again.")],
            "next_step": "__end__",
        }
