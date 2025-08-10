# Varga AI - AutoGen SME Platform Architecture

## Project Overview

This is an AutoGen-based SaaS platform for SME automation that provides ready-to-use AI agents and tools for Small and Medium Enterprises. The platform follows a strict 1-file-1-class principle with maximum 400 lines per file.

## Architecture Decisions

### Core Technologies
- **Python 3.12+** with uv for dependency management
- **AutoGen AgentChat 0.7.2+** for multi-agent orchestration
- **AutoGen Extensions with OpenAI 0.7.2+** for LLM integration
- **AutoGen Studio 0.1.5+** for visual agent management
- **Loguru** for centralized logging
- **Pydantic** for configuration and validation
- **httpx** for async HTTP operations

### Project Structure

```
src/
├── config/             # Configuration management
│   ├── settings.py     # Pydantic-based configuration
│   └── __init__.py
├── logging/            # Centralized logging service
│   ├── logger.py       # Loguru-based logging with tenant isolation
│   └── __init__.py
├── tools/              # Generic tools foundation
│   ├── base/           # Base classes and interfaces
│   │   ├── tool_interface.py     # Abstract tool interface
│   │   ├── base_tool.py          # Base tool implementation
│   │   ├── tool_registry.py      # Tool discovery and management
│   │   └── __init__.py
│   ├── utilities/      # Common utilities
│   │   ├── error_handler.py      # Comprehensive error handling
│   │   ├── rate_limiter.py       # Advanced rate limiting
│   │   └── __init__.py
│   ├── web_search_tool.py        # Internet search capabilities
│   ├── text_generation_tool.py   # AI text generation
│   ├── chatbot_interface_tool.py # Conversational AI interface
│   ├── tool_initializer.py       # Tool setup and management
│   ├── demo.py                   # Demo and testing script
│   ├── README.md                 # Comprehensive documentation
│   └── __init__.py
└── __init__.py
```

## Implemented Components

### 1. Configuration Management (`src/config/`)
- **PlatformSettings**: Main configuration class with environment validation
- **Tool Configurations**: Specific configs for WebSearch, TextGeneration, and Chatbot tools
- **Environment Variable Support**: Full .env file support with validation
- **Runtime Configuration Updates**: Ability to update tool configs at runtime

### 2. Logging Service (`src/logging/`)
- **Structured Logging**: JSON-structured logs with correlation IDs
- **Tenant Isolation**: Logs include tenant_id for multi-tenant deployments
- **Performance Tracking**: Built-in execution time and tool performance logging
- **Centralized Service**: Global logger instance accessible throughout the platform

### 3. Generic Tools Foundation (`src/tools/`)

#### Base Architecture
- **BaseToolInterface**: Abstract interface defining the contract for all tools
- **BaseTool**: Common implementation with rate limiting, error handling, and retry logic
- **ToolRegistry**: Central registry for tool discovery, registration, and instance management
- **ToolResult**: Standardized result format with status, data, metadata, and execution time

#### Utility Services
- **ErrorHandler**: Comprehensive error categorization, recovery strategies, and structured logging
- **AdvancedRateLimiter**: Multiple rate limiting strategies (token bucket, sliding window) with scopes (global, tenant, user, tool)

#### Implemented Tools

1. **WebSearchTool**
   - Multiple search engines (SerpAPI, Google Search API, Bing)
   - Configurable result filtering and safe search
   - Fallback to DuckDuckGo instant answers
   - AutoGen function calling integration

2. **TextGenerationTool**
   - Multiple LLM providers (OpenAI, Anthropic, Azure OpenAI)
   - Content type templates (email, document, summary, proposal, marketing copy)
   - Jinja2-based parameter substitution
   - Configurable creativity and length controls

3. **ChatbotInterfaceTool**
   - Session-based conversation management
   - Context-aware responses with business information
   - Automatic escalation detection (keywords, conversation patterns)
   - Conversation history and fallback responses

## Key Features

### AutoGen Integration
- Native AutoGen tool registration and function calling
- Automatic schema generation for agent integration
- Compatible with AssistantAgent, UserProxyAgent, and GroupChat

### Multi-Tenant Architecture
- Tenant isolation in logging and rate limiting
- Context propagation with tenant_id and correlation_id
- Secure API key management per tool and tenant

### Observability
- Structured logging with correlation IDs
- Tool execution metrics and performance tracking
- Health checks for all tools
- Registry statistics and monitoring

### Error Handling and Resilience
- Comprehensive error categorization (network, auth, validation, timeout, etc.)
- Automatic retry with exponential backoff
- Rate limit detection and handling
- Recovery strategy generation

### Rate Limiting
- Multiple algorithms (token bucket, sliding window, fixed window)
- Multi-level scopes (global, tenant, user, tool, endpoint)
- Priority-based rule evaluation
- Configurable quotas and burst limits

## Configuration

### Environment Variables
- Tool-specific configuration with `TOOL_*` prefixes
- API key management for different providers
- Rate limiting and performance tuning options
- Environment-specific settings (development, staging, production)

### Example Configuration
```bash
# Web Search
TOOL_WEB_SEARCH_ENABLED=true
SERPAPI_API_KEY=your-api-key

# Text Generation
TOOL_TEXT_GENERATION_MODEL_PROVIDER=openai
OPENAI_API_KEY=your-api-key

# Chatbot
TOOL_CHATBOT_INTERFACE_MAX_CONVERSATION_LENGTH=50
```

## Usage Patterns

### AutoGen Agent Integration
```python
from src.tools import get_tool
from autogen_agentchat.agents import AssistantAgent

# Get tool and integrate with agent
web_search = get_tool("web_search")
agent = AssistantAgent(
    name="research_agent",
    tools=[web_search.get_schema()]
)
```

### Direct Tool Usage
```python
from src.tools.tool_initializer import initialize_tools

await initialize_tools()
web_search = get_tool("web_search")
result = await web_search.execute({
    "query": "AutoGen framework",
    "max_results": 5
})
```

## Development Guidelines

### Code Organization
- Strict 1-file-1-class principle (max 400 lines)
- Type hints and comprehensive docstrings required
- Async-first design for all I/O operations
- Proper resource management and cleanup

### Error Handling
- Use the centralized ErrorHandler for consistent error management
- Categorize errors appropriately (network, auth, validation, etc.)
- Provide recovery strategies where possible
- Log errors with proper context and correlation IDs

### Testing and Demo
- Demo script available at `src/tools/demo.py`
- Health checks implemented for all tools
- Mock-friendly design for unit testing

## Future Enhancements

### Planned Tools
- **Integration Tools**: Google Workspace, Microsoft 365, Slack, CRM systems
- **Analysis Tools**: Data processing, report generation, sentiment analysis
- **Automation Tools**: Workflow orchestration, task scheduling

### Platform Extensions
- Agent marketplace and discovery
- Visual workflow builder
- Real-time monitoring dashboard
- Multi-language support

## Dependencies

Core dependencies added to pyproject.toml:
- loguru: Structured logging
- pydantic: Configuration and validation
- httpx: Async HTTP client
- tenacity: Retry logic
- jinja2: Template processing
- beautifulsoup4: HTML parsing
- aiofiles: Async file operations

This architecture provides a solid foundation for the AutoGen-based SME automation platform, with production-ready tools that can be easily extended and integrated into various agent workflows.