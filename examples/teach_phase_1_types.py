#!/usr/bin/env python3
"""Teach Phase 1: Verify core data types work."""
from merlin.core.types import RobotStatus

print("✓ Teach Phase 1: Types work!")
status = RobotStatus(
    state="IDLE",
    position=[0.0, 0.0],
    heading=0.0,
    battery=95.0,
    gripper_open=True,
    detected_objects=[]
)
print(f"  Status: {status.state}")
print(f"  Position: {status.position}")
print(f"  Battery: {status.battery}%")
assert status.state == "IDLE"
print("✓ All assertions pass")
