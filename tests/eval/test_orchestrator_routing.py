import json
from pathlib import Path
import pytest

from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

from langchain_core.messages import HumanMessage

from core.graph.engine import Engine
from core.graph.state_schema import AgentState

from agents.orchestrator import orchestrator_node
from agents.claims.agent import claims_node
from agents.billing.agent import billing_node
from agents.scheduling.agent import scheduling_node
from agents.backend.sentinel import sentinel_node


DATA_PATH = Path("tests/eval/data/orchestrator_eval.json")
DATA = json.loads(DATA_PATH.read_text())


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


@pytest.mark.parametrize("row", DATA)
def test_orchestrator_routing_accuracy(row):
    final_state = run_graph(row["input"])

    plan = final_state["plan"]
    assert plan is not None, "Execution plan was not created"

    predicted_intent = plan.intent
    predicted_agent = plan.steps[0].agent_id

    # ---- Hard deterministic assertions ----
    assert predicted_intent == row["expected_intent"]
    assert predicted_agent == row["expected_target_agent"]

    # ---- DeepEval semantic validation ----
    test_case = LLMTestCase(
        input=row["input"],
        actual_output=predicted_intent,
        expected_output=row["expected_intent"],
    )

    assert_test(
        test_case,
        [AnswerRelevancyMetric(threshold=0.75)]
    )
