from __future__ import annotations

from typing import Any, Dict, List

import google.generativeai as genai

from .base_agent import BaseAgent


class GeminiAgent(BaseAgent):
    def __init__(self, model: str = "gemini-1.5-flash") -> None:
        super().__init__()
        self.model_name = model
        self.chat = None

    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        model = genai.GenerativeModel(self.model_name)
        self.chat = model.start_chat()
        response = self.chat.send_message(prompt)
        for _ in range(max_iterations - 1):
            if not hasattr(response, "parts") or not response.parts:
                break
            tool_called = False
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call:
                    tool_called = True
                    result = self.mcp_server.execute_tool(
                        part.function_call.name, dict(part.function_call.args)
                    )
                    response = self.chat.send_message(result)
            if not tool_called:
                break
        return getattr(response, "text", str(response))

    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        return []

    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        return []

    def _extract_text(self, response: Any) -> str:
        return ""


