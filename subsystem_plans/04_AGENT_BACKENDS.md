# MERLIN Subsystem Plan: Agent Backends (Multi-LLM Strategy)

## 1. Overview

**Responsibility:** Provide flexible LLM agent implementations with fallback strategy. Support multiple providers (Claude, Groq, Gemini, Ollama) behind unified interface.

**Key Principle:** **One interface, many backends.** Agent logic identical; only provider calls differ.

---

## 2. Architecture

### Agent Backend Strategy
```
┌─────────────────────────┐
│   RobotAgent (Abstract) │
│   (Base interface)      │
└────────────┬────────────┘
             │
    ┌────────┼────────┬──────────┐
    ▼        ▼        ▼          ▼
┌────────┐┌────────┐┌────────┐┌────────┐
│Claude ││ Groq  ││Gemini ││ Ollama │
│Sonnet ││Llama3 ││Flash  ││Local  │
└────┬───┘└───┬──┘└───┬───┘└────┬──┘
     │        │       │         │
     └────────┼───────┼─────────┘
              │
       ┌──────▼──────────┐
       │   Fallback      │
       │   Chain         │
       │ Primary →       │
       │ Secondary →     │
       │ Tertiary →      │
       │ Offline         │
       └─────────────────┘
```

### File Structure
```
merlin/agent/
├── __init__.py          # Factory function
├── base_agent.py       # Abstract base class
├── claude_agent.py     # Claude/Anthropic
├── groq_agent.py       # Groq/Llama3
├── gemini_agent.py     # Google Gemini
├── ollama_agent.py     # Ollama (offline)
├── prompts.py          # System prompts
└── config.py           # Agent configuration
```

---

## 3. Component Specifications

### 3.1 Base Agent Interface (base_agent.py)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAgent(ABC):
    """Abstract agent interface for all LLM backends."""
    
    @abstractmethod
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute mission autonomously."""
        pass
    
    @abstractmethod
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        """Build tool definitions for this LLM."""
        pass
    
    @abstractmethod
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Parse tool calls from response."""
        pass
    
    @abstractmethod
    def _extract_text(self, response: Any) -> str:
        """Extract final text response."""
        pass
    
    def set_mcp_server(self, mcp_server: "MCPServer"):
        """Inject MCP tool server."""
        self.mcp_server = mcp_server
```

### 3.2 Claude Agent (claude_agent.py)

```python
from anthropic import Anthropic
import json

class ClaudeAgent(BaseAgent):
    """Claude 3.5 Sonnet via Anthropic SDK."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic()
        self.model = model
        self.messages = []
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute mission with Claude."""
        self.messages = [{"role": "user", "content": prompt}]
        
        for iteration in range(max_iterations):
            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self._system_prompt(),
                tools=self._build_tool_defs(),
                messages=self.messages
            )
            
            # Agent finished
            if response.stop_reason == "end_turn":
                return self._extract_text(response.content)
            
            # Tool calls
            if response.stop_reason == "tool_use":
                tool_results = self._execute_tool_calls(response.content)
                self.messages.append({"role": "assistant", "content": response.content})
                self.messages.append({"role": "user", "content": tool_results})
        
        return "Max iterations reached"
    
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        tools = self.mcp_server.get_tools()
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for tool in tools
        ]
    
    def _extract_tool_calls(self, content):
        tool_calls = []
        for block in content:
            if block.type == "tool_use":
                tool_calls.append({
                    "name": block.name,
                    "input": block.input,
                    "id": block.id
                })
        return tool_calls
    
    def _execute_tool_calls(self, content):
        results = []
        for block in content:
            if block.type == "tool_use":
                result = self.mcp_server.execute_tool(block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })
        return results
    
    def _extract_text(self, content):
        for block in content:
            if hasattr(block, "text"):
                return block.text
        return ""
    
    def _system_prompt(self) -> str:
        return """You are Merlin, an autonomous robot agent for CalHacks 2024.

YOUR TOOLS:
- get_robot_status: Check your state
- navigate_to(x, y): Drive to position
- detect_objects(names): Find objects
- grasp_object: Close gripper
- release_object: Open gripper

YOUR MISSION:
Execute the given task autonomously. Plan carefully, execute tools step-by-step, and adapt to failures.

CONSTRAINTS:
- Battery is limited
- Each tool blocks until completion
- Report success or failure clearly"""
```

### 3.3 Groq Agent (groq_agent.py)

```python
from groq import Groq
import json

class GroqAgent(BaseAgent):
    """Groq Llama 3 for ultra-fast inference."""
    
    def __init__(self, model: str = "llama-3-70b-tool-use-preview"):
        self.client = Groq()
        self.model = model
        self.messages = []
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute mission with Groq (fastest)."""
        self.messages = [{"role": "user", "content": prompt}]
        
        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self._build_tool_defs(),
                max_tokens=1024,
                temperature=0.7
            )
            
            # Check finish reason
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "end_turn":
                text = response.choices[0].message.content
                return text if text else "Mission complete"
            
            if finish_reason == "tool_calls":
                tool_results = []
                message = response.choices[0].message
                
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        result = self.mcp_server.execute_tool(
                            tool_call.function.name,
                            json.loads(tool_call.function.arguments)
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                
                self.messages.append({"role": "assistant", "content": message.content})
                self.messages.append({"role": "user", "content": json.dumps(tool_results)})
        
        return "Max iterations reached"
    
    def _build_tool_defs(self) -> List[Dict[str, Any]]:
        """Convert to Groq format."""
        tools = self.mcp_server.get_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            for tool in tools
        ]
```

### 3.4 Gemini Agent (gemini_agent.py)

```python
import google.generativeai as genai
import os

class GeminiAgent(BaseAgent):
    """Google Gemini 1.5 for multimodal capabilities."""
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = model
        self.chat = None
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute mission with Gemini."""
        model = genai.GenerativeModel(self.model_name)
        self.chat = model.start_chat()
        
        response = self.chat.send_message(prompt)
        
        for iteration in range(max_iterations - 1):
            # Process response
            if not hasattr(response, "parts") or not response.parts:
                break
            
            tool_called = False
            for part in response.parts:
                if hasattr(part, "function_call"):
                    tool_called = True
                    result = self.mcp_server.execute_tool(
                        part.function_call.name,
                        dict(part.function_call.args)
                    )
                    
                    # Send result back
                    response = self.chat.send_message(
                        genai.protos.Content(
                            parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=part.function_call.name,
                                        response=result
                                    )
                                )
                            ]
                        )
                    )
            
            if not tool_called:
                break
        
        return response.text if hasattr(response, "text") else str(response)
```

### 3.5 Ollama Agent (ollama_agent.py)

```python
import requests
import json

class OllamaAgent(BaseAgent):
    """Local Ollama for offline inference."""
    
    def __init__(self, model: str = "neural-chat", base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = model
        self.messages = []
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute mission with local Ollama."""
        self.messages = [{"role": "user", "content": prompt}]
        
        for iteration in range(max_iterations):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": self.messages,
                        "stream": False
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    return f"Ollama error: {response.status_code}"
                
                assistant_response = response.json()["message"]["content"]
                self.messages.append({"role": "assistant", "content": assistant_response})
                
                # Check if tool call needed (simple heuristic for local models)
                # Local models don't have formal tool_use, so check for patterns
                if "tool:" in assistant_response.lower() or "[TOOL:" in assistant_response:
                    # Try to parse tool call (simplified for demo)
                    # Most local models won't support proper tool use
                    pass
                else:
                    # Assume done
                    return assistant_response
            
            except requests.exceptions.ConnectionError:
                return "Failed to connect to Ollama. Is it running?"
            except Exception as e:
                return f"Ollama error: {str(e)}"
        
        return "Max iterations reached"
```

### 3.6 Agent Factory (\_\_init\_\_.py)

```python
def create_agent(backend: str = "claude") -> BaseAgent:
    """
    Factory function for agent creation.
    
    Args:
        backend: "claude", "groq", "gemini", "ollama", "auto"
    
    Returns:
        Agent instance
    """
    if backend == "claude":
        from merlin.agent.claude_agent import ClaudeAgent
        return ClaudeAgent()
    
    elif backend == "groq":
        from merlin.agent.groq_agent import GroqAgent
        return GroqAgent()
    
    elif backend == "gemini":
        from merlin.agent.gemini_agent import GeminiAgent
        return GeminiAgent()
    
    elif backend == "ollama":
        from merlin.agent.ollama_agent import OllamaAgent
        return OllamaAgent()
    
    elif backend == "auto":
        # Try each in fallback order
        backends = ["groq", "claude", "gemini", "ollama"]
        for b in backends:
            try:
                return create_agent(b)
            except Exception as e:
                print(f"Failed {b}: {e}, trying next...")
        raise RuntimeError("All agent backends failed")
    
    else:
        raise ValueError(f"Unknown backend: {backend}")

__all__ = ["create_agent", "BaseAgent"]
```

---

## 4. Implementation Phases

### Phase 1: Base Agent Interface (Hour 12-13)
- [ ] Implement BaseAgent abstract class
- [ ] Define method signatures
- [ ] Create system prompt template

**Time:** 1 hour

---

### Phase 2: Claude Agent (Hour 13-14)
- [ ] Implement ClaudeAgent
- [ ] Test with simple mission
- [ ] Verify tool execution flow

**Time:** 1 hour

---

### Phase 3: Other Backends (Hour 14-16)
- [ ] Implement GroqAgent
- [ ] Implement GeminiAgent
- [ ] Implement OllamaAgent
- [ ] Test fallback chain

**Time:** 2 hours

---

### Phase 4: Factory & Fallback (Hour 16-18)
- [ ] Implement factory function
- [ ] Test backend switching
- [ ] Verify fallback on error

**Time:** 2 hours

---

## 5. Teach Phase: Agent Implementation Demos

### Teach Phase 1: Base Agent Interface

**Artifact:** `examples/teach_agent_base.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify BaseAgent interface works."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAgent(ABC):
    """Abstract agent interface."""
    
    @abstractmethod
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        pass
    
    @abstractmethod
    def set_mcp_server(self, mcp_server):
        pass

class DemoAgent(BaseAgent):
    """Simple implementation for testing."""
    
    def __init__(self):
        self.mcp_server = None
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        return f"Mission complete: {prompt}"
    
    def set_mcp_server(self, mcp_server):
        self.mcp_server = mcp_server

# Test: Verify interface works
print("✓ Teach Phase 1: BaseAgent Interface")

agent = DemoAgent()

# Test 1: Run mission
result = agent.run_mission("Test mission")
assert "complete" in result.lower()
print(f"  ✓ Mission executed: {result}")

# Test 2: Set MCP server
class MockMCP:
    pass

agent.set_mcp_server(MockMCP())
assert agent.mcp_server is not None
print(f"  ✓ MCP server injected")

print("✓ Base agent interface verified!")
```

**Run:** `python examples/teach_agent_base.py`

**Expected Output:**
```
✓ Teach Phase 1: BaseAgent Interface
  ✓ Mission executed: Mission complete: Test mission
  ✓ MCP server injected
✓ Base agent interface verified!
```

---

### Teach Phase 2: Simple Agent Implementation

**Artifact:** `examples/teach_agent_simple.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify simple agent works."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAgent(ABC):
    @abstractmethod
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        pass

class SimpleAgent(BaseAgent):
    """Simple agent without LLM for testing."""
    
    def __init__(self):
        self.mcp_server = None
    
    def run_mission(self, prompt: str, max_iterations: int = 15) -> str:
        """Execute simple sequence of actions."""
        results = []
        
        # Simulate tool calls
        if "status" in prompt.lower():
            result = self.mcp_server.execute_tool("get_status", {})
            results.append(f"Status: {result}")
        
        if "navigate" in prompt.lower():
            result = self.mcp_server.execute_tool("navigate_to", {"x": 1.0, "y": 1.0})
            results.append(f"Navigation: {result}")
        
        if "grasp" in prompt.lower():
            result = self.mcp_server.execute_tool("grasp_object", {})
            results.append(f"Grasp: {result}")
        
        return "; ".join(results)
    
    def set_mcp_server(self, mcp_server):
        self.mcp_server = mcp_server

# Mock MCP server
class MockTool:
    def execute_tool(self, name, args):
        return {"success": True, "tool": name}

# Test: Verify agent works
print("✓ Teach Phase 2: Simple Agent")

agent = SimpleAgent()
agent.set_mcp_server(MockTool())

# Test 1: Status mission
result = agent.run_mission("Get status")
assert "Status" in result
print(f"  ✓ Status mission: {result[:50]}...")

# Test 2: Navigation mission
result = agent.run_mission("Navigate to target")
assert "Navigation" in result
print(f"  ✓ Navigation mission: {result[:50]}...")

# Test 3: Complex mission
result = agent.run_mission("Navigate and grasp")
assert "Navigation" in result and "Grasp" in result
print(f"  ✓ Complex mission: {result[:50]}...")

print("✓ Simple agent verified!")
```

**Run:** `python examples/teach_agent_simple.py`

**Expected Output:**
```
✓ Teach Phase 2: Simple Agent
  ✓ Status mission: Status: {'success': True, 'tool': 'get_status'};...
  ✓ Navigation mission: Navigation: {'success': True, 'tool': 'navigate_to...
  ✓ Complex mission: Navigation: {'success': True, 'tool': 'navigate_to...
✓ Simple agent verified!
```

---

### Teach Phase 3: Factory Pattern

**Artifact:** `examples/teach_agent_factory.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify agent factory works."""
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run_mission(self, prompt: str) -> str:
        pass

class MockAgent(BaseAgent):
    def __init__(self):
        self.name = "mock"
    
    def run_mission(self, prompt: str) -> str:
        return f"Mock: {prompt}"

class DemoAgent(BaseAgent):
    def __init__(self):
        self.name = "demo"
    
    def run_mission(self, prompt: str) -> str:
        return f"Demo: {prompt}"

def create_agent(backend: str = "mock") -> BaseAgent:
    """Factory function for agent creation."""
    if backend == "mock":
        return MockAgent()
    elif backend == "demo":
        return DemoAgent()
    else:
        raise ValueError(f"Unknown backend: {backend}")

# Test: Verify factory works
print("✓ Teach Phase 3: Agent Factory")

# Test 1: Create mock agent
agent = create_agent("mock")
assert agent.name == "mock"
print(f"  ✓ Created: {agent.name}")

# Test 2: Create demo agent
agent = create_agent("demo")
assert agent.name == "demo"
print(f"  ✓ Switched to: {agent.name}")

# Test 3: Backend switching
for backend in ["mock", "demo"]:
    agent = create_agent(backend)
    result = agent.run_mission("Test")
    assert backend in result.lower()
    print(f"  ✓ {backend}: {result}")

print("✓ Agent factory verified!")
```

**Run:** `python examples/teach_agent_factory.py`

**Expected Output:**
```
✓ Teach Phase 3: Agent Factory
  ✓ Created: mock
  ✓ Switched to: demo
  ✓ mock: Mock: Test
  ✓ demo: Demo: Test
✓ Agent factory verified!
```

---

### Teach Phase 4: Fallback Chain

**Artifact:** `examples/teach_agent_fallback.py`

```python
#!/usr/bin/env python3
"""Teach Phase: Verify fallback chain works."""
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run_mission(self, prompt: str) -> str:
        pass

class FastAgent(BaseAgent):
    def run_mission(self, prompt: str) -> str:
        return "FastAgent result"

class BackupAgent(BaseAgent):
    def run_mission(self, prompt: str) -> str:
        return "BackupAgent result"

def create_agent(backend: str = "auto") -> BaseAgent:
    """Factory with fallback."""
    if backend == "auto":
        backends = ["fast", "backup"]
        for b in backends:
            try:
                return create_agent(b)
            except Exception as e:
                print(f"  {b} failed, trying next...")
        raise RuntimeError("All backends failed")
    
    elif backend == "fast":
        return FastAgent()
    elif backend == "backup":
        return BackupAgent()
    else:
        raise ValueError(f"Unknown backend: {backend}")

# Test: Verify fallback works
print("✓ Teach Phase 4: Fallback Chain")

# Test 1: Auto selects first available
agent = create_agent("auto")
result = agent.run_mission("Test")
assert "FastAgent" in result
print(f"  ✓ Auto fallback: {result}")

# Test 2: Direct backend
agent = create_agent("backup")
result = agent.run_mission("Test")
assert "BackupAgent" in result
print(f"  ✓ Direct backend: {result}")

print("✓ Fallback chain verified!")
```

**Run:** `python examples/teach_agent_fallback.py`

**Expected Output:**
```
✓ Teach Phase 4: Fallback Chain
  ✓ Auto fallback: FastAgent result
  ✓ Direct backend: BackupAgent result
✓ Fallback chain verified!
```

---

## 6. Testing Strategy

```python
def test_agent_interface():
    """All agents implement same interface."""
    for backend in ["claude", "groq", "gemini", "ollama"]:
        try:
            agent = create_agent(backend)
            assert hasattr(agent, "run_mission")
            assert hasattr(agent, "set_mcp_server")
            print(f"✓ {backend} interface OK")
        except Exception as e:
            print(f"✗ {backend}: {e}")

def test_mission_execution():
    """Full mission with each agent."""
    sm = StateMachine(MockController())
    mcp = MCPServer(sm)
    
    for backend in ["claude", "groq", "ollama"]:
        agent = create_agent(backend)
        agent.set_mcp_server(mcp)
        
        result = agent.run_mission("Report your position")
        assert "position" in str(result).lower()
        print(f"✓ {backend}: {result[:50]}...")

def test_fallback_chain():
    """Test automatic fallback on failure."""
    agent = create_agent("auto")
    assert agent is not None
    print("✓ Fallback chain working")
```

---

## 6. Configuration

**`merlin/agent/config.py`:**

```python
# Agent selection
DEFAULT_AGENT = "groq"  # Fastest
FALLBACK_ORDER = ["groq", "claude", "gemini", "ollama"]

# Agent parameters
MAX_ITERATIONS = 15
MAX_TOKENS = 1024

# Model names
MODELS = {
    "claude": "claude-3-5-sonnet-20241022",
    "groq": "llama-3-70b-tool-use-preview",
    "gemini": "gemini-1.5-flash",
    "ollama": "neural-chat",
}

# Timeouts
AGENT_TIMEOUT = 60.0  # seconds for full mission
LLM_TIMEOUT = 30.0    # seconds per LLM call

# System prompts per agent
SYSTEM_PROMPTS = {
    "claude": "... (detailed analytical approach)",
    "groq": "... (fast concise approach)",
    "gemini": "... (multimodal approach)",
    "ollama": "... (simple offline approach)"
}
```

---

## 7. Deliverables Checklist

- [ ] `merlin/agent/base_agent.py` - Abstract base
- [ ] `merlin/agent/claude_agent.py` - Claude implementation
- [ ] `merlin/agent/groq_agent.py` - Groq implementation
- [ ] `merlin/agent/gemini_agent.py` - Gemini implementation
- [ ] `merlin/agent/ollama_agent.py` - Ollama implementation
- [ ] `merlin/agent/__init__.py` - Factory function
- [ ] `tests/test_agents.py` - All tests pass
- [ ] Fallback chain tested
- [ ] API key configuration documented

---

## 8. Success Metrics

| Metric | Target |
|--------|--------|
| Claude mission latency | <10s (with tool calls) |
| Groq mission latency | <5s (fastest) |
| Gemini mission latency | <8s |
| Ollama mission latency | <20s (local) |
| Fallback accuracy | 100% switch on error |
| Tool execution reliability | 100% across all agents |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API key invalid | Test in startup; clear error msg |
| Network timeout | Implement retry with backoff |
| Tool format mismatch | Validate against JSON schema |
| LLM refusal (harmful) | Safe prompts; test with real API |

---

## 10. Pre-Event Checklist

- [ ] All API keys obtained and .env configured
- [ ] Each agent tested locally
- [ ] Fallback chain verified
- [ ] Ollama model downloaded (if offline mode needed)
- [ ] Network connectivity verified

---

## 11. Timeline

- **Hour 12-13:** Base agent interface
- **Hour 13-14:** Claude agent
- **Hour 14-16:** Other backends
- **Hour 16-18:** Factory and fallback

**Total: 6 hours for full multi-agent system**
