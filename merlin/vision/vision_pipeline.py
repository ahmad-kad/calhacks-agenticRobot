"""Real vision pipeline for object detection and tracking."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Any, Dict, List

from merlin.core.types import DetectedObject

logger = logging.getLogger(__name__)


class VisionPipeline:
    """Simulates real computer vision with configurable object database."""

    def __init__(self, scene: Dict[str, List[Dict[str, Any]]] | None = None):
        """
        Initialize vision pipeline with a scene of objects.
        
        Args:
            scene: Dict mapping object names to list of object data
                   Example: {
                       "red_cube": [{"x": 1.5, "y": 0.5, "confidence": 0.95}],
                       "green_sphere": [{"x": 2.0, "y": 1.0, "confidence": 0.87}]
                   }
        """
        self.scene = scene or self._default_scene()
        self.detection_count = 0

    @staticmethod
    def _default_scene() -> Dict[str, List[Dict[str, Any]]]:
        """Default test scene with common objects."""
        return {
            "red_cube": [
                {"x": 1.5, "y": 0.5, "confidence": 0.95},
            ],
            "green_sphere": [
                {"x": 2.0, "y": 1.0, "confidence": 0.87},
            ],
            "blue_block": [
                {"x": 1.2, "y": -0.3, "confidence": 0.92},
            ],
            "yellow_cylinder": [
                {"x": 2.5, "y": 0.8, "confidence": 0.88},
            ],
        }

    def detect(
        self, object_names: List[str], robot_position: List[float] | None = None
    ) -> List[DetectedObject]:
        """
        Detect objects in the scene.
        
        Args:
            object_names: List of object names to search for
            robot_position: Current robot position [x, y]
            
        Returns:
            List of detected objects with positions and confidence scores
        """
        self.detection_count += 1
        detected = []

        for obj_name in object_names:
            if obj_name in self.scene:
                for obj_data in self.scene[obj_name]:
                    detected_obj = DetectedObject(
                        name=obj_name,
                        confidence=obj_data.get("confidence", 0.9),
                        position=[obj_data["x"], obj_data["y"]],
                        bbox=[
                            obj_data["x"] - 0.1,
                            obj_data["y"] - 0.1,
                            obj_data["x"] + 0.1,
                            obj_data["y"] + 0.1,
                        ],
                    )
                    detected.append(detected_obj)
                    logger.info(
                        f"[VISION] Detected: {obj_name} @ [{obj_data['x']}, {obj_data['y']}]"
                        f" (confidence: {obj_data.get('confidence', 0.9):.2f})"
                    )

        logger.info(f"[VISION] Detection #{self.detection_count}: Found {len(detected)} objects")
        return detected

    def get_all_objects(self) -> List[str]:
        """Get list of all objects in the scene."""
        return list(self.scene.keys())

    def to_json(self, detections: List[DetectedObject]) -> str:
        """Convert detections to JSON string."""
        data = [asdict(d) for d in detections]
        return json.dumps(data, indent=2)
