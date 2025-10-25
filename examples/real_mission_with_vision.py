"""
Real mission with vision detection, streaming output, and comprehensive logging.

This demonstrates:
- Real object detection with vision pipeline
- Streaming status updates (like LLM would provide)
- Comprehensive mission logging
- Successful task completion with metrics
"""

import json
import logging
import sys
import time
from datetime import datetime

# Setup path
sys.path.insert(0, '/Users/ahmadkaddoura/calhacks')

from merlin.core.state_machine import StateMachine
from merlin.core.types import RobotStatus, DetectedObject
from merlin.hardware.mock import MockController
from merlin.mcp.server import MCPServer
from merlin.vision.vision_pipeline import VisionPipeline


# Configure streaming logger
class StreamingFormatter(logging.Formatter):
    """Format logs for streaming output (real-time mission feedback)."""

    def format(self, record):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Color codes for terminal
        level_colors = {
            "INFO": "\033[94m",  # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "RESET": "\033[0m"
        }
        
        level = record.levelname
        color = level_colors.get(level, level_colors["INFO"])
        reset = level_colors["RESET"]
        
        return f"{timestamp} {color}[{level:8}]{reset} {record.getMessage()}"


def setup_logging():
    """Setup streaming logger with colored output."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = StreamingFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def stream_status(msg: str, level: str = "INFO"):
    """Stream status message to console."""
    logger = logging.getLogger()
    if level == "SUCCESS":
        logging.INFO = logging.INFO  # Use INFO level for success
        logger.info(f"✅ {msg}")
    elif level == "ERROR":
        logger.error(f"❌ {msg}")
    else:
        logger.info(msg)


def run_real_mission_with_vision():
    """Execute a complete mission with real vision detection."""
    
    logger = setup_logging()
    mission_start = time.time()
    
    print("\n" + "="*80)
    print("  MERLIN: REAL MISSION WITH VISION DETECTION")
    print("="*80 + "\n")
    
    # Initialize components
    stream_status("Initializing robot system...")
    controller = MockController()
    sm = StateMachine(controller)
    mcp = MCPServer(sm)
    vision = VisionPipeline()
    
    # Mission data
    mission_log = {
        "timestamp": datetime.now().isoformat(),
        "mission_name": "Pick Red Cube and Place",
        "status": "RUNNING",
        "steps": [],
        "metrics": {}
    }
    
    try:
        # Step 1: Get initial status
        stream_status("Step 1/5: Checking robot status...")
        result = mcp.execute_tool("get_robot_status", {})
        status = result["status"]
        mission_log["steps"].append({
            "step": 1,
            "action": "get_robot_status",
            "result": status,
            "timestamp": datetime.now().isoformat()
        })
        stream_status(f"  Position: {status['position']}, Battery: {status['battery']:.1f}%")
        
        # Step 2: Navigate to the object location
        stream_status("Step 2/5: Navigating to red cube location...")
        result = mcp.execute_tool("navigate_to", {"x": 1.5, "y": 0.5})
        if result["success"]:
            mission_log["steps"].append({
                "step": 2,
                "action": "navigate_to",
                "target": [1.5, 0.5],
                "result": result["final_position"],
                "timestamp": datetime.now().isoformat()
            })
            stream_status(f"  ✅ Arrived at {result['final_position']}")
        else:
            stream_status(f"  ❌ Navigation failed: {result.get('error')}", "ERROR")
            raise RuntimeError("Navigation failed")
        
        # Step 3: Detect objects (REAL VISION!)
        stream_status("Step 3/5: Scanning for objects with vision...")
        detections = vision.detect(["red_cube", "green_sphere", "blue_block"], status["position"])
        
        mission_log["steps"].append({
            "step": 3,
            "action": "detect_objects",
            "query": ["red_cube", "green_sphere", "blue_block"],
            "detections": [
                {
                    "name": d.name,
                    "confidence": d.confidence,
                    "position": d.position,
                    "bbox": d.bbox
                }
                for d in detections
            ],
            "timestamp": datetime.now().isoformat()
        })
        
        stream_status(f"  ✅ Found {len(detections)} objects:")
        for det in detections:
            stream_status(f"      • {det.name}: confidence {det.confidence:.2%} @ {det.position}")
        
        # Step 4: Grasp the detected red cube
        red_cube = next((d for d in detections if d.name == "red_cube"), None)
        if red_cube:
            stream_status(f"Step 4/5: Grasping red cube at {red_cube.position}...")
            result = mcp.execute_tool("grasp_object", {})
            if result["success"]:
                mission_log["steps"].append({
                    "step": 4,
                    "action": "grasp_object",
                    "result": result["gripper_state"],
                    "timestamp": datetime.now().isoformat()
                })
                stream_status(f"  ✅ Gripper {result['gripper_state']}")
            else:
                stream_status(f"  ❌ Grasp failed: {result.get('error')}", "ERROR")
                raise RuntimeError("Grasp failed")
        else:
            stream_status("  ❌ Red cube not found in detections!", "ERROR")
            raise RuntimeError("Red cube not found")
        
        # Step 5: Navigate to drop location and release
        stream_status("Step 5/5: Navigating to drop location...")
        result = mcp.execute_tool("navigate_to", {"x": 3.0, "y": 1.0})
        if result["success"]:
            mission_log["steps"].append({
                "step": 5,
                "action": "navigate_to_drop_location",
                "target": [3.0, 1.0],
                "result": result["final_position"],
                "timestamp": datetime.now().isoformat()
            })
            stream_status(f"  ✅ Arrived at drop location {result['final_position']}")
            
            # Release
            stream_status("  Releasing object...")
            result = mcp.execute_tool("release_object", {})
            if result["success"]:
                mission_log["steps"].append({
                    "step": "5b",
                    "action": "release_object",
                    "result": result["gripper_state"],
                    "timestamp": datetime.now().isoformat()
                })
                stream_status(f"  ✅ Gripper {result['gripper_state']}")
            else:
                stream_status(f"  ❌ Release failed: {result.get('error')}", "ERROR")
                raise RuntimeError("Release failed")
        else:
            stream_status(f"  ❌ Navigation to drop failed: {result.get('error')}", "ERROR")
            raise RuntimeError("Drop location navigation failed")
        
        # Final status
        stream_status("Getting final robot status...")
        result = mcp.execute_tool("get_robot_status", {})
        final_status = result["status"]
        mission_log["steps"].append({
            "step": 6,
            "action": "get_robot_status_final",
            "result": final_status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Calculate metrics
        mission_duration = time.time() - mission_start
        battery_used = 95.0 - final_status["battery"]
        
        mission_log["status"] = "SUCCESS"
        mission_log["metrics"] = {
            "duration_seconds": round(mission_duration, 2),
            "battery_used_percent": round(battery_used, 2),
            "battery_remaining_percent": round(final_status["battery"], 2),
            "final_position": final_status["position"],
            "objects_detected": len(detections),
            "vision_detections": [d.name for d in detections]
        }
        
        # Print success summary
        print("\n" + "="*80)
        print("  ✅ MISSION SUCCESSFUL!")
        print("="*80)
        print(f"\nMission Duration:      {mission_duration:.2f} seconds")
        print(f"Battery Used:          {battery_used:.1f}%")
        print(f"Battery Remaining:     {final_status['battery']:.1f}%")
        print(f"Final Position:        {final_status['position']}")
        print(f"Objects Detected:      {len(detections)} (via real vision)")
        print(f"Gripper State:         {'OPEN' if final_status['gripper_open'] else 'CLOSED'}")
        print("="*80 + "\n")
        
    except Exception as e:
        mission_log["status"] = "FAILED"
        mission_log["error"] = str(e)
        stream_status(f"Mission failed: {e}", "ERROR")
        print("\n" + "="*80)
        print(f"  ❌ MISSION FAILED: {e}")
        print("="*80 + "\n")
    
    # Save mission log
    log_file = "/Users/ahmadkaddoura/calhacks/mission_log_real_vision.json"
    with open(log_file, "w") as f:
        json.dump(mission_log, f, indent=2, default=str)
    
    stream_status(f"Mission log saved to: {log_file}")
    
    # Print mission log
    print("\n" + "="*80)
    print("  MISSION LOG (JSON)")
    print("="*80 + "\n")
    print(json.dumps(mission_log, indent=2, default=str))
    print("\n" + "="*80 + "\n")
    
    return mission_log["status"] == "SUCCESS"


if __name__ == "__main__":
    success = run_real_mission_with_vision()
    exit(0 if success else 1)
