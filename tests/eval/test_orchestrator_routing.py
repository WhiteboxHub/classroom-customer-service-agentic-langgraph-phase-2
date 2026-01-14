import json
from pathlib import Path
import pytest

from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval

from langchain_core.messages import HumanMessage

from core.graph.engine import Engine
from core.graph.state_schema import AgentState

from agents.orchestrator import orchestrator_node
from agents.claims.agent import claims_node
from agents.billing.agent import billing_node
from agents.scheduling.agent import scheduling_node
from agents.backend.sentinel import sentinel_node


# -----------------------------
# Load evaluation dataset
# -----------------------------
DATA_PATH = Path("tests/eval/data/orchestrator_eval.json")
DATA = json.loads(DATA_PATH.read_text())


# -----------------------------
# Graph runner
# -----------------------------
def run_graph(user_input: str):
    engine = Engine()
    engine.build_complete_graph(
        orchestrator_node,
        claims_node,
        billing_node,
        scheduling_node,
        sentinel_node,
    )
    graph = engine.compile()

    state: AgentState = {
        "messages": [HumanMessage(content=user_input)],
        "plan": None,
        "current_step": None,
        "next_step": None,
        "scratchpad": {},
        "user_info": {},
        "tool_calls": [],
        "approval_requests": [],
        "audit_trail": [],
        "sentinel_veto": None,
        "execution_metadata": {},
    }

    return graph.invoke(state)


# -----------------------------
# DeepEval: Routing quality
# -----------------------------
routing_quality_metric = GEval(
    name="Orchestrator Routing Quality",
    criteria="""
    Evaluate whether the orchestrator selected the correct intent
    and target agent based on the user's input.

    The routing should be:
    - Correct
    - Unambiguous
    - Aligned with the user's request
    """,
    evaluation_steps=[
        "Analyze the user input",
        "Review the predicted intent",
        "Review the selected agent",
        "Determine whether routing is correct"
    ],
    threshold=0.8
)


# -----------------------------
# Tests
# -----------------------------
@pytest.mark.parametrize("row", DATA)
def test_orchestrator_routing(row):
    final_state = run_graph(row["input"])

    # ---- Plan existence ----
    plan = final_state["plan"]
    assert plan is not None, "Execution plan was not created"

    predicted_intent = plan.intent
    predicted_agent = plan.steps[0].agent_id

    # ---- Hard deterministic assertions (PRIMARY) ----
    assert predicted_intent == row["expected_intent"]
    assert predicted_agent == row["expected_target_agent"]

    # ---- Safety assertion ----
    assert final_state["sentinel_veto"] == row["safety_expected"]

    # ---- DeepEval semantic validation (SECONDARY) ----
    test_case = LLMTestCase(
        input=row["input"],
        actual_output={
            "intent": predicted_intent,
            "agent": predicted_agent,
        },
        expected_output={
            "intent": row["expected_intent"],
            "agent": row["expected_target_agent"],
        },
    )

    assert_test(test_case, [routing_quality_metric])
