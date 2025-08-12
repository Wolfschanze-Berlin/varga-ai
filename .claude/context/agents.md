# Agent Usage Guide for Varga AI AutoGen Platform

## Table of Contents
1. [Quick Reference](#quick-reference)
2. [Development Agents](#development-agents)
3. [Business Domain Agents](#business-domain-agents)
4. [Agent Invocation Patterns](#agent-invocation-patterns)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Quick Reference

### Priority Agent Activation Sequence
```
Phase 1: autogen-specialist → python-pro → backend-architect → sql-pro
Phase 2: telegram-bot-specialist → frontend-developer → test-automator
Phase 3: performance-engineer → database-optimizer → security-auditor
Phase 4: terraform-specialist → api-documenter → code-reviewer
```

### Golden Rules
1. **ALWAYS** use `context7` MCP tool before starting any implementation
2. **ALWAYS** invoke `autogen-specialist` for AutoGen-specific code
3. **NEVER** skip `test-automator` before marking features complete
4. **ALWAYS** use `code-reviewer` after significant changes
5. **USE** `context-manager` for tasks exceeding 10k tokens

---

## Development Agents

### 1. autogen-specialist
**Purpose**: AutoGen framework implementation, multi-agent orchestration
**When to Use**:
- Setting up new AutoGen agents
- Implementing GroupChat, Swarm, or GraphFlow patterns
- Configuring agent communication patterns
- Troubleshooting AutoGen-specific issues

**Invocation Example**:
```
Task tool → autogen-specialist
Prompt: "Create a RoundRobinGroupChat implementation for the lead qualification workflow with 3 agents: 
1) Lead scorer that evaluates lead quality
2) Lead router that assigns to sales reps
3) Follow-up scheduler that creates calendar events
Use MessageFilterAgent to reduce token usage and implement proper error handling"
```

### 2. python-pro
**Purpose**: Core Python implementation with async patterns, decorators
**When to Use**:
- Writing agent class implementations
- Implementing async/await patterns for Telegram bot
- Creating decorators for agent methods
- Optimizing Python performance

**Invocation Example**:
```
Task tool → python-pro
Prompt: "Implement the LeadQualifierAgent class following these requirements:
- Inherit from AutoGen's AssistantAgent
- Use async/await for all external API calls
- Implement retry logic with exponential backoff
- Use loguru for centralized logging
- Max 400 lines per file, follow 1 class per file principle"
```

### 3. backend-architect
**Purpose**: API design, microservices, database schemas
**When to Use**:
- Designing new REST endpoints
- Creating database schemas for multi-tenancy
- Planning microservice boundaries
- Reviewing system architecture

**Invocation Example**:
```
Task tool → backend-architect
Prompt: "Design RESTful API endpoints for the agent marketplace with:
- Multi-tenant isolation using schema-based approach
- Pagination for agent listing (25 items per page)
- Search/filter by category, industry, and capabilities
- Rate limiting per tenant (100 requests/minute)
- OpenAPI specification compatible structure"
```

### 4. telegram-bot-specialist
**Purpose**: Telegram bot integration and webhook configuration
**When to Use**:
- Setting up Telegram bot webhooks
- Implementing command handlers
- Creating inline keyboards and callbacks
- Managing conversation state

**Invocation Example**:
```
Task tool → telegram-bot-specialist
Prompt: "Implement Telegram bot integration that:
- Uses python-telegram-bot with async/await
- Routes /start command to lead qualification agent
- Maintains session state in Redis
- Implements inline keyboard for agent selection
- Handles webhook with secret token validation"
```

### 5. sql-pro
**Purpose**: Database design and query optimization
**When to Use**:
- Creating normalized schemas
- Writing complex analytical queries
- Optimizing slow queries
- Implementing database migrations

**Invocation Example**:
```
Task tool → sql-pro
Prompt: "Design PostgreSQL schema for multi-tenant agent usage tracking:
- Schema-based isolation per tenant
- Tables: agent_executions, agent_metrics, usage_logs
- Partitioning by date for usage_logs
- Indexes for common query patterns
- Window functions for analytics dashboard"
```

### 6. test-automator
**Purpose**: Comprehensive test suite creation
**When to Use**:
- After implementing new features
- Creating integration tests for agent workflows
- Setting up E2E tests
- Mocking AutoGen interactions

**Invocation Example**:
```
Task tool → test-automator
Prompt: "Create test suite for LeadQualifierAgent:
- Unit tests for score calculation logic
- Integration test with mock AutoGen runtime
- Test async Telegram bot interaction
- Mock external API calls
- Achieve 80% code coverage
- Use pytest with async fixtures"
```

### 7. deployment-engineer
**Purpose**: CI/CD, Docker, Kubernetes configuration
**When to Use**:
- Setting up GitHub Actions workflows
- Creating Docker containers for agents
- Configuring ECS deployments
- Implementing infrastructure automation

**Invocation Example**:
```
Task tool → deployment-engineer
Prompt: "Set up CI/CD pipeline with:
- GitHub Actions for automated testing on PR
- Docker multi-stage builds for agent containers
- ECS task definitions for agent deployment
- Automatic deployment to staging on main branch
- Manual approval for production deployment"
```

### 8. performance-engineer
**Purpose**: Performance optimization and load testing
**When to Use**:
- Profiling slow agent executions
- Optimizing LLM token usage
- Implementing caching strategies
- Load testing the platform

**Invocation Example**:
```
Task tool → performance-engineer
Prompt: "Optimize agent performance:
- Profile token usage per agent execution
- Implement Redis caching for frequent queries
- Add request batching for LLM calls
- Set up monitoring with CloudWatch metrics
- Load test for 500 concurrent agent executions"
```

### 9. security-auditor
**Purpose**: Security review and compliance
**When to Use**:
- Before production deployment
- Implementing authentication/authorization
- Reviewing multi-tenant isolation
- Ensuring OWASP compliance

**Invocation Example**:
```
Task tool → security-auditor
Prompt: "Security audit for multi-tenant platform:
- Verify schema-based isolation is bulletproof
- Review JWT implementation for API auth
- Check for SQL injection vulnerabilities
- Validate input sanitization in agents
- Ensure secrets are properly managed in AWS Secrets Manager"
```

### 10. code-reviewer
**Purpose**: Code quality and best practices review
**When to Use**:
- After completing feature implementation
- Before merging to main branch
- After major refactoring
- Weekly code quality checks

**Invocation Example**:
```
Task tool → code-reviewer
Prompt: "Review the lead qualification agent implementation for:
- AutoGen best practices adherence
- Proper error handling and logging
- Code organization (1 file = 1 class, max 400 lines)
- Async/await pattern correctness
- Test coverage adequacy"
```

---

## Business Domain Agents

### Sales Category
```
agents/categories/sales/
├── lead_qualifier/
│   ├── agent.py         # Main agent implementation
│   ├── config.yaml      # Agent configuration
│   ├── prompts/         # System prompts
│   ├── tools/           # External integrations
│   └── tests/           # Test suite
├── appointment_scheduler/
├── quote_generator/
├── follow_up_agent/
└── pipeline_manager/
```

**Implementation Pattern**:
```python
# agent.py structure
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

class LeadQualifierAgent(AssistantAgent):
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name="lead_qualifier",
            model_client=model_client,
            system_message=self._load_prompt(),
            description="Qualifies and scores incoming leads"
        )
```

### Customer Service Category
- **ticket_handler**: Routes support tickets
- **faq_responder**: Handles common questions
- **escalation_manager**: Identifies critical issues
- **feedback_collector**: Gathers customer feedback

### Operations Category
- **inventory_tracker**: Monitors stock levels
- **order_processor**: Handles fulfillment
- **workflow_automator**: Custom workflows
- **task_dispatcher**: Assigns tasks

### Finance Category
- **invoice_processor**: Generates invoices
- **expense_tracker**: Categorizes expenses
- **payment_reminder**: Payment follow-ups
- **receipt_manager**: Document processing

### Marketing Category
- **content_creator**: Generates content
- **social_media_scheduler**: Plans posts
- **email_campaign_manager**: Email marketing
- **analytics_reporter**: Tracks metrics

---

## Agent Invocation Patterns

### Single Agent Invocation
```
Task tool → [agent_name]
Description: "Clear 3-5 word task description"
Prompt: "Detailed requirements..."
```

### Parallel Agent Invocation
```
# For independent tasks, invoke multiple agents in one message
Task tool → python-pro
Task tool → sql-pro
Task tool → test-automator
```

### Sequential Agent Pipeline
```
1. Task tool → backend-architect (design API)
2. Task tool → python-pro (implement API)
3. Task tool → test-automator (create tests)
4. Task tool → code-reviewer (review implementation)
```

### Complex Workflow Pattern
```
# For tasks > 10k tokens
Task tool → context-manager
Prompt: "Coordinate the following multi-agent workflow:
1. autogen-specialist: Set up GroupChat
2. python-pro: Implement 5 agent classes
3. test-automator: Create integration tests
4. deployment-engineer: Containerize agents
Maintain context across all steps and provide unified summary"
```

---

## Best Practices

### 1. Documentation First
```
ALWAYS: Update gutenberg/docs/ after implementing features
ALWAYS: Use api-documenter for new endpoints
ALWAYS: Maintain .claude/context/history.json
```

### 2. Testing Strategy
```
BEFORE marking complete: test-automator
MINIMUM coverage: 80%
ALWAYS test: Agent interactions, API endpoints, Telegram handlers
```

### 3. Error Handling
```
USE: error-detective for production issues
IMPLEMENT: Retry logic with exponential backoff
LOG: All errors with loguru centralized logging
```

### 4. Performance Optimization
```
MONITOR: Token usage per agent
CACHE: Frequent queries in Redis
PROFILE: Before and after optimization
LOAD TEST: 2x expected capacity
```

### 5. Security Checklist
```
✓ Multi-tenant isolation verified
✓ Authentication implemented (JWT/OAuth2)
✓ Input validation on all endpoints
✓ Secrets in AWS Secrets Manager
✓ OWASP compliance checked
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. AutoGen Agent Not Responding
```
Task tool → autogen-specialist + debugger
Prompt: "Debug non-responsive agent. Check:
- Message handler registration
- Topic subscription configuration
- Async/await implementation
- Error in agent initialization"
```

#### 2. Telegram Bot Webhook Failures
```
Task tool → telegram-bot-specialist + network-engineer
Prompt: "Diagnose webhook issues:
- Verify SSL certificate
- Check secret token
- Validate webhook URL
- Review nginx/HAProxy configuration"
```

#### 3. Database Performance Issues
```
Task tool → database-optimizer + sql-pro
Prompt: "Optimize slow queries:
- Run EXPLAIN ANALYZE
- Add appropriate indexes
- Consider query restructuring
- Implement caching layer"
```

#### 4. High Token Usage
```
Task tool → performance-engineer
Prompt: "Reduce token consumption:
- Implement MessageFilterAgent
- Optimize prompts
- Use context windowing
- Cache LLM responses"
```

#### 5. Multi-tenant Data Leak
```
Task tool → security-auditor + database-admin
Prompt: "URGENT: Verify tenant isolation:
- Check schema permissions
- Review connection pooling
- Audit all queries for tenant filtering
- Implement row-level security"
```

---

## Agent Metrics and Monitoring

### Key Metrics to Track
```
- Agent execution time (target: <2s)
- Token usage per execution
- Success/failure rates
- API response times
- Webhook processing time
- Database query performance
```

### Monitoring Setup
```
Task tool → deployment-engineer
Prompt: "Set up monitoring:
- CloudWatch dashboards for agent metrics
- Sentry for error tracking
- Custom metrics for business KPIs
- Alerts for critical failures"
```

---

## Quick Command Reference

### Development Commands
```bash
# Activate virtual environment
uv shell

# Run main application
uv run python main.py

# Run tests
uv run pytest

# Start Docusaurus docs
cd gutenberg && npm start
```

### Agent Testing Commands
```python
# Test single agent
await test_automator.run_agent_test("lead_qualifier")

# Integration test
await test_automator.run_workflow_test("sales_pipeline")

# Load test
await performance_engineer.run_load_test(users=500)
```

---

## Emergency Procedures

### Production Issue
1. `Task tool → incident-responder` (IMMEDIATE)
2. `Task tool → error-detective` (Root cause)
3. `Task tool → debugger` (Fix implementation)
4. `Task tool → deployment-engineer` (Deploy hotfix)
5. `Task tool → code-reviewer` (Post-mortem)

### Security Breach
1. `Task tool → security-auditor` (IMMEDIATE)
2. `Task tool → incident-responder` (Containment)
3. `Task tool → database-admin` (Audit logs)
4. `Task tool → deployment-engineer` (Patch deployment)

---

## Version History
- v1.0.0 - Initial agent usage guide
- Last Updated: 2024-01-11
- Next Review: After Phase 1 completion

---

## Notes
- All agents follow 1 file = 1 class principle (max 400 lines)
- Use loguru for centralized logging
- Document all changes in .claude/context/history.json
- Context7 MCP tool for latest documentation
- Parallel invocation for independent tasks