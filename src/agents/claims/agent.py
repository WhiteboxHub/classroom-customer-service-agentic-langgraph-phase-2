"""
Claims Agent Node: LLM-assisted tool selection and execution.
LLM decides which tools to use, but graph controls execution flow.
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
from src.rag import RagEngine
# from core.llm import get_llm
# from core.graph.state_schema import AgentState, ToolCall, AuditEvent
# from core.security.audit_logger import AuditLogger
# from interfaces.mcp_client import MCPClient
# from rag import RagEngine

rag = RagEngine()
mcp_client = MCPClient()
audit_logger = AuditLogger()


async def claims_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Claims agent: LLM selects tools, graph executes them.
    
    Architectural rules:
    - LLM suggests tools but never calls them directly
    - All tool calls go through MCP client with permission checks
    - State is the single source of truth
    
    Args:
        state: Current agent state
    
    Returns:
        State updates with tool calls and response
    """
    print("--- CLAIMS AGENT NODE ---")
    
    # Get context
    messages = state.get("messages", [])
    plan = state.get("plan")
    scratchpad = state.get("scratchpad", {})
    
    if not messages:
        return {"next_step": "__end__"}
    
    last_message = messages[-1]
    user_query = last_message.content if hasattr(last_message, "content") else str(last_message)
    
    # 1. RAG Lookup for policy context
    context_docs = rag.search(user_query)
    context_str = "\n".join(context_docs) if context_docs else "No relevant policy documents found."
    
    # 2. Get available tools for this agent
    available_tools = mcp_client.get_available_tools("claims")
    tools_list = [f"- {t['name']}: {t['description']}" for t in available_tools]
    tools_str = "\n".join(tools_list) if tools_list else "No tools available."
    
    # 3. LLM decides which tools to use
    llm = get_llm("claims")
    
    system_prompt = """You are a Claims Specialist for XYZ Corp.
Your goal is to assist customers with claim status inquiries, filing new claims, and understanding coverage details.
Always be empathetic but precise with policy codes.

You can use these tools:
{tools}

Respond with JSON in this format:
{{
    "reasoning": "Why you need these tools",
    "tool_calls": [
        {{
            "tool_name": "lookup_claim_status",
            "arguments": {{"claim_id": "CLM-1234"}}
        }}
    ],
    "response_template": "Draft response using tool results (use placeholders like {{tool_result}})"
}}"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("system", "Policy Context:\n{context}"),
        ("user", "User query: {query}\n\nDetermine which tools to use and draft a response."),
    ])
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        llm_response = await chain.ainvoke({
            "tools": tools_str,
            "context": context_str,
            "query": user_query,
        })
        
        # Extract tool calls from LLM response
        tool_calls_data = llm_response.get("tool_calls", [])
        response_template = llm_response.get("response_template", "I'll help you with your claim inquiry.")
        
        # Create ToolCall objects and execute them
        new_tool_calls = []
        tool_results = {}
        
        for tool_call_data in tool_calls_data:
            tool_name = tool_call_data.get("tool_name")
            arguments = tool_call_data.get("arguments", {})
            
            # Create tool call object
            tool_call = mcp_client.create_tool_call("claims", tool_name, arguments)
            tool_call.status = "approved"  # Auto-approve for read operations
            
            # Execute tool (with permission check)
            result = mcp_client.call_tool("claims", tool_name, arguments, state)
            tool_call.status = "executed" if result.get("status") == "success" else "failed"
            tool_call.result = result.get("result")
            tool_call.error = result.get("error")
            
            new_tool_calls.append(tool_call)
            tool_results[tool_name] = result
        
        # 4. Generate final response using tool results
        # Replace placeholders in response template
        final_response = response_template
        for tool_name, result in tool_results.items():
            placeholder = f"{{{{tool_result}}}}"
            if placeholder in final_response:
                result_str = json.dumps(result.get("result", {}), indent=2)
                final_response = final_response.replace(placeholder, result_str, 1)
        
        # If no placeholders, append tool results
        if "{{tool_result}}" not in response_template and tool_results:
            result_summary = "\n\nTool Results:\n" + "\n".join([
                f"{name}: {json.dumps(r.get('result', {}), indent=2)}"
                for name, r in tool_results.items()
            ])
            final_response += result_summary
        
        # Create audit event
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            node_name="claims",
            event_type="tool_execution",
            details={
                "tools_called": [tc.tool_name for tc in new_tool_calls],
                "tools_count": len(new_tool_calls),
            },
        )
        
        audit_logger.log_event(
            actor="claims",
            action="execute_tools",
            resource="claims_tools",
            status="success",
            details={"tools": [tc.tool_name for tc in new_tool_calls]},
        )
        
        print(f"Claims Agent: Executed {len(new_tool_calls)} tool(s)")
        
        return {
            "messages": [AIMessage(content=final_response)],
            "tool_calls": new_tool_calls,
            "audit_trail": [audit_event],
            # "next_step": "__end__",
        }
    
    except Exception as e:
        print(f"Claims agent error: {e}")
        audit_logger.log_event(
            actor="claims",
            action="execute_tools",
            resource="claims_tools",
            status="error",
            details={"error": str(e)},
        )
        
        # Fallback response
        return {
            "messages": [AIMessage(content="I apologize, but I encountered an error processing your claim inquiry. Please try again or contact support.")],
            # "next_step": "__end__",
        }
