from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    # Load .env if present
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()  # safe if file missing
except Exception:
    # dotenv is optional at runtime; continue without raising
    pass


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    return value if value is not None else default


@dataclass
class MerlinConfig:
    backend: str = "mock"  # mock | mujoco | xle (future)
    agent: str = "auto"  # auto | groq | claude | gemini | ollama
    log_level: str = "INFO"
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"


def load_config() -> MerlinConfig:
    return MerlinConfig(
        backend=get_env("MERLIN_BACKEND", "mock"),
        agent=get_env("MERLIN_AGENT", "auto"),
        log_level=get_env("MERLIN_LOG_LEVEL", "INFO"),
        anthropic_api_key=get_env("ANTHROPIC_API_KEY"),
        groq_api_key=get_env("GROQ_API_KEY"),
        google_api_key=get_env("GOOGLE_API_KEY"),
        ollama_base_url=get_env("OLLAMA_BASE_URL", "http://localhost:11434") or "http://localhost:11434",
    )


