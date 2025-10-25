from __future__ import annotations

import math
import subprocess
import time
from typing import Optional

from merlin.core.controller import RobotController
from merlin.core.types import RobotStatus


class GazeboController(RobotController):
    """Gazebo simulator backend via ROS2 bridge (optional dependency).
    
    Requires: gazebo, ros2, ros2_control
    Falls back gracefully if not available.
    """

    def __init__(self, model_name: str = "turtlebot3_waffle", headless: bool = False) -> None:
        try:
            import rclpy
            from geometry_msgs.msg import Twist
            from nav_msgs.msg import Odometry
        except ImportError:
            raise ImportError("ROS2 not installed; install ros2 and rclpy to use Gazebo backend")

        self.model_name = model_name
        self.headless = headless
        
        # Try to init ROS2 node
        if not rclpy.ok():
            rclpy.init()
        
        self.node = rclpy.create_node("merlin_gazebo_controller")
        
        # Publishers/subscribers
        self.cmd_vel_pub = self.node.create_publisher(Twist, f"/{model_name}/cmd_vel", 10)
        self.odom_sub = self.node.create_subscription(
            Odometry, f"/{model_name}/odom", self._odom_callback, 10
        )
        
        # State cache
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.detected_objects = []
        
        # Command cache
        self._target_vel = 0.0
        self._target_omega = 0.0
        
        self._startup_gazebo()

    def _startup_gazebo(self) -> None:
        """Start Gazebo if not already running."""
        try:
            # Check if Gazebo is running
            result = subprocess.run(
                ["pgrep", "-f", "gazebo"],
                capture_output=True,
                timeout=2,
            )
            if result.returncode != 0:
                # Start Gazebo with model
                cmd = [
                    "gazebo",
                    "--verbose" if not self.headless else "",
                    f"--model-database-uri='{self.model_name}'",
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)  # Wait for Gazebo to start
        except Exception as e:
            print(f"Warning: Could not start Gazebo: {e}")

    def _odom_callback(self, msg) -> None:
        """Update robot pose from Gazebo odometry."""
        self.position = [msg.pose.pose.position.x, msg.pose.pose.position.y]
        
        # Extract yaw from quaternion
        quat = msg.pose.pose.orientation
        yaw = math.atan2(
            2 * (quat.w * quat.z + quat.x * quat.y),
            1 - 2 * (quat.y**2 + quat.z**2),
        )
        self.heading = math.degrees(yaw) % 360

    def update(self, delta_t: float = 0.016) -> None:
        """Step the simulation and update state."""
        import rclpy
        
        # Spin once to process callbacks
        rclpy.spin_once(self.node, timeout_sec=0.001)
        
        # Battery drain
        if abs(self._target_vel) > 1e-2 or abs(self._target_omega) > 1e-2:
            self.battery = max(0.0, self.battery - 0.01)

    def set_velocity(self, vel: float, omega: float) -> None:
        """Send velocity command to Gazebo."""
        from geometry_msgs.msg import Twist
        
        self._target_vel = max(-0.5, min(0.5, vel))
        self._target_omega = max(-0.5, min(0.5, omega))
        
        msg = Twist()
        msg.linear.x = self._target_vel
        msg.angular.z = self._target_omega
        self.cmd_vel_pub.publish(msg)

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
