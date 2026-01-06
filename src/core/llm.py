"""
LLM initialization and configuration.
Centralized LLM access following the architectural rule: LLMs are "brains" (planning, reasoning, evaluation).
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

load_dotenv()

# Default model configuration
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
DEFAULT_TEMPERATURE = 0.2

# Agent-specific temperatures from config
AGENT_TEMPERATURES = {
    "orchestrator": 0.1,
    "claims": 0.2,
    "billing": 0.1,
    "scheduling": 0.3,
    "sentinel": 0.0,  # Deterministic safety checks
}


def get_llm(agent_name: Optional[str] = None, temperature: Optional[float] = None) -> BaseChatModel:
    """
    Get an LLM instance configured for a specific agent.
    
    Args:
        agent_name: Name of the agent (used to lookup temperature from config)
        temperature: Override temperature (if None, uses agent-specific default)
    
    Returns:
        Configured ChatOpenAI instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Determine temperature
    if temperature is None:
        if agent_name and agent_name in AGENT_TEMPERATURES:
            temp = AGENT_TEMPERATURES[agent_name]
        else:
            temp = DEFAULT_TEMPERATURE
    else:
        temp = temperature
    
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        temperature=temp,
        api_key=api_key,
    )

