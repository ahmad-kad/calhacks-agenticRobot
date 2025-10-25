from merlin.core.state_machine import StateMachine
from merlin.hardware.mock import MockController
from merlin.mcp.server import MCPServer


def test_navigation_tool_blocks_and_arrives():
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    result = mcp.execute_tool("navigate_to", {"x": 1.0, "y": 0.0})
    assert result["success"] is True
    assert isinstance(result.get("final_position"), list)


def test_grasp_and_release_tools():
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    r1 = mcp.execute_tool("grasp_object", {})
    assert r1["success"] is True
    r2 = mcp.execute_tool("release_object", {})
    assert r2["success"] is True


