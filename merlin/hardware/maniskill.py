from __future__ import annotations

import math
import time
from typing import Optional

from merlin.core.controller import RobotController
from merlin.core.types import RobotStatus


try:
    import gymnasium as gym
    from mani_skill.envs import make as ms_make
except ImportError:
    gym = None
    ms_make = None


class ManiSkillController(RobotController):
    """XLeRobot controller via ManiSkill simulation (optional dependency).
    
    Requires: mani-skill, pygame
    Environment: ReplicaCAD_SceneManipulation-v1
    Robot: xlerobot (dual-arm) or xlerobot_single (single-arm)
    """

    def __init__(
        self,
        robot: str = "xlerobot_single",
        control_mode: str = "pd_joint_delta_pos",
        render_mode: str = "rgb_array",
        headless: bool = True,
    ) -> None:
        if gym is None or ms_make is None:
            raise ImportError("ManiSkill not installed; pip install mani-skill")

        self.robot = robot
        self.control_mode = control_mode
        self.render_mode = render_mode
        self.headless = headless

        # Create environment
        try:
            self.env = ms_make(
                "ReplicaCAD_SceneManipulation-v1",
                robot=robot,
                control_mode=control_mode,
                render_mode=render_mode if not headless else "rgb_array",
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create ManiSkill environment. "
                f"Ensure XLeRobot files are installed in ManiSkill package: {e}"
            )

        # Reset environment
        obs, _ = self.env.reset()
        
        # State cache
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.detected_objects = []
        
        # Command cache
        self._target_vel = 0.0
        self._target_omega = 0.0
        self._last_update = time.time()

    def update(self, delta_t: float = 0.016) -> None:
        """Step ManiSkill environment and extract robot state."""
        try:
            # Build action: [joint deltas for arm, gripper command]
            # For simplicity, map velocity to arm motion delta.
            # In production, use inverse kinematics or learned policy.
            action = self._build_action()
            
            obs, _, terminated, truncated, _ = self.env.step(action)
            
            # Extract robot pose from observation
            # ManiSkill observations vary; common: agent_pos, agent_qpos (joint positions)
            if isinstance(obs, dict):
                # Try common observation keys
                if "agent_pos" in obs:
                    pos = obs["agent_pos"]
                    self.position = [float(pos[0]), float(pos[1])]
                    self.heading = float(pos[2]) * 180 / math.pi if len(pos) > 2 else 0.0
            
            # Battery drain during motion
            if abs(self._target_vel) > 1e-2 or abs(self._target_omega) > 1e-2:
                self.battery = max(0.0, self.battery - 0.01)
            
            # Reset if episode ended
            if terminated or truncated:
                obs, _ = self.env.reset()
                
        except Exception as e:
            print(f"Warning: ManiSkill step failed: {e}")

    def _build_action(self):
        """Build ManiSkill action from target velocity/omega commands.
        
        For simplicity, map velocity to arm motion delta.
        In production, use inverse kinematics or learned policy.
        """
        # Placeholder: return zero action for stability
        # Real implementation would use IK or learned controller
        
        if self.robot == "xlerobot_single":
            # Single-arm + gripper: 7 + 1 = 8 DOF
            action = [0.0] * 8
            # First 7: arm joints (delta positions)
            # Last 1: gripper (0=closed, 1=open)
            action[-1] = 1.0 if self.gripper_open else 0.0
        else:  # xlerobot (dual-arm)
            # Dual-arm + gripper: 14 + 1 = 15 DOF
            action = [0.0] * 15
            action[-1] = 1.0 if self.gripper_open else 0.0
        
        return action

    def set_velocity(self, vel: float, omega: float) -> None:
        """Store target velocity (will be converted to arm commands in update)."""
        self._target_vel = max(-0.5, min(0.5, vel))
        self._target_omega = max(-0.5, min(0.5, omega))

    def set_gripper(self, open_cmd: bool) -> None:
        """Set gripper state."""
        self.gripper_open = bool(open_cmd)

    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state="IDLE",
            position=[self.position[0], self.position[1]],
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=list(self.detected_objects),
        )

    def close(self) -> None:
        """Clean up environment."""
        try:
            self.env.close()
        except Exception:
            pass
