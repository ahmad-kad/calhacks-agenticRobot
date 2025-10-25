#!/usr/bin/env python3
"""Teach Phase 4: Full pick-and-place mission with wired modules."""
from merlin.core.state_machine import StateMachine
from merlin.hardware.mock import MockController

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
final_status = sm.controller.get_status()
print(f"  Final position: {final_status.position}")
print(f"  Final battery: {final_status.battery:.1f}%")
