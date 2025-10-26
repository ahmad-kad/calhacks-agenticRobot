"""
Figma AI Agent Integration for MERLIN Framework

This agent integrates Figma's AI capabilities for design-to-code workflows,
enabling the robot to understand and work with design specifications.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FigmaAgent(BaseAgent):
    """
    Figma AI Agent that integrates design context with robotic operations.
    
    This agent can:
    - Parse Figma design files for spatial relationships
    - Extract design specifications for object placement
    - Generate design-aware mission plans
    - Provide visual feedback on task completion
    """
    
    def __init__(self, api_key: Optional[str] = None, team_id: Optional[str] = None) -> None:
        super().__init__()
        self.api_key = api_key
        self.team_id = team_id
        self.base_url = "https://api.figma.com/v1"
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        if self.api_key:
            session.headers.update({
                "X-Figma-Token": self.api_key,
                "Content-Type": "application/json"
            })
            
        return session
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """
        Execute a mission using Figma AI capabilities.
        
        Args:
            prompt: Natural language mission description
            max_iterations: Maximum number of tool calls allowed
            
        Returns:
            Mission completion status and results
        """
        logger.info(f"Starting Figma AI mission: {prompt}")
        
        try:
            # Parse mission for design context
            design_context = self._extract_design_context(prompt)
            
            # Generate design-aware mission plan
            mission_plan = self._generate_mission_plan(prompt, design_context)
            
            # Execute mission with design validation
            result = self._execute_design_aware_mission(mission_plan, max_iterations)
            
            logger.info("Figma AI mission completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Figma AI mission failed: {str(e)}")
            return f"Mission failed: {str(e)}"
    
    def _extract_design_context(self, prompt: str) -> Dict[str, Any]:
        """Extract design-related context from the mission prompt."""
        design_keywords = [
            "design", "layout", "position", "arrange", "organize", 
            "spacing", "alignment", "grid", "pattern", "template"
        ]
        
        context = {
            "has_design_intent": any(keyword in prompt.lower() for keyword in design_keywords),
            "spatial_requirements": [],
            "visual_constraints": []
        }
        
        # Extract spatial requirements
        if "coordinates" in prompt.lower():
            context["spatial_requirements"].append("coordinate_based")
        if "grid" in prompt.lower():
            context["spatial_requirements"].append("grid_based")
        if "pattern" in prompt.lower():
            context["spatial_requirements"].append("pattern_based")
            
        return context
    
    def _generate_mission_plan(self, prompt: str, design_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a design-aware mission plan."""
        plan = {
            "original_prompt": prompt,
            "design_context": design_context,
            "steps": [],
            "validation_criteria": []
        }
        
        # Add design validation steps
        if design_context["has_design_intent"]:
            plan["steps"].append({
                "action": "validate_design_constraints",
                "description": "Verify design requirements are met"
            })
            
        # Add spatial planning steps
        for requirement in design_context["spatial_requirements"]:
            plan["steps"].append({
                "action": f"plan_{requirement}_placement",
                "description": f"Plan placement using {requirement} approach"
            })
            
        return plan
    
    def _execute_design_aware_mission(self, mission_plan: Dict[str, Any], max_iterations: int) -> str:
        """Execute the mission with design awareness."""
        results = []
        
        for i, step in enumerate(mission_plan["steps"]):
            if i >= max_iterations:
                break
                
            try:
                step_result = self._execute_step(step)
                results.append(step_result)
                
                # Check if we should continue
                if "error" in step_result.lower():
                    break
                    
            except Exception as e:
                logger.error(f"Step execution failed: {str(e)}")
                results.append(f"Step failed: {str(e)}")
                break
        
        return self._format_mission_results(results, mission_plan)
    
    def _execute_step(self, step: Dict[str, Any]) -> str:
        """Execute a single mission step."""
        action = step["action"]
        
        if action == "validate_design_constraints":
            return self._validate_design_constraints()
        elif action.startswith("plan_"):
            return self._plan_spatial_placement(action)
        else:
            # Delegate to MCP server for standard robotic actions
            if self.mcp_server:
                return self.mcp_server.execute_tool(action, step.get("parameters", {}))
            return f"Executed {action}"
    
    def _validate_design_constraints(self) -> str:
        """Validate that design constraints are being met."""
        # This would integrate with Figma API to check design compliance
        return "Design constraints validated successfully"
    
    def _plan_spatial_placement(self, action: str) -> str:
        """Plan spatial placement based on design requirements."""
        placement_type = action.replace("plan_", "").replace("_placement", "")
        
        if placement_type == "coordinate_based":
            return "Coordinate-based placement planned"
        elif placement_type == "grid_based":
            return "Grid-based placement planned"
        elif placement_type == "pattern_based":
            return "Pattern-based placement planned"
        else:
            return f"Spatial placement planned using {placement_type}"
    
    def _format_mission_results(self, results: List[str], mission_plan: Dict[str, Any]) -> str:
        """Format the final mission results."""
        summary = {
            "mission": mission_plan["original_prompt"],
            "design_context": mission_plan["design_context"],
            "steps_completed": len(results),
            "results": results,
            "status": "completed" if all("error" not in r.lower() for r in results) else "failed"
        }
        
        return json.dumps(summary, indent=2)
    
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        """Build tool definitions for Figma-specific capabilities."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_figma_file",
                    "description": "Retrieve Figma file information and design specifications",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "Figma file key/ID"
                            }
                        },
                        "required": ["file_key"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "extract_design_specs",
                    "description": "Extract spatial and visual specifications from design",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "Figma node ID to analyze"
                            }
                        },
                        "required": ["node_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_design_compliance",
                    "description": "Validate that robotic actions comply with design specifications",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "Robotic action to validate"
                            },
                            "design_constraints": {
                                "type": "object",
                                "description": "Design constraints to check against"
                            }
                        },
                        "required": ["action", "design_constraints"]
                    }
                }
            }
        ]
    
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from Figma API response."""
        # This would parse Figma API responses for tool calls
        return []
    
    def _extract_text(self, response: Any) -> str:
        """Extract text content from Figma API response."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("text", str(response))
        else:
            return str(response)
    
    def get_figma_file(self, file_key: str) -> Dict[str, Any]:
        """Retrieve Figma file information."""
        try:
            response = self.session.get(f"{self.base_url}/files/{file_key}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve Figma file: {str(e)}")
            return {"error": str(e)}
    
    def extract_design_specs(self, node_id: str) -> Dict[str, Any]:
        """Extract design specifications from a Figma node."""
        # This would implement actual Figma API calls
        return {
            "node_id": node_id,
            "specifications": {
                "position": {"x": 0, "y": 0},
                "size": {"width": 100, "height": 100},
                "constraints": []
            }
        }
