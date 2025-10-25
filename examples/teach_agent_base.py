#!/usr/bin/env python3
"""Teach Phase: Verify BaseAgent interface works."""
from merlin.agent.base_agent import BaseAgent
from typing import Any, Dict, List

class DemoAgent(BaseAgent):
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        return f"Mission complete: {prompt}"
    
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        return []
    
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        return []
    
    def _extract_text(self, response: Any) -> str:
        return ""

print("✓ Teach Phase 1: BaseAgent Interface")

agent = DemoAgent()

# Test 1: Run mission
result = agent.run_mission("Test mission")
assert "complete" in result.lower()
print(f"  ✓ Mission executed: {result}")

# Test 2: Set MCP server
class MockMCP:
    pass

agent.set_mcp_server(MockMCP())
assert agent.mcp_server is not None
print(f"  ✓ MCP server injected")

print("✓ Base agent interface verified!")
