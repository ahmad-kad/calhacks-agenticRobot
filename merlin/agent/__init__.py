from __future__ import annotations

import os
from typing import Literal

from .base_agent import BaseAgent


def _has(key: str) -> bool:
    v = os.getenv(key)
    return bool(v and v.strip())


def create_agent(backend: Literal["claude", "groq", "gemini", "ollama", "simple", "figma", "letta", "reva", "auto"] = "auto") -> BaseAgent:
    if backend == "claude":
        from .claude_agent import ClaudeAgent

        return ClaudeAgent()
    elif backend == "groq":
        from .groq_agent import GroqAgent

        return GroqAgent()
    elif backend == "gemini":
        from .gemini_agent import GeminiAgent

        return GeminiAgent()
    elif backend == "ollama":
        from .ollama_agent import OllamaAgent

        return OllamaAgent()
    elif backend == "simple":
        from .simple_agent import SimpleAgent

        return SimpleAgent()
    elif backend == "figma":
        from .figma_agent import FigmaAgent

        return FigmaAgent()
    elif backend == "letta":
        from .letta_agent import LettaAgent

        return LettaAgent()
    elif backend == "reva":
        from .reva_agent import RevaAgent

        return RevaAgent()
    elif backend == "auto":
        # Prefer online backends if API keys are present; fallback to Ollama, then SimpleAgent
        order = []
        if _has("GROQ_API_KEY"):
            order.append("groq")
        if _has("ANTHROPIC_API_KEY"):
            order.append("claude")
        if _has("GOOGLE_API_KEY"):
            order.append("gemini")
        if _has("FIGMA_API_KEY"):
            order.append("figma")
        if _has("LETTA_API_KEY"):
            order.append("letta")
        if _has("REVA_API_KEY"):
            order.append("reva")
        order.append("ollama")
        order.append("simple")  # Fallback: always works

        for b in order:
            try:
                return create_agent(b)  # type: ignore[arg-type]
            except Exception:
                continue
        # Last resort: SimpleAgent (always works)
        from .simple_agent import SimpleAgent

        return SimpleAgent()
    else:
        raise ValueError(f"Unknown agent backend: {backend}")


__all__ = ["BaseAgent", "create_agent"]


