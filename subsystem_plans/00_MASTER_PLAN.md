# MERLIN: Master Implementation Plan

## Project Overview

**MERLIN** is a complete autonomous robot agent system that integrates:
- **Claude LLM** for intelligent reasoning
- **State Machine** for robust autonomous execution
- **MCP Tools** for standardized tool interface
- **Multi-backend Agent Support** for flexibility
- **Hardware Abstraction** for mock/sim/real hardware

**Goal:** Build a working autonomous robot demo in 40 hours (CalHacks)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Agent (LLM)                       │
│                  (Top-level reasoning)                      │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │   MCP Server    │
    │  (5 core tools) │
    └────────┬────────┘
             │
    ┌────────▼────────────┐
    │  State Machine      │
    │  (60 Hz autonomous) │
    └────────┬────────────┘
             │
    ┌────────▼────────────────┐
    │ Hardware Abstraction    │
    │ (Mock/MuJoCo/XLE)       │
    └────────┬────────────────┘
             │
    ┌────────▼────────────────┐
    │  Robot Hardware         │
    │  (Physical or simulated)│
    └─────────────────────────┘
```

---

## Subsystem Breakdown

### 1. **Core State Machine** (Hours 2-6)
- **Status:** Foundation
- **Responsibility:** Autonomous 60Hz execution loop
- **Deliverable:** Robot can navigate and manipulate
- **Key Files:**
  - `merlin/core/types.py`
  - `merlin/core/state_machine.py`
  - `merlin/core/controller.py`

**Key Metrics:**
- Update rate: 60 Hz ±2 Hz
- Navigation accuracy: <0.3m
- Timeout safety: 100%

---

### 2. **Hardware Abstraction** (Hours 3-20)
- **Status:** Multi-backend support
- **Responsibility:** Unified interface to different hardware
- **Deliverable:** Switch backends with one line of code
- **Key Files:**
  - `merlin/hardware/mock.py`
  - `merlin/hardware/simulator.py` (MuJoCo)
  - `merlin/hardware/xle_driver.py` (optional)

**Backends:**
| Backend | Speed | Cost | Physics | Use Case |
|---------|-------|------|---------|----------|
| Mock | Instant | Free | None | Testing |
| MuJoCo | Fast | Free | Realistic | Validation |
| XLE | Real-time | Hardware | Real | Final demo |

---

### 3. **MCP Server** (Hours 8-12)
- **Status:** Tool registry and execution
- **Responsibility:** Standardized interface for agent
- **Deliverable:** 5 core tools working
- **Key Files:**
  - `merlin/mcp/server.py`
  - `merlin/mcp/tools/base.py`
  - `merlin/mcp/tools/perception.py`
  - `merlin/mcp/tools/action.py`

**5 Core Tools:**
1. `get_robot_status()` - Poll telemetry
2. `navigate_to(x, y)` - Drive to position
3. `detect_objects(names)` - Find objects
4. `grasp_object()` - Close gripper
5. `release_object()` - Open gripper

---

### 4. **Agent Backends** (Hours 12-18)
- **Status:** Multi-LLM flexibility
- **Responsibility:** Provide multiple LLM implementations
- **Deliverable:** Claude + Groq + Gemini + Ollama
- **Key Files:**
  - `merlin/agent/base_agent.py`
  - `merlin/agent/claude_agent.py`
  - `merlin/agent/groq_agent.py`
  - `merlin/agent/gemini_agent.py`
  - `merlin/agent/ollama_agent.py`

**Agent Selection:**
- **Primary:** Groq (fastest, <5s per mission)
- **Secondary:** Claude (best reasoning)
- **Tertiary:** Gemini (multimodal)
- **Offline:** Ollama (no internet)

---

### 5. **Perception Pipeline** (Hours 25-35, Optional)
- **Status:** Vision integration
- **Responsibility:** Object detection and tracking
- **Key Files:**
  - `merlin/perception/vision.py` (YOLOv8)
  - `merlin/perception/odometry.py` (EKF)

---

### 6. **Frontend** (Hours 35-40, Optional)
- **Status:** Visualization and control
- **Key Technologies:**
  - Web Dashboard (FastAPI + React)
  - Gazebo/RViz (3D visualization)
  - Real-time status updates

---

## Implementation Timeline

### **Phase 1: Foundation (Hours 0-6)**
Goal: Basic robot working with mock hardware

- [ ] Hour 0-2: Project setup, environment
- [ ] Hour 2-3: Core types and interfaces
- [ ] Hour 3-4: Mock controller
- [ ] Hour 4-5: State machine core
- [ ] Hour 5-6: State-specific logic

**Checkpoint:** Robot can move and manipulate in simulation

---

### **Phase 2: Tool Interface (Hours 6-12)**
Goal: MCP tools callable and working

- [ ] Hour 6-8: MCP base class and schemas
- [ ] Hour 8-10: Implement 5 core tools
- [ ] Hour 10-12: MCPServer registry and testing

**Checkpoint:** Each tool works independently

---

### **Phase 3: Agent Integration (Hours 12-18)**
Goal: Claude agent completing missions

- [ ] Hour 12-14: Base agent + Claude
- [ ] Hour 14-16: Groq + Gemini + Ollama
- [ ] Hour 16-18: Fallback chain and factory

**Checkpoint:** Agent can run full missions

---

### **Phase 4: Hardware Integration (Hours 18-25)**
Goal: Real or realistic physics

- [ ] Hour 18-20: MuJoCo simulator
- [ ] Hour 20-25: Real hardware (optional)

**Checkpoint:** Algorithm validated against physics

---

### **Phase 5: Perception (Hours 25-35)**
Goal: Vision-based object detection

- [ ] Hour 25-28: YOLOv8 pipeline
- [ ] Hour 28-35: Integration with tools

**Checkpoint:** Agent can find and pick objects

---

### **Phase 6: Polish (Hours 35-40)**
Goal: Demo-ready

- [ ] Hour 35-38: Edge cases and recovery
- [ ] Hour 38-39: Performance optimization
- [ ] Hour 39-40: Presentation prep

**Checkpoint:** Smooth working demo

---

## Critical Path

**DO THESE FIRST:**

1. ✅ State machine (Phases 1) - Everything depends on this
2. ✅ MCP tools (Phase 2) - Agent needs these
3. ✅ Claude agent (Phase 3) - Full system alive
4. ⚠️ MuJoCo (Phase 4) - Validate algorithms
5. ⚠️ Vision (Phase 5) - Cool demo feature
6. ⚠️ Frontend (Phase 6) - Nice to have

---

## File Structure

```
merlin-robot/
├── merlin/
│   ├── __init__.py
│   ├── core/
│   │   ├── types.py           # RobotStatus, RobotState
│   │   ├── controller.py      # RobotController interface
│   │   └── state_machine.py   # StateMachine (core)
│   ├── hardware/
│   │   ├── __init__.py        # Factory function
│   │   ├── mock.py            # MockController
│   │   ├── simulator.py       # MuJoCoController
│   │   └── xle_driver.py      # XLEController
│   ├── mcp/
│   │   ├── server.py          # MCPServer registry
│   │   ├── tools/
│   │   │   ├── base.py        # MCPTool base class
│   │   │   ├── perception.py  # detect_objects, etc
│   │   │   └── action.py      # navigate_to, grasp, etc
│   ├── agent/
│   │   ├── base_agent.py      # BaseAgent interface
│   │   ├── claude_agent.py    # Claude implementation
│   │   ├── groq_agent.py      # Groq implementation
│   │   ├── gemini_agent.py    # Gemini implementation
│   │   ├── ollama_agent.py    # Ollama implementation
│   │   └── __init__.py        # Factory function
│   ├── perception/
│   │   ├── vision.py          # YOLOv8 wrapper
│   │   └── odometry.py        # EKF pose estimation
│   ├── utils/
│   │   ├── logger.py
│   │   └── config.py
│   └── missions/
│       ├── find_object.py
│       ├── pick_and_place.py
│       └── multi_object.py
├── tests/
│   ├── test_state_machine.py
│   ├── test_hardware.py
│   ├── test_mcp_tools.py
│   ├── test_agents.py
│   └── conftest.py
├── examples/
│   ├── basic_mission.py
│   ├── vision_demo.py
│   └── sim_demo.py
├── requirements.txt
├── main.py              # Entry point
└── README.md
```

---

## Dependencies

### **Core (Required)**
```
anthropic==0.28.0      # Claude API
pydantic==2.6.4        # Validation
python-dotenv==1.0.0   # Config
```

### **Multi-Agent Support**
```
groq==0.9.0            # Groq API
google-generativeai==0.5.0  # Gemini API
requests==2.31.0       # HTTP (for Ollama)
```

### **Hardware (Optional)**
```
mujoco==3.1.5          # Physics sim
opencv-python==4.9.0.80  # Image processing
ultralytics==8.1.34    # YOLOv8
```

### **Testing**
```
pytest==7.4.4
pytest-cov==4.1.0
```

---

## Success Criteria

### **Phase 1: Foundation ✅**
- [ ] State machine runs at 60 Hz
- [ ] Robot moves in mock backend
- [ ] Gripper opens/closes
- [ ] Battery drains realistically

### **Phase 2: Tools ✅**
- [ ] All 5 tools defined
- [ ] Tools block correctly
- [ ] Results return valid JSON
- [ ] Integration with state machine

### **Phase 3: Agent ✅**
- [ ] Claude completes simple missions
- [ ] Multi-agent fallback works
- [ ] Full mission: navigate → detect → grasp → release

### **Phase 4: Physics ✅**
- [ ] MuJoCo physics match mock kinematics
- [ ] Algorithm validates in realistic setting

### **Phase 5: Vision ✅**
- [ ] YOLOv8 detects objects reliably
- [ ] 3D position estimation works
- [ ] Agent picks objects in sim

### **Phase 6: Polish ✅**
- [ ] Edge cases handled (battery low, timeout, etc)
- [ ] Performance optimized (60 Hz maintained)
- [ ] Demo-ready and impressive

---

## Development Workflow

### **Daily Standup Questions**
1. What subsystem am I on?
2. What's the current blocker?
3. What's my next concrete deliverable?
4. Are my tests passing?

### **Git Workflow**
```bash
# Create feature branch
git checkout -b feat/subsystem-name

# Work incrementally
git commit -m "Add [subsystem]: [specific feature]"

# Before pushing
pytest tests/ -v
python -m flake8 merlin/

# Merge
git push origin feat/subsystem-name
```

### **Testing Before Demo**
```bash
# Unit tests
pytest tests/ -v

# Integration tests
python -c "
from merlin.agent import create_agent
from merlin.hardware import create_controller
from merlin.core import StateMachine
from merlin.mcp import MCPServer

controller = create_controller('mock')
sm = StateMachine(controller)
mcp = MCPServer(sm)
agent = create_agent('claude')
agent.set_mcp_server(mcp)
result = agent.run_mission('Find the red cube and pick it up')
print(result)
"

# All backends
for backend in mock mujoco ollama; do
  python main.py --backend $backend --mission "Test"
done
```

---

## Risk Management

### **Critical Risks**

| Risk | Impact | Mitigation |
|------|--------|-----------|
| State machine latency | HIGH | Profile early, optimize controller |
| API key quota exceeded | HIGH | Cache responses, use fallback |
| MuJoCo setup complex | MEDIUM | Use dm_control pre-built models |
| Physics accuracy | MEDIUM | Validate against real robot |
| Network failure | MEDIUM | Pre-download models, use Ollama |

### **Contingency Plans**

- **If Claude unavailable:** Fall back to Groq → Gemini → Ollama
- **If MuJoCo fails:** Skip physics validation, use mock
- **If vision too slow:** Use coarse detection, pre-filter objects
- **If battery low:** Reduce mission scope or switch to mock

---

## Pre-Event Checklist

### **3 Days Before**
- [ ] All dependencies installed
- [ ] API keys obtained and tested
- [ ] YOLOv8 models downloaded
- [ ] Ollama model downloaded
- [ ] Full integration test passes

### **Day Before**
- [ ] Full mission test on all backends
- [ ] Performance benchmarks recorded
- [ ] Demo script prepared
- [ ] Presentation outline done

### **Event Day**
- [ ] All systems tested at venue
- [ ] Backup plans ready
- [ ] Live demo recording backup

---

## Performance Targets

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| State machine frequency | 60 Hz | Design goal | Must maintain |
| Navigation accuracy | <0.3m | TBD | Tuned in Phase 4 |
| Tool execution latency | <50ms | TBD | Mock only |
| Agent mission time | <30s | TBD | Groq + Mock |
| Battery runtime | >10 min | TBD | Sim dependent |

---

## Resources

### **Documentation**
- [`01_CORE_STATE_MACHINE.md`](01_CORE_STATE_MACHINE.md) - State machine details
- [`02_HARDWARE_ABSTRACTION.md`](02_HARDWARE_ABSTRACTION.md) - Hardware integration
- [`03_MCP_SERVER.md`](03_MCP_SERVER.md) - Tool definitions
- [`04_AGENT_BACKENDS.md`](04_AGENT_BACKENDS.md) - Multi-agent strategy

### **API Documentation**
- [Anthropic Claude](https://docs.anthropic.com)
- [Groq Console](https://console.groq.com)
- [Google Gemini](https://ai.google.dev)
- [MuJoCo](https://mujoco.org)
- [YOLOv8](https://docs.ultralytics.com)

### **Tools**
- IDE: VSCode or PyCharm
- Testing: pytest
- Profiling: cProfile
- Visualization: Gazebo / RViz

---

## Quick Start

```bash
# 1. Clone and setup
mkdir merlin-robot && cd merlin-robot
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
echo 'ANTHROPIC_API_KEY=sk-...' > .env
echo 'GROQ_API_KEY=gsk-...' >> .env

# 4. Run basic test
python main.py --backend mock --mission "Test mission"

# 5. Run full test
pytest tests/ -v
```

---

## Success Metrics Summary

✅ **Minimum Viable Product (MVPg):**
- Mock robot completes 1 complex mission
- Works with Claude agent
- Code is clean and tested

✅ **Solid Implementation:**
- All 5 MCP tools working
- Multi-agent fallback
- Basic vision integration
- Runs on hardware or MuJoCo

✅ **Production Ready:**
- Handles edge cases
- Performance optimized
- Full documentation
- Impressive live demo

---

## Contact & Support

**Implementation Questions:** See specific subsystem plans
**Architecture Decisions:** Review architecture overview above
**Debugging:** Check logs in `merlin.log` and test suite

---

**Total Timeline: 40 hours → Working autonomous robot demo** 🚀

Good luck at CalHacks 2024!
