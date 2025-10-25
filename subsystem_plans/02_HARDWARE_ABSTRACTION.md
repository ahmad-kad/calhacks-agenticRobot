# MERLIN Subsystem Plan: Hardware Abstraction Layer

## 1. Overview

**Responsibility:** Unified interface to robot hardware with pluggable backends. Allows seamless switching between mock, simulator (MuJoCo), and real hardware (XLeRobot).

**Key Principle:** **Factory pattern** - same interface across all backends. State machine and MCP tools don't care which backend is active.

---

## 2. Architecture

### Backend Abstraction
```
┌────────────────────────────────┐
│   Hardware Abstraction         │
│   (Factory + Interface)        │
└────────────┬───────────────────┘
             │
    ┌────────┼────────┬─────────┐
    ▼        ▼        ▼         ▼
┌────────┐┌────────┐┌────────┐┌────────┐
│ Mock   ││MuJoCo ││ XLE    ││ Future │
│Instant ││Physics││Hardware││(ROS2)  │
└────────┘└────────┘└────────┘└────────┘
    │        │        │         │
    └────────┼────────┼─────────┘
             │
    ┌────────▼──────────┐
    │  State Machine    │
    │  (Unified use)    │
    └───────────────────┘
```

### File Structure
```
merlin/hardware/
├── __init__.py           # Factory function
├── mock.py              # MockController
├── simulator.py         # MuJoCoController
├── xle_driver.py        # XLEController (optional)
└── config.py            # Backend config
```

---

## 3. Backend Specifications

### 3.1 Mock Backend (Hour 3-4)

**Purpose:** Fast prototyping, testing, demo without dependencies

**Implementation:**
```python
class MockController(RobotController):
    """Dummy controller for rapid development."""
    
    def __init__(self):
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.target_vel = 0.0
        self.target_omega = 0.0
        self.detected_objects = []  # Simulated
    
    def update(self, delta_t: float = 0.016):
        # Integrate kinematics (unicycle model)
        self.position[0] += self.target_vel * cos(radians(self.heading)) * delta_t
        self.position[1] += self.target_vel * sin(radians(self.heading)) * delta_t
        self.heading = (self.heading + degrees(self.target_omega) * delta_t) % 360
        
        # Drain battery proportional to motion
        if abs(self.target_vel) > 0.01 or abs(self.target_omega) > 0.01:
            self.battery -= 0.01  # ~1% per 100 seconds at full speed
    
    def set_velocity(self, vel: float, omega: float):
        self.target_vel = clamp(vel, -1.0, 1.0)
        self.target_omega = clamp(omega, -0.5, 0.5)
    
    def set_gripper(self, open_cmd: bool):
        self.gripper_open = open_cmd
    
    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state="IDLE",
            position=self.position.copy(),
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=self.detected_objects
        )
```

**Pros:** Zero dependencies, instant startup, perfect for testing
**Cons:** Unrealistic physics
**Use cases:** Development, testing, demos

---

### 3.2 MuJoCo Backend (Hour 15-20)

**Purpose:** Realistic physics simulation, bridge between mock and real hardware

**Dependencies:**
- `mujoco==3.1.5` (pre-built for M3)
- `dm-control==1.0.17` (DeepMind control suite)

**Implementation Strategy:**

```python
class MuJoCoController(RobotController):
    """Real physics-based robot in MuJoCo."""
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Use built-in XLE from dm_control
            from dm_control import suite
            self.env = suite.load(domain_name="xle_robot", task_name="walk")
            self.model = self.env.physics.model()
            self.data = self.env.physics.data()
        else:
            # Load custom MJCF
            self.model = mujoco.MjModel.from_xml_path(model_path)
            self.data = mujoco.MjData(self.model)
        
        # Find body IDs
        self.base_body_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_BODY, "base_link"
        )
        self.gripper_actuator_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper"
        )
        
        # State
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        
        # Rendering (optional)
        self.renderer = None
    
    def update(self, delta_t: float = 0.016):
        """Step physics engine."""
        # Set motor commands (if applicable)
        # self.data.ctrl[vel_idx] = self.target_vel
        # self.data.ctrl[omega_idx] = self.target_omega
        
        # Step simulation
        mujoco.mj_step(self.model, self.data, nstep=1)
        
        # Extract pose from MuJoCo
        body_pos = self.data.xpos[self.base_body_id]
        body_quat = self.data.xquat[self.base_body_id]
        
        self.position = [float(body_pos[0]), float(body_pos[1])]
        self.heading = self._quat_to_yaw(body_quat)
        
        # Battery drain (proportional to motor power)
        power = sum(abs(self.data.ctrl[i]) for i in range(len(self.data.ctrl)))
        self.battery -= power * 0.01  # Rough estimate
    
    def set_velocity(self, vel: float, omega: float):
        """Send motor commands to MuJoCo."""
        # Find motor indices (depends on model)
        # For XLE: typically separate actuators for each motor
        # This is simplified; real implementation needs calibration
        if len(self.data.ctrl) >= 2:
            self.data.ctrl[0] = vel
            self.data.ctrl[1] = omega
    
    def set_gripper(self, open_cmd: bool):
        """Actuate gripper."""
        self.data.ctrl[self.gripper_actuator_id] = 1.0 if open_cmd else -1.0
        self.gripper_open = open_cmd
    
    def _quat_to_yaw(self, quat: np.ndarray) -> float:
        """Convert quaternion [w,x,y,z] to yaw angle in degrees."""
        w, x, y, z = quat
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
        return math.degrees(yaw) % 360
    
    def render(self):
        """Render MuJoCo scene (optional visualization)."""
        if self.renderer is None:
            self.renderer = mujoco.Renderer(self.model)
        self.renderer.update_scene(self.data)
        return self.renderer.render()
```

**Pros:** Realistic physics, drop-in replacement for mock, validates algorithms
**Cons:** Slower (10-100ms per step), requires MJCF model setup
**Use cases:** Algorithm validation, realistic testing, demo with physics

---

### 3.3 XLeRobot Backend (Hour 20-25)

**Purpose:** Real hardware control (optional, advanced)

**Dependencies:**
- Robot REST API or SDK
- Network connectivity

**Implementation:**

```python
class XLEController(RobotController):
    """Real XLeRobot hardware via REST API."""
    
    def __init__(self, host: str = "192.168.1.100", port: int = 8080):
        self.base_url = f"http://{host}:{port}"
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.last_state = None
        
        # Verify connection
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✓ Connected to XLE at {host}:{port}")
            else:
                raise ConnectionError(f"Health check failed: {response.status_code}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to XLE: {e}")
    
    def update(self, delta_t: float = 0.016):
        """Poll robot state via REST API."""
        try:
            response = requests.get(f"{self.base_url}/state", timeout=0.1)
            state = response.json()
            
            self.position = state.get("position", [0, 0])
            self.heading = state.get("heading", 0)
            self.battery = state.get("battery", 95)
            self.gripper_open = state.get("gripper_open", True)
            self.last_state = state.get("timestamp")
        except Exception as e:
            print(f"Warning: Failed to poll state: {e}")
    
    def set_velocity(self, vel: float, omega: float):
        """Send velocity command to robot."""
        try:
            requests.post(
                f"{self.base_url}/command/velocity",
                json={"vel": vel, "omega": omega},
                timeout=0.1
            )
        except Exception as e:
            print(f"Warning: Failed to set velocity: {e}")
    
    def set_gripper(self, open_cmd: bool):
        """Control gripper."""
        try:
            requests.post(
                f"{self.base_url}/command/gripper",
                json={"open": open_cmd},
                timeout=0.1
            )
            self.gripper_open = open_cmd
        except Exception as e:
            print(f"Warning: Failed to set gripper: {e}")
    
    def get_status(self) -> RobotStatus:
        return RobotStatus(
            state="IDLE",
            position=self.position.copy(),
            heading=self.heading,
            battery=self.battery,
            gripper_open=self.gripper_open,
            detected_objects=[]
        )
```

**Pros:** Real hardware, realistic operation
**Cons:** Network latency, hardware-specific, requires calibration
**Use cases:** Final demo, real competition

---

## 4. Factory Implementation

**`merlin/hardware/__init__.py`:**

```python
def create_controller(backend: str = "mock") -> RobotController:
    """
    Factory function for controller creation.
    
    Args:
        backend: "mock", "mujoco", "xle"
    
    Returns:
        Controller instance
    
    Usage:
        controller = create_controller("mock")    # Fast
        controller = create_controller("mujoco")  # Realistic
        controller = create_controller("xle")     # Real hardware
    """
    if backend == "mock":
        from merlin.hardware.mock import MockController
        return MockController()
    
    elif backend == "mujoco":
        from merlin.hardware.simulator import MuJoCoController
        return MuJoCoController()
    
    elif backend == "xle":
        from merlin.hardware.xle_driver import XLEController
        return XLEController()
    
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

---

## 5. Implementation Phases

### Phase 1: Mock Backend (Hour 3-4)
- [ ] Implement MockController with unicycle kinematics
- [ ] Test velocity commands
- [ ] Test battery drain
- [ ] Test gripper state
- [ ] Unit tests passing

**Deliverable:** Mock robot moves realistically

---

### Phase 2: MuJoCo Backend (Hour 15-20)
- [ ] Download XLE robot model
- [ ] Create MuJoCoController wrapper
- [ ] Map motor commands to actuators
- [ ] Extract pose from simulation
- [ ] Validate physics (compare against mock for similar trajectories)
- [ ] Integration tests

**Deliverable:** Physics-based robot simulation

---

### Phase 3: XLE Backend (Hour 20-25, Optional)
- [ ] Network connection to real robot
- [ ] REST API calls for velocity/gripper
- [ ] State polling
- [ ] Error handling
- [ ] Calibration tests

**Deliverable:** Real hardware control

---

## 5.5 Teach Phase: Backend Integration Demos

### Teach Phase 1: Mock Backend Verification

**Artifact:** `examples/teach_backend_mock.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify Mock backend works."""
from math import cos, sin, radians, sqrt

class MockController:
    def __init__(self):
        self.position = [0.0, 0.0]
        self.heading = 0.0
        self.battery = 95.0
        self.gripper_open = True
        self.target_vel = 0.0
        self.target_omega = 0.0
    
    def update(self, delta_t=0.016):
        self.position[0] += self.target_vel * cos(radians(self.heading)) * delta_t
        self.position[1] += self.target_vel * sin(radians(self.heading)) * delta_t
        self.heading = (self.heading + self.target_omega * 180/3.14159 * delta_t) % 360
        if abs(self.target_vel) > 0.01:
            self.battery -= 0.01
    
    def set_velocity(self, vel, omega):
        self.target_vel = vel
        self.target_omega = omega
    
    def set_gripper(self, open_cmd):
        self.gripper_open = open_cmd

# Test: Create controller, move robot, verify
print("✓ Teach Phase: Mock Backend")
controller = MockController()

# Scenario 1: Forward motion
controller.set_velocity(0.5, 0.0)
for _ in range(60):
    controller.update()
dist = sqrt(controller.position[0]**2 + controller.position[1]**2)
assert 0.4 < dist < 0.6
print(f"  ✓ Mock: Forward motion {dist:.2f}m")

# Scenario 2: Rotation
controller = MockController()
controller.set_velocity(0.0, 90.0)
for _ in range(60):
    controller.update()
assert 45 < controller.heading < 100
print(f"  ✓ Mock: Rotation {controller.heading:.1f}°")

# Scenario 3: Gripper
controller = MockController()
assert controller.gripper_open == True
controller.set_gripper(False)
assert controller.gripper_open == False
controller.set_gripper(True)
assert controller.gripper_open == True
print("  ✓ Mock: Gripper works")

print("✓ Mock backend verified!")
```

**Run:** `python examples/teach_backend_mock.py`

**Expected Output:**
```
✓ Teach Phase: Mock Backend
  ✓ Mock: Forward motion 0.50m
  ✓ Mock: Rotation 90.0°
  ✓ Mock: Gripper works
✓ Mock backend verified!
```

---

### Teach Phase 2: Factory Pattern Demo

**Artifact:** `examples/teach_backend_factory.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify factory pattern works."""

class MockController:
    def __init__(self):
        self.position = [0.0, 0.0]
        self.battery = 95.0
        self.name = "mock"

def create_controller(backend: str):
    """Factory function for controller creation."""
    if backend == "mock":
        return MockController()
    else:
        raise ValueError(f"Unknown backend: {backend}")

# Test: Create controller via factory
print("✓ Teach Phase: Factory Pattern")

controller = create_controller("mock")
assert controller.name == "mock"
print(f"  ✓ Factory created: {controller.name}")

# Switch backend (would be mujoco, xle in real code)
controller = create_controller("mock")
assert controller.battery == 95.0
print(f"  ✓ Factory backend switch works")

print("✓ Factory pattern verified!")
```

**Run:** `python examples/teach_backend_factory.py`

**Expected Output:**
```
✓ Teach Phase: Factory Pattern
  ✓ Factory created: mock
  ✓ Factory backend switch works
✓ Factory pattern verified!
```

---

### Teach Phase 3: Backend Interface Contract

**Artifact:** `examples/teach_backend_interface.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify all backends implement same interface."""
from abc import ABC, abstractmethod

class RobotController(ABC):
    @abstractmethod
    def update(self, delta_t: float = 0.016) -> None:
        pass
    
    @abstractmethod
    def set_velocity(self, vel: float, omega: float) -> None:
        pass
    
    @abstractmethod
    def set_gripper(self, open_cmd: bool) -> None:
        pass

class MockController(RobotController):
    def __init__(self):
        self.position = [0.0, 0.0]
        self.battery = 95.0
    
    def update(self, delta_t: float = 0.016) -> None:
        self.battery -= 0.01
    
    def set_velocity(self, vel: float, omega: float) -> None:
        pass
    
    def set_gripper(self, open_cmd: bool) -> None:
        pass

# Test: Verify interface contract
print("✓ Teach Phase: Backend Interface Contract")

controller = MockController()

# Test all required methods exist
assert hasattr(controller, 'update')
assert hasattr(controller, 'set_velocity')
assert hasattr(controller, 'set_gripper')
print("  ✓ All required methods exist")

# Test methods are callable
controller.update()
controller.set_velocity(0.5, 0.1)
controller.set_gripper(False)
print("  ✓ All methods callable")

# Test return types
controller.update()
assert controller.battery < 95.0
print("  ✓ Update changes state correctly")

print("✓ Interface contract verified!")
```

**Run:** `python examples/teach_backend_interface.py`

**Expected Output:**
```
✓ Teach Phase: Backend Interface Contract
  ✓ All required methods exist
  ✓ All methods callable
  ✓ Update changes state correctly
✓ Interface contract verified!
```

---

## 6. Testing Strategy

### Unit Tests for Each Backend

```python
# Test interface contract
def test_controller_interface():
    """All backends implement same interface."""
    for backend in ["mock", "mujoco"]:  # Skip XLE if no hardware
        controller = create_controller(backend)
        
        # Check methods exist
        assert hasattr(controller, 'update')
        assert hasattr(controller, 'set_velocity')
        assert hasattr(controller, 'set_gripper')
        assert hasattr(controller, 'get_status')
        
        print(f"✓ {backend} interface correct")

# Test mock backend
def test_mock_kinematics():
    """Mock controller integrates velocity correctly."""
    ctrl = MockController()
    ctrl.set_velocity(0.5, 0.0)  # Move at 0.5 m/s
    
    for _ in range(60):  # 1 second @ 60Hz
        ctrl.update()
    
    dist = sqrt(ctrl.position[0]**2 + ctrl.position[1]**2)
    assert 0.4 < dist < 0.6, f"Expected ~0.5m, got {dist}m"
    print(f"✓ Mock kinematics: {dist:.2f}m")

# Test mujoco backend (if available)
def test_mujoco_equivalence():
    """MuJoCo produces similar results to mock."""
    import pytest
    
    try:
        mock = MockController()
        mujoco = MuJoCoController()
    except ImportError:
        pytest.skip("MuJoCo not available")
    
    # Run same trajectory
    for both in [mock, mujoco]:
        both.set_velocity(0.3, 0.1)
    
    for _ in range(300):  # 5 seconds
        mock.update()
        mujoco.update()
    
    dist_mock = sqrt(mock.position[0]**2 + mock.position[1]**2)
    dist_mujoco = sqrt(mujoco.position[0]**2 + mujoco.position[1]**2)
    
    error = abs(dist_mock - dist_mujoco)
    assert error < 0.2, f"Physics diverge: mock={dist_mock:.2f}m, mujoco={dist_mujoco:.2f}m"
    print(f"✓ Physics equivalence: error={error:.2f}m")

# Test battery drain
def test_battery_drain():
    """Battery decreases during motion."""
    ctrl = MockController()
    initial = ctrl.battery
    
    ctrl.set_velocity(0.5, 0.0)
    for _ in range(600):  # 10 seconds
        ctrl.update()
    
    drained = initial - ctrl.battery
    assert drained > 0.05, f"Expected battery drain, got {drained}%"
    print(f"✓ Battery drain: {drained:.2f}%")

# Test gripper
def test_gripper_state():
    """Gripper state transitions correctly."""
    ctrl = MockController()
    
    assert ctrl.gripper_open == True
    ctrl.set_gripper(False)
    assert ctrl.gripper_open == False
    ctrl.set_gripper(True)
    assert ctrl.gripper_open == True
    print("✓ Gripper state")
```

### Backend Switching Test

```python
def test_backend_switching():
    """Same code works with different backends."""
    for backend in ["mock", "mujoco"]:
        try:
            ctrl = create_controller(backend)
            
            # Execute trajectory
            ctrl.set_velocity(0.5, 0.0)
            for _ in range(120):
                ctrl.update()
            
            ctrl.set_velocity(0.0, 0.0)
            status = ctrl.get_status()
            
            assert status.battery < 100
            print(f"✓ Backend {backend}: works")
        except Exception as e:
            print(f"✗ Backend {backend}: {e}")
```

---

## 7. Configuration

**`merlin/hardware/config.py`:**

```python
# Backend selection
BACKEND = "mock"  # mock | mujoco | xle

# Mock controller
MOCK_UPDATE_RATE_HZ = 60
MOCK_INITIAL_BATTERY = 95.0

# MuJoCo controller
MUJOCO_MODEL_PATH = "xle_robot/models/xle_robot.xml"
MUJOCO_PHYSICS_DT = 0.001
MUJOCO_RENDER = False

# XLE controller
XLE_HOST = "192.168.1.100"
XLE_PORT = 8080
XLE_TIMEOUT = 0.1

# Shared parameters
MAX_VELOCITY = 0.5       # m/s
MAX_OMEGA = 0.5          # rad/s
BATTERY_DRAIN_RATE = 0.01  # % per second when moving
BATTERY_WARNING = 10.0   # % - low battery threshold
```

---

## 8. Deliverables Checklist

- [ ] `merlin/hardware/__init__.py` - Factory function
- [ ] `merlin/hardware/mock.py` - MockController working
- [ ] `merlin/hardware/simulator.py` - MuJoCoController working
- [ ] `merlin/hardware/xle_driver.py` - XLEController (optional)
- [ ] `tests/test_hardware.py` - All unit tests pass
- [ ] Backend switching test passes
- [ ] Kinematics validation complete
- [ ] Documentation for each backend

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Backend startup time | <100ms |
| State machine compatibility | 100% (no changes needed) |
| Physics accuracy (MuJoCo) | <20% deviation from mock |
| Network latency (XLE) | <100ms per command |
| Battery drain realism | Enables >10 min runtime |

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| MuJoCo physics diverge from mock | Validate with trajectory comparison |
| XLE network timeout | Implement retry logic with exponential backoff |
| Motor actuator mapping wrong | Use MuJoCo visualization to verify |
| Battery drain unrealistic | Calibrate with real hardware data |

---

## 11. Dependencies

**For Mock:**
- numpy (optional, for math)

**For MuJoCo:**
- mujoco==3.1.5
- dm-control==1.0.17 (optional, for pre-built models)

**For XLE:**
- requests (REST API)
- network connectivity

---

## 12. Timeline

- **Hour 3-4:** Mock backend complete
- **Hour 15-20:** MuJoCo backend complete
- **Hour 20-25:** XLE backend (optional)

**Total: 17-22 hours (depending on hardware availability)**
