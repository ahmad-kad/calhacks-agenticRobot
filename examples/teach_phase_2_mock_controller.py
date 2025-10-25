#!/usr/bin/env python3
"""Teach Phase 2: Verify mock controller kinematics work."""
import math
from merlin.hardware.mock import MockController

print("✓ Teach Phase 2: Mock controller works!")
controller = MockController()
controller.set_velocity(0.5, 0.0)

for _ in range(60):  # 60 Hz for 1 second
    controller.update()

status = controller.get_status()
distance = math.sqrt(status.position[0]**2 + status.position[1]**2)

print(f"  Distance traveled: {distance:.2f}m (expected ~0.5m)")
print(f"  Position: {status.position}")
print(f"  Battery: {status.battery:.1f}%")
assert 0.4 < distance < 0.6, f"Distance {distance} out of range"
print("✓ Kinematics verified")
