from __future__ import annotations

from typing import Any, Dict, List

from merlin.core.state_machine import StateMachine
from merlin.mcp.tools.base import MCPTool
from merlin.mcp.tools.action import (
    ToolGetRobotStatus,
    ToolNavigateTo,
    ToolGrasp,
    ToolRelease,
)
from merlin.mcp.tools.perception import ToolDetectObjects


class MCPServer:
    def __init__(self, state_machine: StateMachine, vision_pipeline: Any | None = None):
        self.state_machine = state_machine
        self.vision_pipeline = vision_pipeline
        self.tools: Dict[str, MCPTool] = {
            "get_robot_status": ToolGetRobotStatus(state_machine),
            "navigate_to": ToolNavigateTo(state_machine),
            "detect_objects": ToolDetectObjects(state_machine, vision_pipeline),
            "grasp_object": ToolGrasp(state_machine),
            "release_object": ToolRelease(state_machine),
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools.values()
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        tool = self.tools[tool_name]
        return tool.execute(**tool_input)

    def add_tool(self, tool: MCPTool) -> None:
        self.tools[tool.name] = tool


