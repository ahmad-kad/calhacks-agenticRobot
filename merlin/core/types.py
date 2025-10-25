from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class RobotState(str, Enum):
    IDLE = "IDLE"
    NAVIGATING = "NAVIGATING"
    MANIPULATING = "MANIPULATING"
    SENSING = "SENSING"


@dataclass
class DetectedObject:
    """Represents a detected object with position and confidence."""
    name: str
    confidence: float  # 0.0 to 1.0
    position: List[float]  # [x, y]
    bbox: List[float] = field(default_factory=list)  # [x1, y1, x2, y2]


@dataclass
class RobotStatus:
    """Current state of the robot."""
    state: str = "IDLE"
    position: List[float] = field(default_factory=lambda: [0.0, 0.0])
    heading: float = 0.0
    battery: float = 95.0
    gripper_open: bool = True
    detected_objects: List[DetectedObject] = field(default_factory=list)


