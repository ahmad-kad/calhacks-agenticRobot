from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    """Abstract agent interface for all LLM backends."""

    def __init__(self) -> None:
        self.mcp_server = None

    def set_mcp_server(self, mcp_server: Any) -> None:
        self.mcp_server = mcp_server

    @abstractmethod
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        pass

    @abstractmethod
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def _extract_text(self, response: Any) -> str:
        pass


