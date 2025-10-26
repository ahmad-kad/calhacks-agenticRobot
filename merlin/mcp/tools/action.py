from __future__ import annotations

import math
import time
from typing import Any, Dict, List

from merlin.core.state_machine import StateMachine
from merlin.core.types import RobotStatus
from .base import MCPTool


class ToolGetRobotStatus(MCPTool):
    def __init__(self, sm: StateMachine):
        self.state_machine = sm

    @property
    def name(self) -> str:
        return "get_robot_status"

    @property
    def description(self) -> str:
        return "Get current position, battery, state, and detected objects"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> Dict[str, Any]:
        status = self.state_machine.controller.get_status()
        return {
            "success": True,
            "status": {
                "state": status.state,
                "position": status.position,
                "heading": status.heading,
                "battery": status.battery,
                "gripper_open": status.gripper_open,
                "detected_objects": status.detected_objects,
            },
        }


class ToolNavigateTo(MCPTool):
    NAVIGATION_TIMEOUT = 60.0  # Increased from 30.0 to 60.0 seconds

    def __init__(self, sm: StateMachine):
        self.state_machine = sm

    @property
    def name(self) -> str:
        return "navigate_to"

    @property
    def description(self) -> str:
        return "Drive to [x, y] coordinates. Blocks until arrival or timeout."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
            },
            "required": ["x", "y"],
        }

    def execute(self, x: float, y: float, **kwargs) -> Dict[str, Any]:
        target = [float(x), float(y)]
        
        # Reset battery at start of new navigation command
        # This simulates a fresh battery for each new mission prompt
        if self.state_machine.state.value == "IDLE":
            self.state_machine.controller.battery = 95.0
        
        if not self.state_machine.set_goal("NAVIGATING", {"target_position": target}):
            return {"success": False, "error": "Failed to set goal"}

        start = time.time()
        while time.time() - start < self.NAVIGATION_TIMEOUT:
            status = self.state_machine.update()
            dist = math.hypot(status.position[0] - x, status.position[1] - y)
            # Use state machine's arrival threshold instead of hardcoded value
            if status.state == "IDLE" and dist < self.state_machine.arrival_threshold:
                return {"success": True, "final_position": status.position}
            time.sleep(0.016)
        return {"success": False, "error": "Navigation timeout"}


class ToolGrasp(MCPTool):
    MANIPULATION_TIMEOUT = 3.0

    def __init__(self, sm: StateMachine):
        self.state_machine = sm

    @property
    def name(self) -> str:
        return "grasp_object"

    @property
    def description(self) -> str:
        return "Close gripper to grasp object"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> Dict[str, Any]:
        if not self.state_machine.set_goal("MANIPULATING", {"task": "grasp"}):
            return {"success": False, "error": "Failed to set grasp goal"}
        start = time.time()
        while time.time() - start < self.MANIPULATION_TIMEOUT:
            status = self.state_machine.update()
            if status.state == "IDLE":
                return {"success": True, "gripper_state": "closed"}
            time.sleep(0.016)
        return {"success": False, "error": "Grasp timeout"}


class ToolRelease(MCPTool):
    MANIPULATION_TIMEOUT = 3.0

    def __init__(self, sm: StateMachine):
        self.state_machine = sm

    @property
    def name(self) -> str:
        return "release_object"

    @property
    def description(self) -> str:
        return "Open gripper to release object"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> Dict[str, Any]:
        if not self.state_machine.set_goal("MANIPULATING", {"task": "release"}):
            return {"success": False, "error": "Failed to set release goal"}
        start = time.time()
        while time.time() - start < self.MANIPULATION_TIMEOUT:
            status = self.state_machine.update()
            if status.state == "IDLE":
                return {"success": True, "gripper_state": "open"}
            time.sleep(0.016)
        return {"success": False, "error": "Release timeout"}


