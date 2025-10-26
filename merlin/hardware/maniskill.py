from __future__ import annotations

import math
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from merlin.core.controller import RobotController
from merlin.core.types import RobotStatus

# Custom exception
class SimulationError(Exception):
    """Raised for ManiSkill simulation issues."""

try:
    import gymnasium as gym
    from mani_skill.envs import make as ms_make
    import structlog
    logger = structlog.get_logger()
except ImportError:
    gym = None
    ms_make = None
    logger = None

@dataclass
class SimConfig:
    """Config for ManiSkill environments (SOLID: Dependency Inversion)."""
    env_id: str = "ReplicaCAD_SceneManipulation-v1"
    robot: str = "xlerobot_single"
    control_mode: str = "pd_joint_delta_pos"
    render_mode: str = "rgb_array"
    headless: bool = True
    max_steps: int = 1000  # Prevent infinite episodes
    seed: Optional[int] = None  # For randomization

class ManiSkillController(RobotController):
    """XLeRobot controller via ManiSkill simulation (optional dependency).
    
    Requires: mani-skill, pygame
    Environment: ReplicaCAD_SceneManipulation-v1
    Robot: xlerobot (dual-arm) or xlerobot_single (single-arm)
    """
    def __init__(
        self,
        config: SimConfig = SimConfig(),
    ) -> None:
        if gym is None or ms_make is None:
            raise ImportError("ManiSkill not installed; pip install mani-skill")
        if logger is None:
            raise ImportError("structlog not installed; pip install structlog")

        self.config = config
        self.robot = config.robot
        self.control_mode = config.control_mode
        self.render_mode = config.render_mode
        self.headless = config.headless

        # Vision integration (lazy)
        self.vision_pipeline = None

        # Create environment
        try:
            self.env = ms_make(
                config.env_id,
                robot=config.robot,
                control_mode=config.control_mode,
                render_mode=config.render_mode if not config.headless else "rgb_array",
                max_episode_steps=config.max_steps,
                seed=config.seed,
            )
        except Exception as e:
            raise SimulationError(
                f"Failed to create ManiSkill environment. "
                f"Ensure XLeRobot files are installed in ManiSkill package: {e}"
            )

        # Reset environment
        obs, info = self.env.reset()
        logger.info("ManiSkill env created", env_id=config.env_id, robot=config.robot, seed=config.seed)
        
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

        # IK solver (optional, using library)
        self.ik_solver = None
        try:
            import pytorch_kinematics as pk
            urdf_path = "/path/to/xlerobot.urdf"  # Update with actual path from assets
            with open(urdf_path) as f:
                urdf = f.read()
            self.ik_solver = pk.build_serial_chain_from_urdf(urdf, "base_link", "gripper")
            logger.info("IK solver initialized", solver="pytorch-kinematics")
        except (ImportError, FileNotFoundError) as e:
            logger.warning(f"IK solver unavailable: {e}; using basic actions")

    def update(self, delta_t: float = 0.016) -> None:
        """Step ManiSkill environment and extract robot state."""
        try:
            # Build action
            action = self._build_action()
            
            obs, reward, terminated, truncated, info = self.env.step(action)
            
            # Extract robot pose from observation
            if isinstance(obs, dict):
                if "agent_pos" in obs:
                    pos = obs["agent_pos"]
                    self.position = [float(pos[0]), float(pos[1])]
                    self.heading = float(pos[2]) * 180 / math.pi if len(pos) > 2 else 0.0
            
            # Battery drain during motion
            if abs(self._target_vel) > 1e-2 or abs(self._target_omega) > 1e-2:
                self.battery = max(0.0, self.battery - 0.01 * delta_t / 0.016)
            
            # Integrate vision if render_mode supports it
            if self.render_mode in ["rgb_array", "human"] and self.vision_pipeline is None:
                from merlin.vision.vision_pipeline import VisionPipeline
                self.vision_pipeline = VisionPipeline()
            
            if self.vision_pipeline:
                rgb = self.env.render() if hasattr(self.env, 'render') else None
                if rgb is not None:
                    detections = self.vision_pipeline.detect_from_image(rgb, ["red_cube", "green_sphere"])  # Example query
                    self.detected_objects = detections
                    logger.debug("Vision integrated", detections=len(detections))

            # Reset if episode ended
            if terminated or truncated:
                self.reset_scene()
                logger.info("Episode reset due to termination")
                
        except Exception as e:
            logger.error("ManiSkill step failed", error=str(e))
            raise SimulationError(f"Update failed: {e}")

    def _build_action(self) -> Dict[str, Any]:
        """Build action with kinematics if available."""
        if self.ik_solver:
            # Placeholder: Compute joint deltas from target (vel/omega -> pose)
            try:
                import transforms3d
                # Simple mapping
                dt = time.time() - self._last_update
                delta_pose = transforms3d.axangles.axangle2mat([0, 0, self._target_omega * dt], self._target_vel * dt)
                joint_deltas = self.ik_solver.inverse_kinematics(delta_pose)
                action = joint_deltas.tolist() + [1.0 if self.gripper_open else 0.0]
                logger.debug("IK action computed", num_joints=len(joint_deltas))
            except Exception as e:
                logger.warning(f"IK computation failed: {e}; fallback to zero action")
                action = [0.0] * (8 if self.robot == "xlerobot_single" else 15)
                action[-1] = 1.0 if self.gripper_open else 0.0
        else:
            # Fallback
            action = [0.0] * (8 if self.robot == "xlerobot_single" else 15)
            action[-1] = 1.0 if self.gripper_open else 0.0
        
        self._last_update = time.time()
        return action

    def reset_scene(self, variant: str = "default", seed: Optional[int] = None) -> None:
        """Reset with randomization (e.g., object positions, lighting)."""
        try:
            new_seed = seed or int(time.time())
            self.config.seed = new_seed
            obs, info = self.env.reset(seed=new_seed)
            
            # ManiSkill-specific randomization (if API supports)
            if hasattr(self.env, 'randomize_scene'):
                # Example: Randomize objects in ReplicaCAD
                num_objects = 3 if variant == "cluttered" else 1
                self.env.randomize_scene(num_objects=num_objects, lighting_var=0.5)  # Placeholder API
                logger.info("Scene randomized", variant=variant, num_objects=num_objects, seed=new_seed)
            else:
                # Basic seed-based reset for reproducibility
                logger.info("Basic seed reset", seed=new_seed)
            
            # Re-init vision if needed
            self.detected_objects = []
            
            # Reset state cache
            self.position = [0.0, 0.0]
            self.heading = 0.0
            self.battery = 95.0
            self.gripper_open = True
            
        except Exception as e:
            logger.error("Scene reset failed", variant=variant, error=str(e))
            raise SimulationError(f"Reset failed for {variant}: {e}")

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
            if self.env:
                self.env.close()
            if self.vision_pipeline:
                self.vision_pipeline.close()  # If applicable
            logger.info("ManiSkill controller closed")
        except Exception as e:
            if logger:
                logger.warning("Close failed", error=str(e))
