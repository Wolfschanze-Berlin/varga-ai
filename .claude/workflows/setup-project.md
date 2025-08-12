# Generic Project Setup Workflow

## Overview
This workflow provides a comprehensive, adaptable framework for setting up any software project with Claude Code. It incorporates best practices from production projects and can be customized based on project type, language, and requirements.

## Prerequisites
- [ ] Claude Code installed and configured
- [ ] Access to project repository/folder
- [ ] Understanding of project requirements
- [ ] Necessary API keys and credentials (if applicable)

---

## Phase 1: Discovery & Analysis (Day 1)

### 1.1 Initial Context Gathering
```bash
# Commands to run
ls -la                    # Check project structure
git status               # Check git status
git log --oneline -10   # Review recent commits
```

**Actions:**
1. **Read Existing Documentation**
   - [ ] Check for README.md, CONTRIBUTING.md, docs/
   - [ ] Look for .claude/, .github/, or similar meta folders
   - [ ] Review package.json, pyproject.toml, go.mod, Cargo.toml, etc.
   - [ ] Check for existing CI/CD configurations
   - [ ] Read projectBrief.md or similar project specifications

2. **Analyze Project Type**
   - [ ] Identify primary language(s)
   - [ ] Detect framework(s) in use
   - [ ] Determine project category:
     - [ ] Web Application (Frontend/Backend/Full-stack)
     - [ ] CLI Tool
     - [ ] Library/Package
     - [ ] API/Microservice
     - [ ] Desktop Application
     - [ ] Mobile Application
     - [ ] Data Pipeline
     - [ ] Machine Learning Model
     - [ ] Multi-Agent System (AutoGen/LangChain)
     - [ ] Other: ___________

3. **Technology Stack Assessment**
   ```
   Primary Language: ___________
   Framework(s): ___________
   Database(s): ___________
   Testing Framework: ___________
   Build Tool(s): ___________
   Package Manager: ___________
   AI/ML Frameworks: ___________
   ```

4. **Existing Patterns Detection**
   - [ ] Code organization (monorepo, microservices, modular)
   - [ ] File naming conventions
   - [ ] Import/module patterns
   - [ ] Error handling approaches
   - [ ] Logging mechanisms

### 1.2 Developer Agent Selection 🤖

**CRITICAL STEP: Select appropriate developer agents for this project**

1. **Check Available Agents**
   ```bash
   # Use Claude command to see available agents
   /agents
   
   # Or refer to .claude/context/agents.md if it exists
   cat .claude/context/agents.md
   ```

2. **Analyze Project Requirements for Agent Selection**

   **For Core Development:**
   - [ ] **autogen-specialist** - If using AutoGen framework
   - [ ] **python-pro** - For Python projects
   - [ ] **javascript-pro** / **typescript-pro** - For JS/TS projects
   - [ ] **golang-pro** - For Go projects
   - [ ] **rust-pro** - For Rust projects
   - [ ] **java-pro** - For Java projects
   - [ ] **cpp-pro** / **c-pro** - For C/C++ projects

   **For Architecture & Design:**
   - [ ] **backend-architect** - For API/backend services
   - [ ] **frontend-developer** - For UI/frontend work
   - [ ] **database-optimizer** / **sql-pro** - For database-heavy projects
   - [ ] **graphql-architect** - For GraphQL APIs
   - [ ] **cloud-architect** - For cloud-native applications

   **For Specialized Needs:**
   - [ ] **telegram-bot-specialist** - For Telegram bot integration
   - [ ] **ai-engineer** / **ml-engineer** - For AI/ML projects
   - [ ] **mobile-developer** - For mobile apps
   - [ ] **data-engineer** - For data pipelines
   - [ ] **payment-integration** - For e-commerce/payment systems

   **For Quality & Operations:**
   - [ ] **test-automator** - Always needed for testing
   - [ ] **security-auditor** - For security-critical applications
   - [ ] **deployment-engineer** - For CI/CD setup
   - [ ] **performance-engineer** - For performance-critical systems
   - [ ] **debugger** - For troubleshooting complex issues

   **For Documentation & Support:**
   - [ ] **api-documenter** - For API documentation
   - [ ] **code-reviewer** - For code quality checks
   - [ ] **architect-reviewer** - For architecture validation

3. **Document Selected Agents**
   ```markdown
   # Selected Developer Agents for [Project Name]
   
   ## Primary Agents
   - [agent_name]: [reason for selection]
   - [agent_name]: [reason for selection]
   
   ## Supporting Agents
   - [agent_name]: [when to use]
   - [agent_name]: [when to use]
   
   ## Specialized Agents
   - [agent_name]: [specific use case]
   ```

4. **Update Claude Memory with Agent Selection**
   ```
   Task tool → Task
   Description: "Update project agent memory"
   Prompt: "Store the following agent selection for [project_name]:
   Primary agents: [list]
   Supporting agents: [list]
   Reason: [project type and requirements]
   Usage patterns: [when to use each agent]"
   ```

5. **Create Agent Usage Guide for Project**
   Create `.claude/context/project-agents.md`:
   ```markdown
   # Project-Specific Agent Usage Guide
   
   ## Agent Activation Sequence
   Phase 1: [agent1] → [agent2]
   Phase 2: [agent3] → [agent4]
   
   ## Agent Invocation Examples
   ### [Agent Name]
   Task tool → [agent_name]
   Prompt: "[Specific prompt for this project]"
   
   ## Project-Specific Patterns
   - Use [agent] for [specific task]
   - Combine [agent1] + [agent2] for [complex task]
   ```

### 1.3 Dependency Analysis
**For Python Projects:**
```bash
# Check for virtual environment
ls -la | grep -E "venv|.venv|env"
# Check package manager
ls | grep -E "requirements.txt|pyproject.toml|Pipfile|poetry.lock"
```

**For JavaScript/TypeScript:**
```bash
# Check package manager
ls | grep -E "package.json|yarn.lock|pnpm-lock.yaml"
# Check for TypeScript
ls | grep -E "tsconfig.json"
```

**For Other Languages:**
- Go: `go.mod`, `go.sum`
- Rust: `Cargo.toml`, `Cargo.lock`
- Java: `pom.xml`, `build.gradle`
- C#: `*.csproj`, `*.sln`
- Ruby: `Gemfile`, `Gemfile.lock`

### 1.4 Initial Documentation
Create `.claude/context/discovery.md` with findings:
```markdown
# Project Discovery Report
Date: [DATE]

## Project Overview
- Name: 
- Type: 
- Purpose: 
- Current State: 

## Technology Stack
- Language(s): 
- Framework(s): 
- Database(s): 
- Key Dependencies: 

## Selected Developer Agents
- Primary: [agents]
- Supporting: [agents]
- Specialized: [agents]

## Existing Structure
[Document folder structure]

## Observations
[Key findings and patterns]

## Recommendations
[Suggested improvements]
```

---

## Phase 2: Foundation Setup (Day 1-2)

### 2.1 Create Claude Context Structure
```bash
mkdir -p .claude/context
mkdir -p .claude/workflows
mkdir -p .claude/plans
mkdir -p .claude/templates
```

### 2.2 Initialize Tracking Files

**Create `.claude/context/history.json`:**
```json
{
  "project": {
    "name": "[PROJECT_NAME]",
    "type": "[PROJECT_TYPE]",
    "initialized": "[DATE]",
    "language": "[PRIMARY_LANGUAGE]",
    "framework": "[FRAMEWORK]",
    "selected_agents": {
      "primary": [],
      "supporting": [],
      "specialized": []
    }
  },
  "history": [],
  "learned": {
    "patterns": [],
    "conventions": [],
    "decisions": [],
    "agent_usage": []
  }
}
```

**Create `.claude/context/project_instructions.md`:**
```markdown
# Project Instructions

## Project Identity
- **Name**: [PROJECT_NAME]
- **Purpose**: [BRIEF_DESCRIPTION]
- **Target Users**: [TARGET_AUDIENCE]
- **Key Features**: [LIST_MAIN_FEATURES]

## Architecture Overview
[Describe high-level architecture]

## Developer Agents
### Primary Agents
- [agent]: [usage]

### Supporting Agents
- [agent]: [usage]

### Agent Workflow
[Describe typical agent workflow]

## Development Workflow
### Setup
[Setup instructions]

### Commands
[Common commands]

### Testing
[Testing approach]

## Conventions
### Code Style
- [List conventions]

### File Organization
- [Structure patterns]

### Naming Conventions
- [Naming patterns]

## Important Notes
[Critical information]
```

### 2.3 Set Up Version Control

**Update/Create `.gitignore`:**
```bash
# Use appropriate template based on language
# Python template
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.env
.env.local

# JavaScript/TypeScript
node_modules/
dist/
build/
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Claude Context (selective)
.claude/plans/*/notes/
.claude/workflows/temp/
```

### 2.4 Configure Development Environment

**For Python:**
```bash
# Create virtual environment
python -m venv .venv  # or: uv venv

# Create/Update pyproject.toml
[tool.project]
name = "[PROJECT_NAME]"
version = "0.1.0"
requires-python = ">=3.8"
```

**For JavaScript/TypeScript:**
```json
// Update package.json
{
  "scripts": {
    "dev": "...",
    "build": "...",
    "test": "...",
    "lint": "..."
  }
}
```

### 2.5 Agent-Driven Setup Tasks

**Use selected agents for initial setup:**
```bash
# Example: Use backend-architect for API design
Task tool → backend-architect
Prompt: "Design initial API structure for [project description]"

# Example: Use sql-pro for database schema
Task tool → sql-pro
Prompt: "Create database schema for [requirements]"

# Example: Use deployment-engineer for CI/CD
Task tool → deployment-engineer
Prompt: "Set up GitHub Actions workflow for [language/framework]"
```

---

## Phase 3: Documentation & Knowledge Base (Day 2-3)

### 3.1 Create Comprehensive Documentation

**Generate README.md if missing:**
```markdown
# [Project Name]

## Overview
[Brief description]

## Features
- [ ] Feature 1
- [ ] Feature 2

## Installation
\```bash
# Installation steps
\```

## Usage
\```bash
# Usage examples
\```

## Development
\```bash
# Development setup
\```

## Testing
\```bash
# Test commands
\```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
[License type]
```

### 3.2 Set Up Task Management

**Create `.claude/context/tasks.json`:**
```json
{
  "phases": [
    {
      "name": "Setup",
      "tasks": [],
      "assigned_agents": []
    },
    {
      "name": "Development",
      "tasks": [],
      "assigned_agents": []
    },
    {
      "name": "Testing",
      "tasks": [],
      "assigned_agents": []
    },
    {
      "name": "Deployment",
      "tasks": [],
      "assigned_agents": []
    }
  ],
  "current_focus": "",
  "blockers": [],
  "agent_assignments": {}
}
```

### 3.3 Document Patterns and Decisions

**Create `.claude/context/patterns.md`:**
```markdown
# Project Patterns & Conventions

## Code Patterns
### [Pattern Name]
- **Context**: When to use
- **Solution**: How to implement
- **Example**: Code sample
- **Agent**: Which agent handles this

## Architecture Decisions
### ADR-001: [Decision Title]
- **Date**: 
- **Status**: Accepted/Rejected/Deprecated
- **Context**: 
- **Decision**: 
- **Consequences**: 
- **Reviewing Agent**: [agent that validated this]
```

---

## Phase 4: Integration & Tools (Day 3-4)

### 4.1 Configure Testing Framework

**Use test-automator agent:**
```
Task tool → test-automator
Prompt: "Set up testing framework for [language/framework] with:
- Unit test structure
- Integration test setup
- Coverage configuration
- CI integration"
```

**Python (pytest):**
```bash
# Install pytest
pip install pytest pytest-asyncio pytest-cov

# Create pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**JavaScript (Jest/Vitest):**
```javascript
// jest.config.js or vitest.config.js
export default {
  testEnvironment: 'node',
  coverageDirectory: 'coverage',
  collectCoverageFrom: ['src/**/*.{js,ts}']
}
```

### 4.2 Set Up Linting & Formatting

**Use code-reviewer agent for setup:**
```
Task tool → code-reviewer
Prompt: "Configure linting and formatting for [language] with:
- Recommended style guide
- Pre-commit hooks
- IDE integration"
```

### 4.3 Configure Logging

**Python (Loguru):**
```python
# src/logging/logger.py
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    level="INFO"
)
```

**JavaScript (Winston/Pino):**
```javascript
// src/utils/logger.js
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});
```

### 4.4 Create Demo/Example Files

```python
# demo.py or examples/demo.js
"""
Demo script showing main functionality
"""
def main():
    print("Demo functionality")

if __name__ == "__main__":
    main()
```

---

## Phase 5: Quality Assurance (Day 4-5)

### 5.1 Implement Testing Strategy

**Use test-automator for comprehensive testing:**
```
Task tool → test-automator
Prompt: "Create comprehensive test suite with:
- Unit tests for core functionality
- Integration tests for APIs
- E2E tests for critical paths
- Performance benchmarks"
```

**Test Structure:**
```
tests/
├── unit/
│   └── test_[module].py
├── integration/
│   └── test_[feature].py
├── fixtures/
│   └── [test_data]
└── conftest.py  # pytest
```

### 5.2 Set Up CI/CD

**Use deployment-engineer:**
```
Task tool → deployment-engineer
Prompt: "Create CI/CD pipeline with:
- Automated testing on PR
- Build verification
- Security scanning
- Deployment to [environment]"
```

**GitHub Actions (`.github/workflows/ci.yml`):**
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up environment
        # Language-specific setup
      - name: Run tests
        run: |
          # Test commands
```

### 5.3 Security Audit

**Use security-auditor:**
```
Task tool → security-auditor
Prompt: "Perform security audit for [project type]:
- Check for exposed secrets
- Review authentication
- Validate input handling
- Check dependencies for vulnerabilities"
```

### 5.4 Performance Optimization

**Use performance-engineer:**
```
Task tool → performance-engineer
Prompt: "Optimize performance for [project type]:
- Profile critical paths
- Implement caching
- Optimize database queries
- Set up monitoring"
```

---

## Phase 6: Optimization & Finalization (Day 5-6)

### 6.1 Code Review

**Use code-reviewer and architect-reviewer:**
```
Task tool → code-reviewer
Prompt: "Review entire codebase for:
- Code quality
- Best practices
- Potential bugs
- Documentation completeness"

Task tool → architect-reviewer
Prompt: "Review architecture for:
- Scalability
- Maintainability
- Security
- Performance"
```

### 6.2 Documentation Polish

**Use api-documenter if applicable:**
```
Task tool → api-documenter
Prompt: "Generate complete API documentation with:
- OpenAPI specification
- Usage examples
- Authentication guide
- Error codes reference"
```

### 6.3 Final Agent Memory Update

```
Task tool → Task
Description: "Finalize project memory"
Prompt: "Update memory with:
- Final agent selection and usage patterns
- Key architectural decisions
- Important patterns discovered
- Performance benchmarks
- Security considerations
- Deployment procedures"
```

### 6.4 Final Checklist
- [ ] All tests passing
- [ ] Documentation complete
- [ ] CI/CD configured
- [ ] Environment variables documented
- [ ] Deployment instructions clear
- [ ] Rollback procedures defined
- [ ] Agent usage patterns documented
- [ ] Memory updated with project knowledge

---

## Agent Selection Quick Reference

### By Project Type

**Web Application:**
- Primary: `frontend-developer`, `backend-architect`, `sql-pro`
- Supporting: `test-automator`, `security-auditor`, `deployment-engineer`
- Optional: `ui-ux-designer`, `performance-engineer`

**CLI Tool:**
- Primary: Language-specific pro agent (e.g., `python-pro`, `golang-pro`)
- Supporting: `test-automator`, `api-documenter`
- Optional: `deployment-engineer`

**API/Microservice:**
- Primary: `backend-architect`, `sql-pro`, `api-documenter`
- Supporting: `test-automator`, `security-auditor`, `performance-engineer`
- Optional: `graphql-architect`, `database-optimizer`

**Machine Learning Project:**
- Primary: `ml-engineer`, `python-pro`, `data-engineer`
- Supporting: `test-automator`, `performance-engineer`
- Optional: `mlops-engineer`, `data-scientist`

**Multi-Agent System (AutoGen):**
- Primary: `autogen-specialist`, `python-pro`, `backend-architect`
- Supporting: `test-automator`, `deployment-engineer`
- Optional: `ai-engineer`, `prompt-engineer`

**Mobile Application:**
- Primary: `mobile-developer`, `ios-developer` or `android-developer`
- Supporting: `test-automator`, `ui-ux-designer`
- Optional: `backend-architect` (for backend)

### By Technology Stack

**Python Projects:**
- Always: `python-pro`, `test-automator`
- Web: Add `backend-architect`
- Data: Add `data-engineer`, `sql-pro`
- ML: Add `ml-engineer`

**JavaScript/TypeScript:**
- Always: `javascript-pro` or `typescript-pro`, `test-automator`
- Frontend: Add `frontend-developer`
- Backend: Add `backend-architect`
- Full-stack: Add both

**Go Projects:**
- Always: `golang-pro`, `test-automator`
- API: Add `backend-architect`
- CLI: Focus on `golang-pro`

**Database-Heavy Projects:**
- Always: `sql-pro`, `database-optimizer`
- Add: `database-admin` for operations

---

## Conditional Paths

### For Existing Projects
1. **Preserve Existing Patterns**
   - Don't force new conventions
   - Document existing patterns
   - Suggest improvements gradually
   - Respect existing agent workflows

2. **Incremental Integration**
   - Start with .claude/context/ setup
   - Add testing gradually
   - Improve documentation iteratively
   - Introduce agents one at a time

### For New Projects
1. **Establish Best Practices Early**
   - Set up proper structure from start
   - Implement testing immediately
   - Configure CI/CD early
   - Define agent usage patterns upfront

2. **Use Scaffolding Tools**
   - `create-react-app`, `create-next-app`
   - `django-admin startproject`
   - `cargo new`, `go mod init`
   - Let agents handle the scaffolding

### For Different Project Types

**Web Applications:**
- Focus on frontend/backend separation
- Set up API documentation
- Configure CORS and security
- Implement authentication early
- Use `frontend-developer` + `backend-architect`

**CLI Tools:**
- Design command structure
- Implement help system
- Add progress indicators
- Handle signals properly
- Primary agent based on language

**Libraries/Packages:**
- Focus on API design
- Comprehensive documentation
- Extensive test coverage
- Version management strategy
- Use `api-documenter` heavily

**APIs/Microservices:**
- OpenAPI specification
- Rate limiting
- Health checks
- Service discovery
- `backend-architect` + `api-documenter`

---

## Memory Integration

After setup, update Claude's memory:
```
Task tool → Task
Description: "Update project memory"
Prompt: "Store project configuration, patterns, key decisions, and agent usage patterns in memory for future reference"
```

### Memory Update Template
```
Project: [name]
Type: [type]
Stack: [technologies]
Agents:
  Primary: [list]
  Supporting: [list]
  Usage Patterns:
    - Use [agent] for [task]
    - Combine [agents] for [workflow]
Key Decisions:
  - [decision and rationale]
Patterns:
  - [pattern and usage]
Performance Benchmarks:
  - [metric]: [value]
```

---

## Rollback Procedures

If setup causes issues:
1. **Git Reset**
   ```bash
   git reset --hard HEAD~1  # Rollback last commit
   git clean -fd            # Remove untracked files
   ```

2. **Manual Cleanup**
   - Remove .claude/ folder if needed
   - Restore original configuration files
   - Document what went wrong in history.json

3. **Agent Error Recovery**
   ```
   Task tool → debugger
   Prompt: "Debug setup issue: [describe problem]"
   
   Task tool → incident-responder
   Prompt: "Recover from failed setup: [error details]"
   ```

---

## Success Criteria

### Phase 1 Success
- [ ] Complete understanding of project structure
- [ ] All dependencies identified
- [ ] Technology stack documented
- [ ] **Developer agents selected and documented**
- [ ] **Memory updated with agent selection**

### Phase 2 Success
- [ ] .claude/context/ structure created
- [ ] Tracking files initialized
- [ ] Version control configured
- [ ] **Agent usage guide created**

### Phase 3 Success
- [ ] Comprehensive documentation exists
- [ ] Task management system active
- [ ] Patterns documented
- [ ] **Agent assignments documented**

### Phase 4 Success
- [ ] Testing framework operational
- [ ] Linting/formatting configured
- [ ] Logging implemented
- [ ] **Agents used for setup tasks**

### Phase 5 Success
- [ ] Tests written and passing
- [ ] CI/CD pipeline active
- [ ] Security audit complete
- [ ] Performance optimized
- [ ] **All quality agents involved**

### Phase 6 Success
- [ ] Code reviewed by agents
- [ ] Architecture validated
- [ ] Documentation polished
- [ ] **Final memory update complete**
- [ ] Project ready for development/deployment

---

## Quick Commands Reference

```bash
# Create Claude structure
mkdir -p .claude/{context,workflows,plans,templates}

# Initialize tracking
echo '{"history":[],"learned":{}}' > .claude/context/history.json

# Check available agents
/agents

# Common agent invocations
Task tool → autogen-specialist  # For AutoGen projects
Task tool → python-pro          # For Python code
Task tool → test-automator      # For testing
Task tool → code-reviewer       # For code review

# Common language commands
# Python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Node.js
npm install
npm run dev

# Go
go mod download
go run main.go

# Rust
cargo build
cargo run

# Git
git add .
git commit -m "Initial project setup with Claude workflow"
git push
```

---

## Notes
- Adapt this workflow to your specific needs
- Skip sections that don't apply
- Add project-specific steps as needed
- Document all deviations in history.json
- Use TodoWrite tool to track progress
- **Always select and document appropriate agents**
- **Update memory with agent usage patterns**
- **Create project-specific agent guides**

---

## Version
- **Version**: 1.1.0
- **Last Updated**: 2025-01-11
- **Based On**: Varga AI Project Patterns
- **Compatibility**: Claude Code v1.0+
- **Enhancement**: Added comprehensive agent selection and memory integration