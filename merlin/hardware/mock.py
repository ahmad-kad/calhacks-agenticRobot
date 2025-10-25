from __future__ import annotations

import math
from dataclasses import dataclass

from merlin.core.controller import RobotController
from merlin.core.types import RobotStatus


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


class MockController(RobotController):
    """Simple unicycle kinematics mock controller."""

    def __init__(self) -> None:
        self.position = [0.0, 0.0]
        self.heading = 0.0  # degrees
        self.battery = 95.0
        self.gripper_open = True
        self._target_vel = 0.0  # m/s
        self._target_omega = 0.0  # rad/s
        self.detected_objects = []
        self.state = "IDLE"  # Track current state

    def update(self, delta_t: float = 0.016) -> None:
        # Integrate unicycle model
        self.position[0] += self._target_vel * math.cos(math.radians(self.heading)) * delta_t
        self.position[1] += self._target_vel * math.sin(math.radians(self.heading)) * delta_t
        self.heading = (self.heading + math.degrees(self._target_omega) * delta_t) % 360

        # Battery drain when moving
        if abs(self._target_vel) > 1e-2 or abs(self._target_omega) > 1e-2:
            self.battery -= 0.01
            self.battery = max(0.0, self.battery)

    def set_velocity(self, vel: float, omega: float) -> None:
        self._target_vel = _clamp(vel, -1.0, 1.0)  # Increased from 0.5 to 1.0
        self._target_omega = _clamp(omega, -0.5, 0.5)

    def set_gripper(self, open_cmd: bool) -> None:
        self.gripper_open = bool(open_cmd)

    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state=self.state,
            position=[self.position[0], self.position[1]],
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=list(self.detected_objects),
        )


