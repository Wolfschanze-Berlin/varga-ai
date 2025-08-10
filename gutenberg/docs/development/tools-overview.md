---
sidebar_position: 2
title: Tools Overview
description: Comprehensive documentation for all available tools in the Varga AI platform
---

# AutoGen SME Platform - Generic Tools

This directory contains the foundational generic tools for the AutoGen-based SME automation platform. These tools provide essential capabilities that can be reused across different agent types and business use cases.

## Overview

The tools are designed with the following principles:

- **AutoGen Integration**: Native support for AutoGen's tool registration and function calling
- **Multi-tenant Architecture**: Built-in tenant isolation and context management
- **Rate Limiting**: Sophisticated rate limiting with multiple strategies and scopes
- **Error Handling**: Comprehensive error handling with categorization and recovery strategies
- **Observability**: Structured logging with correlation IDs and performance metrics
- **Scalability**: Async-first design with proper resource management

## Available Tools

### 1. Web Search Tool (`WebSearchTool`)

Provides internet search capabilities for agents to gather information.

**Capabilities:**
- Multiple search engine support (SerpAPI, Google Search API, Bing)
- Configurable result filtering and formatting
- Safe search and content filtering
- Automatic retry and fallback mechanisms

**Usage:**
```python
from src.tools import get_tool

web_search = get_tool("web_search")
result = await web_search.execute({
    "query": "AutoGen Microsoft AI framework",
    "max_results": 10,
    "include_snippets": True,
    "safe_search": True
})
```

### 2. Text Generation Tool (`TextGenerationTool`)

Provides AI-powered text generation capabilities for various content types.

**Capabilities:**
- Multiple content types (email, document, summary, proposal, marketing copy)
- Template-based generation with parameter substitution
- Multiple LLM providers (OpenAI, Anthropic, Azure OpenAI)
- Configurable creativity and length controls

**Usage:**
```python
text_gen = get_tool("text_generation")
result = await text_gen.execute({
    "content_type": "email",
    "prompt": "Meeting follow-up about project status",
    "parameters": {
        "tone": "professional",
        "recipient": "team members"
    },
    "max_tokens": 500
})
```

### 3. Chatbot Interface Tool (`ChatbotInterfaceTool`)

Provides conversational AI capabilities for customer interactions.

**Capabilities:**
- Session-based conversation management
- Context-aware responses with business information
- Automatic escalation detection and handling
- Conversation history and analytics
- Fallback responses for error scenarios

**Usage:**
```python
chatbot = get_tool("chatbot_interface")

# Start conversation
result = await chatbot.execute({
    "action": "start_conversation",
    "business_context": {
        "business_name": "Acme Corp",
        "business_type": "E-commerce"
    }
})

# Send message
result = await chatbot.execute({
    "action": "send_message",
    "conversation_id": conversation_id,
    "user_message": "I need help with my order"
})
```

## Architecture

### Directory Structure

```
src/tools/
├── base/                   # Base classes and interfaces
│   ├── tool_interface.py   # Abstract base class for all tools
│   ├── base_tool.py        # Common tool implementation
│   └── tool_registry.py    # Tool discovery and management
├── utilities/              # Common utilities
│   ├── error_handler.py    # Error handling and recovery
│   └── rate_limiter.py     # Advanced rate limiting
├── web_search_tool.py      # Web search implementation
├── text_generation_tool.py # Text generation implementation
├── chatbot_interface_tool.py # Chatbot interface implementation
├── tool_initializer.py     # Tool setup and initialization
└── demo.py                # Demo and testing script
```

### Base Components

#### `BaseToolInterface`
Abstract interface that all tools must implement:
- `execute()`: Main execution method
- `validate_input()`: Input validation
- `health_check()`: Health monitoring
- `metadata`: Tool description and schema

#### `BaseTool`
Base implementation providing:
- Rate limiting with configurable strategies
- Error handling and retry logic
- HTTP client management
- Structured logging
- AutoGen schema generation

#### `ToolRegistry`
Central registry for tool management:
- Tool registration and discovery
- Instance creation and caching
- Metadata and schema access
- Auto-discovery from packages

### Utilities

#### Error Handling
Comprehensive error handling system:
- Error categorization (network, auth, validation, etc.)
- Severity levels (low, medium, high, critical)
- Recovery strategy generation
- Structured error logging

#### Rate Limiting
Advanced rate limiting with multiple strategies:
- Token bucket and sliding window algorithms
- Multiple scopes (global, tenant, user, tool)
- Priority-based rule evaluation
- Automatic quota management

## Configuration

### Environment Variables

```bash
# Web Search Tool
TOOL_WEB_SEARCH_ENABLED=true
TOOL_WEB_SEARCH_SEARCH_ENGINE=serpapi
SERPAPI_API_KEY=your-api-key

# Text Generation Tool  
TOOL_TEXT_GENERATION_ENABLED=true
TOOL_TEXT_GENERATION_MODEL_PROVIDER=openai
OPENAI_API_KEY=your-api-key

# Chatbot Interface Tool
TOOL_CHATBOT_INTERFACE_ENABLED=true
TOOL_CHATBOT_INTERFACE_MODEL_PROVIDER=openai
TOOL_CHATBOT_INTERFACE_MAX_CONVERSATION_LENGTH=50
```

### Programmatic Configuration

```python
from src.config import get_config_manager

config_manager = get_config_manager()

# Update tool configuration
config_manager.update_tool_config("web_search", {
    "max_results": 20,
    "rate_limit_per_minute": 100
})
```

## Usage Patterns

### AutoGen Integration

```python
from autogen_agentchat.agents import AssistantAgent
from src.tools import get_tool

# Get tool instance
web_search = get_tool("web_search")

# Create agent with tool
agent = AssistantAgent(
    name="research_agent",
    model_client=model_client,
    tools=[web_search.get_schema()]
)

# Tool will be called automatically by AutoGen
```

### Direct Tool Usage

```python
from src.tools.tool_initializer import initialize_tools

# Initialize all tools
await initialize_tools()

# Use tools directly
web_search = get_tool("web_search")
result = await web_search.execute(
    input_data={"query": "AI automation trends"},
    context={"tenant_id": "acme-corp", "user_id": "user-123"}
)
```

### Custom Tool Development

```python
from src.tools.base import BaseTool, ToolMetadata, ToolCapability, ToolResult, ToolStatus

class CustomTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="custom_tool",
            description="My custom tool",
            version="1.0.0",
            capabilities=[ToolCapability.INTEGRATION],
            input_schema={...},
            output_schema={...}
        )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        # Validate input
        return True
    
    async def _do_execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        # Implement tool logic
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={"result": "success"}
        )
```

## Monitoring and Observability

### Structured Logging

All tools generate structured logs with:
- Tool name and version
- Execution time and status
- Tenant and user context
- Correlation IDs for tracing
- Error details and stack traces

### Health Checks

Tools provide health check endpoints:
```python
web_search = get_tool("web_search")
is_healthy = await web_search.health_check()
```

### Metrics and Analytics

Tool registry provides statistics:
```python
from src.tools import get_tool_registry

registry = get_tool_registry()
stats = registry.get_registry_stats()
# Returns: tool counts, capability distribution, instance counts
```

## Testing

### Running Demos

```bash
cd src/tools
python demo.py
```

### Unit Testing

```python
import pytest
from src.tools import WebSearchTool

@pytest.mark.asyncio
async def test_web_search():
    tool = WebSearchTool({"api_key": "test-key"})
    
    # Mock API responses
    # Test tool functionality
```

## Best Practices

1. **Always use context**: Include tenant_id and correlation_id for proper isolation and tracing
2. **Handle errors gracefully**: Use the error handling utilities for consistent error management
3. **Respect rate limits**: Configure appropriate rate limits for your use case
4. **Monitor health**: Implement proper health checks for production deployments
5. **Use structured logging**: Include relevant metadata in log messages
6. **Cleanup resources**: Always call cleanup methods when shutting down

## Contributing

When adding new tools:

1. Inherit from `BaseTool` or implement `BaseToolInterface`
2. Follow the 1-file-1-class principle (max 400 lines)
3. Include comprehensive docstrings and type hints
4. Add proper input validation and error handling
5. Register tools in the initializer
6. Add configuration options
7. Include tests and documentation

## Security Considerations

- API keys are handled securely through environment variables
- Input validation prevents injection attacks
- Rate limiting protects against abuse
- Tenant isolation ensures data privacy
- Error messages don't leak sensitive information