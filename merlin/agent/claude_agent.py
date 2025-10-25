from __future__ import annotations

from typing import Any, Dict, List

from anthropic import Anthropic

from .base_agent import BaseAgent


class ClaudeAgent(BaseAgent):
    def __init__(self, model: str = "claude-3-5-sonnet-20241022") -> None:
        super().__init__()
        self.client = Anthropic()
        self.model = model
        self.messages: List[Dict[str, str]] = []

    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        self.messages = [{"role": "user", "content": prompt}]
        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=self._system_prompt(),
                tools=self._build_tool_defs(),
                messages=self.messages,
            )
            if response.stop_reason == "end_turn":
                return self._extract_text(response.content)
            if response.stop_reason == "tool_use":
                tool_results = self._execute_tool_calls(response.content)
                self.messages.append({"role": "assistant", "content": response.content})
                self.messages.append({"role": "user", "content": tool_results})
        return "Max iterations reached"

    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        tools = self.mcp_server.get_tools()
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in tools
        ]

    def _extract_tool_calls(self, content: Any) -> List[Dict[str, Any]]:
        calls: List[Dict[str, Any]] = []
        for block in content:
            if getattr(block, "type", None) == "tool_use":
                calls.append({"name": block.name, "input": block.input, "id": block.id})
        return calls

    def _execute_tool_calls(self, content: Any) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for block in content:
            if getattr(block, "type", None) == "tool_use":
                result = self.mcp_server.execute_tool(block.name, dict(block.input))
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        return results

    def _extract_text(self, content: Any) -> str:
        for block in content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def _system_prompt(self) -> str:
        return (
            "You are Merlin, an autonomous robot agent. Use tools to complete missions."
        )


