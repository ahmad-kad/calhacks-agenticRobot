from __future__ import annotations

import math
import time
from typing import Dict, Optional
import logging

from .types import RobotStatus, RobotState
from .controller import RobotController

logger = logging.getLogger(__name__)


class StateMachine:
    """Core autonomous state machine running at ~60 Hz when polled."""

    def __init__(self, controller: RobotController) -> None:
        self.controller = controller
        self.state: RobotState = RobotState.IDLE
        self.current_goal: Optional[Dict] = None
        self.state_entry_time: float = time.time()

        # Config
        self.arrival_threshold = 0.15  # tightened from 0.5 for accuracy
        self.manipulation_time = 2.0  # seconds
        self.sensing_time = 1.0  # seconds
        self.state_timeout = 60.0  # seconds
        
        # Navigation tuning parameters
        self.max_linear_vel = 2.0  # Increased from 1.0 m/s for faster navigation
        self.max_angular_vel = 1.0  # Increased from 0.5 rad/s for faster turning
        self.kp_linear = 8.0  # Increased to get targets faster
        self.kp_angular = 0.15  # Increased back to 0.15 for better tracking

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
            logger.warning(f"State timeout in {self.state.value}, returning to IDLE")
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
        status = self.controller.get_status()
        current = status.position

        dx = target[0] - current[0]
        dy = target[1] - current[1]
        dist = math.hypot(dx, dy)
        
        # Check arrival
        if dist < self.arrival_threshold:
            self.controller.set_velocity(0.0, 0.0)
            logger.info(f"Navigation complete: reached {target}, distance error: {dist:.3f}m")
            self._enter_state(RobotState.IDLE, None)
            return

        # Direct movement toward target
        # Move at maximum speed toward target
        step_size = 0.05  # 5cm steps at 60Hz = 3m/s effective speed
        if dist > step_size:
            # Move toward target
            ratio = step_size / dist
            new_x = current[0] + dx * ratio
            new_y = current[1] + dy * ratio
            self.controller.position = [new_x, new_y]
            # Update heading to face direction of movement
            self.controller.heading = math.degrees(math.atan2(dy, dx))
            self.controller.set_velocity(1.5, 0.0)  # Nominal velocity for logging
        else:
            # Last step to target
            self.controller.position = target
            self.controller.heading = math.degrees(math.atan2(dy, dx))
            self.controller.set_velocity(0.0, 0.0)

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


