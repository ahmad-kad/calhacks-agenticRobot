from __future__ import annotations

from typing import Literal

from merlin.core.controller import RobotController


def create_controller(backend: Literal["mock", "mujoco", "gazebo", "maniskill", "xle"] = "mock") -> RobotController:
    if backend == "mock":
        from .mock import MockController

        return MockController()
    elif backend == "mujoco":
        from .simulator import MuJoCoController

        return MuJoCoController()
    elif backend == "gazebo":
        from .gazebo import GazeboController

        return GazeboController()
    elif backend == "maniskill":
        from .maniskill import ManiSkillController

        return ManiSkillController()
    elif backend == "xle":
        raise NotImplementedError("XLE backend not implemented yet")
    else:
        raise ValueError(f"Unknown backend: {backend}")


