import json
import pytest
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ExactMatchMetric
from typing import List

# Import your orchestrator node
from src.agents.orchestrator import orchestrator_node


# ---------- Helper: Load Golden Dataset ----------

def load_golden_dataset(path: str) -> List[LLMTestCase]:
    with open(path, "r") as f:
        data = json.load(f)

    test_cases = []
    for row in data:
        test_cases.append(
            LLMTestCase(
                input=row["input"],
                expected_output=row["expected"],
                context=[row.get("category", "uncategorized")],
                name=row.get("id"),
            )
        )
    return test_cases


# ---------- Helper: Run Orchestrator ----------

async def run_orchestrator(query: str) -> str:
    """
    Executes orchestrator and returns JSON string
    compatible with DeepEval expectations.
    """
    state = {
        "messages": [{"role": "user", "content": query}]
    }

    result = await orchestrator_node(state)

    # Normalize output for evaluation
    output = {
        "intent": result["plan"].intent,
        "target_agent": result["next_step"],
    }

    return json.dumps(output)


# ---------- Metrics ----------

intent_match = ExactMatchMetric(
    threshold=1.0,
    verbose_mode=True,
)

target_agent_match = ExactMatchMetric(
    threshold=1.0
)


# ---------- Pytest Entry ----------

@pytest.mark.asyncio
async def test_orchestrator_routing():
    test_cases = load_golden_dataset(
        r"C:\Users\AI_ML PC_4\Desktop\Working_new\classroom-customer-service-agentic-langgraph-phase-2\tests\eval\data\golden_orchestrator_dataset.json"
    )

    await evaluate(
        test_cases=test_cases,
        model=run_orchestrator,
        metrics=[
            intent_match,
            target_agent_match,
        ],
    )
