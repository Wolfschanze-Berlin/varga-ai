# Architectural Decisions - DB-001 PostgreSQL Implementation

## Decision Log

### Decision 1: Schema-based Multi-tenancy
**Date**: 2025-01-11  
**Status**: Approved  

**Decision**: Use PostgreSQL schemas for tenant isolation, where each tenant gets their own schema within a shared database.

**Context**: 
- Need to support 1,000+ SME tenants
- Data isolation is critical for compliance
- Must balance security with operational complexity

**Alternatives Considered**:
1. **Row-level multi-tenancy**: Add tenant_id to all tables
   - Pros: Simple migrations, easy cross-tenant queries
   - Cons: High risk of data leaks, complex row-level security

2. **Database-per-tenant**: Separate database for each tenant
   - Pros: Complete isolation, independent scaling
   - Cons: Expensive, complex connection management, hard to maintain

**Rationale**:
- Schema isolation provides good security boundary
- Easier to manage than 1,000+ databases
- PostgreSQL handles schemas efficiently
- Allows shared public schema for platform data
- Complies with data isolation requirements

**Implications**:
- Must implement schema switching middleware
- Migrations need to run across all schemas
- Connection pool must be carefully managed
- Monitor schema count limits (PostgreSQL has practical limits)

---

### Decision 2: Async SQLAlchemy with asyncpg
**Date**: 2025-01-11  
**Status**: Approved  

**Decision**: Use SQLAlchemy 2.0+ with async support via asyncpg driver.

**Context**:
- Platform is async-first (FastAPI, async tools)
- Need high concurrent connection handling
- Performance critical for multi-tenant system

**Rationale**:
- Native async prevents blocking operations
- Better performance than sync + thread pools
- asyncpg is the fastest PostgreSQL driver for Python
- SQLAlchemy provides good ORM abstractions

**Implications**:
- All database operations must be async
- Need careful session management
- Must use async context managers
- Testing requires async test fixtures

---

### Decision 3: Repository Pattern for Data Access
**Date**: 2025-01-11  
**Status**: Approved  

**Decision**: Implement repository pattern on top of SQLAlchemy models.

**Context**:
- Need to abstract database operations from business logic
- Multiple agents/tools will access same data
- Want to centralize query optimization

**Rationale**:
- Separates data access from business logic
- Easier to test with mock repositories
- Central place for query optimization
- Can add caching layer transparently

**Implications**:
- Additional abstraction layer to maintain
- All data access through repositories
- Need repository factory for dependency injection

---

### Decision 4: Connection Pool Strategy
**Date**: 2025-01-11  
**Status**: Approved  

**Decision**: Use connection pool with 20 min, 100 max connections, with per-tenant connection limiting.

**Context**:
- PostgreSQL default max connections is 100
- Need to support concurrent requests from multiple tenants
- Must prevent single tenant from exhausting pool

**Rationale**:
- 20 min ensures quick response for active tenants
- 100 max prevents database overload
- Per-tenant limits ensure fair resource sharing
- Can adjust based on monitoring

**Implications**:
- Need connection pool monitoring
- May need to increase PostgreSQL max_connections
- Implement queueing for connection-heavy operations

---

### Decision 5: Alembic for Migrations
**Date**: 2025-01-11  
**Status**: Approved  

**Decision**: Use Alembic for database migrations with custom multi-schema support.

**Context**:
- Need version-controlled database changes
- Must apply migrations to all tenant schemas
- Require rollback capability

**Rationale**:
- Alembic is the standard for SQLAlchemy
- Can customize for multi-schema migrations
- Provides version tracking and rollback
- Integrates well with CI/CD

**Implications**:
- Need custom migration runner for all schemas
- Longer migration times with many tenants
- Must test migrations thoroughly before production

---

### Decision 6: Table Prefix Convention
**Date**: 2025-01-11  
**Status**: Approved  

**Decision**: Implement consistent table prefixes for easier maintenance and organization.

**Context**:
- Multi-tenant system will have many tables per schema
- Need clear organization for maintenance
- Database tooling works better with predictable naming
- Easier to identify table purpose at a glance

**Prefix Convention**:
- `sys_` - System tables (public schema)
- `core_` - Core platform tables (users, orgs)
- `agent_` - Agent-related tables
- `task_` - Task management tables
- `wf_` - Workflow tables
- `int_` - Integration tables
- `log_` - Logging and audit tables
- `cache_` - Cache tables
- `temp_` - Temporary processing tables

**Rationale**:
- Groups related tables together in listings
- Makes purpose immediately clear
- Simplifies permission management (GRANT on agent_* tables)
- Easier to write maintenance scripts
- Prevents naming conflicts
- Helps with database documentation generation

**Implications**:
- All models must follow prefix convention
- Migrations must use consistent prefixes
- Need to update SQLAlchemy table naming
- Documentation must include prefix guide

**Example Implementation**:
```python
class User(Base):
    __tablename__ = "core_users"
    
class AgentDefinition(Base):
    __tablename__ = "agent_definitions"
```

---

## Pending Decisions

### RDS vs Aurora PostgreSQL
**Date Raised**: 2025-01-11  
**Status**: Pending  
**Deadline**: Before production deployment  

**Options**:
1. **RDS PostgreSQL**
   - Pros: Lower cost, simpler, predictable pricing
   - Cons: Manual scaling, longer failover

2. **Aurora PostgreSQL**
   - Pros: Auto-scaling, faster failover, better performance
   - Cons: Higher cost, complexity, vendor lock-in

**Factors to Consider**:
- Initial budget constraints
- Expected growth rate
- Performance requirements
- Operational complexity tolerance

---

## Decision Review Schedule

- **Monthly**: Review connection pool settings based on metrics
- **Quarterly**: Review multi-tenant strategy as tenant count grows
- **Yearly**: Review database technology choice

---

## References

- [PostgreSQL Schema Documentation](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Multi-tenant SaaS Architecture](https://www.citusdata.com/blog/2016/10/03/designing-your-saas-database-for-high-scalability/)
- [Repository Pattern in Python](https://www.cosmicpython.com/book/chapter_02_repository.html)