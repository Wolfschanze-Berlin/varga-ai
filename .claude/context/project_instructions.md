# Varga AI Project Management Instructions

## 🎯 Project Identity

**Name**: Varga AI - AutoGen SME Automation Platform  
**Vision**: Democratize AI automation for Small and Medium Enterprises through ready-to-use, configurable AI agents  
**Target**: 1,000 SME signups and $500K revenue in Year 1  

## 🏗️ Architecture Overview

### Core Stack
- **Python 3.12+** with `uv` package manager (ALWAYS use `uv` commands)
- **AutoGen Framework** (AgentChat 0.7.2+) for multi-agent orchestration
- **Loguru** for centralized logging (NEVER use print statements)
- **Pydantic** for all configuration management
- **Docusaurus** for documentation site (gutenberg/ directory)

### Key Architectural Principles
1. **Strict 1-file-1-class rule**: Maximum 400 lines per file
2. **Multi-tenant by design**: All components must support tenant isolation
3. **Async-first**: All I/O operations must be async
4. **Configuration-driven**: Use Pydantic models for all configs
5. **Tool-based architecture**: Everything is a tool that agents can use

## 📁 Project Structure

```
varga-ai/
├── agents/                     # AutoGen agent implementations
│   ├── base/                  # Base agent classes and registry
│   ├── categories/            # Domain-specific agents
│   │   ├── assistant/        # Smart assistant agents
│   │   ├── education/        # Educational agents (Language Teacher)
│   │   ├── marketing/        # Marketing agents (Image Generator)
│   │   ├── sales/           # Sales automation agents (TODO)
│   │   ├── customer_service/ # Customer service agents (TODO)
│   │   ├── operations/      # Operations agents (TODO)
│   │   └── finance/         # Finance agents (TODO)
│   └── shared/               # Shared interfaces and utilities
│
├── src/                       # Core platform code
│   ├── config/               # Configuration management
│   ├── logging/              # Centralized logging service
│   └── tools/                # Tool implementations
│       ├── base/             # Base tool classes
│       ├── integrations/     # External integrations
│       │   ├── browser_automation/  # Browser automation tools
│       │   ├── communication/       # Telegram, Slack, etc.
│       │   ├── image_generation/    # DALL-E integration
│       │   ├── memory/             # Conversation memory
│       │   └── web/                # Web search tools
│       └── utilities/        # Common utilities
│
├── gutenberg/                 # Docusaurus documentation site
│   ├── docs/                 # Documentation pages
│   │   ├── project/         # Project documentation
│   │   ├── telegram-bots/   # Telegram bot docs
│   │   └── agents/          # Agent documentation (TODO)
│   └── src/                 # React components
│
└── .claude/                  # Claude Code configuration
    └── context/             # Project context and history
```

## 🚀 Development Workflow

### Starting Development
```bash
# ALWAYS start by checking environment
uv venv  # Create virtual environment if needed
uv sync  # Install/update dependencies
source .venv/bin/activate  # Activate environment

# Check current branch
git status
git branch

# Read context FIRST
cat .claude/context/history.json
```

### Adding New Features

1. **ALWAYS update history.json** when making significant changes
2. **Create proper documentation** in gutenberg/docs/
3. **Follow the pattern**: Look at existing implementations first
4. **Test locally** before committing

### Working with Agents

When creating a new agent:
1. Create folder in `agents/categories/{category}/{agent_name}/`
2. Required files:
   - `agent.py` - Main agent implementation
   - `config.yaml` - Configuration
   - `README.md` - Documentation
   - `prompts/` - Prompt templates
   - `tools/` - Agent-specific tools
   - `tests/` - Test suite

### Working with Tools

When creating a new tool:
1. Inherit from `BaseTool` in `src/tools/base/base_tool.py`
2. Register in `ToolRegistry`
3. Add configuration to `src/config/settings.py`
4. Create integration test in tool directory
5. Document in tool's README.md

## 🔧 Key Components Already Implemented

### 1. Language Teacher Agent (`agents/categories/education/language_teacher/`)
- **Status**: COMPLETE with Telegram integration
- **Features**: Adaptive learning, spaced repetition, NLP processing
- **AI Models**: IRT/BKT for personalization, SM-2+ for retention
- **Integration**: Full Telegram bot with voice support

### 2. Image Generator Agent (`agents/categories/marketing/image_generator/`)
- **Status**: COMPLETE with DALL-E integration
- **Features**: Marketing image generation, style customization
- **Integration**: AutoGen conversation manager

### 3. Smart Assistant (`agents/categories/assistant/`)
- **Status**: COMPLETE with orchestration
- **Features**: Multi-capability assistant with tool selection
- **Integration**: Telegram bot main entry point

### 4. Browser Automation (`src/tools/integrations/browser_automation/`)
- **Status**: COMPLETE with browser_use integration
- **Features**: Web scraping, form filling, automated browsing
- **Integration**: Task classifier and session management

### 5. Telegram Integration (`src/tools/integrations/communication/telegram_tool.py`)
- **Status**: COMPLETE
- **Features**: Full bot support, media handling, inline keyboards
- **Scripts**: `telegram_bot_main.py`, `language_teacher_bot.py`

## 📋 Implementation Priorities

### Phase 1: Core Platform (Current)
- [x] Base tool architecture
- [x] Configuration management
- [x] Logging service
- [x] Language Teacher agent
- [x] Telegram integration
- [x] Browser automation
- [ ] Database layer (PostgreSQL + SQLAlchemy)
- [ ] Authentication system

### Phase 2: Agent Library
- [ ] Sales agents (Lead Qualifier, Appointment Scheduler)
- [ ] Customer Service agents (Ticket Handler, FAQ Responder)
- [ ] Finance agents (Invoice Processor, Payment Reminder)
- [ ] Operations agents (Inventory Tracker, Workflow Automator)

### Phase 3: Platform Features
- [ ] Visual workflow builder
- [ ] Agent marketplace UI
- [ ] Analytics dashboard
- [ ] Billing integration (Stripe)

## 🛠️ Configuration Management

### Environment Variables
```bash
# Always use .env file (never commit)
cp .env.template .env

# Key variables:
OPENAI_API_KEY=xxx
TELEGRAM_BOT_TOKEN=xxx
SERPAPI_API_KEY=xxx
DATABASE_URL=postgresql://...
```

### Tool Configuration
- Each tool has config in `src/config/settings.py`
- Runtime updates via `config_manager.update_tool_config()`
- Tool-specific YAML files in tool directories

## 📝 Documentation Standards

### Code Documentation
- **Docstrings**: Google style for all classes/functions
- **Type hints**: Required for all parameters and returns
- **Comments**: Only for complex logic, avoid obvious comments

### Project Documentation
- **Location**: All docs in `gutenberg/docs/`
- **Format**: MDX with Docusaurus frontmatter
- **Structure**: Hierarchical with clear navigation
- **Diagrams**: Use Mermaid for architecture/flow diagrams

### Update Process
1. Make code changes
2. Update relevant docs in gutenberg/
3. Update `.claude/context/history.json`
4. Update sidebars.ts if adding new pages

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/         # Component tests
├── integration/  # Tool/agent integration tests
├── e2e/         # End-to-end workflow tests
└── fixtures/    # Test data and mocks
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/unit/test_language_teacher.py

# Run with coverage
uv run pytest --cov=src --cov=agents
```

## 🚢 Deployment

### Local Development
```bash
# Start documentation site
cd gutenberg && npm start

# Run Telegram bot
uv run python telegram_bot_main.py

# Run language teacher bot
uv run python language_teacher_bot.py
```

### Production Deployment
- **Infrastructure**: AWS (ECS, RDS, S3)
- **CI/CD**: GitHub Actions
- **Monitoring**: CloudWatch + Sentry
- **Database**: PostgreSQL on RDS

## ⚠️ Critical Rules

### MUST DO
1. **ALWAYS** use `uv` for Python package management
2. **ALWAYS** update `.claude/context/history.json` for significant changes
3. **ALWAYS** check existing patterns before implementing new features
4. **ALWAYS** use centralized logging (never print())
5. **ALWAYS** follow 1-file-1-class rule (max 400 lines)
6. **ALWAYS** write docs in `gutenberg/` with proper structure

### NEVER DO
1. **NEVER** commit `.env` files or secrets
2. **NEVER** create files without checking existing patterns
3. **NEVER** use synchronous I/O in async functions
4. **NEVER** bypass the tool registry for tool management
5. **NEVER** create agents without proper folder structure

## 🔍 Quick Reference

### Common Commands
```bash
# Virtual environment
uv venv && source .venv/bin/activate

# Install/update deps
uv sync

# Add new dependency
uv add package_name

# Run main app
uv run python main.py

# Run Telegram bot
uv run python telegram_bot_main.py

# Documentation
cd gutenberg && npm start

# Git workflow
git status
git add -A
git commit -m "feat: description"
git push origin dev
```

### Key Files
- `projectBrief.md` - Full project specification
- `CLAUDE.md` - Claude Code instructions
- `.claude/context/history.json` - Development history
- `src/config/settings.py` - Main configuration
- `agents/base/agent_registry.py` - Agent registry
- `src/tools/base/tool_registry.py` - Tool registry

### Integration Points
- **Telegram Bot**: `telegram_bot_main.py` + `TelegramBot` tool
- **AutoGen Agents**: `agents/categories/*/agent.py`
- **Tool System**: `src/tools/base/base_tool.py`
- **Configuration**: `src/config/config_manager.py`
- **Logging**: `src/logging/logger.py`

## 📊 Success Metrics

### Technical Metrics
- 80% test coverage
- <2s API response time
- 99.9% uptime
- Zero critical bugs in production

### Business Metrics
- 1,000 SME signups Year 1
- $500K revenue Year 1
- 25-30 production agents
- 5 main integration categories

## 🆘 Troubleshooting

### Common Issues

1. **Import errors**: Check virtual environment activation
2. **Config errors**: Verify .env file exists and has required keys
3. **Tool not found**: Ensure tool is registered in ToolRegistry
4. **Agent errors**: Check config.yaml and prompts directory
5. **Telegram bot issues**: Verify bot token and permissions

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use logger for debugging
from src.logging import get_logger
logger = get_logger("debug")
logger.debug("Debug message")
```

## 📚 Learning Resources

### Internal Documentation
- `/gutenberg/docs/` - Project documentation
- Agent READMEs in each agent folder
- Tool documentation in tool directories

### External Resources
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Docusaurus Documentation](https://docusaurus.io/)

---

**Remember**: This is a production system for SMEs. Quality, reliability, and user experience are paramount. Always think about the end user (SME employee) when making decisions.