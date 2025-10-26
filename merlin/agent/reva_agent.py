"""
Reva Security Framework Integration for MERLIN Framework

This agent integrates Reva's security and governance capabilities,
providing secure AI operations and policy enforcement.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import requests
from cryptography.fernet import Fernet
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RevaAgent(BaseAgent):
    """
    Reva Agent that provides security and governance for AI operations.
    
    This agent can:
    - Enforce security policies for AI operations
    - Provide secure vector database access
    - Manage agent registry and permissions
    - Monitor and audit AI agent activities
    """
    
    def __init__(self, api_key: Optional[str] = None, environment: str = "sandbox") -> None:
        super().__init__()
        self.api_key = api_key
        self.environment = environment
        self.base_url = f"https://api.reva.ai/v1/{environment}"
        self.policy_engine = PolicyEngine()
        self.audit_logger = AuditLogger()
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """
        Execute a mission with Reva security enforcement.
        
        Args:
            prompt: Natural language mission description
            max_iterations: Maximum number of tool calls allowed
            
        Returns:
            Mission completion status with security audit trail
        """
        logger.info(f"Starting Reva-secured mission: {prompt}")
        
        try:
            # Security pre-flight checks
            security_check = self._perform_security_preflight(prompt)
            if not security_check["approved"]:
                return f"Mission rejected: {security_check['reason']}"
            
            # Register mission in audit log
            mission_id = self.audit_logger.log_mission_start(prompt)
            
            # Execute mission with security monitoring
            results = self._execute_secured_mission(prompt, max_iterations, mission_id)
            
            # Post-mission security audit
            audit_result = self._perform_security_audit(results, mission_id)
            
            # Log mission completion
            self.audit_logger.log_mission_completion(mission_id, results, audit_result)
            
            logger.info("Reva-secured mission completed successfully")
            return self._format_secured_results(results, audit_result)
            
        except Exception as e:
            logger.error(f"Reva-secured mission failed: {str(e)}")
            self.audit_logger.log_security_violation(str(e))
            return f"Mission failed due to security violation: {str(e)}"
    
    def _perform_security_preflight(self, prompt: str) -> Dict[str, Any]:
        """Perform security pre-flight checks on the mission."""
        check_result = {
            "approved": True,
            "reason": "",
            "violations": [],
            "risk_level": "low"
        }
        
        # Check for prohibited actions
        prohibited_keywords = [
            "delete", "remove", "destroy", "hack", "bypass", "override"
        ]
        
        prompt_lower = prompt.lower()
        violations = [kw for kw in prohibited_keywords if kw in prompt_lower]
        
        if violations:
            check_result["approved"] = False
            check_result["reason"] = f"Prohibited actions detected: {', '.join(violations)}"
            check_result["violations"] = violations
            check_result["risk_level"] = "high"
        
        # Check mission complexity for risk assessment
        complexity_score = self._assess_mission_complexity(prompt)
        if complexity_score > 7:
            check_result["risk_level"] = "medium"
        if complexity_score > 10:
            check_result["risk_level"] = "high"
            if not self._has_high_risk_permissions():
                check_result["approved"] = False
                check_result["reason"] = "High-risk mission requires elevated permissions"
        
        return check_result
    
    def _assess_mission_complexity(self, prompt: str) -> int:
        """Assess mission complexity for risk evaluation."""
        complexity_indicators = [
            "multiple", "complex", "advanced", "sophisticated", "intricate",
            "coordinate", "synchronize", "parallel", "simultaneous", "conditional"
        ]
        
        prompt_lower = prompt.lower()
        score = sum(1 for indicator in complexity_indicators if indicator in prompt_lower)
        
        # Add base complexity
        score += len(prompt.split()) // 10
        
        return score
    
    def _has_high_risk_permissions(self) -> bool:
        """Check if agent has high-risk operation permissions."""
        # This would check against Reva's permission system
        return True  # Placeholder
    
    def _execute_secured_mission(
        self, 
        prompt: str, 
        max_iterations: int, 
        mission_id: str
    ) -> Dict[str, Any]:
        """Execute mission with security monitoring."""
        results = {
            "mission_id": mission_id,
            "original_prompt": prompt,
            "execution_log": [],
            "security_events": [],
            "policy_violations": []
        }
        
        # Parse mission into secure steps
        mission_steps = self._parse_mission_steps(prompt)
        
        for i, step in enumerate(mission_steps):
            if i >= max_iterations:
                break
            
            # Check step against security policies
            policy_check = self.policy_engine.check_step_policy(step)
            if not policy_check["approved"]:
                results["policy_violations"].append({
                    "step": i,
                    "violation": policy_check["violation"],
                    "action": "blocked"
                })
                continue
            
            # Execute step with monitoring
            step_result = self._execute_secured_step(step, mission_id)
            results["execution_log"].append(step_result)
            
            # Monitor for security events
            security_event = self._monitor_step_security(step, step_result)
            if security_event:
                results["security_events"].append(security_event)
        
        return results
    
    def _parse_mission_steps(self, prompt: str) -> List[Dict[str, Any]]:
        """Parse mission into individual steps for security evaluation."""
        steps = []
        
        # Simple step parsing - can be enhanced with NLP
        if "pick up" in prompt.lower():
            steps.append({"action": "grasp", "object": "target", "security_level": "medium"})
        if "move to" in prompt.lower():
            steps.append({"action": "navigate", "target": "destination", "security_level": "low"})
        if "place" in prompt.lower():
            steps.append({"action": "place", "location": "target_location", "security_level": "medium"})
        
        return steps
    
    def _execute_secured_step(self, step: Dict[str, Any], mission_id: str) -> Dict[str, Any]:
        """Execute a single step with security monitoring."""
        try:
            # Log step execution
            self.audit_logger.log_step_execution(mission_id, step)
            
            # Execute step through MCP server if available
            if self.mcp_server:
                result = self.mcp_server.execute_tool(step["action"], step)
            else:
                result = {"status": "simulated", "action": step["action"]}
            
            # Add security context
            result["security_level"] = step.get("security_level", "low")
            result["mission_id"] = mission_id
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Secured step execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "security_level": step.get("security_level", "low"),
                "mission_id": mission_id
            }
    
    def _monitor_step_security(self, step: Dict[str, Any], result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Monitor step execution for security events."""
        # Check for suspicious patterns
        if result.get("status") == "error" and "permission" in str(result.get("error", "")).lower():
            return {
                "event_type": "permission_denied",
                "step": step,
                "result": result,
                "severity": "medium"
            }
        
        # Check for high-risk actions
        if step.get("security_level") == "high":
            return {
                "event_type": "high_risk_action",
                "step": step,
                "result": result,
                "severity": "high"
            }
        
        return None
    
    def _perform_security_audit(self, results: Dict[str, Any], mission_id: str) -> Dict[str, Any]:
        """Perform post-mission security audit."""
        audit = {
            "mission_id": mission_id,
            "audit_timestamp": datetime.now().isoformat(),
            "security_score": 0.0,
            "violations_found": len(results["policy_violations"]),
            "security_events": len(results["security_events"]),
            "recommendations": []
        }
        
        # Calculate security score
        total_steps = len(results["execution_log"])
        violations = len(results["policy_violations"])
        events = len(results["security_events"])
        
        if total_steps > 0:
            audit["security_score"] = max(0.0, 1.0 - (violations + events) / total_steps)
        
        # Generate recommendations
        if violations > 0:
            audit["recommendations"].append("Review policy violations and update agent permissions")
        if events > 0:
            audit["recommendations"].append("Investigate security events for potential threats")
        if audit["security_score"] < 0.7:
            audit["recommendations"].append("Consider additional security training for agent")
        
        return audit
    
    def _format_secured_results(self, results: Dict[str, Any], audit: Dict[str, Any]) -> str:
        """Format results with security audit information."""
        summary = {
            "mission_results": results,
            "security_audit": audit,
            "compliance_status": "compliant" if audit["security_score"] >= 0.8 else "needs_review"
        }
        
        return json.dumps(summary, indent=2)
    
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        """Build tool definitions for Reva security capabilities."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_security_policy",
                    "description": "Check if an action complies with security policies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "Action to check against policies"
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context for policy evaluation"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "register_agent",
                    "description": "Register an agent in the Reva agent registry",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Unique identifier for the agent"
                            },
                            "capabilities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of agent capabilities"
                            },
                            "permissions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of agent permissions"
                            }
                        },
                        "required": ["agent_id", "capabilities"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audit_agent_activity",
                    "description": "Audit agent activity for security compliance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of agent to audit"
                            },
                            "time_range": {
                                "type": "object",
                                "description": "Time range for audit"
                            }
                        },
                        "required": ["agent_id"]
                    }
                }
            }
        ]
    
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from Reva API response."""
        return []
    
    def _extract_text(self, response: Any) -> str:
        """Extract text content from Reva API response."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("text", str(response))
        else:
            return str(response)


class PolicyEngine:
    """Policy engine for enforcing security policies."""
    
    def __init__(self):
        self.policies = self._load_default_policies()
    
    def _load_default_policies(self) -> Dict[str, Any]:
        """Load default security policies."""
        return {
            "allowed_actions": ["navigate", "grasp", "place", "detect"],
            "prohibited_actions": ["delete", "modify_system", "access_sensitive"],
            "risk_levels": {
                "low": ["navigate", "detect"],
                "medium": ["grasp", "place"],
                "high": ["modify_environment", "system_access"]
            }
        }
    
    def check_step_policy(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a step complies with security policies."""
        action = step.get("action", "")
        
        if action in self.policies["prohibited_actions"]:
            return {
                "approved": False,
                "violation": f"Action '{action}' is prohibited by security policy"
            }
        
        if action not in self.policies["allowed_actions"]:
            return {
                "approved": False,
                "violation": f"Action '{action}' is not in allowed actions list"
            }
        
        return {"approved": True, "violation": None}


class AuditLogger:
    """Audit logger for tracking security events."""
    
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
    
    def log_mission_start(self, prompt: str) -> str:
        """Log mission start and return mission ID."""
        mission_id = f"mission_{len(self.audit_log)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.audit_log.append({
            "mission_id": mission_id,
            "event_type": "mission_start",
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt
        })
        
        return mission_id
    
    def log_step_execution(self, mission_id: str, step: Dict[str, Any]):
        """Log step execution."""
        self.audit_log.append({
            "mission_id": mission_id,
            "event_type": "step_execution",
            "timestamp": datetime.now().isoformat(),
            "step": step
        })
    
    def log_mission_completion(self, mission_id: str, results: Dict[str, Any], audit: Dict[str, Any]):
        """Log mission completion."""
        self.audit_log.append({
            "mission_id": mission_id,
            "event_type": "mission_completion",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "audit": audit
        })
    
    def log_security_violation(self, violation: str):
        """Log security violation."""
        self.audit_log.append({
            "event_type": "security_violation",
            "timestamp": datetime.now().isoformat(),
            "violation": violation,
            "severity": "high"
        })
