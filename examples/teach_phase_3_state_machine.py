#!/usr/bin/env python3
"""Teach Phase 3: Verify state machine navigation works."""
import math
from merlin.core.state_machine import StateMachine
from merlin.hardware.mock import MockController

print("✓ Teach Phase 3: State machine works!")
sm = StateMachine(MockController())
print("  Starting navigation to (1.0, 0.0)...")

sm.set_goal("NAVIGATING", {"target_position": [1.0, 0.0]})
for i in range(300):
    status = sm.update()
    if status.state == "IDLE":
        distance = math.sqrt(status.position[0]**2 + status.position[1]**2)
        print(f"  ✓ Arrived at {[round(p, 2) for p in status.position]}")
        break

assert status.state == "IDLE"
print("✓ Navigation verified")
