from __future__ import annotations

import math
from typing import Optional

from merlin.core.controller import RobotController
from merlin.core.types import RobotStatus


try:
    import mujoco  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    mujoco = None


class MuJoCoController(RobotController):
    """Physics-based controller using MuJoCo (optional dependency).

    Falls back to raising ImportError if mujoco is not available.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        if mujoco is None:
            raise ImportError("mujoco is not installed")

        # Minimal model: either provided or internal tiny MJCF
        if model_path is None:
            xml = _MINIMAL_MJCF
            self.model = mujoco.MjModel.from_xml_string(xml)
        else:
            self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)

        # State cache
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True

        # Commands (no actuators in minimal model; emulate as base twist)
        self._target_vel = 0.0
        self._target_omega = 0.0

    def update(self, delta_t: float = 0.016) -> None:
        # Advance kinematic pose manually for minimal model
        self.position[0] += self._target_vel * math.cos(math.radians(self.heading)) * delta_t
        self.position[1] += self._target_vel * math.sin(math.radians(self.heading)) * delta_t
        self.heading = (self.heading + math.degrees(self._target_omega) * delta_t) % 360
        if abs(self._target_vel) > 1e-2 or abs(self._target_omega) > 1e-2:
            self.battery = max(0.0, self.battery - 0.01)

        # Step physics to keep data consistent
        mujoco.mj_step(self.model, self.data, nstep=1)

    def set_velocity(self, vel: float, omega: float) -> None:
        self._target_vel = max(-0.5, min(0.5, vel))
        self._target_omega = max(-0.5, min(0.5, omega))

    def set_gripper(self, open_cmd: bool) -> None:
        self.gripper_open = bool(open_cmd)

    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state="IDLE",
            position=[self.position[0], self.position[1]],
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=[],
        )


_MINIMAL_MJCF = """
<mujoco model="minimal">
  <option timestep="0.01"/>
  <worldbody>
    <body name="base" pos="0 0 0">
      <geom type="box" size="0.1 0.1 0.05" rgba="0.8 0.2 0.2 1"/>
    </body>
  </worldbody>
</mujoco>
"""


