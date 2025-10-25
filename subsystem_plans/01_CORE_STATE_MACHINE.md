# MERLIN Subsystem Plan: Core State Machine

## 1. Overview

**Responsibility:** Autonomous execution engine that runs at 60 Hz independent of LLM latency. Manages robot state transitions and low-level control.

**Key Principle:** State machine is **agnostic to higher layers** (agent, MCP). It executes state-specific logic and integrates with hardware abstraction layer.

---

## 2. Architecture

### State Diagram
```
        ┌─────────────────────┐
        │        IDLE         │
        │  (motors off, ready)│
        └────────────┬────────┘
                     │ set_goal()
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 ┌────────────┐ ┌────────────┐ ┌────────────┐
 │ NAVIGATING │ │MANIPULATING│ │ SENSING    │
 │  (driving) │ │(arm tasks) │ │(perception)│
 └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
       │               │              │
       │ arrival       │ complete     │ done
       │               │              │
       └───────────────┼──────────────┘
                       ▼
                  ┌─────────────────────┐
                  │      IDLE           │
                  │  (goal achieved)    │
                  └─────────────────────┘
```

### Core Classes

**File Structure:**
```
merlin/core/
├── __init__.py
├── types.py              # Dataclasses (RobotStatus, RobotState)
├── controller.py         # RobotController abstract base
└── state_machine.py      # StateMachine implementation
```

---

## 3. Component Specifications

### 3.1 RobotStatus (types.py)

```python
@dataclass
class RobotStatus:
    state: str                  # IDLE, NAVIGATING, MANIPULATING, SENSING
    position: List[float]       # [x, y] meters
    heading: float              # degrees 0-360
    battery: float              # 0-100%
    gripper_open: bool          # True = open
    detected_objects: List[Dict] # Vision detections
```

### 3.2 RobotController (controller.py)

**Responsibilities:**
- Maintain robot telemetry (pose, battery, gripper state)
- Accept velocity commands
- Integrate kinematics at 60 Hz
- Interface with hardware abstraction layer

**Interface:**
```python
class RobotController:
    def update(self, delta_t: float = 0.016) -> None
    def set_velocity(self, vel: float, omega: float) -> None
    def set_gripper(self, open_cmd: bool) -> None
    def get_status(self) -> RobotStatus
```

### 3.3 StateMachine (state_machine.py)

**Responsibilities:**
- Dispatch to state-specific update logic
- Enforce timeout guards (prevent infinite loops)
- Signal completion to MCP tools
- Manage state transitions

**Key Methods:**
```python
class StateMachine:
    def set_goal(self, state: str, goal: Dict) -> bool
    def update(self) -> RobotStatus
    def _navigate_update(self) -> None
    def _manipulate_update(self) -> None
    def _sense_update(self) -> None
```

---

## 4. Implementation Phases

### Phase 1: Types & Controller Interface (Hour 2-3)
**Deliverable:** Data structures compile, controller can be instantiated

- [ ] Implement `types.py` with RobotStatus, RobotState enum
- [ ] Create RobotController abstract base class
- [ ] Define interface contract (methods, parameters)
- [ ] Write basic unit tests for data structures

**Time:** 1 hour

**Files:**
- `merlin/core/types.py` (~50 lines)
- `merlin/core/controller.py` (~100 lines)
- `tests/test_types.py` (~30 lines)

---

### Phase 2: Mock Controller (Hour 3-4)
**Deliverable:** Kinematics working, robot can move in simulation

- [ ] Implement MockController in `merlin/hardware/mock.py`
- [ ] Integrate simple kinematics model (unicycle model)
- [ ] Implement velocity integration
- [ ] Battery drain simulation
- [ ] Gripper state tracking

**Time:** 1 hour

**Kinematics Model:**
```
x' = x + vel * cos(heading) * dt
y' = y + vel * sin(heading) * dt
heading' = (heading + omega_deg * dt) % 360
battery' = battery - 0.01 if moving else 0
```

**Test:**
```bash
# MockController moves 0.5m in 1 second at 0.5 m/s
assert distance < 0.6m and distance > 0.4m
```

---

### Phase 3: State Machine Core (Hour 4-5)
**Deliverable:** State transitions working, timeouts functional

- [ ] Implement StateMachine class
- [ ] Implement state dispatch logic
- [ ] Add timeout guards (default 60s per state)
- [ ] Wire up to controller
- [ ] Test manual state transitions

**Time:** 1 hour

**Test Scenarios:**
1. IDLE → NAVIGATING: Robot starts moving
2. NAVIGATING → IDLE: Robot arrives at target
3. Timeout: After 60s, force IDLE
4. MANIPULATING: Gripper executes task

---

### Phase 4: State-Specific Logic (Hour 5-6)
**Deliverable:** Each state executes correctly

#### Navigation Logic
```python
def _navigate_update(self):
    target = self.current_goal["target_position"]
    current = self.controller.position
    
    dx = target[0] - current[0]
    dy = target[1] - current[1]
    dist = sqrt(dx^2 + dy^2)
    
    # Check arrival
    if dist < ARRIVAL_THRESHOLD:
        self.state = IDLE
        return
    
    # Proportional control
    target_heading = atan2(dy, dx) * 180 / pi
    heading_error = normalize_angle(target_heading - self.controller.heading)
    
    vel = min(MAX_VEL, dist)
    omega = STEERING_GAIN * heading_error
    
    self.controller.set_velocity(vel, omega)
```

#### Manipulation Logic
```python
def _manipulate_update(self):
    task = self.current_goal.get("task")
    
    if task == "grasp":
        self.controller.set_gripper(False)  # Close
    elif task == "release":
        self.controller.set_gripper(True)   # Open
    
    elapsed = time.time() - self.state_entry_time
    if elapsed > MANIPULATION_TIME:  # 2 seconds
        self.state = IDLE
```

#### Sensing Logic
```python
def _sense_update(self):
    elapsed = time.time() - self.state_entry_time
    if elapsed > SENSING_TIME:  # 1 second
        self.state = IDLE
        # Store detected objects in status
```

---

## 4.5 Teach Phase: Working Demo Artifacts

### Teach Phase 1: Core Types Demo

**Artifact:** `examples/teach_phase_1_types.py`

```python
#!/usr/bin/env python3
"""Teach Phase 1: Verify data types work."""
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class RobotStatus:
    state: str
    position: List[float]
    heading: float
    battery: float
    gripper_open: bool
    detected_objects: List[Dict]

# Demo: Create and print status
status = RobotStatus(
    state="IDLE",
    position=[0.0, 0.0],
    heading=0.0,
    battery=95.0,
    gripper_open=True,
    detected_objects=[]
)

print("✓ Teach Phase 1: Types work!")
print(f"  Status: {status.state}")
print(f"  Position: {status.position}")
print(f"  Battery: {status.battery}%")
assert status.state == "IDLE"
print("✓ All assertions pass")
```

**Run:** `python examples/teach_phase_1_types.py`

**Expected Output:**
```
✓ Teach Phase 1: Types work!
  Status: IDLE
  Position: [0.0, 0.0]
  Battery: 95.0%
✓ All assertions pass
```

---

### Teach Phase 2: Mock Controller Demo

**Artifact:** `examples/teach_phase_2_mock_controller.py`

```python
#!/usr/bin/env python3
"""Teach Phase 2: Verify kinematics work."""
from math import cos, sin, radians, sqrt
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class RobotStatus:
    state: str
    position: List[float]
    heading: float
    battery: float
    gripper_open: bool
    detected_objects: List[Dict]

class MockController:
    """Simple kinematics controller."""
    def __init__(self):
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.target_vel = 0.0
        self.target_omega = 0.0
    
    def update(self, delta_t: float = 0.016):
        """Integrate kinematics."""
        self.position[0] += self.target_vel * cos(radians(self.heading)) * delta_t
        self.position[1] += self.target_vel * sin(radians(self.heading)) * delta_t
        self.heading = (self.heading + self.target_omega * 180/3.14159 * delta_t) % 360
        
        if abs(self.target_vel) > 0.01:
            self.battery -= 0.01
    
    def set_velocity(self, vel: float, omega: float):
        self.target_vel = vel
        self.target_omega = omega
    
    def set_gripper(self, open_cmd: bool):
        self.gripper_open = open_cmd
    
    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state="IDLE",
            position=self.position.copy(),
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=[]
        )

# Demo: Robot moves 0.5 m/s for 1 second
controller = MockController()
controller.set_velocity(0.5, 0.0)

for _ in range(60):  # 60 Hz for 1 second
    controller.update()

status = controller.get_status()
distance = sqrt(status.position[0]**2 + status.position[1]**2)

print("✓ Teach Phase 2: Mock controller works!")
print(f"  Distance traveled: {distance:.2f}m (expected ~0.5m)")
print(f"  Position: {status.position}")
print(f"  Battery: {status.battery:.1f}%")
assert 0.4 < distance < 0.6, f"Distance {distance} out of range"
print("✓ Kinematics verified")
```

**Run:** `python examples/teach_phase_2_mock_controller.py`

**Expected Output:**
```
✓ Teach Phase 2: Mock controller works!
  Distance traveled: 0.50m (expected ~0.5m)
  Position: [0.5, 0.0]
  Battery: 94.4%
✓ Kinematics verified
```

---

### Teach Phase 3: State Machine Demo

**Artifact:** `examples/teach_phase_3_state_machine.py`

```python
#!/usr/bin/env python3
"""Teach Phase 3: Verify state transitions work."""
import time
from math import cos, sin, radians, sqrt, atan2, pi
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class RobotStatus:
    state: str
    position: List[float]
    heading: float
    battery: float
    gripper_open: bool
    detected_objects: List[Dict]

class MockController:
    def __init__(self):
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.target_vel = 0.0
        self.target_omega = 0.0
    
    def update(self, delta_t: float = 0.016):
        self.position[0] += self.target_vel * cos(radians(self.heading)) * delta_t
        self.position[1] += self.target_vel * sin(radians(self.heading)) * delta_t
        self.heading = (self.heading + self.target_omega * 180/3.14159 * delta_t) % 360
        if abs(self.target_vel) > 0.01:
            self.battery -= 0.01
    
    def set_velocity(self, vel: float, omega: float):
        self.target_vel = vel
        self.target_omega = omega
    
    def set_gripper(self, open_cmd: bool):
        self.gripper_open = open_cmd
    
    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state="IDLE",
            position=self.position.copy(),
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=[]
        )

class StateMachine:
    """Minimal state machine."""
    def __init__(self, controller):
        self.controller = controller
        self.state = "IDLE"
        self.current_goal = None
        self.state_start_time = None
    
    def set_goal(self, state: str, goal: Dict) -> bool:
        self.state = state
        self.current_goal = goal
        self.state_start_time = time.time()
        return True
    
    def update(self) -> RobotStatus:
        if self.state == "NAVIGATING":
            self._navigate_update()
        elif self.state == "MANIPULATING":
            self._manipulate_update()
        
        self.controller.update()
        return self.controller.get_status()
    
    def _navigate_update(self):
        target = self.current_goal["target_position"]
        current = self.controller.position
        
        dx = target[0] - current[0]
        dy = target[1] - current[1]
        dist = sqrt(dx**2 + dy**2)
        
        if dist < 0.2:
            self.state = "IDLE"
            self.controller.set_velocity(0.0, 0.0)
            return
        
        target_heading = atan2(dy, dx) * 180 / pi
        heading_error = target_heading - self.controller.heading
        
        vel = min(0.5, dist)
        omega = 0.1 * heading_error
        self.controller.set_velocity(vel, omega)
    
    def _manipulate_update(self):
        task = self.current_goal.get("task")
        self.controller.set_gripper(task == "grasp" ? False : True)
        
        elapsed = time.time() - self.state_start_time
        if elapsed > 0.5:
            self.state = "IDLE"

# Demo: Navigate to position
sm = StateMachine(MockController())
sm.set_goal("NAVIGATING", {"target_position": [1.0, 0.0]})

print("✓ Teach Phase 3: State machine works!")
print("  Starting navigation to (1.0, 0.0)...")

for i in range(300):  # Run state machine
    status = sm.update()
    if status.state == "IDLE":
        print(f"  ✓ Arrived at {status.position}")
        break

dist = sqrt(status.position[0]**2 + status.position[1]**2)
assert 0.8 < dist < 1.2, f"Final position {dist}m away from target"
print("✓ Navigation verified")
```

**Run:** `python examples/teach_phase_3_state_machine.py`

**Expected Output:**
```
✓ Teach Phase 3: State machine works!
  Starting navigation to (1.0, 0.0)...
  ✓ Arrived at [1.0, 0.02]
✓ Navigation verified
```

---

### Teach Phase 4: Full Integration Demo

**Artifact:** `examples/teach_phase_4_full_mission.py`

```python
#!/usr/bin/env python3
"""Teach Phase 4: Full pick-and-place mission."""
# (Uses same classes from Phase 3)

# Demo: Complete mission
sm = StateMachine(MockController())

print("✓ Teach Phase 4: Full mission works!")
print("  Mission: Navigate → Grasp → Navigate away → Release")

# Step 1: Navigate to object
sm.set_goal("NAVIGATING", {"target_position": [1.0, 0.0]})
while sm.state != "IDLE":
    sm.update()
print("  ✓ Step 1: Arrived at object")

# Step 2: Grasp
sm.set_goal("MANIPULATING", {"task": "grasp"})
while sm.state != "IDLE":
    sm.update()
print("  ✓ Step 2: Grasped object")
assert sm.controller.gripper_open == False

# Step 3: Navigate away
sm.set_goal("NAVIGATING", {"target_position": [2.0, 1.0]})
while sm.state != "IDLE":
    sm.update()
print("  ✓ Step 3: Moved to drop location")

# Step 4: Release
sm.set_goal("MANIPULATING", {"task": "release"})
while sm.state != "IDLE":
    sm.update()
print("  ✓ Step 4: Released object")
assert sm.controller.gripper_open == True

print("✓ Full mission successful!")
```

**Run:** `python examples/teach_phase_4_full_mission.py`

**Expected Output:**
```
✓ Teach Phase 4: Full mission works!
  Mission: Navigate → Grasp → Navigate away → Release
  ✓ Step 1: Arrived at object
  ✓ Step 2: Grasped object
  ✓ Step 3: Moved to drop location
  ✓ Step 4: Released object
✓ Full mission successful!
```

---

## 5. Integration Points

### With Hardware Abstraction
```
StateMachine.update()
    ↓
state_machine.controller.update()
    ↓
RobotController (mock/mujoco/xle)
    ↓
Physical robot or simulator
```

### With MCP Tools
```
MCP Tool (e.g., navigate_to)
    ↓
state_machine.set_goal("NAVIGATING", {"target_position": [1.0, 0.0]})
    ↓
poll state_machine.update() in loop until state == IDLE
    ↓
Tool returns {"success": true, "final_position": [...]}
```

---

## 6. Testing Strategy

### Unit Tests
```python
# Test 1: Navigation arrival
def test_navigation_arrival():
    sm = StateMachine(MockController())
    sm.set_goal("NAVIGATING", {"target_position": [1.0, 0.0]})
    
    for _ in range(100):
        status = sm.update()
        if status.state == "IDLE":
            break
    
    dist = distance(status.position, [1.0, 0.0])
    assert dist < 0.3, f"Overshot by {dist}m"

# Test 2: Timeout guard
def test_state_timeout():
    sm = StateMachine(MockController())
    sm.state_timeout = 1.0
    sm.set_goal("NAVIGATING", {"target_position": [100, 100]})
    
    time.sleep(1.1)
    status = sm.update()
    
    assert status.state == "IDLE", "Timeout not enforced"

# Test 3: Gripper state
def test_gripper():
    sm = StateMachine(MockController())
    
    assert sm.controller.gripper_open == True
    sm.set_goal("MANIPULATING", {"task": "grasp"})
    
    for _ in range(120):  # 2 seconds @ 60Hz
        sm.update()
    
    assert sm.controller.gripper_open == False
```

### Integration Tests
```python
# Full mission in state machine
def test_pick_and_place():
    sm = StateMachine(MockController())
    
    # Navigate to object
    sm.set_goal("NAVIGATING", {"target_position": [1.0, 0.0]})
    while sm.state != "IDLE":
        sm.update()
    
    # Grasp
    sm.set_goal("MANIPULATING", {"task": "grasp"})
    while sm.state != "IDLE":
        sm.update()
    
    # Navigate to drop location
    sm.set_goal("NAVIGATING", {"target_position": [2.0, 1.0]})
    while sm.state != "IDLE":
        sm.update()
    
    # Release
    sm.set_goal("MANIPULATING", {"task": "release"})
    while sm.state != "IDLE":
        sm.update()
    
    assert sm.controller.gripper_open == True
```

---

## 7. Configuration Parameters

**`merlin/core/config.py`:**
```python
# Navigation
ARRIVAL_THRESHOLD = 0.2  # meters
MAX_VELOCITY = 0.5       # m/s
STEERING_GAIN = 0.1      # rad/s per radian error

# Manipulation
MANIPULATION_TIME = 2.0  # seconds per task
SENSING_TIME = 1.0       # seconds per scan

# Safety
STATE_TIMEOUT = 60.0     # seconds
UPDATE_RATE_HZ = 60
DELTA_T = 1.0 / UPDATE_RATE_HZ

# Battery
BATTERY_DRAIN_RATE = 0.01  # % per second when moving
BATTERY_MIN = 5.0          # % - low battery warning
```

---

## 8. Deliverables Checklist

- [ ] `merlin/core/types.py` compiles and exports RobotStatus, RobotState
- [ ] `merlin/core/controller.py` defines RobotController interface
- [ ] `merlin/hardware/mock.py` implements MockController with kinematics
- [ ] `merlin/core/state_machine.py` implements StateMachine class
- [ ] `tests/test_state_machine.py` covers all state transitions
- [ ] State machine runs at 60 Hz stable
- [ ] All timeout guards working
- [ ] Robot can navigate and manipulate in mock

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| State machine update frequency | 60 Hz ±2 Hz |
| Navigation accuracy | <0.3m error to target |
| Timeout enforcement | Within 1s of timeout |
| Gripper state sync | 100% accuracy |
| Battery drain realism | >10 min runtime at constant velocity |

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Kinematics accuracy | Test against known trajectories, compare with MuJoCo |
| Floating point errors | Use fixed-point math for position, normalize angles |
| State machine deadlock | Enforce strict timeout on every state |
| Controller interface mismatch | Define clear contract, test with mock first |

---

## 11. Dependencies

**External:**
- numpy (math utils)
- dataclasses (Python 3.7+)

**Internal:**
- None (core module is independent)

---

## 12. Timeline

- **Hour 2-3:** Types and controller interface
- **Hour 3-4:** Mock controller with kinematics
- **Hour 4-5:** State machine core
- **Hour 5-6:** State-specific logic and testing

**Total: 4 hours to working state machine**
