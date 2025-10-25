# MERLIN Subsystem Planning Documentation Index

## Complete Planning Documents Created (3,308 lines total)

### 📋 Master Documents

| Document | Size | Purpose | Start Here? |
|----------|------|---------|------------|
| **[00_MASTER_PLAN.md](00_MASTER_PLAN.md)** | 527 lines | 40-hour implementation roadmap | ✅ YES |
| **[05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md)** | 642 lines | Complete system design + data flow | ✅ YES |

### 🏗️ Subsystem Planning Documents

| Document | Size | Covers | Hours |
|----------|------|--------|-------|
| **[01_CORE_STATE_MACHINE.md](01_CORE_STATE_MACHINE.md)** | 398 lines | Autonomous 60Hz execution loop | 2-6 |
| **[02_HARDWARE_ABSTRACTION.md](02_HARDWARE_ABSTRACTION.md)** | 556 lines | Mock/MuJoCo/XLE hardware backends | 3-20 |
| **[03_MCP_SERVER.md](03_MCP_SERVER.md)** | 604 lines | 5 core robot tools registry | 8-12 |
| **[04_AGENT_BACKENDS.md](04_AGENT_BACKENDS.md)** | 581 lines | Claude/Groq/Gemini/Ollama agents | 12-18 |

---

## Key Decisions Answered

### ❓ MuJoCo vs ROS2?
**Decision:** Start with **custom architecture + Mock** (no MuJoCo required for demo)
- ✅ Custom: 0 min setup, 60 Hz mock control sufficient
- ⚠️ MuJoCo: 5 min setup, optional physics validation (hour 20+)
- ❌ ROS2: 30 min+ setup, 2-3 day learning curve (skip for now)

See: [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) § 1

### ❓ Where is SLAM & Navigation?
**Decision:** Not in Phase 1, optional Phase 4+
- ✅ Phase 3: Basic proportional control (sufficient for demo)
- ⚠️ Phase 4: TEB path planning (if time allows)
- ❌ Phase 5+: Full SLAM (only for real robots with unknown environments)

See: [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) § 3

### ❓ System Architecture?
**Layered 6-layer design:**
```
Layer 6: Missions
Layer 5: Agent Reasoning (Claude/Groq/Gemini/Ollama)
Layer 4: MCP Tool Server (5 core tools)
Layer 3: State Machine (60 Hz autonomous)
Layer 2: Navigation/Perception/Manipulation
Layer 1: Hardware Backend (Mock/MuJoCo/ROS2/XLE)
```

See: [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) § 2

### ❓ Data Flow & Interactions?
Complete diagrams showing:
- ✅ Mission execution flow (user → agent → tools → hardware)
- ✅ 60 Hz state machine loop with state dispatch
- ✅ Dependency graph (module dependencies)
- ✅ Data types flow (input → processing → output)

See: [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) § 4-6

---

## How to Use These Documents

### For Quick Start (2 hours):
1. Read [00_MASTER_PLAN.md](00_MASTER_PLAN.md) (10 min)
2. Scan [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) § 1-2 (10 min)
3. Start with [01_CORE_STATE_MACHINE.md](01_CORE_STATE_MACHINE.md) (focus on Phase 1)

### For Complete Understanding (4 hours):
1. Read all master documents in order
2. Review each subsystem document
3. Trace through data flow diagrams
4. Study dependency graph

### During Development:
- Reference corresponding subsystem doc
- Follow implementation phases checklist
- Update status against deliverables
- Consult success metrics & testing strategy

### Before Demo:
- Follow [00_MASTER_PLAN.md](00_MASTER_PLAN.md) § Pre-Event Checklist
- Test all subsystems per docs
- Verify performance budgets met

---

## 40-Hour Timeline at a Glance

| Phase | Hours | Subsystem | Status |
|-------|-------|-----------|--------|
| **1: Foundation** | 0-6 | State Machine | Core ✅ |
| **2: Tools** | 6-12 | MCP Server | Core ✅ |
| **3: Agent** | 12-18 | Agent Backends | Core ✅ |
| **4: Hardware** | 18-25 | Hardware Abstraction | Core ✅ |
| **5: Perception** | 25-35 | Vision + SLAM (opt) | Optional |
| **6: Polish** | 35-40 | Testing + Demo | Polish |

**By hour 18: Full working system (agent completes missions!)**

---

## Critical Architecture Decisions

### ✅ What's Included
- Single-machine architecture (no distributed middleware)
- Mock backend for rapid testing
- Custom state machine (not ROS2)
- 5 essential MCP tools
- Multi-LLM agent flexibility
- Extensible hardware abstraction (factory pattern)

### ⚠️ Optional (Good to Have)
- MuJoCo realistic physics simulation
- Advanced navigation (TEB planner)
- Vision perception pipeline
- Web frontend

### ❌ Not Included (Future Work)
- ROS2 middleware integration
- Full SLAM implementation
- Multi-robot coordination
- Distributed systems

---

## Files & Dependencies Summary

### Organized Into 6 Subsystems:
```
merlin/
├── core/              ← State Machine (Doc 01)
├── hardware/          ← Hardware Abstraction (Doc 02)
├── mcp/              ← MCP Server (Doc 03)
├── agent/            ← Agent Backends (Doc 04)
├── perception/       ← Optional Vision
└── missions/         ← Mission Examples
```

### Dependencies (Minimum):
```
anthropic             (Claude API)
pydantic             (Validation)
python-dotenv        (Config)
groq                 (Groq API)
google-generativeai  (Gemini API)
requests             (HTTP)
```

### Optional Hardware:
```
mujoco               (Physics sim)
opencv-python        (Vision)
ultralytics          (YOLOv8)
```

---

## Questions Answered

| Question | Document | Section |
|----------|----------|---------|
| How does state machine work? | 01 | Architecture |
| How to switch backends? | 02 | Factory pattern |
| What are the 5 tools? | 03 | Component specs |
| How do agents integrate? | 04 | Base interface |
| Complete system design? | 05 | Layered architecture |
| Data flow? | 05 | § 4 |
| Dependencies? | 05 | § 5 |
| MuJoCo vs ROS2? | 05 | § 1 |
| Where is SLAM? | 05 | § 3 |
| 40-hour plan? | 00 | Timeline |

---

## Next Steps

1. ✅ **Read** 00_MASTER_PLAN.md (10 min)
2. ✅ **Understand** 05_SYSTEM_ARCHITECTURE.md (20 min)
3. **Start Implementation** → 01_CORE_STATE_MACHINE.md Phase 1
4. **Complete State Machine** (hours 2-6)
5. **Move to MCP Server** → 03_MCP_SERVER.md
6. ... (continue through phases)

---

**Created:** October 24, 2025
**Total Planning:** 3,308 lines across 6 documents
**Estimated Value:** 20+ hours of architecture work compressed into readable documents

**Good luck at CalHacks 2024! 🚀**
