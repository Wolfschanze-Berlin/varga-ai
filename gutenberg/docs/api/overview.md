---
sidebar_position: 1
title: API Overview
description: Complete API documentation and integration guide
---

# API Reference Overview

The Varga AI platform provides a comprehensive REST API for managing agents, workflows, and integrations. All APIs follow REST principles with JSON request/response formats.

## Base URL

```
https://api.varga-ai.com/v1
```

## Authentication

All API requests require authentication via Bearer tokens:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  https://api.varga-ai.com/v1/agents
```

### Getting API Tokens

1. Log into your Varga AI dashboard
2. Navigate to Settings > API Keys
3. Generate a new API token with appropriate scopes

## API Endpoints

### Agents Management

#### List Available Agents
```http
GET /api/v1/agents
```

**Response:**
```json
{
  "agents": [
    {
      "id": "web_search",
      "name": "Web Search Tool",
      "description": "Search the internet for information",
      "category": "utilities",
      "status": "active"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 20
}
```

#### Execute Agent Task
```http
POST /api/v1/agents/{agent_id}/execute
```

**Request Body:**
```json
{
  "task": {
    "query": "Find information about AutoGen framework",
    "max_results": 10
  },
  "context": {
    "tenant_id": "your-tenant-id",
    "user_id": "user-123"
  }
}
```

### Tools API

#### List Available Tools
```http
GET /api/v1/tools
```

#### Tool Configuration
```http
PUT /api/v1/tools/{tool_id}/config
```

### Workflows API

#### Create Workflow
```http
POST /api/v1/workflows
```

#### Execute Workflow
```http
POST /api/v1/workflows/{workflow_id}/execute
```

## Rate Limiting

The API implements multi-scope rate limiting:

- **Global**: 10,000 requests/hour across all tenants
- **Per Tenant**: 1,000 requests/hour per tenant
- **Per User**: 100 requests/hour per user
- **Per Tool**: Tool-specific limits

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

All errors follow the standard format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request parameters are invalid",
    "details": {
      "field": "query",
      "issue": "Query cannot be empty"
    },
    "request_id": "req_123456789"
  }
}
```

### Error Codes

- `INVALID_REQUEST` (400): Malformed request
- `UNAUTHORIZED` (401): Invalid or missing authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `RATE_LIMITED` (429): Rate limit exceeded
- `INTERNAL_ERROR` (500): Server error

## SDKs and Libraries

### Python SDK
```python
from varga_ai import VargaAI

client = VargaAI(api_key="your_api_key")
result = await client.agents.web_search.execute({
    "query": "AutoGen Microsoft framework",
    "max_results": 10
})
```

### JavaScript SDK
```javascript
import { VargaAI } from '@varga-ai/sdk';

const client = new VargaAI({ apiKey: 'your_api_key' });
const result = await client.agents.webSearch.execute({
  query: 'AutoGen Microsoft framework',
  maxResults: 10
});
```

## Webhooks

Configure webhooks to receive real-time notifications:

```http
POST /api/v1/webhooks
```

**Payload:**
```json
{
  "url": "https://your-app.com/webhooks/varga-ai",
  "events": ["agent.completed", "workflow.failed"],
  "secret": "your_webhook_secret"
}
```

## Best Practices

### Pagination
Always use pagination for list endpoints:
```http
GET /api/v1/agents?page=1&limit=20
```

### Idempotency
Use idempotency keys for critical operations:
```http
POST /api/v1/workflows/execute
Idempotency-Key: unique-key-123
```

### Error Handling
Implement exponential backoff for rate-limited requests:
```python
import time
import random

def api_request_with_backoff(request_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return request_func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

### Security
- Always use HTTPS for API requests
- Store API keys securely (environment variables, key vaults)
- Implement proper error handling to avoid exposing sensitive data
- Use webhook secrets to verify payload authenticity

## Support

For API support and questions:
- Check the [User Guides](../guides/getting-started) section
- Review [Implementation Examples](../development/implementation-status)
- Contact our technical support team