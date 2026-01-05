import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# Load .env into os.environ
load_dotenv()


def get_llm(
    provider="openai",
    model=None,
    temperature=0,
):
    if provider == "openai":
        # Optional safety check
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set")

        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            temperature=temperature,
            max_retries=2,
        )

    elif provider == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY not set")

        return ChatGroq(
            model=model or "llama-3.1-8b-instant",
            temperature=temperature,
            max_retries=2,
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")
