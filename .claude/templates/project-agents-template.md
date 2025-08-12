# Project-Specific Agent Selection Guide

**Project Name:** [PROJECT_NAME]  
**Project Type:** [web-app|cli|library|api|ml-model|multi-agent|other]  
**Primary Language:** [python|javascript|typescript|go|rust|java|csharp|other]  
**Framework:** [framework_name]  
**Date:** [DATE]  

---

## 🎯 Agent Selection Analysis

### Project Requirements Assessment

#### Core Development Needs
- [ ] **Language Expertise Required**
  - Primary: [language]
  - Secondary: [languages]
  - Specialized: [domain-specific languages]

- [ ] **Architecture Complexity**
  - [ ] Simple single-file script
  - [ ] Modular application
  - [ ] Microservices architecture
  - [ ] Distributed system
  - [ ] Multi-agent system

- [ ] **Database Requirements**
  - [ ] No database
  - [ ] Simple SQLite
  - [ ] PostgreSQL/MySQL
  - [ ] NoSQL (MongoDB, Redis)
  - [ ] Multi-database architecture

- [ ] **Integration Requirements**
  - [ ] Standalone application
  - [ ] Third-party API integrations
  - [ ] Messaging systems (Telegram, Slack)
  - [ ] Payment processing
  - [ ] AI/ML services

- [ ] **Quality Requirements**
  - Testing Coverage Target: _____%
  - Performance Requirements: _____
  - Security Level: [low|medium|high|critical]
  - Documentation Level: [basic|comprehensive|api-docs]

---

## 🤖 Selected Developer Agents

### Primary Agents (Core Development)
| Agent | Role | When to Use | Priority |
|-------|------|------------|----------|
| `[agent_name]` | [Primary development] | [All development tasks] | P0 |
| `[agent_name]` | [Architecture design] | [System design, API structure] | P0 |
| `[agent_name]` | [Database design] | [Schema, queries, optimization] | P0 |

**Rationale:** [Why these agents were selected as primary]

### Supporting Agents (Quality & Operations)
| Agent | Role | When to Use | Priority |
|-------|------|------------|----------|
| `test-automator` | Testing framework | All test creation | P1 |
| `code-reviewer` | Code quality | After each feature | P1 |
| `deployment-engineer` | CI/CD setup | Initial setup & changes | P1 |
| `security-auditor` | Security review | Before production | P1 |
| `[agent_name]` | [Role] | [When] | P1 |

**Rationale:** [Why these supporting agents are needed]

### Specialized Agents (Project-Specific)
| Agent | Role | When to Use | Priority |
|-------|------|------------|----------|
| `[agent_name]` | [Specific feature] | [Specific scenario] | P2 |
| `[agent_name]` | [Integration] | [When integrating X] | P2 |
| `[agent_name]` | [Optimization] | [Performance tuning] | P3 |

**Rationale:** [Why these specialized agents may be needed]

### Optional Agents (Nice to Have)
| Agent | Role | Benefit | Priority |
|-------|------|---------|----------|
| `[agent_name]` | [Enhancement] | [Value added] | P3 |
| `[agent_name]` | [Future feature] | [Long-term benefit] | P3 |

---

## 📋 Agent Activation Sequence

### Phase 1: Foundation (Days 1-2)
```
1. [primary_language_agent] → Initial code structure
2. [architect_agent] → System design
3. [database_agent] → Schema design (if applicable)
4. deployment-engineer → CI/CD setup
```

### Phase 2: Core Development (Days 3-4)
```
1. [primary_development_agent] → Feature implementation
2. test-automator → Test framework setup
3. [integration_agent] → External service integration
4. code-reviewer → Initial code review
```

### Phase 3: Quality & Optimization (Days 5-6)
```
1. test-automator → Comprehensive test suite
2. security-auditor → Security review
3. performance-engineer → Performance optimization
4. code-reviewer → Final review
```

### Phase 4: Documentation & Deployment (Day 6+)
```
1. api-documenter → API documentation
2. deployment-engineer → Production setup
3. architect-reviewer → Architecture validation
```

---

## 🔧 Agent Invocation Templates

### [Primary Agent Name]
```
Task tool → [agent_name]
Description: "[Task type]"
Prompt: "[Specific prompt template for this project]

Project Context:
- Type: [project_type]
- Stack: [tech_stack]
- Requirements: [key_requirements]

Specific Task:
[Detailed task description]

Constraints:
- [Constraint 1]
- [Constraint 2]

Expected Output:
[What should be delivered]"
```

### test-automator
```
Task tool → test-automator
Description: "Test suite setup"
Prompt: "Create comprehensive test suite for [project_name]:

Tech Stack: [languages/frameworks]
Test Requirements:
- Unit tests for [components]
- Integration tests for [integrations]
- E2E tests for [critical paths]
- Coverage target: [percentage]%

Focus Areas:
- [Critical feature 1]
- [Critical feature 2]

Test Data:
[Describe test data needs]"
```

### code-reviewer
```
Task tool → code-reviewer
Description: "Code review"
Prompt: "Review [component/feature] for [project_name]:

Focus Areas:
- [Language] best practices
- [Framework] patterns
- Security considerations
- Performance implications
- Documentation completeness

Known Issues:
[Any specific concerns]

Standards:
[Project-specific standards]"
```

---

## 🔄 Agent Workflow Patterns

### Pattern 1: Feature Development
```
1. [architect_agent] → Design feature architecture
2. [primary_dev_agent] → Implement feature
3. test-automator → Create tests
4. code-reviewer → Review implementation
```

### Pattern 2: Bug Fix
```
1. debugger → Identify root cause
2. [primary_dev_agent] → Fix implementation
3. test-automator → Add regression test
4. code-reviewer → Verify fix
```

### Pattern 3: Performance Optimization
```
1. performance-engineer → Profile and identify bottlenecks
2. [primary_dev_agent] → Implement optimizations
3. test-automator → Performance benchmarks
4. code-reviewer → Review changes
```

### Pattern 4: Security Audit
```
1. security-auditor → Initial scan
2. [primary_dev_agent] → Fix vulnerabilities
3. test-automator → Security tests
4. security-auditor → Verify fixes
```

---

## 📊 Agent Performance Metrics

### Expected Agent Utilization
| Agent | Expected Tasks | Time Allocation |
|-------|---------------|-----------------|
| [primary_agent] | [number] | [percentage]% |
| test-automator | [number] | [percentage]% |
| code-reviewer | [number] | [percentage]% |
| [other_agent] | [number] | [percentage]% |

### Success Criteria
- [ ] All primary agents successfully invoked
- [ ] Test coverage achieved: _____%
- [ ] Security audit passed
- [ ] Performance targets met
- [ ] Documentation complete

---

## 💾 Memory Update Instructions

### Initial Memory Update
```
Task tool → Task
Description: "Initialize project agent memory"
Prompt: "Store agent selection for [project_name]:

Project Type: [type]
Language: [language]
Framework: [framework]

Selected Agents:
Primary: [list]
Supporting: [list]
Specialized: [list]

Agent Patterns:
- [Pattern 1]
- [Pattern 2]

Key Decisions:
- [Decision 1]
- [Decision 2]"
```

### Ongoing Memory Updates
```
After each phase, update memory with:
- Agent performance
- Discovered patterns
- Lessons learned
- Optimization opportunities
```

---

## 🚨 Agent Escalation Path

### When Issues Arise
1. **Primary Issue**: [primary_agent] attempts resolution
2. **Debug Required**: debugger → error-detective
3. **Architecture Issue**: architect-reviewer validation
4. **Security Concern**: security-auditor immediate review
5. **Performance Problem**: performance-engineer analysis
6. **Critical Failure**: incident-responder → full team

---

## 📝 Notes

### Project-Specific Considerations
- [Special requirement 1]
- [Special requirement 2]
- [Integration consideration]
- [Performance consideration]

### Agent Limitations
- [Agent 1 limitation and workaround]
- [Agent 2 limitation and workaround]

### Future Agent Needs
- [Potential future agent 1]
- [Potential future agent 2]

---

## ✅ Approval

**Agent Selection Approved By:** _________________  
**Date:** _______  
**Review Scheduled:** _______  

---

## 📎 Appendix

### Available Agents Reference
- **Development**: autogen-specialist, python-pro, javascript-pro, golang-pro, rust-pro, java-pro, cpp-pro
- **Architecture**: backend-architect, frontend-developer, database-optimizer, graphql-architect
- **Quality**: test-automator, code-reviewer, security-auditor, performance-engineer
- **Operations**: deployment-engineer, terraform-specialist, cloud-architect
- **Specialized**: telegram-bot-specialist, ai-engineer, ml-engineer, payment-integration
- **Support**: debugger, error-detective, incident-responder

### Quick Invocation Reference
```bash
# Primary development
Task tool → [primary_agent]

# Testing
Task tool → test-automator

# Code review
Task tool → code-reviewer

# Deployment
Task tool → deployment-engineer

# Security
Task tool → security-auditor
```

---

**Template Version:** 1.0.0  
**Created:** 2025-01-11  
**Based On:** Varga AI Agent Patterns