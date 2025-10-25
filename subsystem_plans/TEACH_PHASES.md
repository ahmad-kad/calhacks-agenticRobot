# MERLIN: Teach Phases - Mini-Demos for Artifact Verification

**Purpose:** Each subsystem phase includes working mini-demonstrations with real (non-mock) code. These artifacts prove the phase works before moving to the next one.

---

## Quick Start: Run All Teach Phases

```bash
# Set up examples directory
mkdir -p examples

# Phase 1: Core State Machine
python examples/teach_phase_1_types.py
python examples/teach_phase_2_mock_controller.py
python examples/teach_phase_3_state_machine.py
python examples/teach_phase_4_full_mission.py

# Phase 2: Hardware Abstraction
python examples/teach_backend_mock.py
python examples/teach_backend_factory.py
python examples/teach_backend_interface.py

# Phase 3: MCP Server
python examples/teach_mcp_base_tool.py
python examples/teach_mcp_tools.py
python examples/teach_mcp_server.py

# Phase 4: Agent Backends
python examples/teach_agent_base.py
python examples/teach_agent_simple.py
python examples/teach_agent_factory.py
python examples/teach_agent_fallback.py
```

**Expected:** All scripts pass with ✓ checksmarks

---

## Phase Breakdown

### Phase 1: Core State Machine (Hours 2-6)

**Teach Artifacts:**
| Artifact | File | Verifies | Time |
|----------|------|----------|------|
| Types demo | `teach_phase_1_types.py` | Data structures compile | 5 min |
| Kinematics | `teach_phase_2_mock_controller.py` | Forward motion, rotation, battery | 5 min |
| State transitions | `teach_phase_3_state_machine.py` | Navigation to target position | 10 min |
| Full mission | `teach_phase_4_full_mission.py` | Pick-and-place sequence | 10 min |

**Exit Criteria:**
- ✅ All teach phases pass
- ✅ Robot navigates to position with <0.3m accuracy
- ✅ Gripper opens/closes correctly
- ✅ Battery drains realistically

---

### Phase 2: Hardware Abstraction (Hours 3-20)

**Teach Artifacts:**
| Artifact | File | Verifies | Time |
|----------|------|----------|------|
| Mock backend | `teach_backend_mock.py` | Kinematics, gripper, battery | 5 min |
| Factory pattern | `teach_backend_factory.py` | Controller creation & switching | 5 min |
| Interface contract | `teach_backend_interface.py` | All backends implement same interface | 5 min |

**Exit Criteria:**
- ✅ All backends pass teach phases
- ✅ Factory creates controllers without errors
- ✅ Same code works with different backends

---

### Phase 3: MCP Server (Hours 8-12)

**Teach Artifacts:**
| Artifact | File | Verifies | Time |
|----------|------|----------|------|
| Base tool class | `teach_mcp_base_tool.py` | Abstract base implementation | 5 min |
| Individual tools | `teach_mcp_tools.py` | Each of 5 tools works | 5 min |
| Server registry | `teach_mcp_server.py` | Tool registration & execution | 5 min |

**Exit Criteria:**
- ✅ All 5 tools implemented
- ✅ Tools block until completion
- ✅ Results are valid JSON

---

### Phase 4: Agent Backends (Hours 12-18)

**Teach Artifacts:**
| Artifact | File | Verifies | Time |
|----------|------|----------|------|
| Base interface | `teach_agent_base.py` | Abstract agent interface | 5 min |
| Simple agent | `teach_agent_simple.py` | Agent logic without LLM | 10 min |
| Factory pattern | `teach_agent_factory.py` | Agent creation & switching | 5 min |
| Fallback chain | `teach_agent_fallback.py` | Auto-fallback on errors | 5 min |

**Exit Criteria:**
- ✅ All agent backends implement interface
- ✅ Factory switches backends seamlessly
- ✅ Fallback chain selects working backend

---

## Integration Flow

After each teach phase, the component is ready for integration:

```
Teach Phase 1: State Machine Types ✓
           ↓
Teach Phase 2: Mock Controller ✓
           ↓
Teach Phase 3: State Transitions ✓
           ↓
Teach Phase 4: Full Mission ✓
           ↓
Integration: Combine with Hardware Abstraction
           ↓
Teach Phase (Hardware): Backend Switching ✓
           ↓
Integration: Combine with MCP Server
           ↓
Teach Phase (MCP): Tool Execution ✓
           ↓
Integration: Combine with Agent
           ↓
Teach Phase (Agent): Mission Execution ✓
           ↓
🎉 Full Working System!
```

---

## Example: Teaching Phase 1

### Step 1: Run the teach phase
```bash
$ python examples/teach_phase_1_types.py
✓ Teach Phase 1: Types work!
  Status: IDLE
  Position: [0.0, 0.0]
  Battery: 95.0%
✓ All assertions pass
```

### Step 2: Understand what passed
- ✅ Data types compile without errors
- ✅ RobotStatus can be instantiated
- ✅ All fields are accessible
- ✅ Type hints work correctly

### Step 3: Proceed to Phase 2
```bash
$ python examples/teach_phase_2_mock_controller.py
✓ Teach Phase 2: Mock controller works!
  Distance traveled: 0.50m (expected ~0.5m)
  Position: [0.5, 0.0]
  Battery: 94.4%
✓ Kinematics verified
```

---

## Teaching Phase Success Checklist

For each teach phase, verify:

- [ ] Script runs without errors
- [ ] All assertions pass
- [ ] Output shows expected values
- [ ] No mock implementations used (real code)
- [ ] Code is under 200 lines for clarity
- [ ] Minimal external dependencies
- [ ] Can be run independently
- [ ] Teaches a specific concept

---

## When to Use Teach Phases

### ✅ Use Teaching Phases for:
- Validating each phase works before integration
- Demonstrating understanding to team members
- Quick sanity checks during development
- Building confidence incrementally
- Creating reproducible artifacts

### ❌ Don't Use Teaching Phases for:
- Final production code (extend to full implementation)
- Performance benchmarking (may be slow)
- Edge case testing (test suite handles that)
- Integration tests (separate integration suite)

---

## Next Steps After Teach Phases

Once all teach phases pass:

1. **Extend to Full Implementation**
   - Turn teach phase code into production module
   - Add error handling
   - Add logging
   - Add comments

2. **Integration Testing**
   - Combine modules
   - Test interactions
   - Verify contracts

3. **Performance Testing**
   - Benchmark latencies
   - Profile bottlenecks
   - Optimize critical paths

4. **System Testing**
   - End-to-end missions
   - Stress testing
   - Failure scenarios

---

## Example Teaching Phase Template

```python
#!/usr/bin/env python3
"""Teach Phase: [WHAT THIS TEACHES]."""

# Imports (minimal)
from abc import ABC, abstractmethod
from typing import Dict

# Implementation (focused on teaching one concept)
class SimpleConcept:
    def __init__(self):
        self.value = 0
    
    def increment(self):
        self.value += 1

# Test (demonstrates the concept works)
print("✓ Teach Phase: [CONCEPT]")

obj = SimpleConcept()
obj.increment()
assert obj.value == 1
print("  ✓ Concept works")

print("✓ Teach phase verified!")
```

---

## Reference: All Teach Phases

**Phase 1: Core State Machine**
- `teach_phase_1_types.py` - RobotStatus dataclass
- `teach_phase_2_mock_controller.py` - Kinematics integration
- `teach_phase_3_state_machine.py` - State machine dispatch
- `teach_phase_4_full_mission.py` - Full pick-and-place

**Phase 2: Hardware Abstraction**
- `teach_backend_mock.py` - Mock backend operations
- `teach_backend_factory.py` - Factory pattern
- `teach_backend_interface.py` - Backend contract

**Phase 3: MCP Server**
- `teach_mcp_base_tool.py` - MCPTool base class
- `teach_mcp_tools.py` - 5 core tools
- `teach_mcp_server.py` - Tool registry

**Phase 4: Agent Backends**
- `teach_agent_base.py` - BaseAgent interface
- `teach_agent_simple.py` - Simple agent logic
- `teach_agent_factory.py` - Agent factory
- `teach_agent_fallback.py` - Fallback chain

---

**Total Teaching Phases:** 13 mini-demos
**Total Time:** ~90 minutes to validate full system
**Confidence Level:** High - artifacts prove everything works

Good luck! 🚀
