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
     - [ ] Other: ___________

3. **Technology Stack Assessment**
   ```
   Primary Language: ___________
   Framework(s): ___________
   Database(s): ___________
   Testing Framework: ___________
   Build Tool(s): ___________
   Package Manager: ___________
   ```

4. **Existing Patterns Detection**
   - [ ] Code organization (monorepo, microservices, modular)
   - [ ] File naming conventions
   - [ ] Import/module patterns
   - [ ] Error handling approaches
   - [ ] Logging mechanisms

### 1.2 Dependency Analysis
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

### 1.3 Initial Documentation
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
    "framework": "[FRAMEWORK]"
  },
  "history": [],
  "learned": {
    "patterns": [],
    "conventions": [],
    "decisions": []
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
      "tasks": []
    },
    {
      "name": "Development",
      "tasks": []
    },
    {
      "name": "Testing",
      "tasks": []
    },
    {
      "name": "Deployment",
      "tasks": []
    }
  ],
  "current_focus": "",
  "blockers": []
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

## Architecture Decisions
### ADR-001: [Decision Title]
- **Date**: 
- **Status**: Accepted/Rejected/Deprecated
- **Context**: 
- **Decision**: 
- **Consequences**: 
```

---

## Phase 4: Integration & Tools (Day 3-4)

### 4.1 Configure Testing Framework

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

**Python:**
```bash
# Install tools
pip install black isort flake8  # or: ruff

# Create .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```

**JavaScript/TypeScript:**
```bash
# Install tools
npm install -D eslint prettier

# Create .eslintrc.json and .prettierrc
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

### 5.3 Create Monitoring & Observability

```python
# Metrics collection
# Error tracking (Sentry)
# Performance monitoring
# Health checks
```

---

## Phase 6: Optimization & Finalization (Day 5-6)

### 6.1 Performance Optimization
- [ ] Profile code for bottlenecks
- [ ] Optimize database queries
- [ ] Implement caching where appropriate
- [ ] Minimize bundle sizes (frontend)

### 6.2 Security Review
- [ ] Check for exposed secrets
- [ ] Review authentication/authorization
- [ ] Validate input sanitization
- [ ] Update dependencies for security patches

### 6.3 Documentation Polish
- [ ] Update all README files
- [ ] Generate API documentation
- [ ] Create user guides
- [ ] Document deployment process

### 6.4 Final Checklist
- [ ] All tests passing
- [ ] Documentation complete
- [ ] CI/CD configured
- [ ] Environment variables documented
- [ ] Deployment instructions clear
- [ ] Rollback procedures defined

---

## Conditional Paths

### For Existing Projects
1. **Preserve Existing Patterns**
   - Don't force new conventions
   - Document existing patterns
   - Suggest improvements gradually

2. **Incremental Integration**
   - Start with .claude/context/ setup
   - Add testing gradually
   - Improve documentation iteratively

### For New Projects
1. **Establish Best Practices Early**
   - Set up proper structure from start
   - Implement testing immediately
   - Configure CI/CD early

2. **Use Scaffolding Tools**
   - `create-react-app`, `create-next-app`
   - `django-admin startproject`
   - `cargo new`, `go mod init`

### For Different Project Types

**Web Applications:**
- Focus on frontend/backend separation
- Set up API documentation
- Configure CORS and security
- Implement authentication early

**CLI Tools:**
- Design command structure
- Implement help system
- Add progress indicators
- Handle signals properly

**Libraries/Packages:**
- Focus on API design
- Comprehensive documentation
- Extensive test coverage
- Version management strategy

**APIs/Microservices:**
- OpenAPI specification
- Rate limiting
- Health checks
- Service discovery

---

## Memory Integration

After setup, update Claude's memory:
```
Task tool → Task
Description: "Update project memory"
Prompt: "Store project configuration, patterns, and key decisions in memory for future reference"
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

---

## Success Criteria

### Phase 1 Success
- [ ] Complete understanding of project structure
- [ ] All dependencies identified
- [ ] Technology stack documented

### Phase 2 Success
- [ ] .claude/context/ structure created
- [ ] Tracking files initialized
- [ ] Version control configured

### Phase 3 Success
- [ ] Comprehensive documentation exists
- [ ] Task management system active
- [ ] Patterns documented

### Phase 4 Success
- [ ] Testing framework operational
- [ ] Linting/formatting configured
- [ ] Logging implemented

### Phase 5 Success
- [ ] Tests written and passing
- [ ] CI/CD pipeline active
- [ ] Monitoring in place

### Phase 6 Success
- [ ] Performance optimized
- [ ] Security reviewed
- [ ] Documentation polished
- [ ] Project ready for development/deployment

---

## Quick Commands Reference

```bash
# Create Claude structure
mkdir -p .claude/{context,workflows,plans,templates}

# Initialize tracking
echo '{"history":[],"learned":{}}' > .claude/context/history.json

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
- Update memory after major milestones

---

## Version
- **Version**: 1.0.0
- **Last Updated**: 2025-01-11
- **Based On**: Varga AI Project Patterns
- **Compatibility**: Claude Code v1.0+