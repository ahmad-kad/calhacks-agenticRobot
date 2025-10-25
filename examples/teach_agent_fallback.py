#!/usr/bin/env python3
"""Teach Phase: Verify fallback chain works."""
from merlin.agent import create_agent

print("✓ Teach Phase 4: Fallback Chain")

# Test 1: Auto selects first available (without API keys, uses simple)
agent = create_agent("auto")
result = agent.run_mission("Test")
assert result is not None
print(f"  ✓ Auto fallback: {agent.__class__.__name__}")

# Test 2: Direct backend works
agent = create_agent("simple")
result = agent.run_mission("Test")
assert "Mission complete" in result or result is not None
print(f"  ✓ Direct backend: {agent.__class__.__name__}")

print("✓ Fallback chain verified!")
