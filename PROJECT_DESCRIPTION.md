# Agentic Robot Framework (MERLIN)

## Inspiration
I wanted an LLM to control a robot as part of my school's Autonomy team. I'm looking for ways to automatically test and integrate systems. Agentic AI seems like a good way to "automate" testing features without needing a user to operate each system. The goal was to create a framework where natural language commands could directly control robotic behaviors, enabling autonomous testing and system validation without human intervention.

## What it does
MERLIN (Multi-modal Embodied Robot Learning Intelligence Network) is an agentic AI framework that enables Large Language Models to directly control robotic systems through natural language commands. The system demonstrates:

- **Natural Language Control**: Users can issue commands like "Pick up the red cube and move it to coordinates 2,2" and the robot executes the task autonomously
- **Computer Vision Integration**: Real-time object detection with confidence scoring for precise target identification
- **Autonomous Navigation**: Path planning and obstacle avoidance for safe movement in complex environments
- **Multi-object Manipulation**: Sorting, organizing, and handling multiple objects with sequential task execution
- **Error Recovery**: Adaptive behavior when tasks fail, with automatic retry strategies and alternative approaches
- **Precision Operations**: High-accuracy placement and manipulation with sub-centimeter precision
- **Mission Logging**: Comprehensive logging and monitoring for system validation and testing

The framework operates through a finite state machine that translates LLM decisions into robotic actions, enabling complex behaviors from simple natural language inputs.

## How we built it
The system is built using a modular architecture with several key components:

### **Core Architecture**
- **State Machine Engine**: Finite state machine managing robot behaviors and transitions
- **MCP (Model Context Protocol) Server**: Bridges LLM reasoning with robotic actions
- **Vision Pipeline**: Computer vision system for object detection and scene understanding
- **Hardware Abstraction Layer**: Mock controller for simulation with real hardware interfaces

### **AI Integration**
- **Claude Integration**: Anthropic's Claude model for natural language understanding and decision making
- **Ollama Support**: Local LLM deployment for offline operation
- **Agent Thinking Framework**: Structured reasoning process for complex task decomposition
- **Figma AI Integration**: Design-to-code workflows with spatial relationship understanding
- **Letta Multi-Agent Framework**: Advanced multi-agent coordination and evaluation capabilities
- **Reva Security Framework**: Comprehensive security and governance for AI operations

### **Simulation Environment**
- **3D Robot Simulator**: Custom-built simulation using matplotlib and 3D visualization
- **Mock Hardware Controller**: Simulates real robot hardware for testing and development
- **Mission Scenarios**: Predefined scenarios for testing various capabilities

### **Technical Stack**
- **Python**: Core development language
- **Matplotlib**: 3D visualization and animation
- **Computer Vision**: Object detection and scene analysis
- **JSON**: Mission logging and data persistence
- **Docker**: Containerized deployment for consistent environments

### **Development Process**
1. **Phase 1**: Type definitions and core interfaces
2. **Phase 2**: Mock controller implementation
3. **Phase 3**: State machine development
4. **Phase 4**: Full mission integration with LLM control

## Challenges we ran into
- **No Hardware Access**: Had to improvise using a simulator, which required building a comprehensive mock hardware controller
- **LLM Integration Complexity**: Bridging natural language understanding with robotic actions required careful prompt engineering and state management
- **Simulation Accuracy**: Creating realistic robot behaviors in simulation that would translate to real hardware
- **State Machine Complexity**: Managing complex robotic behaviors through finite state machines while maintaining LLM control
- **Real-time Performance**: Ensuring responsive behavior while maintaining accuracy in object detection and navigation
- **Error Handling**: Implementing robust error recovery mechanisms for autonomous operation

## Accomplishments that we're proud of
- **Successful LLM Control**: The system performs well controlling a finite state machine, demonstrating that LLMs can effectively manage complex robotic behaviors
- **Comprehensive Mission Videos**: Created 8 detailed mission videos showcasing various capabilities from basic pick-and-place to complex multi-object sorting
- **Robust Error Recovery**: Implemented adaptive error handling that allows the system to recover from failures and continue mission execution
- **Multi-modal Integration**: Successfully integrated computer vision, natural language processing, and robotic control into a cohesive system
- **Scalable Architecture**: Built a modular framework that can be extended with additional capabilities and hardware interfaces
- **Real-world Applicability**: Demonstrated practical applications for autonomous testing and system validation

## What we learned
- **LLM Capabilities**: Large Language Models can effectively control robotic systems when properly integrated with structured state machines
- **Simulation Importance**: Comprehensive simulation environments are crucial for developing and testing robotic systems without hardware access
- **Modular Design**: Building systems with clear interfaces between components enables easier testing and integration
- **Error Handling**: Robust error recovery mechanisms are essential for autonomous operation
- **Natural Language Processing**: Converting natural language commands into robotic actions requires careful prompt engineering and context management
- **Performance Optimization**: Balancing real-time responsiveness with accuracy requires careful system design and optimization

## What's next for Agentic Robot Framework
- **Expand Features**: Implement additional models in simulated environments, including more complex manipulation tasks and multi-robot coordination
- **Test on Real Robot**: Deploy the framework on actual robotic hardware to validate simulation results and refine real-world performance
- **Advanced AI Systems**: Explore AI systems to replace the Finite State Machine like Behavior Trees or Goal Action Oriented Programming for more sophisticated decision-making
- **Multi-modal Enhancement**: Integrate additional sensors and perception capabilities for more robust environmental understanding
- **Scalability Improvements**: Develop distributed processing capabilities for handling multiple robots and complex environments
- **Real-time Optimization**: Implement advanced path planning and motion control algorithms for improved performance
- **Safety Systems**: Add comprehensive safety mechanisms and fail-safe procedures for real-world deployment
- **Performance Metrics**: Develop comprehensive benchmarking and evaluation systems for continuous improvement
- **Enhanced AI Framework Integration**: Expand support for additional agentic AI frameworks including LangChain, CrewAI, and AutoGen
- **Design-Aware Operations**: Leverage Figma integration for design-driven robotic behaviors and spatial intelligence
- **Multi-Agent Orchestration**: Utilize Letta framework for complex multi-agent coordination (Swarm Systems) and performance evaluation
- **Enterprise Security**: Implement Reva security framework for production-ready AI governance and compliance

The framework represents a significant step toward fully autonomous robotic systems controlled by natural language, with applications in testing, validation, and autonomous operation across various domains.
