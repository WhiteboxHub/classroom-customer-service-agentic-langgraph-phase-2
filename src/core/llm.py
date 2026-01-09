
"""
LLM initialization and configuration.
Centralized LLM access following the architectural rule:
LLMs are "brains" (planning, reasoning, evaluation).
"""

import os
from typing import Optional
from dotenv import load_dotenv

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

load_dotenv()

# =====================
# Provider configuration
# =====================

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | groq

# OpenAI defaults
OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

# Groq defaults
GROQ_DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

DEFAULT_TEMPERATURE = 0.2

# =====================
# Agent-specific temperatures
# =====================

AGENT_TEMPERATURES = {
    "orchestrator": 0.1,
    "claims": 0.2,
    "billing": 0.1,
    "scheduling": 0.3,
    "sentinel": 0.0,  # Deterministic safety checks
}


# =====================
# Factory
# =====================

def get_llm(
    agent_name: Optional[str] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
) -> BaseChatModel:
    """
    Get an LLM instance configured for a specific agent and provider.

    Args:
        agent_name: Name of the agent (used to lookup temperature)
        temperature: Override temperature (if None, uses agent-specific default)
        provider: Override provider ("openai" or "groq")

    Returns:
        Configured Chat model instance
    """

    provider = provider or DEFAULT_PROVIDER

    # Determine temperature
    if temperature is None:
        temp = AGENT_TEMPERATURES.get(agent_name, DEFAULT_TEMPERATURE)
    else:
        temp = temperature

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return ChatOpenAI(
            model=OPENAI_DEFAULT_MODEL,
            temperature=temp,
            api_key=api_key,
        )

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

        return ChatGroq(
            model=GROQ_DEFAULT_MODEL,
            temperature=temp,
            api_key=api_key,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
