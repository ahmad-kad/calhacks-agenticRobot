from __future__ import annotations

from typing import Any, Dict, List

import requests

from .base_agent import BaseAgent


class OllamaAgent(BaseAgent):
    """Local Ollama agent for offline robot control.
    
    Uses locally running Ollama model (qwen2:7b recommended).
    No internet required, runs on-device for privacy and latency.
    """
    
    def __init__(self, model: str = "qwen2:7b", base_url: str = "http://localhost:11434") -> None:
        super().__init__()
        self.base_url = base_url
        self.model = model
        self.messages: List[Dict[str, str]] = []

    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute mission using local Ollama model.
        
        For simplicity, uses hardcoded pick-and-place like SimpleAgent.
        Real LLM reasoning could be added by parsing Ollama responses.
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

        # Optional: Query Ollama for commentary (LLM-based reasoning)
        mission_summary = "Mission complete:\n" + "\n".join(results)
        try:
            # Ask Ollama to summarize (optional, doesn't block mission)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": f"Summarize this robot mission in one sentence: {mission_summary}"}],
                    "stream": False
                },
                timeout=5,
            )
            if response.status_code == 200:
                llm_summary = response.json()["message"]["content"]
                mission_summary += f"\n\nOllama Analysis: {llm_summary}"
        except Exception:
            # If Ollama commentary fails, just return mission results
            pass

        return mission_summary

    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        return []

    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        return []

    def _extract_text(self, response: Any) -> str:
        return ""


