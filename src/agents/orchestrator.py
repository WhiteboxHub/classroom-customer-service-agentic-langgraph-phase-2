"""
Orchestrator Node: LLM-powered intent classification and planning.
This is the entry point that analyzes user intent and creates an execution plan.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
# from src.core.llm import get_llm
# from src.core.graph.state_schema import AgentState, ExecutionPlan, PlanStep, AuditEvent
# from src.core.security.audit_logger import AuditLogger
from core.llm import get_llm
from core.graph.state_schema import AgentState, ExecutionPlan, PlanStep, AuditEvent
from core.security.audit_logger import AuditLogger
from transformers import pipeline
# from prompts import ORCHESTRATION_PROMPT

audit_logger = AuditLogger()

from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)

print("Loading BERT intent classifier...")

# orchestrator.py → agents → src → project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = PROJECT_ROOT / "intend_classifier" / "distilbert-intent"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

intent_classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    device=-1
)

print("BERT intent classifier loaded")


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

        # --- BERT Intent Classification ---
    bert_result = intent_classifier(user_query)[0]

    detected_intent = bert_result["label"].lower()
    intent_confidence = float(bert_result["score"])

    # Safety guard
    if detected_intent not in ["claims", "billing", "scheduling", "triage"]:
        detected_intent = "triage"

    
    # LLM-powered intent classification and planning
    llm = get_llm("orchestrator", provider="groq")

    
    system_prompt =  """
    You are the Orchestrator for Kaiser Permanente Corp's Customer Call Center.

    IMPORTANT:
    - User intent has ALREADY been classified by a BERT-based model.
    - You MUST NOT reclassify or infer intent.
    - Your role is to validate, plan, and route execution ONLY.

    You will be provided with:
    - user_query
    - detected_intent: one of ["claims", "billing", "scheduling", "triage"]
    - intent_confidence: float between 0.0 and 1.0

    Your responsibilities are:

    1. Validate the detected intent
    - If intent_confidence < 0.65, treat the request as "triage"
    - If the detected intent clearly contradicts the user_query, downgrade to "triage"
    - Do NOT change a high-confidence intent unless there is a clear mismatch

    2. Create a step-by-step execution plan based on the FINAL intent

    3. Select the appropriate target agent
    - intent == "claims" → target_agent MUST be "claims"
    - intent == "billing" → target_agent MUST be "billing"
    - intent == "scheduling" → target_agent MUST be "scheduling"
    - intent == "triage" → choose the safest agent or defer execution

    STRICT CONSTRAINTS:
    - agent_id in EVERY plan step MUST match target_agent
    - Do NOT include cross-domain actions or tools
    - Do NOT simulate intent classification

    Respond ONLY with valid JSON in this exact format:

    {
        "intent": "claims|billing|scheduling|triage",
        "confidence": 0.0-1.0,
        "target_agent": "claims|billing|scheduling",
        "reasoning": "Short justification based on detected intent and confidence",
        "plan_steps": [
            {
                "step_id": "step_1",
                "agent_id": "billing",
                "action": "specific_action_name",
                "reasoning": "Why this step is needed",
                "required_tools": ["tool_name_if_any"]
            }
        ]
    }
    """


    
    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", system_prompt),
    #     ("user", "User query: {query}\n\nAnalyze the intent and create an execution plan."),
    # ])
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        (
            "user",
            "User query: {query}\n"
            "Detected intent: {intent}\n"
            "Intent confidence: {confidence}\n\n"
            "Create an execution plan."
        ),
    ])
    
    # Parse LLM output as JSON
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        # llm_response = await chain.ainvoke({"query": user_query})
        llm_response = await chain.ainvoke({
            "query": user_query,
            "intent": detected_intent,
            "confidence": intent_confidence,
        })
                
        # Validate and structure the response
        intent = llm_response.get("intent", "triage")
        confidence = float(llm_response.get("confidence", 0.5))
        target_agent = llm_response.get("target_agent", intent)
        reasoning = llm_response.get("reasoning", "LLM-generated plan")
        plan_steps_data = llm_response.get("plan_steps", [])
        
        # Create PlanStep objects
        plan_steps = []
        for step_data in plan_steps_data:
            plan_steps.append(PlanStep(
                step_id=step_data.get("step_id", f"step_{len(plan_steps) + 1}"),
                agent_id=step_data.get("agent_id", target_agent),
                action=step_data.get("action", ""),
                reasoning=step_data.get("reasoning", ""),
                required_tools=step_data.get("required_tools", []),
                status="pending",
            ))
        
        # Create execution plan
        execution_plan = ExecutionPlan(
            intent=intent,
            confidence=confidence,
            steps=plan_steps,
            created_at=datetime.utcnow().isoformat(),
        )
        
        # Determine next step
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
        
        return {
            "plan": execution_plan,
            "current_step": plan_steps[0].step_id if plan_steps else None,
            "next_step": next_step,
            "scratchpad": {
                **state.get("scratchpad", {}),
                "orchestrator_reasoning": reasoning,
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
        
        # Fallback: simple keyword-based routing
        user_lower = user_query.lower()
        if "claim" in user_lower or "denied" in user_lower or "coverage" in user_lower:
            return {"next_step": "claims"}
        elif "bill" in user_lower or "invoice" in user_lower or "payment" in user_lower:
            return {"next_step": "billing"}
        elif "schedule" in user_lower or "appoint" in user_lower:
            return {"next_step": "scheduling"}
        
        return {"next_step": "__end__"}
