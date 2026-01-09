"""
Sentinel Node: LLM-powered safety critic with veto power.
This agent has the authority to block execution if safety/compliance violations are detected.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage
from src.core.llm import get_llm
from src.core.graph.state_schema import AgentState, AuditEvent
from src.core.security.audit_logger import AuditLogger
# from core.llm import get_llm
# from core.graph.state_schema import AgentState, AuditEvent
# from core.security.audit_logger import AuditLogger

audit_logger = AuditLogger()


async def sentinel_node(state: AgentState) -> Dict[str, Any]:
    """
    Sentinel node: LLM-powered safety checks with veto power.
    
    Architectural rule: Sentinel has veto power - can block execution.
    
    Args:
        state: Current agent state
    
    Returns:
        State updates with veto decision
    """
    print("--- SENTINEL NODE ---")
    
    # Get context for safety analysis
    messages = state.get("messages", [])
    plan = state.get("plan")
    tool_calls = state.get("tool_calls", [])
    scratchpad = state.get("scratchpad", {})
    
    # Prepare context for LLM
    context_parts = []
    if plan:
        context_parts.append(f"Execution Plan: {plan.intent} with {len(plan.steps)} steps")
    if tool_calls:
        context_parts.append(f"Tool Calls: {[tc.tool_name for tc in tool_calls]}")
    if messages:
        last_msg = messages[-1]
        user_query = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        context_parts.append(f"User Query: {user_query}")
    
    context_str = "\n".join(context_parts)
    
    # LLM-powered safety analysis
    llm = get_llm("sentinel")  # Temperature 0.0 for deterministic safety checks
    
    system_prompt = """You are the Compliance Sentinel for XYZ Corp's Customer Call Center.
Your role is to ensure all operations comply with:
- HIPAA regulations (healthcare data privacy)
- Financial regulations (PCI-DSS for payments)
- Company policies (fraud prevention, data retention)
- Ethical guidelines (no discrimination, fair treatment)

Analyze the execution plan and tool calls for:
1. PII exposure risks
2. Unauthorized data access
3. Financial transaction anomalies
4. Policy violations
5. Security threats

Respond with JSON:
{{
    "safe": true|false,
    "confidence": 0.0-1.0,
    "violations": ["list of detected violations"],
    "reasoning": "Detailed explanation",
    "recommendation": "proceed|block|require_approval"
}}"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Analyze this execution context for safety/compliance:\n\n{context}\n\nShould execution proceed?"),
    ])
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        llm_response = await chain.ainvoke({"context": context_str})
        
        is_safe = llm_response.get("safe", True)
        confidence = float(llm_response.get("confidence", 1.0))
        violations = llm_response.get("violations", [])
        reasoning = llm_response.get("reasoning", "")
        recommendation = llm_response.get("recommendation", "proceed")
        
        # Determine veto decision
        veto_decision = None
        if recommendation == "block" or (not is_safe and confidence > 0.7):
            veto_decision = {
                "vetoed": True,
                "reason": reasoning,
                "violations": violations,
                "timestamp": datetime.utcnow().isoformat(),
            }
            print(f"⚠️ SENTINEL VETO: {reasoning}")
            audit_logger.log_event(
                actor="sentinel",
                action="veto_execution",
                resource="execution_plan",
                status="blocked",
                details={"violations": violations, "reasoning": reasoning},
            )
        else:
            print(f"✓ Sentinel: Safe to proceed (confidence: {confidence:.2f})")
            audit_logger.log_event(
                actor="sentinel",
                action="safety_check",
                resource="execution_plan",
                status="approved",
                details={"confidence": confidence},
            )
        
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            node_name="sentinel",
            event_type="safety_check",
            details={
                "safe": is_safe,
                "confidence": confidence,
                "violations": violations,
                "recommendation": recommendation,
            },
        )
        
        # If vetoed, add warning message
        messages_update = []
        if veto_decision:
            messages_update.append(AIMessage(
                content=f"I apologize, but I cannot proceed with this request due to compliance concerns: {reasoning}. Please contact a human representative for assistance."
            ))
        
        return {
            "sentinel_veto": veto_decision,
            "messages": messages_update,
            "audit_trail": [audit_event],
            "next_step": "__end__" if veto_decision else None,  # End if vetoed, continue otherwise
        }
    
    except Exception as e:
        print(f"Sentinel error: {e}")
        # Fail-safe: if sentinel fails, block execution (safe default)
        audit_logger.log_event(
            actor="sentinel",
            action="safety_check",
            resource="execution_plan",
            status="error",
            details={"error": str(e)},
        )
        
        return {
            "sentinel_veto": {
                "vetoed": True,
                "reason": f"Sentinel check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "next_step": "__end__",
        }
