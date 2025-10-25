# MERLIN Subsystem Plan: MCP Server (Tool Registry & Execution)

## 1. Overview

**Responsibility:** Central registry and executor for all robot tools. Provides standardized interface for LLM agents to interact with state machine.

**Key Principle:** **No MCP tool ever calls state_machine directly.** Tools own state management, blocking logic, and result communication.

---

## 2. Architecture

### Tool Execution Flow
```
Agent (LLM)
    ↓
MCP Server.execute_tool("navigate_to", {x: 1.0, y: 0.0})
    ↓
ToolNavigateTo.execute(x=1.0, y=0.0)
    ├─ Calls state_machine.set_goal("NAVIGATING", {...})
    ├─ Polls state_machine.update() in loop
    ├─ Waits for state == IDLE
    └─ Returns {"success": true, "final_position": [...]}
    ↓
MCP Server returns result to agent
```

### File Structure
```
merlin/mcp/
├── __init__.py
├── server.py            # MCPServer class
├── tools/
│   ├── __init__.py
│   ├── base.py         # MCPTool abstract base
│   ├── perception.py   # Sensing/detection tools
│   └── action.py       # Navigation/manipulation tools
└── schemas.py          # JSON schemas for tool inputs
```

---

## 3. Component Specifications

### 3.1 MCPTool Base Class (tools/base.py)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MCPTool(ABC):
    """Abstract base for all MCP tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (e.g., 'navigate_to')."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for agent."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool inputs."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool. Return JSON-serializable dict."""
        pass
```

### 3.2 Five Core Tools

**Tool 1: get_robot_status()**
```python
class ToolGetRobotStatus(MCPTool):
    """Get current robot telemetry."""
    
    @property
    def name(self) -> str:
        return "get_robot_status"
    
    @property
    def description(self) -> str:
        return "Get current position, battery, state, and detected objects"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        status = self.state_machine._get_status()
        return {
            "success": True,
            "status": {
                "state": status.state,
                "position": status.position,
                "heading": status.heading,
                "battery": status.battery,
                "gripper_open": status.gripper_open,
                "detected_objects": status.detected_objects
            }
        }
```

**Tool 2: navigate_to(x, y)**
```python
class ToolNavigateTo(MCPTool):
    """Navigate to target position."""
    
    NAVIGATION_TIMEOUT = 30.0  # seconds
    
    @property
    def name(self) -> str:
        return "navigate_to"
    
    @property
    def description(self) -> str:
        return "Drive to [x, y] coordinates. Blocks until arrival or timeout."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "Target X in meters"},
                "y": {"type": "number", "description": "Target Y in meters"}
            },
            "required": ["x", "y"]
        }
    
    def execute(self, x: float, y: float, **kwargs) -> Dict[str, Any]:
        """Block until navigation complete or timeout."""
        target = [float(x), float(y)]
        
        # Set goal asynchronously
        success = self.state_machine.set_goal(
            "NAVIGATING", 
            {"target_position": target}
        )
        if not success:
            return {"success": False, "error": "Failed to set goal"}
        
        # Poll until arrival or timeout
        start_time = time.time()
        while time.time() - start_time < self.NAVIGATION_TIMEOUT:
            status = self.state_machine.update()
            
            # Check if arrived
            dist_to_target = math.sqrt(
                (status.position[0] - x)**2 + 
                (status.position[1] - y)**2
            )
            
            if status.state == "IDLE" and dist_to_target < 0.3:
                logger.info(f"Navigation success: {target}")
                return {
                    "success": True,
                    "message": f"Arrived at [{x}, {y}]",
                    "final_position": status.position
                }
            
            time.sleep(0.016)  # 60 Hz polling
        
        # Timeout
        logger.warning(f"Navigation timeout after {self.NAVIGATION_TIMEOUT}s")
        return {
            "success": False,
            "error": "Navigation timeout",
            "last_position": self.state_machine.controller.position
        }
```

**Tool 3: detect_objects(object_names)**
```python
class ToolDetectObjects(MCPTool):
    """Detect objects via vision."""
    
    SENSING_TIMEOUT = 3.0
    
    def __init__(self, state_machine, vision_pipeline=None):
        self.state_machine = state_machine
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
                    "description": "Object types to search for"
                }
            },
            "required": ["object_names"]
        }
    
    def execute(self, object_names: List[str], **kwargs) -> Dict[str, Any]:
        """Trigger sensing and return detections."""
        success = self.state_machine.set_goal(
            "SENSING",
            {"target_objects": object_names}
        )
        if not success:
            return {"success": False, "error": "Failed to set sensing goal"}
        
        # Poll until complete
        start_time = time.time()
        while time.time() - start_time < self.SENSING_TIMEOUT:
            status = self.state_machine.update()
            
            if status.state == "IDLE":
                # Run real vision or use simulated
                if self.vision_pipeline:
                    detections = self.vision_pipeline.detect(object_names)
                else:
                    detections = status.detected_objects
                
                logger.info(f"Detected {len(detections)} objects")
                return {
                    "success": True,
                    "detected": detections,
                    "count": len(detections)
                }
            
            time.sleep(0.016)
        
        return {"success": False, "error": "Sensing timeout"}
```

**Tool 4: grasp_object()**
```python
class ToolGrasp(MCPTool):
    """Close gripper to grasp object."""
    
    MANIPULATION_TIMEOUT = 3.0
    
    @property
    def name(self) -> str:
        return "grasp_object"
    
    @property
    def description(self) -> str:
        return "Close gripper to grasp object"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        success = self.state_machine.set_goal(
            "MANIPULATING",
            {"task": "grasp"}
        )
        if not success:
            return {"success": False, "error": "Failed to set grasp goal"}
        
        start_time = time.time()
        while time.time() - start_time < self.MANIPULATION_TIMEOUT:
            status = self.state_machine.update()
            
            if status.state == "IDLE":
                return {
                    "success": True,
                    "gripper_state": "closed"
                }
            
            time.sleep(0.016)
        
        return {"success": False, "error": "Grasp timeout"}
```

**Tool 5: release_object()**
```python
class ToolRelease(MCPTool):
    """Open gripper to release object."""
    
    MANIPULATION_TIMEOUT = 3.0
    
    @property
    def name(self) -> str:
        return "release_object"
    
    @property
    def description(self) -> str:
        return "Open gripper to release object"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        success = self.state_machine.set_goal(
            "MANIPULATING",
            {"task": "release"}
        )
        if not success:
            return {"success": False, "error": "Failed to set release goal"}
        
        start_time = time.time()
        while time.time() - start_time < self.MANIPULATION_TIMEOUT:
            status = self.state_machine.update()
            
            if status.state == "IDLE":
                return {
                    "success": True,
                    "gripper_state": "open"
                }
            
            time.sleep(0.016)
        
        return {"success": False, "error": "Release timeout"}
```

### 3.3 MCPServer (server.py)

```python
class MCPServer:
    """Central registry of all MCP tools."""
    
    def __init__(self, state_machine: StateMachine, vision_pipeline=None):
        self.state_machine = state_machine
        self.vision_pipeline = vision_pipeline
        
        # Register all tools
        self.tools: Dict[str, MCPTool] = {
            "get_robot_status": ToolGetRobotStatus(state_machine),
            "navigate_to": ToolNavigateTo(state_machine),
            "detect_objects": ToolDetectObjects(state_machine, vision_pipeline),
            "grasp_object": ToolGrasp(state_machine),
            "release_object": ToolRelease(state_machine),
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tool definitions for LLM agent."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            logger.error(f"Unknown tool: {tool_name}")
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        tool = self.tools[tool_name]
        try:
            logger.info(f"Executing {tool_name}({tool_input})")
            result = tool.execute(**tool_input)
            logger.info(f"  → {result}")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def add_tool(self, tool: MCPTool):
        """Add custom tool at runtime."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
```

---

## 4. Implementation Phases

### Phase 1: Base Class & Schemas (Hour 8-9)
- [ ] Implement MCPTool base class
- [ ] Define JSON schemas for each tool
- [ ] Unit tests for base class

**Time:** 1 hour

---

### Phase 2: Core Tools (Hour 9-10)
- [ ] Implement all 5 tools
- [ ] Test each tool individually
- [ ] Validate blocking behavior

**Time:** 1 hour

---

### Phase 3: MCPServer Registry (Hour 10-11)
- [ ] Implement MCPServer
- [ ] Tool registration
- [ ] Tool lookup and execution

**Time:** 1 hour

---

### Phase 4: Integration & Testing (Hour 11-12)
- [ ] Test with state machine
- [ ] Integration tests
- [ ] Full mission with tools

**Time:** 1 hour

---

## 4.5 Teach Phase: MCP Tool Demos

### Teach Phase 1: Base Tool Class

**Artifact:** `examples/teach_mcp_base_tool.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify MCPTool base class works."""
from abc import ABC, abstractmethod
from typing import Dict, Any

class MCPTool(ABC):
    """Abstract base for all MCP tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass

# Implement a simple tool
class TestTool(MCPTool):
    @property
    def name(self) -> str:
        return "test_tool"
    
    @property
    def description(self) -> str:
        return "A test tool"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"success": True, "message": "Tool executed"}

# Test: Verify tool works
print("✓ Teach Phase 1: MCPTool Base Class")

tool = TestTool()
assert tool.name == "test_tool"
print(f"  ✓ Tool name: {tool.name}")

result = tool.execute()
assert result["success"] == True
print(f"  ✓ Tool executed: {result['message']}")

print("✓ Base tool class verified!")
```

**Run:** `python examples/teach_mcp_base_tool.py`

**Expected Output:**
```
✓ Teach Phase 1: MCPTool Base Class
  ✓ Tool name: test_tool
  ✓ Tool executed: Tool executed
✓ Base tool class verified!
```

---

### Teach Phase 2: Individual Tools

**Artifact:** `examples/teach_mcp_tools.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify MCP tools work."""
import json
from abc import ABC, abstractmethod
from typing import Dict, Any

# Mock objects
class MockStateM:
    def __init__(self):
        self.position = [0.5, 0.5]
        self.heading = 45.0
        self.battery = 92.0
        self.gripper_open = True

class MCPTool(ABC):
    def __init__(self, sm):
        self.sm = sm
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass

# Tool implementations
class GetStatus(MCPTool):
    @property
    def name(self):
        return "get_status"
    
    def execute(self, **kwargs):
        return {
            "success": True,
            "position": self.sm.position,
            "heading": self.sm.heading,
            "battery": self.sm.battery,
            "gripper_open": self.sm.gripper_open
        }

class NavigateTo(MCPTool):
    @property
    def name(self):
        return "navigate_to"
    
    def execute(self, x: float, y: float, **kwargs):
        # Simulate navigation
        self.sm.position = [x, y]
        return {"success": True, "message": f"Navigated to [{x}, {y}]"}

class GraspObject(MCPTool):
    @property
    def name(self):
        return "grasp_object"
    
    def execute(self, **kwargs):
        self.sm.gripper_open = False
        return {"success": True, "gripper_state": "closed"}

# Test: Verify tools work
print("✓ Teach Phase 2: Individual MCP Tools")

sm = MockStateM()

# Test 1: Get status
get_status = GetStatus(sm)
result = get_status.execute()
assert result["success"] == True
print(f"  ✓ {get_status.name}: {result['position']}")

# Test 2: Navigate
nav = NavigateTo(sm)
result = nav.execute(x=1.0, y=1.0)
assert sm.position == [1.0, 1.0]
print(f"  ✓ {nav.name}: {result['message']}")

# Test 3: Grasp
grasp = GraspObject(sm)
result = grasp.execute()
assert sm.gripper_open == False
print(f"  ✓ {grasp.name}: {result['gripper_state']}")

print("✓ All tools verified!")
```

**Run:** `python examples/teach_mcp_tools.py`

**Expected Output:**
```
✓ Teach Phase 2: Individual MCP Tools
  ✓ get_status: [0.5, 0.5]
  ✓ navigate_to: Navigated to [1.0, 1.0]
  ✓ grasp_object: closed
✓ All tools verified!
```

---

### Teach Phase 3: MCPServer Registry

**Artifact:** `examples/teach_mcp_server.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify MCPServer registry works."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MCPTool(ABC):
    def __init__(self, sm):
        self.sm = sm
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass

class GetStatus(MCPTool):
    @property
    def name(self):
        return "get_status"
    
    def execute(self, **kwargs):
        return {"success": True, "battery": 90.0}

class MCPServer:
    """Tool registry."""
    def __init__(self, sm):
        self.sm = sm
        self.tools: Dict[str, MCPTool] = {
            "get_status": GetStatus(sm),
        }
    
    def get_tools(self) -> List[str]:
        """List available tools."""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, tool_input: Dict) -> Dict[str, Any]:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        return self.tools[tool_name].execute(**tool_input)
    
    def add_tool(self, tool: MCPTool):
        """Add custom tool."""
        self.tools[tool.name] = tool

# Test: Verify server works
print("✓ Teach Phase 3: MCPServer Registry")

class MockSM:
    pass

server = MCPServer(MockSM())

# Test 1: List tools
tools = server.get_tools()
assert "get_status" in tools
print(f"  ✓ Available tools: {tools}")

# Test 2: Execute tool
result = server.execute_tool("get_status", {})
assert result["success"] == True
print(f"  ✓ Executed get_status: battery={result['battery']}%")

# Test 3: Unknown tool
result = server.execute_tool("unknown", {})
assert result["success"] == False
print(f"  ✓ Error handling: {result['error']}")

print("✓ MCPServer registry verified!")
```

**Run:** `python examples/teach_mcp_server.py`

**Expected Output:**
```
✓ Teach Phase 3: MCPServer Registry
  ✓ Available tools: ['get_status']
  ✓ Executed get_status: battery=90.0%
  ✓ Error handling: Unknown tool: unknown
✓ MCPServer registry verified!
```

---

## 5. Testing Strategy

### Unit Tests

```python
def test_get_robot_status():
    """Test status tool returns valid format."""
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    
    result = mcp.execute_tool("get_robot_status", {})
    
    assert result["success"] == True
    assert "status" in result
    assert "position" in result["status"]
    assert "battery" in result["status"]

def test_navigate_to():
    """Test navigation blocks until arrival."""
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    
    start_time = time.time()
    result = mcp.execute_tool("navigate_to", {"x": 1.0, "y": 0.0})
    elapsed = time.time() - start_time
    
    assert result["success"] == True
    assert elapsed > 1.0  # Should take time to move
    assert distance(result["final_position"], [1.0, 0.0]) < 0.3

def test_detect_objects():
    """Test detection returns proper format."""
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    
    result = mcp.execute_tool("detect_objects", {"object_names": ["red_cube"]})
    
    assert result["success"] == True
    assert "detected" in result
    assert "count" in result

def test_grasp_and_release():
    """Test gripper commands."""
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    
    # Grasp
    result = mcp.execute_tool("grasp_object", {})
    assert result["success"] == True
    assert sm.controller.gripper_open == False
    
    # Release
    result = mcp.execute_tool("release_object", {})
    assert result["success"] == True
    assert sm.controller.gripper_open == True
```

### Integration Tests

```python
def test_full_mission_with_tools():
    """Full mission using MCP tools."""
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    
    # 1. Get status
    result = mcp.execute_tool("get_robot_status", {})
    assert result["success"]
    
    # 2. Detect objects
    result = mcp.execute_tool("detect_objects", {"object_names": ["cube"]})
    assert result["success"]
    
    # 3. Navigate
    result = mcp.execute_tool("navigate_to", {"x": 1.0, "y": 0.0})
    assert result["success"]
    
    # 4. Grasp
    result = mcp.execute_tool("grasp_object", {})
    assert result["success"]
    
    # 5. Navigate away
    result = mcp.execute_tool("navigate_to", {"x": 2.0, "y": 1.0})
    assert result["success"]
    
    # 6. Release
    result = mcp.execute_tool("release_object", {})
    assert result["success"]
```

---

## 6. Configuration

**`merlin/mcp/config.py`:**

```python
# Tool timeouts
NAVIGATION_TIMEOUT = 30.0  # seconds
SENSING_TIMEOUT = 3.0
MANIPULATION_TIMEOUT = 3.0

# Navigation thresholds
ARRIVAL_THRESHOLD = 0.3  # meters

# Tool retry policy
MAX_RETRIES = 3
RETRY_BACKOFF_MS = 100

# Logging
LOG_TOOL_CALLS = True
LOG_TOOL_RESULTS = True
```

---

## 7. Deliverables Checklist

- [ ] `merlin/mcp/tools/base.py` - MCPTool abstract base
- [ ] `merlin/mcp/tools/perception.py` - Perception tools
- [ ] `merlin/mcp/tools/action.py` - Action tools
- [ ] `merlin/mcp/server.py` - MCPServer registry
- [ ] `tests/test_mcp_tools.py` - All unit tests pass
- [ ] Integration tests with state machine
- [ ] Tool schema documentation
- [ ] Performance benchmarks (tool execution time)

---

## 8. Success Metrics

| Metric | Target |
|--------|--------|
| Tool startup latency | <50ms |
| Navigation tool accuracy | <0.3m error |
| Tool execution reliability | 100% (no crashes) |
| Blocking behavior | Correct (waits for completion) |
| Result JSON validity | 100% (no malformed results) |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Tool timeout too short | Conservative defaults (30s nav, 3s manip) |
| Infinite loop in polling | Strict timeout enforcement |
| State machine diverge | Clear contracts between tool and SM |
| JSON result malformed | Validate all results with json.dumps() |

---

## 10. Dependencies

**External:**
- json (stdlib)
- time (stdlib)
- logging (stdlib)
- math (stdlib)

**Internal:**
- StateMachine
- RobotStatus (from core.types)

---

## 11. Future Extensions

- Add tool for battery warning
- Add tool for object search with learning
- Add tool for multi-step missions
- Add tool for replanning on failure

---

## 12. Timeline

- **Hour 8-9:** Base class and schemas
- **Hour 9-10:** Core tools implementation
- **Hour 10-11:** MCPServer and registry
- **Hour 11-12:** Integration and testing

**Total: 4 hours to working MCP server**
