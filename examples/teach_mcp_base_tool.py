#!/usr/bin/env python3
"""Teach Phase: Verify MCPTool base class works."""
from merlin.mcp.tools.base import MCPTool
from typing import Any, Dict

class TestTool(MCPTool):
    @property
    def name(self) -> str:
        return "test_tool"
    
    @property
    def description(self) -> str:
        return "A test tool"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"success": True, "message": "Tool executed"}

print("✓ Teach Phase 1: MCPTool Base Class")

tool = TestTool()
assert tool.name == "test_tool"
print(f"  ✓ Tool name: {tool.name}")

result = tool.execute()
assert result["success"] == True
print(f"  ✓ Tool executed: {result['message']}")

print("✓ Base tool class verified!")
