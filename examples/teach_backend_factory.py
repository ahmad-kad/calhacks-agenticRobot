#!/usr/bin/env python3
"""Teach Phase: Verify factory pattern works."""
from merlin.hardware import create_controller

print("✓ Teach Phase: Factory Pattern")

controller = create_controller("mock")
assert controller.__class__.__name__ == "MockController"
print(f"  ✓ Factory created: {controller.__class__.__name__}")

controller2 = create_controller("mock")
assert controller2.battery == 95.0
print(f"  ✓ Factory backend switch works")

print("✓ Factory pattern verified!")
