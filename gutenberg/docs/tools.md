---
sidebar_position: 4
---

# Tools Reference

This document provides comprehensive documentation for all available tools in the Varga AI Platform.

## Overview

The platform includes a robust foundation of generic tools designed to handle common business automation tasks. All tools follow a consistent architecture and provide AutoGen integration out of the box.

## Tool Architecture

### Base Components

All tools inherit from the base architecture which provides:

- **Standardized Interface**: Consistent API across all tools
- **Error Handling**: Comprehensive error management with recovery strategies
- **Rate Limiting**: Advanced multi-scope rate limiting
- **Logging**: Structured logging with tenant isolation
- **Health Monitoring**: Built-in health checks and metrics
- **AutoGen Integration**: Native AutoGen function calling support

### Tool Registry

The `ToolRegistry` manages all available tools and provides:

- **Automatic Discovery**: Tools are automatically registered
- **Health Monitoring**: Real-time health status for all tools
- **Metadata Management**: Tool capabilities, schemas, and documentation
- **Usage Statistics**: Track tool usage and performance metrics

## Generic Tools

### 1. Web Search Tool

**Purpose**: Provides internet search capabilities for research and information gathering.

**Capabilities**:
- Multiple search engine support (SerpAPI, Google Search API, Bing)
- Configurable result filtering and formatting
- Safe search and content filtering
- Automatic retry and fallback mechanisms
- DuckDuckGo fallback for no-API-key scenarios

**Configuration**:
```python
TOOL_WEB_SEARCH_API_KEY=your_serp_api_key
TOOL_WEB_SEARCH_ENGINE=google  # google, bing, duckduckgo
TOOL_WEB_SEARCH_SAFE_SEARCH=true
TOOL_WEB_SEARCH_MAX_RESULTS=10
```

**Usage Example**:
```python
from src.tools import get_tool

web_search = get_tool("web_search")
result = await web_search.execute({
    "query": "AutoGen framework documentation",
    "max_results": 5,
    "country": "us",
    "language": "en"
})
```

**AutoGen Integration**:
```python
from autogen_agentchat.agents import AssistantAgent

web_search = get_tool("web_search")
agent = AssistantAgent(
    name="research_agent",
    tools=[web_search.get_schema()],
    system_message="You are a research assistant that can search the web for information."
)
```

**Key Features**:
- Up to 50 results per search
- Snippet extraction and URL validation
- Country and language filtering
- Safe search enforcement
- Automatic fallback to DuckDuckGo if API keys are unavailable

### 2. Text Generation Tool

**Purpose**: Generates various types of business content using AI language models.

**Capabilities**:
- Multiple LLM providers (OpenAI, Anthropic, Azure OpenAI)
- 12 specialized content type templates
- Jinja2-based parameter substitution
- Configurable creativity and length controls
- Token usage tracking and cost monitoring

**Content Types Available**:
1. **Email** - Professional email composition
2. **Letter** - Formal business letters
3. **Document** - Technical documentation
4. **Report** - Business reports and analysis
5. **Summary** - Content summarization
6. **Proposal** - Business proposals
7. **Marketing Copy** - Marketing materials
8. **Social Media** - Social media posts
9. **Blog Post** - Blog articles
10. **Product Description** - E-commerce descriptions
11. **Press Release** - Public relations content
12. **Meeting Notes** - Meeting documentation

**Configuration**:
```python
TOOL_TEXT_GENERATION_PROVIDER=openai  # openai, anthropic, azure
TOOL_TEXT_GENERATION_MODEL=gpt-4
TOOL_TEXT_GENERATION_API_KEY=your_api_key
TOOL_TEXT_GENERATION_MAX_TOKENS=2000
TOOL_TEXT_GENERATION_TEMPERATURE=0.7
```

**Usage Example**:
```python
text_gen = get_tool("text_generation")
result = await text_gen.execute({
    "content_type": "email",
    "subject": "Project Update",
    "recipient_name": "John Doe",
    "sender_name": "Jane Smith",
    "context": "Weekly project status update",
    "tone": "professional",
    "length": "medium"
})
```

**Template Variables**:
- `subject`: Email/document subject
- `recipient_name`: Target recipient
- `sender_name`: Content author
- `company_name`: Organization name
- `context`: Business context
- `tone`: Communication tone
- `length`: Content length preference

### 3. Chatbot Interface Tool

**Purpose**: Provides conversational AI capabilities with session management and escalation handling.

**Capabilities**:
- Session-based conversation management
- Context-aware responses with business information
- Automatic escalation detection and handling
- Conversation history and analytics
- Multi-turn conversation support

**Configuration**:
```python
TOOL_CHATBOT_PROVIDER=openai
TOOL_CHATBOT_MODEL=gpt-4
TOOL_CHATBOT_API_KEY=your_api_key
TOOL_CHATBOT_MAX_HISTORY=10
TOOL_CHATBOT_ESCALATION_KEYWORDS=["manager", "supervisor", "complaint"]
```

**Usage Example**:
```python
chatbot = get_tool("chatbot_interface")
result = await chatbot.execute({
    "session_id": "customer_123",
    "message": "I need help with my order",
    "user_name": "John Customer",
    "business_context": {
        "company_name": "Acme Corp",
        "business_hours": "9 AM - 5 PM EST",
        "support_email": "support@acme.com"
    }
})
```

**Escalation Detection**:
The tool automatically detects when conversations should be escalated based on:
- **Keywords**: Specific escalation keywords
- **Sentiment**: Negative sentiment detection
- **Conversation Length**: Extended conversations without resolution
- **Pattern Recognition**: Common escalation patterns

**Conversation Status**:
- `active`: Ongoing conversation
- `paused`: Temporarily paused
- `ended`: Conversation completed
- `escalated`: Escalated to human agent

## Tool Utilities

### Error Handling

The error handling system provides comprehensive error management:

**Error Categories**:
- `NetworkError`: Connection and API issues
- `AuthenticationError`: Authentication failures
- `ValidationError`: Input validation issues
- `RateLimitError`: Rate limit exceeded
- `ConfigurationError`: Configuration problems
- `ToolExecutionError`: Tool-specific execution errors

**Error Severity Levels**:
- `LOW`: Minor issues that don't affect functionality
- `MEDIUM`: Issues that may affect some functionality
- `HIGH`: Issues that significantly impact functionality
- `CRITICAL`: Issues that completely prevent functionality

**Recovery Strategies**:
- Automatic retry with exponential backoff
- Fallback to alternative providers
- Graceful degradation
- Error reporting and logging

### Rate Limiting

The rate limiting system supports multiple algorithms and scopes:

**Algorithms**:
- **Token Bucket**: Allows burst traffic with sustained rate limiting
- **Sliding Window**: Precise rate limiting over time windows

**Scopes**:
- `global`: Platform-wide limits
- `tenant`: Per-tenant limits
- `user`: Per-user limits
- `tool`: Per-tool limits
- `endpoint`: Per-endpoint limits

**Configuration Example**:
```python
rate_rules = [
    RateLimitRule(
        scope="tenant",
        limit=1000,
        window=3600,  # 1 hour
        priority=1
    ),
    RateLimitRule(
        scope="tool",
        tool_name="web_search",
        limit=100,
        window=300,  # 5 minutes
        priority=2
    )
]
```

## Tool Development

### Creating Custom Tools

To create a custom tool, inherit from `BaseTool`:

```python
from src.tools.base import BaseTool, ToolMetadata, ToolResult, ToolCapability

class CustomTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="custom_tool",
            description="A custom tool for specific business needs",
            version="1.0.0",
            capabilities=[
                ToolCapability.TEXT_PROCESSING,
                ToolCapability.API_INTEGRATION
            ],
            requires_auth=True,
            rate_limit_tier="standard"
        )
    
    async def _do_execute(self, input_data: dict, context: dict) -> ToolResult:
        # Implement your tool logic here
        try:
            # Process input_data
            result = await your_business_logic(input_data)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"execution_time": 0.5}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_type="execution_error"
            )
```

### Tool Registration

Tools are automatically registered when imported. You can also manually register tools:

```python
from src.tools.base import get_registry

registry = get_registry()
registry.register_tool(CustomTool())
```

### Health Checks

All tools support health checks:

```python
tool = get_tool("custom_tool")
health_status = await tool.health_check()

if health_status.is_healthy:
    print("Tool is healthy")
else:
    print(f"Tool issues: {health_status.issues}")
```

## Configuration Management

### Environment Variables

Tools are configured using environment variables with the `TOOL_` prefix:

```bash
# Global tool settings
TOOL_DEFAULT_TIMEOUT=30
TOOL_MAX_RETRIES=3
TOOL_LOG_LEVEL=INFO

# Tool-specific settings
TOOL_WEB_SEARCH_API_KEY=your_api_key
TOOL_TEXT_GENERATION_PROVIDER=openai
TOOL_CHATBOT_MAX_HISTORY=10
```

### Configuration Classes

Each tool has its own configuration class:

```python
from src.config.settings import WebSearchConfig, TextGenerationConfig

# Access tool configuration
web_config = WebSearchConfig()
print(f"Max results: {web_config.max_results}")

text_config = TextGenerationConfig()
print(f"Provider: {text_config.provider}")
```

### Runtime Configuration Updates

Configuration can be updated at runtime:

```python
from src.config import get_config_manager

config_manager = get_config_manager()
await config_manager.update_tool_config(
    "web_search",
    {"max_results": 20, "safe_search": False}
)
```

## Best Practices

### Performance Optimization

1. **Use Async Operations**: All tools support async execution
2. **Configure Appropriate Timeouts**: Set reasonable timeouts for external API calls
3. **Implement Caching**: Cache frequently requested data
4. **Monitor Resource Usage**: Track memory and CPU usage

### Error Handling

1. **Use Structured Errors**: Always use the provided error classes
2. **Provide Recovery Strategies**: Implement fallback mechanisms
3. **Log Errors Appropriately**: Use structured logging with context
4. **Monitor Error Rates**: Track and alert on error patterns

### Security

1. **Validate All Inputs**: Always validate and sanitize inputs
2. **Use Secure Configuration**: Store API keys securely
3. **Implement Rate Limiting**: Protect against abuse
4. **Log Security Events**: Monitor for suspicious activity

### Testing

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test tool interactions
3. **Mock External Services**: Use mocks for API calls
4. **Load Testing**: Test performance under load

## Monitoring and Observability

### Metrics

All tools provide comprehensive metrics:

- **Execution Count**: Number of tool executions
- **Success Rate**: Percentage of successful executions
- **Average Response Time**: Average execution time
- **Error Rate**: Percentage of failed executions
- **Resource Usage**: CPU and memory consumption

### Logging

Structured logging includes:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "tool_name": "web_search",
  "operation": "execute",
  "tenant_id": "tenant_123",
  "correlation_id": "req_456",
  "duration_ms": 250,
  "success": true,
  "metadata": {
    "query": "AutoGen documentation",
    "results_count": 5
  }
}
```

### Health Monitoring

Regular health checks ensure tool availability:

```python
# Check individual tool health
tool_health = await tool.health_check()

# Check all tools health
registry = get_registry()
health_report = await registry.health_check_all()
```

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure API keys are properly configured
   - Check key permissions and quotas
   - Verify environment variable names

2. **Rate Limit Exceeded**:
   - Check rate limit configuration
   - Implement exponential backoff
   - Consider using multiple API keys

3. **Timeout Errors**:
   - Increase timeout values
   - Check network connectivity
   - Implement retry mechanisms

4. **Authentication Failures**:
   - Verify credentials
   - Check token expiration
   - Ensure proper OAuth flows

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger("src.tools").setLevel(logging.DEBUG)
```

### Tool Inspector

Use the tool inspector for runtime debugging:

```python
from src.tools.demo import inspect_tool

await inspect_tool("web_search")
```