#!/usr/bin/env python3
"""Teach Phase: Verify all 5 MCP tools work."""
from merlin.core.state_machine import StateMachine
from merlin.hardware.mock import MockController
from merlin.mcp.server import MCPServer

sm = StateMachine(MockController())
mcp = MCPServer(sm)

print("✓ Testing all 5 MCP tools")

# Test 1: Status
result = mcp.execute_tool("get_robot_status", {})
assert result["success"]
print(f"  ✓ get_robot_status: battery={result['status']['battery']:.1f}%")

# Test 2: Navigate
result = mcp.execute_tool("navigate_to", {"x": 1.0, "y": 0.0})
assert result["success"]
print(f"  ✓ navigate_to: arrived at {result['final_position']}")

# Test 3: Grasp
result = mcp.execute_tool("grasp_object", {})
assert result["success"]
print(f"  ✓ grasp_object: {result['gripper_state']}")

# Test 4: Detect (mock)
result = mcp.execute_tool("detect_objects", {"object_names": ["cube"]})
assert result["success"]
print(f"  ✓ detect_objects: found {result['count']} objects")

# Test 5: Release
result = mcp.execute_tool("release_object", {})
assert result["success"]
print(f"  ✓ release_object: {result['gripper_state']}")

print("✓ All 5 MCP tools work!")
