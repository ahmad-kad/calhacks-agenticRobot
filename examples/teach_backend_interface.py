#!/usr/bin/env python3
"""Teach Phase: Verify backend interface contract."""
from merlin.hardware import create_controller

print("✓ Teach Phase: Backend Interface Contract")

controller = create_controller("mock")

# Test all required methods exist
assert hasattr(controller, 'update')
assert hasattr(controller, 'set_velocity')
assert hasattr(controller, 'set_gripper')
assert hasattr(controller, 'get_status')
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
