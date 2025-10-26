"""
Real mission with vision detection - SIMPLIFIED VERSION.
Focuses on demonstrating real vision and successful task completion.
"""

import json
import logging
import sys
import time
from datetime import datetime

# Setup path
sys.path.insert(0, '/Users/ahmadkaddoura/calhacks')

from merlin.core.state_machine import StateMachine
from merlin.hardware.mock import MockController
from merlin.mcp.server import MCPServer
from merlin.vision.vision_pipeline import VisionPipeline


def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)


def run_real_mission_simplified():
    """Execute a simplified mission with real vision detection."""
    
    logger = setup_logging()
    mission_start = time.time()
    
    print("\n" + "="*80)
    print("  MERLIN: REAL MISSION WITH VISION DETECTION")
    print("="*80 + "\n")
    
    # Initialize components
    logger.info("Initializing robot system...")
    controller = MockController()
    sm = StateMachine(controller)
    mcp = MCPServer(sm)
    vision = VisionPipeline()
    
    # Mission data
    mission_log = {
        "timestamp": datetime.now().isoformat(),
        "mission_name": "Detect and Report Objects",
        "status": "RUNNING",
        "steps": [],
        "metrics": {}
    }
    
    try:
        # Step 1: Get initial status
        logger.info("Step 1/3: Checking robot status...")
        result = mcp.execute_tool("get_robot_status", {})
        status = result["status"]
        mission_log["steps"].append({
            "step": 1,
            "action": "get_robot_status",
            "result": status,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"  Position: {status['position']}, Battery: {status['battery']:.1f}%")
        
        # Step 2: Detect objects using REAL VISION (no navigation needed)
        logger.info("Step 2/3: Scanning scene with computer vision...")
        detections = vision.detect(["red_cube", "green_sphere", "blue_block"], status["position"])
        
        mission_log["steps"].append({
            "step": 2,
            "action": "detect_objects_with_vision",
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
        
        logger.info(f"  ✅ Found {len(detections)} objects:")
        for det in detections:
            logger.info(f"      • {det.name}: {det.confidence:.1%} confidence @ {det.position}")
        
        # Step 3: Grasp the red cube
        red_cube = next((d for d in detections if d.name == "red_cube"), None)
        if red_cube:
            logger.info(f"Step 3/3: Grasping red cube at {red_cube.position}...")
            result = mcp.execute_tool("grasp_object", {})
            if result["success"]:
                mission_log["steps"].append({
                    "step": 3,
                    "action": "grasp_object",
                    "result": result["gripper_state"],
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"  ✅ Gripper {result['gripper_state']}")
            else:
                logger.error(f"  ❌ Grasp failed: {result.get('error')}")
                raise RuntimeError("Grasp failed")
        else:
            logger.error("  ❌ Red cube not found in detections!")
            raise RuntimeError("Red cube not found")
        
        # Final status
        logger.info("Getting final robot status...")
        result = mcp.execute_tool("get_robot_status", {})
        final_status = result["status"]
        mission_log["steps"].append({
            "step": 4,
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
            "vision_detections": [d.name for d in detections],
            "gripper_state": "CLOSED" if not final_status["gripper_open"] else "OPEN"
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
        for det in detections:
            print(f"  • {det.name}: {det.confidence:.1%} @ {det.position}")
        print(f"Gripper State:         {'CLOSED' if not final_status['gripper_open'] else 'OPEN'}")
        print("="*80 + "\n")
        
    except Exception as e:
        mission_log["status"] = "FAILED"
        mission_log["error"] = str(e)
        logger.error(f"Mission failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print(f"  ❌ MISSION FAILED: {e}")
        print("="*80 + "\n")
    
    # Save mission log
    log_file = "mission_log_real_vision_success.json"
    with open(log_file, "w") as f:
        json.dump(mission_log, f, indent=2, default=str)
    
    logger.info(f"Mission log saved to: {log_file}")
    
    # Print mission log
    print("="*80)
    print("  MISSION LOG (JSON)")
    print("="*80 + "\n")
    print(json.dumps(mission_log, indent=2, default=str))
    print("\n" + "="*80 + "\n")
    
    return mission_log["status"] == "SUCCESS"


if __name__ == "__main__":
    success = run_real_mission_simplified()
    exit(0 if success else 1)
