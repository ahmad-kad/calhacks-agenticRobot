from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple, Optional

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
        
        # Available objects in the environment
        self.available_objects = {
            'red': {'name': 'red_cube', 'position': [1.5, 0.5], 'color': 'red'},
            'green': {'name': 'green_sphere', 'position': [2.0, 1.0], 'color': 'green'},
            'blue': {'name': 'blue_block', 'position': [1.2, -0.3], 'color': 'blue'},
            'cube': {'name': 'red_cube', 'position': [1.5, 0.5], 'color': 'red'},
            'sphere': {'name': 'green_sphere', 'position': [2.0, 1.0], 'color': 'green'},
            'block': {'name': 'blue_block', 'position': [1.2, -0.3], 'color': 'blue'}
        }

    def randomize_scene(self) -> None:
        """Randomize object positions for variety in each mission."""
        import random
        
        # Randomize positions within 0-5 range for x,y,z coordinates
        positions = [
            [random.uniform(0.5, 4.5), random.uniform(0.5, 4.5), random.uniform(0.1, 1.5)],  # red_cube
            [random.uniform(0.5, 4.5), random.uniform(0.5, 4.5), random.uniform(0.1, 1.5)],  # green_sphere  
            [random.uniform(0.5, 4.5), random.uniform(0.5, 4.5), random.uniform(0.1, 1.5)]   # blue_block
        ]
        
        # Update object positions
        self.available_objects['red']['position'] = positions[0]
        self.available_objects['green']['position'] = positions[1]
        self.available_objects['blue']['position'] = positions[2]
        
        # Also update the name-based entries
        self.available_objects['cube']['position'] = positions[0]
        self.available_objects['sphere']['position'] = positions[1]
        self.available_objects['block']['position'] = positions[2]
        
        print(f"🎲 Scene randomized:")
        print(f"   • Red cube: {positions[0]}")
        print(f"   • Green sphere: {positions[1]}")
        print(f"   • Blue block: {positions[2]}")
    
    def get_random_robot_position(self) -> List[float]:
        """Get a random robot position that doesn't overlap with objects."""
        import random
        
        max_attempts = 50
        min_distance = 0.8  # Minimum distance from objects
        
        for attempt in range(max_attempts):
            # Generate random position in scene bounds
            robot_pos = [
                random.uniform(0.5, 4.5),
                random.uniform(0.5, 4.5)
            ]
            
            # Check distance from all objects
            too_close = False
            for obj_key, obj_info in self.available_objects.items():
                if obj_key in ['red', 'green', 'blue']:
                    obj_pos = obj_info['position'][:2]  # Only check x,y
                    distance = ((robot_pos[0] - obj_pos[0])**2 + (robot_pos[1] - obj_pos[1])**2)**0.5
                    if distance < min_distance:
                        too_close = True
                        break
            
            if not too_close:
                return robot_pos
        
        # Fallback position if no good position found
        return [0.5, 0.5]

    def parse_mission_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parse natural language prompt and return structured JSON command for FSM.
        
        Args:
            prompt: Natural language mission prompt (e.g., "pick up green object and put it at 2,2")
            
        Returns:
            Dictionary with structured command for FSM execution
        """
        prompt_lower = prompt.lower()
        
        # First, try to use Ollama for intelligent parsing
        try:
            llm_result = self._parse_with_llm(prompt)
            if llm_result:
                return llm_result
        except Exception as e:
            print(f"LLM parsing failed: {e}, falling back to regex")
        
        # Fallback to regex parsing
        object_name, coordinates = self._parse_with_regex(prompt_lower)
        return self._create_fsm_command(object_name, coordinates)
    
    def _parse_with_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Use Ollama to parse the mission prompt intelligently and return FSM command."""
        try:
            system_prompt = """You are a robot mission parser. Convert natural language prompts into structured JSON commands for a robot FSM.

Available objects:
- red cube at [1.5, 0.5]
- green sphere at [2.0, 1.0] 
- blue block at [1.2, -0.3]

Respond with JSON only in this format:
{
  "mission_type": "pick_and_place",
  "target_object": {
    "name": "object_name",
    "position": [x, y],
    "color": "color"
  },
  "destination": {
    "position": [x, y]
  },
  "phases": [
    {"name": "scan", "duration": 1},
    {"name": "navigate_to_object", "duration": 2},
    {"name": "approach", "duration": 1},
    {"name": "grasp", "duration": 1},
    {"name": "navigate_to_destination", "duration": 2},
    {"name": "place", "duration": 1},
    {"name": "complete", "duration": 1}
  ]
}

Examples:
- "pick up green object and put it at 2,2" -> {"mission_type": "pick_and_place", "target_object": {"name": "green_sphere", "position": [2.0, 1.0], "color": "green"}, "destination": {"position": [2.0, 2.0]}, "phases": [...]}
- "move blue to 1,1" -> {"mission_type": "pick_and_place", "target_object": {"name": "blue_block", "position": [1.2, -0.3], "color": "blue"}, "destination": {"position": [1.0, 1.0]}, "phases": [...]}"""

            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                },
                timeout=10,
            )
            
            if response.status_code == 200:
                content = response.json()["message"]["content"]
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
        except Exception as e:
            print(f"LLM parsing error: {e}")
        
        return None
    
    def _parse_with_regex(self, prompt: str) -> Tuple[Optional[str], Optional[List[float]]]:
        """Fallback regex parsing for mission prompt."""
        # Extract coordinates
        coord_patterns = [
            r'at\s+(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)',  # "at 0,0"
            r'to\s+(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)',  # "to 0,0"
            r'location\s+(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)',  # "location 0,0"
            r'coordinates?\s+(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)',  # "coords 0,0"
            r'\(\s*(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)\s*\)',  # "(0,0)"
        ]
        
        coordinates = None
        for pattern in coord_patterns:
            match = re.search(pattern, prompt)
            if match:
                try:
                    coordinates = [float(match.group(1)), float(match.group(2))]
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract object type
        object_name = None
        for obj_key, obj_info in self.available_objects.items():
            if obj_key in prompt:
                object_name = obj_info['name']
                break
        
        return (object_name, coordinates)
    
    def _create_fsm_command(self, object_name: Optional[str], coordinates: Optional[List[float]]) -> Dict[str, Any]:
        """Create a structured FSM command from parsed object and coordinates."""
        # Default values
        if not object_name:
            object_name = "red_cube"
        if not coordinates:
            coordinates = [0.0, 0.0]
        
        # Normalize object name (handle spaces vs underscores)
        normalized_name = object_name.replace(' ', '_')
        
        # Get object info - try both normalized name and first part
        object_info = None
        for key, info in self.available_objects.items():
            if info['name'] == normalized_name or key in normalized_name.lower():
                object_info = info
                break
        
        # Fallback to default if not found
        if not object_info:
            object_info = {
                'name': normalized_name,
                'position': [1.5, 0.5],
                'color': 'red'
            }
        
        return {
            "mission_type": "pick_and_place",
            "target_object": {
                "name": object_info['name'],
                "position": object_info['position'],
                "color": object_info['color']
            },
            "destination": {
                "position": coordinates
            },
            "phases": [
                {"name": "scan", "duration": 1},
                {"name": "navigate_to_object", "duration": 2},
                {"name": "approach", "duration": 1},
                {"name": "grasp", "duration": 1},
                {"name": "navigate_to_destination", "duration": 2},
                {"name": "place", "duration": 1},
                {"name": "complete", "duration": 1}
            ]
        }

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


