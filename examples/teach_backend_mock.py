#!/usr/bin/env python3
"""Teach Phase: Verify mock backend works."""
import math
from merlin.hardware.mock import MockController

print("✓ Teach Phase: Mock Backend")
controller = MockController()

# Scenario 1: Forward motion
controller.set_velocity(0.5, 0.0)
for _ in range(60):
    controller.update()
dist = math.sqrt(controller.position[0]**2 + controller.position[1]**2)
assert 0.4 < dist < 0.6
print(f"  ✓ Mock: Forward motion {dist:.2f}m")

# Scenario 2: Rotation
controller = MockController()
controller.set_velocity(0.0, 0.5)
for _ in range(60):
    controller.update()
assert 20 < controller.heading < 60
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
