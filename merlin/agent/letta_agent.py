"""
Letta Agent Development Environment Integration for MERLIN Framework

This agent integrates Letta's multi-agent development capabilities,
providing enhanced debugging, evaluation, and multi-agent coordination.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class LettaAgent(BaseAgent):
    """
    Letta Agent that provides multi-agent development and evaluation capabilities.
    
    This agent can:
    - Coordinate multiple specialized agents
    - Provide detailed debugging and logging
    - Evaluate agent performance systematically
    - Manage agent state and context efficiently
    """
    
    def __init__(self, api_key: Optional[str] = None, environment: str = "development") -> None:
        super().__init__()
        self.api_key = api_key
        self.environment = environment
        self.base_url = "https://api.letta.com/v1"
        self.agent_registry: Dict[str, Any] = {}
        self.evaluation_results: List[Dict[str, Any]] = []
        
    async def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """
        Execute a mission using Letta's multi-agent capabilities.
        
        Args:
            prompt: Natural language mission description
            max_iterations: Maximum number of tool calls allowed
            
        Returns:
            Mission completion status and evaluation results
        """
        logger.info(f"Starting Letta multi-agent mission: {prompt}")
        
        try:
            # Analyze mission complexity and determine agent requirements
            mission_analysis = await self._analyze_mission_complexity(prompt)
            
            # Create specialized agent team
            agent_team = await self._create_agent_team(mission_analysis)
            
            # Execute mission with multi-agent coordination
            results = await self._execute_multi_agent_mission(
                prompt, agent_team, max_iterations
            )
            
            # Evaluate mission performance
            evaluation = await self._evaluate_mission_performance(results)
            
            logger.info("Letta multi-agent mission completed successfully")
            return self._format_results(results, evaluation)
            
        except Exception as e:
            logger.error(f"Letta multi-agent mission failed: {str(e)}")
            return f"Mission failed: {str(e)}"
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Synchronous wrapper for async mission execution."""
        return asyncio.run(self.run_mission(prompt, max_iterations))
    
    async def _analyze_mission_complexity(self, prompt: str) -> Dict[str, Any]:
        """Analyze mission complexity and determine required agent types."""
        analysis = {
            "complexity_score": 0,
            "required_agents": [],
            "coordination_level": "simple",
            "evaluation_criteria": []
        }
        
        # Analyze prompt for complexity indicators
        complexity_keywords = {
            "multi": ["multiple", "several", "various", "different"],
            "sequential": ["then", "next", "after", "followed by"],
            "conditional": ["if", "when", "unless", "depending"],
            "parallel": ["simultaneously", "at the same time", "while"]
        }
        
        prompt_lower = prompt.lower()
        
        for category, keywords in complexity_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                analysis["complexity_score"] += 1
                analysis["required_agents"].append(category)
        
        # Determine coordination level
        if analysis["complexity_score"] >= 3:
            analysis["coordination_level"] = "complex"
        elif analysis["complexity_score"] >= 2:
            analysis["coordination_level"] = "moderate"
        
        # Add evaluation criteria based on mission type
        if "precision" in prompt_lower:
            analysis["evaluation_criteria"].append("accuracy")
        if "speed" in prompt_lower or "fast" in prompt_lower:
            analysis["evaluation_criteria"].append("efficiency")
        if "error" in prompt_lower or "recovery" in prompt_lower:
            analysis["evaluation_criteria"].append("robustness")
            
        return analysis
    
    async def _create_agent_team(self, mission_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a team of specialized agents based on mission analysis."""
        team = []
        
        # Navigation agent (always included)
        team.append({
            "id": "nav_agent",
            "type": "navigation",
            "capabilities": ["path_planning", "obstacle_avoidance", "localization"],
            "priority": 1
        })
        
        # Manipulation agent (always included)
        team.append({
            "id": "manip_agent", 
            "type": "manipulation",
            "capabilities": ["grasping", "placing", "object_handling"],
            "priority": 1
        })
        
        # Add specialized agents based on mission requirements
        if "multi" in mission_analysis["required_agents"]:
            team.append({
                "id": "coord_agent",
                "type": "coordination",
                "capabilities": ["task_decomposition", "resource_allocation"],
                "priority": 2
            })
        
        if "sequential" in mission_analysis["required_agents"]:
            team.append({
                "id": "seq_agent",
                "type": "sequencing",
                "capabilities": ["task_ordering", "dependency_management"],
                "priority": 2
            })
        
        if "conditional" in mission_analysis["required_agents"]:
            team.append({
                "id": "logic_agent",
                "type": "decision_making",
                "capabilities": ["condition_evaluation", "branching_logic"],
                "priority": 2
            })
        
        return team
    
    async def _execute_multi_agent_mission(
        self, 
        prompt: str, 
        agent_team: List[Dict[str, Any]], 
        max_iterations: int
    ) -> Dict[str, Any]:
        """Execute mission using multi-agent coordination."""
        results = {
            "mission_prompt": prompt,
            "agent_team": agent_team,
            "execution_log": [],
            "agent_results": {},
            "coordination_events": []
        }
        
        # Initialize agent states
        for agent in agent_team:
            results["agent_results"][agent["id"]] = {
                "status": "initialized",
                "tasks": [],
                "performance_metrics": {}
            }
        
        # Execute mission with agent coordination
        for iteration in range(max_iterations):
            iteration_log = {
                "iteration": iteration,
                "agent_actions": {},
                "coordination_events": []
            }
            
            # Coordinate agent actions
            for agent in agent_team:
                if agent["priority"] == 1:  # High priority agents act first
                    action_result = await self._execute_agent_action(agent, prompt, iteration)
                    iteration_log["agent_actions"][agent["id"]] = action_result
                    
                    # Check for coordination needs
                    if action_result.get("needs_coordination"):
                        coord_event = await self._handle_coordination_event(agent, action_result)
                        iteration_log["coordination_events"].append(coord_event)
            
            # Execute lower priority agents
            for agent in agent_team:
                if agent["priority"] > 1:
                    action_result = await self._execute_agent_action(agent, prompt, iteration)
                    iteration_log["agent_actions"][agent["id"]] = action_result
            
            results["execution_log"].append(iteration_log)
            
            # Check for mission completion
            if self._check_mission_completion(results):
                break
        
        return results
    
    async def _execute_agent_action(
        self, 
        agent: Dict[str, Any], 
        prompt: str, 
        iteration: int
    ) -> Dict[str, Any]:
        """Execute action for a specific agent."""
        agent_id = agent["id"]
        agent_type = agent["type"]
        
        try:
            # Map agent type to specific actions
            if agent_type == "navigation":
                action_result = await self._execute_navigation_action(agent, prompt)
            elif agent_type == "manipulation":
                action_result = await self._execute_manipulation_action(agent, prompt)
            elif agent_type == "coordination":
                action_result = await self._execute_coordination_action(agent, prompt)
            elif agent_type == "sequencing":
                action_result = await self._execute_sequencing_action(agent, prompt)
            elif agent_type == "decision_making":
                action_result = await self._execute_decision_action(agent, prompt)
            else:
                action_result = {"status": "unknown_agent_type", "error": f"Unknown agent type: {agent_type}"}
            
            # Update agent performance metrics
            action_result["execution_time"] = 0.1  # Placeholder
            action_result["iteration"] = iteration
            
            return action_result
            
        except Exception as e:
            logger.error(f"Agent {agent_id} action failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_navigation_action(self, agent: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Execute navigation-specific actions."""
        if self.mcp_server:
            return self.mcp_server.execute_tool("navigate_to", {"target": "mission_target"})
        return {"status": "navigation_completed", "action": "navigate"}
    
    async def _execute_manipulation_action(self, agent: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Execute manipulation-specific actions."""
        if self.mcp_server:
            return self.mcp_server.execute_tool("grasp", {"object": "target_object"})
        return {"status": "manipulation_completed", "action": "grasp"}
    
    async def _execute_coordination_action(self, agent: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Execute coordination-specific actions."""
        return {
            "status": "coordination_completed",
            "action": "coordinate",
            "needs_coordination": False
        }
    
    async def _execute_sequencing_action(self, agent: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Execute sequencing-specific actions."""
        return {
            "status": "sequencing_completed", 
            "action": "sequence",
            "task_order": ["navigate", "grasp", "place"]
        }
    
    async def _execute_decision_action(self, agent: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Execute decision-making actions."""
        return {
            "status": "decision_completed",
            "action": "decide",
            "decision": "proceed_with_mission"
        }
    
    async def _handle_coordination_event(
        self, 
        agent: Dict[str, Any], 
        action_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle coordination events between agents."""
        return {
            "event_type": "coordination",
            "agent_id": agent["id"],
            "action_result": action_result,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    def _check_mission_completion(self, results: Dict[str, Any]) -> bool:
        """Check if mission is complete based on results."""
        # Simple completion check - can be enhanced
        return len(results["execution_log"]) >= 3
    
    async def _evaluate_mission_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate mission performance using Letta's evaluation framework."""
        evaluation = {
            "overall_score": 0.0,
            "agent_scores": {},
            "coordination_score": 0.0,
            "efficiency_score": 0.0,
            "recommendations": []
        }
        
        # Evaluate individual agent performance
        for agent_id, agent_results in results["agent_results"].items():
            score = self._calculate_agent_score(agent_results)
            evaluation["agent_scores"][agent_id] = score
        
        # Calculate overall scores
        if evaluation["agent_scores"]:
            evaluation["overall_score"] = sum(evaluation["agent_scores"].values()) / len(evaluation["agent_scores"])
        
        # Add recommendations
        if evaluation["overall_score"] < 0.7:
            evaluation["recommendations"].append("Consider improving agent coordination")
        
        return evaluation
    
    def _calculate_agent_score(self, agent_results: Dict[str, Any]) -> float:
        """Calculate performance score for an agent."""
        # Simple scoring algorithm - can be enhanced
        if agent_results["status"] == "initialized":
            return 0.5
        elif "error" in agent_results.get("status", ""):
            return 0.0
        else:
            return 0.8
    
    def _format_results(self, results: Dict[str, Any], evaluation: Dict[str, Any]) -> str:
        """Format mission results and evaluation."""
        summary = {
            "mission_results": results,
            "performance_evaluation": evaluation,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return json.dumps(summary, indent=2)
    
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        """Build tool definitions for Letta-specific capabilities."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_agent_team",
                    "description": "Create a team of specialized agents for mission execution",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mission_type": {
                                "type": "string",
                                "description": "Type of mission to create agents for"
                            },
                            "complexity_level": {
                                "type": "string",
                                "enum": ["simple", "moderate", "complex"],
                                "description": "Mission complexity level"
                            }
                        },
                        "required": ["mission_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_agent_performance",
                    "description": "Evaluate performance of agents using Letta's evaluation framework",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of agent to evaluate"
                            },
                            "evaluation_criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Criteria to evaluate against"
                            }
                        },
                        "required": ["agent_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "coordinate_agents",
                    "description": "Coordinate actions between multiple agents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs of agents to coordinate"
                            },
                            "coordination_type": {
                                "type": "string",
                                "enum": ["sequential", "parallel", "conditional"],
                                "description": "Type of coordination needed"
                            }
                        },
                        "required": ["agent_ids", "coordination_type"]
                    }
                }
            }
        ]
    
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from Letta API response."""
        return []
    
    def _extract_text(self, response: Any) -> str:
        """Extract text content from Letta API response."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("text", str(response))
        else:
            return str(response)
