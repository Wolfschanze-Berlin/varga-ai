# Enhanced AutoGen Image Generation Agent

A comprehensive demonstration of advanced AutoGen patterns and capabilities for collaborative AI image generation workflows. This enhanced implementation showcases sophisticated multi-agent coordination, conversation management, and workflow orchestration using Microsoft's AutoGen framework.

## 🚀 Key Features & AutoGen Enhancements

### 1. **Enhanced Agent Architecture**
- **Advanced conversation patterns** with state management
- **Multi-agent collaboration** workflows
- **Intelligent message routing** based on context
- **Dynamic function calling** with comprehensive schemas
- **Context-aware response generation**

### 2. **Workflow Orchestration**
- **Multi-agent workflow coordination** with dependency management
- **Sequential, parallel, and conditional** execution patterns
- **Workflow templates** for different use cases
- **Performance monitoring** and metrics collection
- **Error handling and recovery** mechanisms

### 3. **Conversation Management**
- **Sophisticated conversation state** transitions
- **Consensus building** and decision-making processes
- **Context compression** and memory management
- **Thread-based conversation** tracking
- **Agent capability profiles** for optimal collaboration

### 4. **Advanced AutoGen Patterns**
- **Group chat orchestration** with intelligent speaker selection
- **Function calling schemas** for complex operations
- **Resilient agent wrappers** with retry mechanisms
- **Circuit breaker patterns** for error resilience
- **Performance optimization** utilities

## 📁 File Structure

```
agents/categories/marketing/image_generator/
├── agent.py                           # Original implementation
├── enhanced_agent.py                  # Enhanced agent with AutoGen patterns
├── workflow_orchestrator.py           # Multi-agent workflow coordination
├── autogen_conversation_manager.py    # Advanced conversation management
├── autogen_tools.py                   # AutoGen-specific utilities and tools
├── usage_examples.py                  # Comprehensive usage demonstrations
├── config.yaml                        # Agent configuration
├── README.md                          # This file
└── prompts/
    └── system_prompts.md              # System message templates
```

## 🎯 AutoGen-Specific Improvements

### **Enhanced Agent (`enhanced_agent.py`)**

**Key Improvements:**
- **Multi-stage workflow coordination** with specialist agent personas
- **Advanced conversation state management** (concept → refinement → generation → review)
- **Intelligent agent-to-agent communication** patterns
- **Function calling integration** with comprehensive schemas
- **Context-aware message handling** with routing based on conversation type

**Showcase Features:**
```python
# Demonstrates sophisticated workflow coordination
async def generate_image_with_workflow(self, request, context):
    # Stage 1: Concept Development with Creative Director
    concept_result = await self._concept_development_stage(image_request)
    
    # Stage 2: Prompt Engineering 
    prompt_result = await self._prompt_engineering_stage(image_request)
    
    # Stage 3: Image Generation
    generation_result = await self._generation_stage(image_request)
    
    # Stage 4: Quality Review
    review_result = await self._quality_review_stage(image_request)
```

### **Workflow Orchestrator (`workflow_orchestrator.py`)**

**Key Features:**
- **Complex workflow templates** (Collaborative, Iterative Refinement, Brand Review, Campaign Series)
- **Dependency-aware step execution** with proper ordering
- **Specialized agent creation** with role-based system messages
- **Group chat management** for workflow execution
- **Performance metrics** and execution analytics

**Example Workflow Types:**
```python
class WorkflowType(Enum):
    SIMPLE = "simple"
    COLLABORATIVE = "collaborative"
    ITERATIVE_REFINEMENT = "iterative_refinement" 
    BRAND_REVIEW = "brand_review"
    CAMPAIGN_SERIES = "campaign_series"
```

### **Conversation Manager (`autogen_conversation_manager.py`)**

**Advanced Patterns:**
- **Conversation state transitions** with intelligent flow management
- **Agent capability profiles** for optimal speaker selection
- **Consensus building facilitation** with different methods (unanimous, majority, weighted)
- **Context compression** and memory management
- **Performance monitoring** with detailed analytics

**Conversation Flow Example:**
```python
# Demonstrates intelligent conversation state transitions
INITIATED → CONCEPT_DEVELOPMENT → COLLABORATIVE_REVIEW → 
CONSENSUS_BUILDING → DECISION_MAKING → EXECUTION → COMPLETED
```

### **AutoGen Tools (`autogen_tools.py`)**

**Specialized Utilities:**
- **Function calling schemas** for complex operations
- **Conversation patterns** for sequential and consensus workflows
- **Error handling patterns** with circuit breakers and retry logic
- **Performance optimization** wrappers
- **System message templates** for different agent roles

## 🛠 Usage Examples

### Basic Enhanced Agent Usage

```python
from agents.categories.marketing.image_generator.enhanced_agent import EnhancedImageGeneratorAgent
from agents.base.base_agent import AgentConfig

# Create enhanced agent
config = AgentConfig(
    name="enhanced_image_generator",
    description="Enhanced marketing image generator with AutoGen capabilities",
    category="marketing",
    system_message="Enhanced system message with AutoGen patterns"
)

agent = EnhancedImageGeneratorAgent(config)
await agent.initialize()

# Execute with enhanced capabilities
response = await agent.execute(
    "Create a professional social media image for a tech startup launch",
    context={"enable_collaboration": True}
)
```

### Workflow Orchestration

```python
from agents.categories.marketing.image_generator.workflow_orchestrator import ImageGenerationOrchestrator, WorkflowType

# Create orchestrator
orchestrator = ImageGenerationOrchestrator(config)
await orchestrator.setup()

# Create and execute collaborative workflow
workflow_id = await orchestrator.create_workflow(
    workflow_type=WorkflowType.COLLABORATIVE,
    request="Create a professional advertisement for a luxury car brand",
    context={"brand": "luxury_automotive"}
)

# Execute workflow with specialist agents
result = await orchestrator.execute_workflow(workflow_id, image_agent)
```

### Advanced Conversation Management

```python
from agents.categories.marketing.image_generator.autogen_conversation_manager import AutoGenConversationManager

# Create conversation manager
conv_manager = AutoGenConversationManager(config)
await conv_manager.setup()

# Start collaborative conversation
thread_id = await conv_manager.start_conversation(
    template_type="collaborative_refinement",
    initial_message="We need to refine our creative approach",
    participants=["creative_director", "prompt_engineer", "qa_reviewer"]
)

# Execute conversation to completion
result = await conv_manager.execute_conversation(thread_id)
```

### Function Calling Patterns

```python
from agents.categories.marketing.image_generator.autogen_tools import AutoGenImageTools

# Register advanced functions with agent
function_implementations = {
    "generate_marketing_image": generate_marketing_image_impl,
    "start_collaborative_review": start_collaborative_review_impl,
    "coordinate_agent_workflow": coordinate_agent_workflow_impl
}

AutoGenImageTools.register_functions_with_agent(
    agent.get_agent(), 
    function_implementations
)
```

## 📊 Comprehensive Examples

Run the complete demonstration suite:

```python
from agents.categories.marketing.image_generator.usage_examples import run_autogen_examples

# Run all examples demonstrating AutoGen capabilities
results = await run_autogen_examples()
```

Individual example demonstrations:

```python
# Basic enhanced agent patterns
await demo_basic_enhanced_agent()

# Workflow orchestration 
await demo_workflow_orchestration()

# Conversation management
await demo_conversation_management()

# Function calling patterns
await demo_function_calling()

# Group chat and consensus
await demo_group_chat_consensus()

# Error handling and resilience
await demo_error_handling()
```

## 🔧 Configuration

### Agent Configuration (`config.yaml`)

The enhanced agent supports comprehensive configuration including:

- **Workflow templates** for different collaboration patterns
- **Marketing templates** with platform-specific optimizations
- **Quality standards** and compliance requirements
- **Performance limits** and monitoring settings
- **Security and compliance** configurations

### System Messages

Enhanced system messages leverage AutoGen capabilities:

```python
system_message = AutoGenImageTools.create_enhanced_system_message(
    role="image_generator_coordinator",
    specialties=["workflow_coordination", "multi_agent_communication"],
    context={"workflow_type": "collaborative"}
)
```

## 🎨 Key AutoGen Pattern Demonstrations

### 1. **Multi-Agent Collaboration**
- Specialist agents with defined roles and capabilities
- Intelligent speaker selection based on conversation context
- Coordinated workflow execution with dependency management

### 2. **Advanced Conversation Management**
- State-aware conversation flows
- Context compression and memory optimization
- Consensus building and decision facilitation

### 3. **Function Calling Integration**
- Comprehensive function schemas for complex operations
- Coordinated function execution across multiple agents
- Error handling and retry mechanisms

### 4. **Group Chat Orchestration**
- Dynamic group formation based on task requirements
- Intelligent conversation routing and management
- Performance monitoring and optimization

### 5. **Error Resilience**
- Circuit breaker patterns for group chats
- Resilient agent wrappers with retry logic
- Graceful degradation and recovery mechanisms

## 📈 Performance Features

- **Execution metrics** and performance monitoring
- **Conversation analytics** with success rate tracking
- **Agent performance profiling** with optimization suggestions
- **Resource usage optimization** with context compression
- **Scalability patterns** for production deployment

## 🧪 Testing and Validation

The implementation includes comprehensive examples that validate:

- **Multi-agent workflow coordination** accuracy
- **Conversation state management** reliability  
- **Function calling integration** effectiveness
- **Error handling and recovery** robustness
- **Performance optimization** impact

## 🚀 Getting Started

1. **Setup the enhanced agent:**
   ```python
   from agents.categories.marketing.image_generator.enhanced_agent import EnhancedImageGeneratorAgent
   
   # Configure and initialize
   agent = EnhancedImageGeneratorAgent(config)
   await agent.initialize()
   ```

2. **Run example demonstrations:**
   ```python
   from agents.categories.marketing.image_generator.usage_examples import run_autogen_examples
   
   # See all capabilities in action
   results = await run_autogen_examples()
   ```

3. **Explore specific patterns:**
   - Check individual files for detailed implementations
   - Review usage examples for specific use cases
   - Adapt patterns to your specific requirements

## 💡 Key Learning Points

This enhanced implementation demonstrates:

1. **Sophisticated AutoGen Patterns** - How to leverage AutoGen's advanced features beyond basic chat
2. **Multi-Agent Coordination** - Best practices for orchestrating complex agent interactions
3. **Conversation Management** - Advanced patterns for managing long-running, stateful conversations
4. **Function Integration** - Proper patterns for integrating tools and external services
5. **Production Readiness** - Error handling, monitoring, and optimization for real-world deployment

## 🔗 Integration with Existing Project

The enhanced implementation:
- **Extends the existing DALL-E tool** without breaking compatibility
- **Follows project patterns** (1 file 1 class, loguru logging)
- **Integrates with base agent classes** and configuration management
- **Maintains backward compatibility** while adding advanced features
- **Provides upgrade path** from basic to advanced AutoGen usage

---

This enhanced implementation showcases how AutoGen can be leveraged for sophisticated AI agent coordination, making it an excellent example of advanced AutoGen patterns in action. The comprehensive examples and detailed documentation make it easy to understand and adapt these patterns for other use cases.