from __future__ import annotations

import argparse
import json

from merlin.agent import create_agent
from merlin.core.state_machine import StateMachine
from merlin.hardware import create_controller
from merlin.mcp.server import MCPServer
from merlin.utils.config import load_config
from merlin.utils.logger import get_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MERLIN mission runner")
    parser.add_argument("--backend", default=None, help="mock|mujoco|gazebo|xle")
    parser.add_argument("--agent", default=None, help="auto|groq|claude|gemini|ollama|simple")
    parser.add_argument("--mission", default="Pick and place demo", help="Mission prompt")
    return parser.parse_args()


def main() -> int:
    cfg = load_config()
    args = parse_args()
    logger = get_logger()

    backend = args.backend or cfg.backend
    agent_backend = args.agent or cfg.agent
    mission_prompt = args.mission

    logger.info("startup", config={"backend": backend, "agent": agent_backend})

    try:
        # Create hardware backend
        controller = create_controller(backend)
        logger.info("hardware_created", backend=backend)

        # Create state machine
        sm = StateMachine(controller)
        logger.info("state_machine_created")

        # Create MCP server
        mcp = MCPServer(sm)
        logger.info("mcp_server_created", tools=len(mcp.get_tools()))

        # Create agent
        agent = create_agent(agent_backend)
        agent.set_mcp_server(mcp)
        logger.info("agent_created", agent=agent.__class__.__name__)

        # Run mission
        logger.info("mission_start", prompt=mission_prompt)
        result = agent.run_mission(mission_prompt)
        logger.info("mission_complete", result_length=len(result))

        # Return result as JSON
        output = {
            "ok": True,
            "backend": backend,
            "agent": agent.__class__.__name__,
            "mission": mission_prompt,
            "result": result,
        }
        print(json.dumps(output, indent=2))
        return 0

    except Exception as e:
        logger.error("mission_failed", error=str(e), exc_info=True)
        output = {
            "ok": False,
            "backend": backend,
            "agent": agent_backend,
            "mission": mission_prompt,
            "error": str(e),
        }
        print(json.dumps(output, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


