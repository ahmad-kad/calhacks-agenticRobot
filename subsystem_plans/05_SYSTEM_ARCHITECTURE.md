# MERLIN System Architecture: Complete Data Flow & Integration

## 1. MuJoCo vs ROS2 vs Custom Architecture

### Decision Matrix

| Aspect | MuJoCo | ROS2 | Custom (Current) |
|--------|--------|------|-----------------|
| **Purpose** | Physics simulation | Middleware + tools | Focused framework |
| **Learning curve** | Moderate | Steep | Gentle |
| **Setup time** | 5 min | 30 min+ | 0 min |
| **Performance** | 1000 FPS sim | 50-100 Hz real | 60 Hz mock |
| **Best for** | Validation, prototyping | Production, real robots | CalHacks demo |
| **Dependencies** | ~5 libs | 50+ packages | ~3 libs |
| **Scalability** | Single machine | Distributed | Single machine |
| **Hardware support** | Simulation only | Real robots + sim | Both (with adapters) |

### Recommendation

**For CalHacks 40-hour timeline:**
- ✅ **Start with:** Custom architecture + Mock (this plan)
- ✅ **Add:** MuJoCo physics backend (optional, hour 20+)
- ⚠️ **Consider:** ROS2 as future extension, NOT immediate priority

**Why custom > ROS2 for this project:**
- ROS2 has steep learning curve (2-3 days to productivity)
- Our project is self-contained (doesn't need distributed middleware)
- Mock backend is sufficient for full agent testing
- Can add ROS2 adapter later if needed

**When to use ROS2:**
- Production deployment on real robot
- Multi-robot coordination
- Integration with existing robot software
- Team > 4 people

---

## 2. Complete System Architecture

### 2.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Layer 6: Missions                         │
│          (find_object, pick_and_place, etc)                │
├─────────────────────────────────────────────────────────────┤
│                   Layer 5: Agent Reasoning                  │
│   Claude/Groq/Gemini (LLM with tool-use capability)        │
├─────────────────────────────────────────────────────────────┤
│                   Layer 4: MCP Tool Server                  │
│   (5 core tools + extensible architecture)                 │
├─────────────────────────────────────────────────────────────┤
│              Layer 3: State Machine (60 Hz)                 │
│  (IDLE → NAVIGATING, MANIPULATING, SENSING)               │
├─────────────────────────────────────────────────────────────┤
│      Layer 2: Hardware Abstraction + Control                │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Navigation │  │ Perception│ │Manipulation│             │
│  │ (PID/TEB)  │  │ (Vision)  │ │ (Gripper)  │             │
│  └────────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────────┤
│      Layer 1: Hardware Backend (Pluggable)                  │
│  ┌────────┐  ┌────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Mock   │  │ MuJoCo │  │ ROS2 *  │  │ XLE **  │        │
│  │(Instant)  │(Sim)   │  │(Future) │  │(Optional)        │
│  └────────┘  └────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
  * Future extension    ** Optional, advanced
```

### 2.2 Component Interaction Diagram

```
┌─────────────┐
│   Claude    │ (LLM reasoning)
│   Agent     │
└──────┬──────┘
       │ run_mission("Find red cube")
       │
       ▼
┌──────────────────┐
│  MCP Server      │ (Tool registry)
│  ├─ get_status   │
│  ├─ navigate_to  │
│  ├─ detect_*     │
│  ├─ grasp_*      │
│  └─ release_*    │
└──────┬───────────┘
       │ execute_tool(name, input)
       │
       ▼
┌──────────────────────┐
│  State Machine       │ (60Hz autonomous loop)
│  ├─ set_goal()       │
│  ├─ update()         │
│  └─ state dispatch   │
└──────┬───────────────┘
       │ state-specific logic
       ├──────┬──────────┬────────┐
       ▼      ▼          ▼        ▼
    [NAV]  [SENSE]   [MANIP]  [IDLE]
       │      │        │        │
       ├──────┼────────┼────────┤
       └──────┬────────┴────────┘
              │
              ▼
    ┌─────────────────────┐
    │Hardware Abstraction │ (Factory pattern)
    │  ├─ update()        │
    │  ├─ set_velocity()  │
    │  ├─ set_gripper()   │
    │  └─ get_status()    │
    └─────────┬───────────┘
              │
    ┌─────────┴──────────┬──────────┐
    ▼                    ▼          ▼
 [Mock]            [MuJoCo]      [ROS2]
 Instant           Physics       Real Robot
 Kinematics        Simulation    (Future)
```

---

## 3. Missing Subsystems: SLAM & Navigation Stack

### 3.1 Why They're Not in Phase 1

| System | Phase | Reason |
|--------|-------|--------|
| **Navigation (TEB)** | 3 | Basic proportional control sufficient for demo |
| **SLAM** | 5+ | Only needed for real robots with unknown environments |
| **Path planning** | 4+ | Direct point-to-point navigation works for demo |
| **Localization (EKF)** | 4 | Mock/MuJoCo have perfect odometry |

### 3.2 Adding Navigation Stack (Optional, Hour 20+)

```python
# merlin/navigation/controller.py
class NavigationController:
    """Advanced navigation using TEB (Timed Elastic Band)."""
    
    def __init__(self):
        self.planner = TEB_LocalPlanner()  # From nav2 or custom
        self.current_pose = [0, 0, 0]
        self.goal_pose = None
    
    def plan_to(self, target_x, target_y):
        """Plan path to target using costmap + TEB."""
        # 1. Create local costmap
        # 2. Plan trajectory using TEB
        # 3. Generate velocity commands
        trajectory = self.planner.plan(self.current_pose, [target_x, target_y])
        return trajectory

# Use in state machine
class StateMachine:
    def _navigate_update(self):
        # Replace simple proportional control
        if self.use_advanced_nav:
            trajectory = self.nav_controller.plan_to(target_x, target_y)
            vel, omega = self.nav_controller.get_next_command()
        else:
            # Simple proportional control (current)
            vel, omega = compute_proportional_control(...)
        
        self.controller.set_velocity(vel, omega)
```

### 3.3 Adding SLAM (Optional, Real Robot Only)

```python
# merlin/perception/slam.py
class SLAMModule:
    """SLAM for real robots using ORB-SLAM2 or Cartographer."""
    
    def __init__(self, camera_feed):
        self.camera = camera_feed
        self.slam = ORB_SLAM2()  # Or Cartographer
        self.map = None
        self.pose = [0, 0, 0]
    
    def update(self, frame):
        """Update SLAM with new camera frame."""
        self.pose, self.map = self.slam.process_frame(frame)
        return self.pose, self.map

# Integration point
class StateMachine:
    def _sense_update(self):
        if self.use_slam:
            frame = self.camera.capture()
            self.slam.update(frame)
            self.map = self.slam.map
        
        # Existing vision pipeline
        detections = self.vision.detect_objects(frame)
```

---

## 4. Complete Data Flow Diagram

### 4.1 Mission Execution Flow

```
User Input
  │
  ▼
┌────────────────────────────────┐
│ agent.run_mission(prompt)      │
│ "Find red cube and pick it up" │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ LLM Call 1: Claude                     │
│ Input: system_prompt + tools           │
│ Output: tool_use("detect_objects")     │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ MCP Server: execute_tool()             │
│ Tool: detect_objects(["red_cube"])     │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ State Machine: SENSING state           │
│ ├─ Set goal: {"target_objects": [...]}│
│ └─ Poll for 1-3 seconds                │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ Hardware abstraction: get_status()     │
│ ├─ Run vision (YOLOv8)                 │
│ └─ Return detections                   │
└────────────┬───────────────────────────┘
             │ Return: [{"name": "red_cube", "position": [1.5, 0]}]
             │
             ▼
┌────────────────────────────────────────┐
│ MCP Tool returns to LLM                │
│ Result: {"detected": [...]}            │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ LLM Call 2: Claude                     │
│ Input: previous tools + results        │
│ Output: tool_use("navigate_to")        │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ MCP Server: navigate_to(x=1.5, y=0)   │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│ State Machine: NAVIGATING state        │
│ ├─ Set goal: {"target_position": [...]}│
│ └─ Poll for 30s or until arrival       │
└────────────┬───────────────────────────┘
             │ (Repeats: compute_control → update → check_arrival)
             │
             ▼
┌────────────────────────────────────────┐
│ Returns arrival confirmation           │
└────────────┬───────────────────────────┘
             │
             ▼ (... continue grasp → navigate → release ...)
             │
             ▼
┌────────────────────────────────────────┐
│ LLM Call N: Claude                     │
│ Output: "Successfully picked up..."    │
└────────────────────────────────────────┘
```

### 4.2 State Machine 60 Hz Loop

```
Entry Point: main_loop()
   │
   └─────────────────────────────────┐
            (repeat at 60 Hz)         │
                   ▼                  │
         ┌─────────────────┐          │
         │ state_machine   │          │
         │  .update()      │          │
         └────────┬────────┘          │
                  │                   │
         ┌────────▼──────────┐        │
         │ Current state?    │        │
         └────────┬──────────┘        │
                  │                   │
      ┌───────────┼───────────┬──────┐│
      │           │           │      ││
      ▼           ▼           ▼      ▼│
   [IDLE]   [NAVIGATING] [MANIPULATING] [SENSING]
      │           │           │      ││
      │    ┌──────▼────────┐  │      ││
      │    │ Compute PID   │  │      ││
      │    │ commands:     │  │      ││
      │    │ vel, omega    │  │      ││
      │    └──────┬────────┘  │      ││
      │           │           │      ││
      │    ┌──────▼──────────┐│      ││
      │    │ Check arrival   ││      ││
      │    │ if arrived →    ││      ││
      │    │  transition     ││      ││
      │    │  to IDLE        ││      ││
      │    └──────┬──────────┘│      ││
      └───────────┼───────────┼──────┘│
                  │           │       │
                  ▼           ▼       │
         ┌────────────────────┐       │
         │ controller.update()│       │
         │ ├─ integrate kinematics   │
         │ ├─ apply motor commands   │
         │ └─ update position        │
         └────────┬───────────┘       │
                  │                   │
                  └─────────────┬─────┘
                                │
                            sleep(16ms)
                            to maintain
                            60 Hz
```

---

## 5. Dependency Graph

### 5.1 Module Dependencies

```
merlin/
├── agent/
│   ├── base_agent.py
│   ├── claude_agent.py ──┐
│   ├── groq_agent.py ──┐ │ (depend on)
│   ├── gemini_agent.py─┤─┼──→ mcp/
│   ├── ollama_agent.py─┤ │    └─ server.py
│   └── __init__.py     │ │       └─ tools/
│                       └─┴──→ core/
│                              ├─ state_machine.py
│                              ├─ types.py
│                              └─ controller.py
│                                 └─ hardware/
│                                    ├─ mock.py
│                                    ├─ simulator.py
│                                    └─ xle_driver.py
│
├── mcp/
│   ├── server.py ───────────→ core/
│   ├── tools/
│   │   ├── base.py
│   │   ├── perception.py ───→ perception/
│   │   │                      └─ vision.py
│   │   └── action.py
│   └── schemas.py
│
├── core/
│   ├── state_machine.py ───→ hardware/
│   ├── controller.py
│   └── types.py
│
├── hardware/
│   ├── mock.py ──────────→ core/types.py
│   ├── simulator.py ─────→ mujoco (external)
│   ├── xle_driver.py ────→ requests (external)
│   └── __init__.py (factory)
│
├── perception/
│   ├── vision.py ────────→ ultralytics (external)
│   ├── odometry.py ──────→ numpy (external)
│   └── slam.py (optional)
│
└── missions/
    ├── find_object.py ──→ agent/
    ├── pick_and_place.py→ agent/
    └── multi_object.py ─→ agent/
```

### 5.2 External Dependencies

```
Core (Must Have)
├── anthropic==0.28.0      (Claude API)
├── python-dotenv==1.0.0   (Config)
└── pydantic==2.6.4        (Validation)

Multi-Agent (Required)
├── groq==0.9.0            (Groq API)
├── google-generativeai     (Gemini API)
└── requests==2.31.0       (HTTP)

Hardware Backends
├── Mock: None (uses stdlib)
├── MuJoCo: mujoco==3.1.5 + dm-control==1.0.17
├── ROS2: ros2 (future)
└── XLE: requests + network

Perception (Optional)
├── opencv-python==4.9.0.80 (Image processing)
├── ultralytics==8.1.34     (YOLOv8)
└── numpy==1.26.4           (Math)

Development
├── pytest==7.4.4
├── black (formatting)
├── mypy (type checking)
└── flake8 (linting)
```

---

## 6. Data Types Flow

### 6.1 Mission Input → Output

```
INPUT (str)
  │
  ├─→ "Find the red cube"
  │
  ▼
┌─────────────────────────┐
│ Agent Processing        │
│ Multiple LLM iterations │
└──────────┬──────────────┘
           │
           ├─→ Call MCP tools
           │   └─ Tool input: {"object_names": ["red_cube"]}
           │       Tool output: RobotToolResult(success=True, detected=[...])
           │
           ├─→ Tool input: {"x": 1.5, "y": 0.0}
           │       Tool output: RobotToolResult(success=True, final_position=[1.48, 0.02])
           │
           └─→ Tool input: {}
               Tool output: RobotToolResult(success=True, gripper_state="closed")
           │
           ▼
OUTPUT (str)
  │
  └─→ "Successfully picked up the red cube at position [1.48, 0.02]"
```

### 6.2 Tool Result JSON Format

```json
{
  "success": true,
  "status": {
    "position": [1.48, 0.02],
    "heading": 45.5,
    "battery": 92.3,
    "gripper_open": false,
    "detected_objects": [
      {
        "name": "red_cube",
        "position": [1.5, 0.0],
        "confidence": 0.95
      }
    ]
  },
  "message": "Operation completed successfully",
  "timing": {
    "execution_ms": 5234,
    "iterations": 315
  }
}
```

---

## 7. Integration Points

### 7.1 Adding ROS2 Backend (Future)

```python
# merlin/hardware/ros2_driver.py
import rclpy
from rclpy.node import Node

class ROS2Controller(RobotController):
    """ROS2-based hardware abstraction."""
    
    def __init__(self, node_name="merlin_controller"):
        rclpy.init()
        self.node = Node(node_name)
        
        # Publishers
        self.pub_cmd_vel = self.node.create_publisher(
            Twist, '/cmd_vel', 10
        )
        
        # Subscribers
        self.node.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )
    
    def update(self, delta_t=0.016):
        rclpy.spin_once(self.node, timeout_sec=0.001)
    
    def set_velocity(self, vel: float, omega: float):
        msg = Twist()
        msg.linear.x = vel
        msg.angular.z = omega
        self.pub_cmd_vel.publish(msg)

# Usage (drop-in replacement)
controller = create_controller("ros2")  # Just change backend!
```

### 7.2 Adding SLAM Module

```python
# In perception/vision.py, add:
from perception.slam import SLAMModule

class VisionPipeline:
    def __init__(self, use_slam=False):
        self.model = YOLO("yolov8n.pt")
        self.slam = SLAMModule() if use_slam else None
    
    def detect_objects(self, frame, object_names):
        if self.slam:
            pose, map_data = self.slam.update(frame)
            # Use map for better localization
        
        detections = self.model(frame)
        return self.process_detections(detections, object_names)
```

---

## 8. Recommendation: Quick Start Path

### For CalHacks 40-hour deadline:

**Hour 0-18: Core System**
```
1. State Machine (Hours 2-6) ✅
2. MCP Tools (Hours 8-12) ✅
3. Claude Agent (Hours 12-18) ✅
→ Full working system with mock backend
```

**Hour 18-25: Optional Enhancements**
```
4. MuJoCo Physics (Hours 18-20)
   └─ Realistic physics validation
5. Advanced Navigation (Hours 20-23)
   └─ TEB planner (if time)
6. Vision Integration (Hours 23-25)
   └─ YOLOv8 object detection
```

**Hour 25-40: Polish & Demo**
```
7. Edge cases & recovery (Hours 25-35)
8. Performance tuning (Hours 35-38)
9. Demo prep (Hours 38-40)
```

### Skip for Now (Add Later):
- ❌ ROS2 (2-3 day learning curve)
- ❌ Full SLAM (only for real robots)
- ❌ Distributed systems (single machine sufficient)

---

## 9. System Interaction Summary

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User ──(mission prompt)──→ Agent                         │
│                               │                            │
│                    (tool calls with args)                  │
│                               ▼                            │
│                          MCP Server                        │
│                               │                            │
│               ┌───────────────┼───────────────┐            │
│               ▼               ▼               ▼            │
│         (get_status)   (navigate_to)   (detect_objects)  │
│               │               │               │            │
│               └───────────────┼───────────────┘            │
│                               ▼                            │
│                        State Machine                       │
│                     (60 Hz update loop)                    │
│                               │                            │
│                  ┌────────────┼────────────┐               │
│                  ▼            ▼            ▼               │
│              Navigation  Perception  Manipulation          │
│                  │            │            │               │
│                  └────────────┼────────────┘               │
│                               ▼                            │
│                      Hardware Abstraction                  │
│                               │                            │
│          ┌────────────┬───────┼────────┬──────────┐       │
│          ▼            ▼       ▼        ▼          ▼       │
│        Mock       MuJoCo    ROS2*    XLE**   Other       │
│      (Instant)    (Sim)   (Future)  (Opt)    (Ext)       │
│          │            │       │        │          │       │
│          └────────────┴───────┼────────┴──────────┘       │
│                               ▼                            │
│                         Robot State                        │
│                    (position, velocity,                   │
│                     battery, gripper, etc)                │
│                               │                            │
│                    ┌──────────┴──────────┐                │
│                    ▼                     ▼                │
│              Back to Agent         Display/Log            │
│            (agent perceives)       (for user)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Performance Budget

| Component | Latency | Budget |
|-----------|---------|--------|
| State Machine cycle | 16ms | Must maintain 60 Hz |
| Navigation control computation | 5ms | <30% of cycle |
| Perception (vision) | 30-50ms | 2-3 cycles acceptable |
| MCP tool execution | 100-500ms | Varies by tool |
| Agent decision (LLM) | 1-10s | Async from state machine |
| **Total mission** | 30-300s | 40-hour duration acceptable |

---

This is your complete system architecture. Use it as a reference for integration decisions!
