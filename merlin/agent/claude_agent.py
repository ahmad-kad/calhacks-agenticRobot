from __future__ import annotations

from typing import Any, Dict, List
import json

from anthropic import Anthropic

from .base_agent import BaseAgent


class ClaudeAgent(BaseAgent):
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", verbose: bool = True) -> None:
        super().__init__()
        self.client = Anthropic()
        self.model = model
        self.messages: List[Dict[str, str]] = []
        self.verbose = verbose
        self.thought_log: List[Dict[str, Any]] = []
        self.iteration = 0

    def _log_thought(self, step: str, content: str, details: Dict[str, Any] = None) -> None:
        """Log agent's thought process for transparency."""
        log_entry = {
            "iteration": self.iteration,
            "step": step,
            "content": content,
            "details": details or {}
        }
        self.thought_log.append(log_entry)
        
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"🧠 AGENT THOUGHT #{self.iteration} - {step.upper()}")
            print(f"{'='*80}")
            print(f"\n{content}")
            if details:
                print(f"\n📊 Details:")
                print(json.dumps(details, indent=2, default=str))
            print(f"{'='*80}\n")

    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        self._log_thought(
            "mission_start",
            f"Starting mission with prompt: {prompt}",
            {"model": self.model, "max_iterations": max_iterations}
        )
        
        self.messages = [{"role": "user", "content": prompt}]
        
        for i in range(max_iterations):
            self.iteration = i + 1
            
            self._log_thought(
                "api_call",
                f"Sending request to {self.model}...",
                {"iteration": self.iteration, "messages_count": len(self.messages)}
            )
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=self._system_prompt(),
                tools=self._build_tool_defs(),
                messages=self.messages,
            )
            
            # Log the raw response
            self._log_thought(
                "api_response",
                f"Received response with stop_reason: {response.stop_reason}",
                {
                    "stop_reason": response.stop_reason,
                    "content_blocks": len(response.content),
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }
            )
            
            # Extract and log any thinking/reasoning
            thinking_text = ""
            for block in response.content:
                if hasattr(block, "type") and block.type == "thinking":
                    thinking_text = block.thinking
                    self._log_thought(
                        "agent_thinking",
                        f"Claude's internal reasoning:\n\n{thinking_text}",
                        {"thinking_length": len(thinking_text)}
                    )
            
            # Extract and log text response
            text_response = self._extract_text(response.content)
            if text_response:
                self._log_thought(
                    "agent_response",
                    f"Agent says:\n\n{text_response}",
                    {"response_length": len(text_response)}
                )
            
            # Handle end turn
            if response.stop_reason == "end_turn":
                final_text = text_response or "Mission complete"
                self._log_thought(
                    "mission_complete",
                    f"Mission completed successfully!\n\nFinal response: {final_text}",
                    {"iterations": self.iteration, "total_thoughts": len(self.thought_log)}
                )
                return final_text
            
            # Handle tool use
            if response.stop_reason == "tool_use":
                tool_calls = self._extract_tool_calls(response.content)
                
                self._log_thought(
                    "tool_use",
                    f"Agent is calling {len(tool_calls)} tool(s)",
                    {
                        "tool_count": len(tool_calls),
                        "tools": [{"name": tc["name"], "input": tc["input"]} for tc in tool_calls]
                    }
                )
                
                tool_results = self._execute_tool_calls(response.content)
                
                # Log tool execution results
                for j, (tc, result) in enumerate(zip(tool_calls, tool_results)):
                    self._log_thought(
                        f"tool_result_{j+1}",
                        f"Tool '{tc['name']}' executed successfully",
                        {
                            "tool_name": tc["name"],
                            "tool_input": tc["input"],
                            "result": result.get("content", "N/A")
                        }
                    )
                
                # Add to message history
                self.messages.append({"role": "assistant", "content": response.content})
                self.messages.append({"role": "user", "content": json.dumps(tool_results)})
        
        self._log_thought(
            "max_iterations",
            f"Reached maximum iterations ({max_iterations}) without completion",
            {"total_thoughts": len(self.thought_log)}
        )
        return "Max iterations reached"

    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        tools = self.mcp_server.get_tools()
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in tools
        ]

    def _extract_tool_calls(self, content: Any) -> List[Dict[str, Any]]:
        calls: List[Dict[str, Any]] = []
        for block in content:
            if getattr(block, "type", None) == "tool_use":
                calls.append({"name": block.name, "input": block.input, "id": block.id})
        return calls

    def _execute_tool_calls(self, content: Any) -> List[Dict[str, Any]]:
        results = []
        for block in content:
            if getattr(block, "type", None) == "tool_use":
                result = self.mcp_server.execute_tool(block.name, dict(block.input))
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        return results

    def _extract_text(self, content: Any) -> str:
        for block in content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def _system_prompt(self) -> str:
        return (
            "You are Merlin, an autonomous robot agent. Use tools to complete missions. "
            "Think step by step about what needs to be done, then execute the necessary actions. "
            "Be concise but thorough in your reasoning."
        )
    
    def get_thought_log(self) -> str:
        """Return the complete thought process as a formatted string."""
        if not self.thought_log:
            return "No thoughts recorded yet."
        
        output = f"\n{'='*80}\n"
        output += "📋 COMPLETE AGENT THOUGHT PROCESS LOG\n"
        output += f"{'='*80}\n\n"
        
        for entry in self.thought_log:
            output += f"Iteration {entry['iteration']} - {entry['step'].upper()}\n"
            output += "-" * 80 + "\n"
            output += f"{entry['content']}\n"
            if entry['details']:
                output += f"\nDetails: {json.dumps(entry['details'], indent=2, default=str)}\n"
            output += "\n"
        
        output += f"{'='*80}\n"
        output += f"Total Thoughts: {len(self.thought_log)}\n"
        output += f"{'='*80}\n"
        
        return output


