# """
# Orchestrator Node: LLM-powered intent classification and planning.
# This is the entry point that analyzes user intent and creates an execution plan.
# """
# import json
# import uuid
# from datetime import datetime
# from typing import Dict, Any
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# from src.core.llm import get_llm
# from src.core.graph.state_schema import AgentState, ExecutionPlan, PlanStep, AuditEvent
# from src.core.security.audit_logger import AuditLogger
# # from core.llm import get_llm
# # from core.graph.state_schema import AgentState, ExecutionPlan, PlanStep, AuditEvent
# # from core.security.audit_logger import AuditLogger

# audit_logger = AuditLogger()


# async def orchestrator_node(state: AgentState) -> Dict[str, Any]:
#     """
#     Orchestrator node: LLM analyzes intent and creates execution plan.
    
#     Architectural rule: LLM generates structured plan, graph controls execution.
    
#     Args:
#         state: Current agent state
    
#     Returns:
#         State updates with plan and next_step
#     """
#     print("--- ORCHESTRATOR NODE ---")
    
#     # Get last user message
#     messages = state.get("messages", [])
#     if not messages:
#         return {"next_step": "__end__"}
    
#     last_message = messages[-1]
#     user_query = last_message.content if hasattr(last_message, "content") else str(last_message)
    
#     # LLM-powered intent classification and planning
#     llm = get_llm("orchestrator", provider="groq")

    
#     system_prompt = """You are the Orchestrator for XYZ Corp's Customer Call Center.

#             Your job is to:
#             1. Classify the user's intent (claims, billing, scheduling, or triage)
#                 a. Any query related to payments, invoices, balances, refunds, charges, or premiums MUST be classified as billing
#                 b. Any query related to claim status, claim denial, claim approval, claim documents, or appeals MUST be classified as claims
#                 c. Any query related to appointments, rescheduling, availability, or calendars MUST be classified as scheduling
#                 d. If the request does not clearly belong to one category, classify it as triage

#             2. Create a step-by-step execution plan that matches the classified intent

#             3. Determine which agent should handle the request
#             - If intent is "claims", target_agent MUST be "claims"
#             - If intent is "billing", target_agent MUST be "billing"
#             - If intent is "scheduling", target_agent MUST be "scheduling"
#             - If intent is "triage", choose the most appropriate agent or defer execution

#             IMPORTANT CONSTRAINTS:
#             - The value of "agent_id" in every plan step MUST match the selected target_agent
#             - Do NOT use claims-related actions or tools unless the intent is "claims"
#             - Do NOT route to the claims agent unless the intent is clearly claims-related
#             - The example below is illustrative only; adapt actions and tools based on intent

#             Respond with JSON in this exact format:
#             {{
#                 "intent": "claims|billing|scheduling|triage",
#                 "confidence": 0.0-1.0,
#                 "target_agent": "claims|billing|scheduling",
#                 "reasoning": "Brief explanation",
#                 "plan_steps": [
#                     {{
#                         "step_id": "step_1",
#                         "agent_id": "claims",
#                         "action": "lookup_claim_status",
#                         "reasoning": "Why this step",
#                         "required_tools": ["lookup_claim_status"]
#                     }}
#                 ]
#             }}
#             """


    
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         ("user", "User query: {query}\n\nAnalyze the intent and create an execution plan."),
#     ])
    
#     # Parse LLM output as JSON
#     parser = JsonOutputParser()
#     chain = prompt | llm | parser
    
#     try:
#         llm_response = await chain.ainvoke({"query": user_query})
        
#         # Validate and structure the response
#         intent = llm_response.get("intent", "triage")
#         confidence = float(llm_response.get("confidence", 0.5))
#         target_agent = llm_response.get("target_agent", intent)
#         reasoning = llm_response.get("reasoning", "LLM-generated plan")
#         plan_steps_data = llm_response.get("plan_steps", [])
        
#         # Create PlanStep objects
#         plan_steps = []
#         for step_data in plan_steps_data:
#             plan_steps.append(PlanStep(
#                 step_id=step_data.get("step_id", f"step_{len(plan_steps) + 1}"),
#                 agent_id=step_data.get("agent_id", target_agent),
#                 action=step_data.get("action", ""),
#                 reasoning=step_data.get("reasoning", ""),
#                 required_tools=step_data.get("required_tools", []),
#                 status="pending",
#             ))
        
#         # Create execution plan
#         execution_plan = ExecutionPlan(
#             intent=intent,
#             confidence=confidence,
#             steps=plan_steps,
#             created_at=datetime.utcnow().isoformat(),
#         )
        
#         # Determine next step
#         if target_agent in ["claims", "billing", "scheduling"]:
#             next_step = target_agent
#         else:
#             next_step = "__end__"
        
#         # Create audit event
#         audit_event = AuditEvent(
#             event_id=str(uuid.uuid4()),
#             timestamp=datetime.utcnow().isoformat(),
#             node_name="orchestrator",
#             event_type="plan_created",
#             details={
#                 "intent": intent,
#                 "confidence": confidence,
#                 "target_agent": target_agent,
#                 "plan_steps_count": len(plan_steps),
#             },
#         )
        
#         # Log audit event
#         audit_logger.log_event(
#             actor="orchestrator",
#             action="create_plan",
#             resource="execution_plan",
#             status="success",
#             details={"intent": intent, "target_agent": target_agent},
#         )
        
#         print(f"Orchestrator: Intent={intent}, Target={target_agent}, Confidence={confidence:.2f}")
        
#         return {
#             "plan": execution_plan,
#             "current_step": plan_steps[0].step_id if plan_steps else None,
#             "next_step": next_step,
#             "scratchpad": {
#                 **state.get("scratchpad", {}),
#                 "orchestrator_reasoning": reasoning,
#             },
#             "audit_trail": [audit_event],
#         }
    
#     except Exception as e:
#         print(f"Orchestrator error: {e}")
#         audit_logger.log_event(
#             actor="orchestrator",
#             action="create_plan",
#             resource="execution_plan",
#             status="error",
#             details={"error": str(e)},
#         )
        
#         # Fallback: simple keyword-based routing
#         user_lower = user_query.lower()
#         if "claim" in user_lower or "denied" in user_lower or "coverage" in user_lower:
#             return {"next_step": "claims"}
#         elif "bill" in user_lower or "invoice" in user_lower or "payment" in user_lower:
#             return {"next_step": "billing"}
#         elif "schedule" in user_lower or "appoint" in user_lower:
#             return {"next_step": "scheduling"}
        
#         return {"next_step": "__end__"}


"""
Orchestrator Node: LLM-powered intent classification and planning.
This is the entry point that analyzes user intent and creates an execution plan.
"""
import uuid
from datetime import datetime
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.core.llm import get_llm
from src.core.graph.state_schema import AgentState, ExecutionPlan, PlanStep, AuditEvent
from src.core.security.audit_logger import AuditLogger

audit_logger = AuditLogger()


async def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """
    Orchestrator node: LLM analyzes intent and creates execution plan.

    Architectural rule: LLM generates structured plan, graph controls execution.

    Args:
        state: Current agent state

    Returns:
        State updates with plan and next_step
    """
    print("--- ORCHESTRATOR NODE ---")

    # Get last user message
    messages = state.get("messages", [])
    if not messages:
        return {"next_step": "__end__"}

    last_message = messages[-1]
    user_query = last_message.content if hasattr(last_message, "content") else str(last_message)

    # LLM-powered intent classification and planning
    llm = get_llm("orchestrator", provider="groq")

    # Change 1: Harden system prompt (JSON-only output, no prose)
    # Curly braces escaped: {{ }} to avoid LangChain/Python formatting conflicts
    system_prompt = """You are the Orchestrator for XYZ Corp's Customer Call Center.

Your role is STRICTLY to classify intent and decide routing.
You do NOT explain reasoning.
You do NOT add commentary.
You do NOT include text outside JSON.

Classify intent as one of:
- claims
- billing
- scheduling
- triage

Return ONLY valid JSON.
NO markdown.
NO explanations.
NO extra text.

Required JSON schema:
{{
  "intent": "claims|billing|scheduling|triage",
  "confidence": 0.0,
  "target_agent": "claims|billing|scheduling|triage",
  "plan_steps": [
    {{
      "step_id": "step_1",
      "agent_id": "claims|billing|scheduling",
      "action": "string",
      "required_tools": []
    }}
  ]
}}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User query: {query}\n\nAnalyze the intent and create an execution plan."),
    ])

    # Parse LLM output as JSON
    parser = JsonOutputParser()
    chain = prompt | llm | parser

    try:
        llm_response = await chain.ainvoke({"query": user_query})

        # ✅ Change 3: Defensive parse guard (non-breaking)
        if not isinstance(llm_response, dict):
            raise ValueError("Orchestrator output is not valid JSON object")

        # Validate and structure the response
        intent = llm_response.get("intent", "triage")
        confidence = float(llm_response.get("confidence", 0.5))
        target_agent = llm_response.get("target_agent", intent)
        plan_steps_data = llm_response.get("plan_steps", [])

        # ✅ Change 2: Remove reasoning usage (safe)
        reasoning = "auto-generated routing decision"

        # Create PlanStep objects
        plan_steps = []
        for step_data in plan_steps_data:
            plan_steps.append(
                PlanStep(
                    step_id=step_data.get("step_id", f"step_{len(plan_steps) + 1}"),
                    agent_id=step_data.get("agent_id", target_agent),
                    action=step_data.get("action", ""),
                    reasoning="",  # ✅ intentionally blank (no LLM reasoning stored)
                    required_tools=step_data.get("required_tools", []),
                    status="pending",
                )
            )

        # Create execution plan
        execution_plan = ExecutionPlan(
            intent=intent,
            confidence=confidence,
            steps=plan_steps,
            created_at=datetime.utcnow().isoformat(),
        )

        # Determine next step (routing)
        if target_agent in ["claims", "billing", "scheduling"]:
            next_step = target_agent
        else:
            next_step = "__end__"

        # Create audit event
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            node_name="orchestrator",
            event_type="plan_created",
            details={
                "intent": intent,
                "confidence": confidence,
                "target_agent": target_agent,
                "plan_steps_count": len(plan_steps),
            },
        )

        # Log audit event
        audit_logger.log_event(
            actor="orchestrator",
            action="create_plan",
            resource="execution_plan",
            status="success",
            details={"intent": intent, "target_agent": target_agent},
        )

        print(f"Orchestrator: Intent={intent}, Target={target_agent}, Confidence={confidence:.2f}")

        # ✅ Change 4: stop storing LLM reasoning (static scratchpad)
        return {
            "plan": execution_plan,
            "current_step": plan_steps[0].step_id if plan_steps else None,
            "next_step": next_step,
            "scratchpad": {
                **state.get("scratchpad", {}),
                "orchestrator_reasoning": "intent classified and routed",
            },
            "audit_trail": [audit_event],
        }

    except Exception as e:
        print(f"Orchestrator error: {e}")
        audit_logger.log_event(
            actor="orchestrator",
            action="create_plan",
            resource="execution_plan",
            status="error",
            details={"error": str(e)},
        )

        # Fallback: simple keyword-based routing (unchanged)
        user_lower = user_query.lower()
        if "claim" in user_lower or "denied" in user_lower or "coverage" in user_lower:
            return {"next_step": "claims"}
        elif "bill" in user_lower or "invoice" in user_lower or "payment" in user_lower:
            return {"next_step": "billing"}
        elif "schedule" in user_lower or "appoint" in user_lower:
            return {"next_step": "scheduling"}

        return {"next_step": "__end__"}
