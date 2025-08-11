# Plan: PostgreSQL Database Layer Implementation

## Overview

**Objective**: Implement a production-ready PostgreSQL database layer with SQLAlchemy ORM, supporting multi-tenant schema isolation for the Varga AI platform.

**Task Reference**: DB-001

**Scope**: 
- **Included**: PostgreSQL setup, SQLAlchemy models, multi-tenant isolation, migrations, connection pooling
- **Excluded**: Data seeding, backup strategies, read replicas

**Timeline**: 5 days

**Priority**: P0 (Critical - blocks all development)

## Context

### Current State
- No database layer exists
- Platform configuration uses Pydantic models
- Tools and agents have no persistence
- Multi-tenancy not implemented

### Dependencies
- [ ] PostgreSQL 15+ available (local or RDS)
- [ ] Python environment with SQLAlchemy 2.0+
- [ ] Alembic for migrations

### Constraints
- **Technical**: Must support async operations with asyncpg
- **Business**: Must scale to 1,000+ tenants
- **Compliance**: GDPR-compliant data isolation required

### Stakeholders
- **Primary**: All agents and tools requiring data persistence
- **Secondary**: DevOps team for deployment

## Approach

### Strategy
Implement schema-based multi-tenancy where each tenant has an isolated schema within a shared PostgreSQL database, using SQLAlchemy ORM with async support via asyncpg.

### Key Decisions
1. **Schema-based isolation**: Each tenant gets their own schema
   - Rationale: Better isolation than row-level, simpler than database-per-tenant
2. **Async SQLAlchemy**: Use async sessions throughout
   - Rationale: Platform is async-first, better performance
3. **Connection pooling**: Use asyncpg pool with 20 min, 100 max connections
   - Rationale: Balance resource usage with concurrent tenant needs

### Alternatives Considered
1. **Row-level multi-tenancy**: Single schema with tenant_id columns
   - Pros: Simpler migrations, easier cross-tenant queries
   - Cons: Risk of data leaks, complex security
   - Rejected because: Security risk too high for SME data
2. **Database-per-tenant**: Separate database for each tenant
   - Pros: Complete isolation, independent scaling
   - Cons: Complex management, expensive at scale
   - Rejected because: Too complex for 1,000+ tenants target

## Implementation Steps

### Step 1: Database Setup and Configuration
**Description**: Set up PostgreSQL connection and base configuration

**Acceptance Criteria**:
- [ ] PostgreSQL connection established
- [ ] Database URL configurable via environment
- [ ] Connection pool configured
- [ ] Health check endpoint working

**Estimated Time**: 4 hours

**Dependencies**: None

**Sub-steps**:
1. Create `src/database/config.py` with connection settings
2. Set up asyncpg connection pool
3. Add database settings to `src/config/settings.py`
4. Create health check function

### Step 2: Base Model and Session Management
**Description**: Create SQLAlchemy base model and session factory

**Acceptance Criteria**:
- [ ] Base model with common fields (id, created_at, updated_at)
- [ ] Async session factory
- [ ] Context manager for sessions
- [ ] Transaction support

**Estimated Time**: 3 hours

**Dependencies**: Step 1

**Sub-steps**:
1. Create `src/database/base.py` with BaseModel
2. Implement `src/database/session.py` with async session factory
3. Add session middleware for FastAPI

### Step 3: Multi-Tenant Schema Manager
**Description**: Implement schema creation and switching for tenants

**Acceptance Criteria**:
- [ ] Create schema for new tenant
- [ ] Switch schema based on tenant context
- [ ] Schema isolation verified
- [ ] Cleanup/deletion support

**Estimated Time**: 6 hours

**Dependencies**: Step 2

**Sub-steps**:
1. Create `src/database/tenant_manager.py`
2. Implement schema creation with proper permissions
3. Add schema switching middleware
4. Create tenant registry table in public schema

### Step 4: Core Entity Models
**Description**: Create SQLAlchemy models for core platform entities

**Acceptance Criteria**:
- [ ] User model with authentication fields
- [ ] Agent model with configuration
- [ ] Task model with status tracking
- [ ] Workflow model with steps
- [ ] Integration model for external services

**Estimated Time**: 8 hours

**Dependencies**: Step 3

**Sub-steps**:
1. Create `src/database/models/user.py`
2. Create `src/database/models/agent.py`
3. Create `src/database/models/task.py`
4. Create `src/database/models/workflow.py`
5. Create `src/database/models/integration.py`

### Step 5: Migration System with Alembic
**Description**: Set up Alembic for database migrations

**Acceptance Criteria**:
- [ ] Alembic configured for multi-schema
- [ ] Initial migration created
- [ ] Migration commands documented
- [ ] Rollback tested

**Estimated Time**: 4 hours

**Dependencies**: Step 4

**Sub-steps**:
1. Initialize Alembic in project
2. Configure for async and multi-tenant
3. Create initial migration
4. Add migration commands to documentation

### Step 6: Repository Pattern Implementation
**Description**: Create repository classes for data access

**Acceptance Criteria**:
- [ ] Base repository with CRUD operations
- [ ] User repository with auth queries
- [ ] Agent repository with filtering
- [ ] Type-safe query methods

**Estimated Time**: 6 hours

**Dependencies**: Step 5

**Sub-steps**:
1. Create `src/database/repositories/base.py`
2. Implement specific repositories
3. Add query optimization
4. Create repository factory

### Step 7: Integration Testing
**Description**: Comprehensive testing of database layer

**Acceptance Criteria**:
- [ ] Unit tests for models
- [ ] Integration tests for repositories
- [ ] Multi-tenant isolation tests
- [ ] Performance benchmarks

**Estimated Time**: 5 hours

**Dependencies**: Step 6

## Technical Details

### File Structure
```
src/database/
├── __init__.py
├── config.py           # Database configuration
├── base.py            # Base model class
├── session.py         # Session management
├── tenant_manager.py  # Multi-tenant logic
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── agent.py
│   ├── task.py
│   ├── workflow.py
│   └── integration.py
├── repositories/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   └── agent.py
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
└── tests/
    ├── test_models.py
    ├── test_tenant.py
    └── test_repositories.py
```

### Database Schema
```sql
-- Public schema for tenant registry
CREATE TABLE sys_tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    schema_name VARCHAR(63) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

CREATE TABLE sys_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- Per-tenant schema structure
CREATE SCHEMA tenant_{id};

-- Within tenant schema with table prefixes for organization
-- Core tables (prefix: core_)
CREATE TABLE core_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE core_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent tables (prefix: agent_)
CREATE TABLE agent_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID REFERENCES agent_definitions(id),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task tables (prefix: task_)
CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    agent_id UUID REFERENCES agent_definitions(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES task_definitions(id),
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Workflow tables (prefix: wf_)
CREATE TABLE wf_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE wf_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES wf_definitions(id),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Integration tables (prefix: int_)
CREATE TABLE int_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(100),
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE int_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES int_connections(id),
    url TEXT,
    events JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Table Prefix Convention
| Prefix | Category | Description |
|--------|----------|-------------|
| sys_ | System | Platform-level tables in public schema |
| core_ | Core | User, organization, and tenant data |
| agent_ | Agents | Agent definitions and instances |
| task_ | Tasks | Task definitions and executions |
| wf_ | Workflows | Workflow definitions and runs |
| int_ | Integrations | External service connections |
| log_ | Logging | Audit and activity logs |
| cache_ | Cache | Cached data and results |
| temp_ | Temporary | Temporary processing tables |

### Configuration
```python
# Environment variables
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/varga_ai
DATABASE_POOL_MIN=20
DATABASE_POOL_MAX=100
DATABASE_ECHO=false
```

## Testing Strategy

### Unit Tests
- [ ] Model field validation
- [ ] Schema generation
- [ ] Repository methods

### Integration Tests
- [ ] Multi-tenant schema creation
- [ ] Schema isolation verification
- [ ] Connection pool behavior
- [ ] Transaction rollback

### Performance Benchmarks
- **Target**: <50ms query time for simple queries
- **Load**: 100 concurrent connections
- **Tenant switching**: <10ms overhead

## Risk Analysis

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Schema limit reached | Low | High | Monitor schema count, implement archival |
| Connection pool exhaustion | Medium | High | Implement connection limiting per tenant |
| Migration failures | Medium | Medium | Test migrations in staging first |

### Rollback Plan
1. **Trigger**: Migration failure or data corruption
2. **Steps**:
   - Stop application servers
   - Restore database from backup
   - Revert code changes
   - Clear connection pools
3. **Data Recovery**: Point-in-time recovery from RDS
4. **Communication**: Notify all developers via Slack

## Success Metrics

### Completion Criteria
- [ ] All models created and tested
- [ ] Multi-tenant isolation working
- [ ] 100% test coverage for critical paths
- [ ] Performance benchmarks met
- [ ] Documentation complete

### Performance Targets
- **Query Response**: <50ms for simple queries
- **Schema Creation**: <2s per tenant
- **Connection Time**: <100ms

### Quality Metrics
- **Code Coverage**: >90%
- **Type Coverage**: 100%
- **Zero SQL injection vulnerabilities**

## Notes

### Open Questions
- [ ] Decision needed: RDS vs Aurora for production

### Assumptions
- PostgreSQL 15+ features available
- Async operations supported throughout stack
- Schema-based isolation acceptable for compliance

### References
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Schema Documentation](https://www.postgresql.org/docs/15/ddl-schemas.html)
- [Multi-tenant Architecture Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)

---

**Plan Created**: 2025-01-11  
**Last Updated**: 2025-01-11  
**Status**: planning