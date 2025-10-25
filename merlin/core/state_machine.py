from __future__ import annotations

import math
import time
from typing import Dict, Optional

from .types import RobotStatus, RobotState
from .controller import RobotController


class StateMachine:
    """Core autonomous state machine running at ~60 Hz when polled."""

    def __init__(self, controller: RobotController) -> None:
        self.controller = controller
        self.state: RobotState = RobotState.IDLE
        self.current_goal: Optional[Dict] = None
        self.state_entry_time: float = time.time()

        # Config
        self.arrival_threshold = 0.5  # meters (loosened from 0.2)
        self.manipulation_time = 2.0  # seconds
        self.sensing_time = 1.0  # seconds
        self.state_timeout = 60.0  # seconds

    def _enter_state(self, state: RobotState, goal: Optional[Dict]) -> None:
        self.state = state
        self.current_goal = goal
        self.state_entry_time = time.time()

    def set_goal(self, state: str, goal: Dict) -> bool:
        try:
            state_enum = RobotState(state)
        except ValueError:
            return False
        self._enter_state(state_enum, goal)
        return True

    def update(self, delta_t: float = 0.016) -> RobotStatus:
        # Timeout guard
        if time.time() - self.state_entry_time > self.state_timeout:
            self._enter_state(RobotState.IDLE, None)

        if self.state == RobotState.NAVIGATING:
            self._navigate_update()
        elif self.state == RobotState.MANIPULATING:
            self._manipulate_update()
        elif self.state == RobotState.SENSING:
            self._sense_update()

        self.controller.update(delta_t)
        
        # Sync state with controller
        self.controller.state = self.state.value
        
        return self.controller.get_status()

    # State-specific updates
    def _navigate_update(self) -> None:
        assert self.current_goal is not None
        target = self.current_goal.get("target_position", [0.0, 0.0])
        current = self.controller.get_status().position

        dx = target[0] - current[0]
        dy = target[1] - current[1]
        dist = math.hypot(dx, dy)
        if dist < self.arrival_threshold:
            self.controller.set_velocity(0.0, 0.0)
            self._enter_state(RobotState.IDLE, None)
            return

        # Proportional control
        target_heading = math.degrees(math.atan2(dy, dx))
        heading = self.controller.get_status().heading
        heading_error = (target_heading - heading + 540.0) % 360.0 - 180.0

        vel = min(1.0, dist * 5.0)  # Aggressive acceleration towards target
        omega = 0.1 * math.radians(heading_error)
        self.controller.set_velocity(vel, omega)

    def _manipulate_update(self) -> None:
        assert self.current_goal is not None
        task = self.current_goal.get("task")
        if task == "grasp":
            self.controller.set_gripper(False)
        elif task == "release":
            self.controller.set_gripper(True)

        if time.time() - self.state_entry_time > self.manipulation_time:
            self._enter_state(RobotState.IDLE, None)

    def _sense_update(self) -> None:
        # Placeholder: sensing completes after fixed time
        if time.time() - self.state_entry_time > self.sensing_time:
            self._enter_state(RobotState.IDLE, None)


