from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .base_agent import BaseAgent


class SimpleAgent(BaseAgent):
    """Demo agent without LLM: hardcoded mission that uses real MCP tools.
    
    Useful for testing and demo without API keys.
    Executes a pick-and-place mission using MCP tools.
    """

    def __init__(self) -> None:
        super().__init__()

    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute a hardcoded mission using MCP tools.
        
        Mission: Get status → Navigate to [1.0, 0.0] → Detect objects → 
                 Grasp → Navigate to [2.0, 1.0] → Release → Report final status
        """
        if not self.mcp_server:
            return "Error: MCP server not set"

        results = []

        # Step 1: Get initial status
        res = self.mcp_server.execute_tool("get_robot_status", {})
        results.append(f"Initial status: battery={res['status']['battery']:.1f}%")

        # Step 2: Navigate to object
        res = self.mcp_server.execute_tool("navigate_to", {"x": 1.0, "y": 0.0})
        if res["success"]:
            results.append(f"Navigated to object at {res['final_position']}")
        else:
            results.append(f"Navigation failed: {res.get('error')}")
            return "\n".join(results)

        # Step 3: Detect objects
        res = self.mcp_server.execute_tool("detect_objects", {"object_names": ["cube", "block"]})
        if res["success"]:
            results.append(f"Detected {res['count']} objects")

        # Step 4: Grasp object
        res = self.mcp_server.execute_tool("grasp_object", {})
        if res["success"]:
            results.append(f"Grasped object: {res['gripper_state']}")

        # Step 5: Navigate to drop location
        res = self.mcp_server.execute_tool("navigate_to", {"x": 2.0, "y": 1.0})
        if res["success"]:
            results.append(f"Navigated to drop location at {res['final_position']}")

        # Step 6: Release object
        res = self.mcp_server.execute_tool("release_object", {})
        if res["success"]:
            results.append(f"Released object: {res['gripper_state']}")

        # Step 7: Final status
        res = self.mcp_server.execute_tool("get_robot_status", {})
        results.append(f"Final status: battery={res['status']['battery']:.1f}%, gripper={res['status']['gripper_open']}")

        return "Mission complete:\n" + "\n".join(results)

    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        return []

    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        return []

    def _extract_text(self, response: Any) -> str:
        return ""
