from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from merlin.core.state_machine import StateMachine
from .base import MCPTool


class ToolDetectObjects(MCPTool):
    SENSING_TIMEOUT = 3.0

    def __init__(self, sm: StateMachine, vision_pipeline: Optional[object] = None):
        self.state_machine = sm
        self.vision_pipeline = vision_pipeline

    @property
    def name(self) -> str:
        return "detect_objects"

    @property
    def description(self) -> str:
        return "Scan for objects and return their positions"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "object_names": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["object_names"],
        }

    def execute(self, object_names: List[str], **kwargs) -> Dict[str, Any]:
        if not self.state_machine.set_goal("SENSING", {"target_objects": object_names}):
            return {"success": False, "error": "Failed to set sensing goal"}

        start = time.time()
        while time.time() - start < self.SENSING_TIMEOUT:
            status = self.state_machine.update()
            if status.state == "IDLE":
                if self.vision_pipeline:
                    # Placeholder call into optional vision pipeline
                    try:
                        detections = self.vision_pipeline.detect(object_names)
                    except Exception:
                        detections = []
                else:
                    detections = status.detected_objects
                return {"success": True, "detected": detections, "count": len(detections)}
            time.sleep(0.016)
        return {"success": False, "error": "Sensing timeout"}


