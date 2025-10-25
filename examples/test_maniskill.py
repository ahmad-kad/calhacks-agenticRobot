#!/usr/bin/env python3
"""Test ManiSkill backend with XLeRobot simulation.

Setup steps:
1. conda create -y -n merlin-sim python=3.11
2. conda activate merlin-sim
3. pip install mani-skill pygame rerun-sdk
4. python -m mani_skill.utils.download_asset "ReplicaCAD"
5. Download XLeRobot files and copy to ManiSkill agents/robots, assets/robots, envs/scenes
6. Add xlerobot to /agents/robots/__init__.py in ManiSkill
7. Run this script
"""

import sys

try:
    from merlin.hardware import create_controller
    from merlin.core.state_machine import StateMachine
    from merlin.mcp.server import MCPServer
    from merlin.agent import create_agent
except ImportError as e:
    print(f"Error: MERLIN modules not found. Add to PYTHONPATH: {e}")
    sys.exit(1)

print("=" * 60)
print("MERLIN + ManiSkill + XLeRobot Integration Test")
print("=" * 60)

try:
    print("\n1. Creating ManiSkill backend (XLeRobot single-arm)...")
    controller = create_controller("maniskill")
    print("   ✓ ManiSkill environment created")
    
    print("\n2. Creating state machine...")
    sm = StateMachine(controller)
    print("   ✓ State machine ready")
    
    print("\n3. Creating MCP server (5 tools)...")
    mcp = MCPServer(sm)
    print(f"   ✓ MCP server with {len(mcp.get_tools())} tools")
    
    print("\n4. Creating agent...")
    agent = create_agent("simple")
    agent.set_mcp_server(mcp)
    print(f"   ✓ Agent: {agent.__class__.__name__}")
    
    print("\n5. Running mission in ManiSkill simulation...")
    print("   Mission: Get status → Navigate → Grasp → Report\n")
    
    result = agent.run_mission("Pick and place in ManiSkill")
    print(result)
    
    print("\n" + "=" * 60)
    print("✓ ManiSkill integration test PASSED!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Develop and test agent missions in sim")
    print("2. Validate robot control before real hardware")
    print("3. Use learned policies with XLeRobot")
    print("\nNext: Deploy to real XLeRobot hardware!")
    
except ImportError as e:
    print(f"\n✗ ManiSkill not installed: {e}")
    print("\nSetup ManiSkill:")
    print("  pip install mani-skill")
    print("  python -m mani_skill.utils.download_asset 'ReplicaCAD'")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
