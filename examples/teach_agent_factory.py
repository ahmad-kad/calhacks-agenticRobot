#!/usr/bin/env python3
"""Teach Phase: Verify agent factory works."""
from merlin.agent import create_agent

print("✓ Teach Phase 3: Agent Factory")

# Test 1: Create simple agent
agent = create_agent("simple")
assert agent.__class__.__name__ == "SimpleAgent"
print(f"  ✓ Created: {agent.__class__.__name__}")

# Test 2: Auto fallback (no API keys set, should use simple)
agent = create_agent("auto")
assert agent is not None
print(f"  ✓ Auto fallback: {agent.__class__.__name__}")

print("✓ Agent factory verified!")
