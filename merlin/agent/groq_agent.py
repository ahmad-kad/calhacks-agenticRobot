from __future__ import annotations

import json
from typing import Any, Dict, List

from groq import Groq

from .base_agent import BaseAgent


class GroqAgent(BaseAgent):
    def __init__(self, model: str = "llama-3-70b-tool-use-preview") -> None:
        super().__init__()
        self.client = Groq()
        self.model = model
        self.messages: List[Dict[str, Any]] = []

    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        self.messages = [{"role": "user", "content": prompt}]
        for _ in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self._build_tool_defs(),
                max_tokens=512,
                temperature=0.7,
            )
            choice = response.choices[0]
            if choice.finish_reason == "stop":
                text = choice.message.content
                return text or "Mission complete"
            if choice.finish_reason in ("tool_calls", "tool_use"):
                tool_results: List[Dict[str, Any]] = []
                message = choice.message
                for tc in getattr(message, "tool_calls", []) or []:
                    args = json.loads(tc.function.arguments)
                    result = self.mcp_server.execute_tool(tc.function.name, args)
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})
                self.messages.append({"role": "assistant", "content": message.content})
                self.messages.append({"role": "user", "content": json.dumps(tool_results)})
        return "Max iterations reached"

    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        tools = self.mcp_server.get_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        return []

    def _extract_text(self, response: Any) -> str:
        return ""


