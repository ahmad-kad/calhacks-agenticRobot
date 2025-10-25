from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .types import RobotStatus


class RobotController(ABC):
    """Abstract hardware controller interface.

    Implementations: MockController, MuJoCoController, XLEController (future).
    """

    @abstractmethod
    def update(self, delta_t: float = 0.016) -> None:
        """Integrate kinematics / step physics by delta_t seconds."""

    @abstractmethod
    def set_velocity(self, vel: float, omega: float) -> None:
        """Set target linear velocity (m/s) and angular rate (rad/s)."""

    @abstractmethod
    def set_gripper(self, open_cmd: bool) -> None:
        """Open (True) or close (False) gripper."""

    @abstractmethod
    def get_status(self) -> RobotStatus:
        """Return current robot telemetry as RobotStatus."""


