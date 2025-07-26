# Hanzo Memory Service - Full API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Memory Management API](#memory-management-api)
4. [Knowledge Base API](#knowledge-base-api)
5. [Chat Management API](#chat-management-api)
6. [MCP Server](#mcp-server)
7. [Data Models](#data-models)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

## Overview

The Hanzo Memory Service provides a comprehensive API for managing memories, knowledge bases, and chat histories with intelligent search and retrieval capabilities.

**Base URL**: `http://localhost:4000`

**API Version**: `v1`

## Authentication

The API uses Bearer token authentication. Include your API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

Alternative authentication methods:
- `x-hanzo-api-key` header
- `x-api-key` header
- `apikey` in request body (for backwards compatibility)

### Disabling Auth for Development

Set `HANZO_DISABLE_AUTH=true` in your environment to disable authentication.

## Memory Management API

### POST /v1/remember

Retrieve relevant memories and store a new memory in one operation.

**Request Body:**
```json
{
  "apikey": "optional-api-key",
  "userid": "user-123",
  "messagecontent": "Remember that I prefer dark mode interfaces",
  "additionalcontext": "User preferences discussion",
  "strippii": false,
  "filterresults": true,
  "includememoryid": false
}
```

**Parameters:**
- `userid` (required): User identifier
- `messagecontent` (required): Content to remember and search for
- `additionalcontext`: Additional context for the memory
- `strippii`: Strip personally identifiable information (default: false)
- `filterresults`: Use LLM to filter search results for relevance (default: false)
- `includememoryid`: Include memory IDs in response (default: false)

**Response:**
```json
{
  "user_id": "user-123",
  "relevant_memories": [
    "User prefers VS Code as their editor",
    "User likes dark themes in general"
  ],
  "memory_stored": true,
  "usage_info": {
    "current": 42,
    "limit": 10000
  }
}
```

### POST /v1/memories/add

Add explicit memories without importance analysis.

**Request Body:**
```json
{
  "apikey": "optional-api-key",
  "userid": "user-123",
  "memoriestoadd": [
    "User is allergic to shellfish",
    "User's birthday is March 15th"
  ]
}
```

**Response:**
```json
{
  "userid": "user-123",
  "added_count": 2,
  "memory_ids": ["mem_abc123", "mem_def456"],
  "usage_info": {
    "current": 44,
    "limit": 10000
  }
}
```

### POST /v1/memories/get

Retrieve stored memories with pagination.

**Request Body:**
```json
{
  "apikey": "optional-api-key",
  "userid": "user-123",
  "memoryid": "mem_abc123",  // Optional: get specific memory
  "limit": 50,
  "startafter": "mem_xyz789"
}
```

**Response:**
```json
{
  "user_id": "user-123",
  "memories": [
    {
      "memory_id": "mem_abc123",
      "content": "User is allergic to shellfish",
      "importance": 8.5,
      "metadata": {
        "category": "health",
        "added_at": "2024-01-15T10:30:00Z"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "has_more": true,
    "last_id": "mem_ghi789"
  },
  "usage_info": {
    "current": 44,
    "limit": 10000
  }
}
```

### POST /v1/memories/delete

Delete a specific memory.

**Request Body:**
```json
{
  "apikey": "optional-api-key",
  "userid": "user-123",
  "memoryid": "mem_abc123"
}
```

**Response:**
```json
{
  "message": "Memory deleted successfully",
  "memory_id": "mem_abc123",
  "userid": "user-123"
}
```

### POST /v1/user/delete

Delete all memories for a user.

**Request Body:**
```json
{
  "apikey": "optional-api-key",
  "userid": "user-123",
  "confirmdelete": true
}
```

**Response:**
```json
{
  "message": "All user memories deleted",
  "userid": "user-123",
  "deleted_count": 44
}
```

## Knowledge Base API

### POST /v1/kb/create

Create a new knowledge base.

**Request Body:**
```json
{
  "userid": "user-123",
  "name": "Python Programming",
  "kb_id": "kb_python",  // Optional custom ID
  "description": "Knowledge about Python programming",
  "project_id": "proj_456"  // Optional
}
```

**Response:**
```json
{
  "kb_id": "kb_python",
  "message": "Knowledge base 'Python Programming' created successfully"
}
```

### GET /v1/kb/list

List knowledge bases for a user.

**Query Parameters:**
- `userid` (required): User ID
- `project_id`: Filter by project ID

**Response:**
```json
{
  "userid": "user-123",
  "knowledge_bases": [
    {
      "kb_id": "kb_python",
      "name": "Python Programming",
      "description": "Knowledge about Python programming",
      "fact_count": 150,
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 1
}
```

### POST /v1/kb/facts/add

Add facts to a knowledge base.

**Request Body:**
```json
{
  "userid": "user-123",
  "kb_id": "kb_python",
  "facts": [
    {
      "content": "Python uses indentation for code blocks",
      "metadata": {
        "category": "syntax",
        "importance": "high"
      },
      "parent_id": null,
      "fact_id": "fact_001"  // Optional custom ID
    },
    {
      "content": "Standard indentation is 4 spaces",
      "parent_id": "fact_001",
      "metadata": {
        "category": "style"
      }
    }
  ]
}
```

**Response:**
```json
{
  "kb_id": "kb_python",
  "facts_added": 2,
  "facts": [
    {
      "fact_id": "fact_001",
      "content": "Python uses indentation for code blocks"
    },
    {
      "fact_id": "fact_abc123",
      "content": "Standard indentation is 4 spaces"
    }
  ]
}
```

### POST /v1/kb/facts/get

Get facts from a knowledge base.

**Request Body:**
```json
{
  "userid": "user-123",
  "kb_id": "kb_python",
  "query": "indentation rules",  // Optional: search query
  "fact_id": "fact_001",  // Optional: get specific fact
  "subtree": true,  // Get fact and all children
  "limit": 50
}
```

**Response:**
```json
{
  "kb_id": "kb_python",
  "facts": [
    {
      "fact_id": "fact_001",
      "content": "Python uses indentation for code blocks",
      "parent_id": null,
      "metadata": {
        "category": "syntax",
        "importance": "high"
      },
      "similarity_score": 0.95
    },
    {
      "fact_id": "fact_abc123",
      "content": "Standard indentation is 4 spaces",
      "parent_id": "fact_001",
      "metadata": {
        "category": "style"
      },
      "similarity_score": 0.88
    }
  ],
  "total": 2
}
```

### POST /v1/kb/facts/delete

Delete a fact from a knowledge base.

**Request Body:**
```json
{
  "userid": "user-123",
  "kb_id": "kb_python",
  "fact_id": "fact_001",
  "cascade": true  // Delete all child facts
}
```

**Response:**
```json
{
  "kb_id": "kb_python",
  "fact_id": "fact_001",
  "deleted": true,
  "cascade": true
}
```

## Chat Management API

### POST /v1/chat/sessions/create

Create a new chat session.

**Request Body:**
```json
{
  "userid": "user-123",
  "session_id": "session_abc",  // Optional custom ID
  "project_id": "proj_456",  // Optional
  "title": "Python Help Session",
  "metadata": {
    "client": "web",
    "version": "1.0"
  }
}
```

**Response:**
```json
{
  "session_id": "session_abc",
  "userid": "user-123",
  "project_id": "proj_456",
  "created": true
}
```

### POST /v1/chat/messages/add

Add a message to a chat session with automatic de-duplication.

**Request Body:**
```json
{
  "userid": "user-123",
  "session_id": "session_abc",
  "role": "user",  // user, assistant, or system
  "content": "How do I create a virtual environment in Python?",
  "project_id": "proj_456",  // Optional
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Response:**
```json
{
  "chat_id": "msg_xyz789",
  "session_id": "session_abc",
  "duplicate": false  // True if message was deduplicated
}
```

### GET /v1/chat/sessions/{session_id}/messages

Get messages for a chat session.

**Path Parameters:**
- `session_id`: The session ID

**Query Parameters:**
- `userid` (required): User ID
- `limit`: Maximum messages to return (default: 100, max: 1000)

**Response:**
```json
{
  "session_id": "session_abc",
  "messages": [
    {
      "chat_id": "msg_001",
      "role": "user",
      "content": "How do I create a virtual environment in Python?",
      "metadata": {
        "timestamp": "2024-01-15T10:30:00Z"
      },
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "chat_id": "msg_002",
      "role": "assistant",
      "content": "You can create a virtual environment using: python -m venv myenv",
      "metadata": {
        "model": "gpt-4"
      },
      "created_at": "2024-01-15T10:30:15Z"
    }
  ],
  "total": 2
}
```

### POST /v1/chat/search

Search across chat messages.

**Query Parameters:**
- `query` (required): Search query
- `userid` (required): User ID
- `project_id`: Filter by project
- `session_id`: Filter by session
- `limit`: Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "query": "virtual environment",
  "messages": [
    {
      "chat_id": "msg_001",
      "session_id": "session_abc",
      "role": "user",
      "content": "How do I create a virtual environment in Python?",
      "similarity_score": 0.95,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

## MCP Server

The service includes a Model Context Protocol (MCP) server for AI tool integration.

### Installation

Add to Claude Desktop configuration:

```json
{
  "mcpServers": {
    "hanzo-memory": {
      "command": "uv",
      "args": ["run", "hanzo-memory-mcp"],
      "cwd": "/path/to/hanzo/memory"
    }
  }
}
```

### Available Tools

1. **remember** - Store and retrieve memories
2. **recall** - Search for memories
3. **create_project** - Create a new project
4. **create_knowledge_base** - Create a knowledge base
5. **add_fact** - Add facts to a knowledge base
6. **search_facts** - Search facts in a knowledge base
7. **summarize_for_knowledge** - Generate knowledge instructions

## Data Models

### Memory
```typescript
interface Memory {
  memory_id: string;
  user_id: string;
  project_id: string;
  content: string;
  importance: number;  // 0-10
  metadata: Record<string, any>;
  embedding?: number[];  // Vector embedding
  created_at: string;
  updated_at: string;
}
```

### Knowledge Base
```typescript
interface KnowledgeBase {
  kb_id: string;
  user_id: string;
  project_id: string;
  name: string;
  description: string;
  metadata: Record<string, any>;
  fact_count: number;
  created_at: string;
  updated_at: string;
}
```

### Fact
```typescript
interface Fact {
  fact_id: string;
  kb_id: string;
  content: string;
  parent_id?: string;  // For hierarchical facts
  metadata: Record<string, any>;
  embedding?: number[];
  created_at: string;
  updated_at: string;
}
```

### Chat Message
```typescript
interface ChatMessage {
  chat_id: string;
  session_id: string;
  user_id: string;
  project_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata: Record<string, any>;
  embedding?: number[];
  created_at: string;
}
```

## Error Handling

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

## Rate Limiting

Default limits (configurable):
- 1000 requests per hour per API key
- 100 concurrent requests per API key
- 10MB maximum request size

## Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:4000"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Store a memory
response = requests.post(
    f"{BASE_URL}/v1/remember",
    headers=headers,
    json={
        "userid": "user-123",
        "messagecontent": "I prefer TypeScript over JavaScript",
        "additionalcontext": "Programming preferences"
    }
)

print(response.json())
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = "http://localhost:4000";
const API_KEY = "your-api-key";

// Add facts to knowledge base
const response = await fetch(`${BASE_URL}/v1/kb/facts/add`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    userid: "user-123",
    kb_id: "kb_typescript",
    facts: [
      {
        content: "TypeScript is a superset of JavaScript",
        metadata: { category: "definition" }
      }
    ]
  })
});

const result = await response.json();
console.log(result);
```

### cURL Examples

```bash
# Create a chat session
curl -X POST http://localhost:4000/v1/chat/sessions/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "userid": "user-123",
    "title": "Help with Python"
  }'

# Search memories
curl -X POST http://localhost:4000/v1/remember \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "userid": "user-123",
    "messagecontent": "What are my programming preferences?",
    "filterresults": true
  }'
```

## Performance Considerations

1. **Embeddings** are generated locally using FastEmbed (no API calls)
2. **Vector search** uses InfinityDB's efficient in-memory indexing
3. **De-duplication** uses similarity threshold (0.99) to prevent exact duplicates
4. **Batch operations** are recommended for bulk inserts
5. **Caching** can be enabled with Redis for high-traffic scenarios

## Security Best Practices

1. Always use HTTPS in production
2. Rotate API keys regularly
3. Enable rate limiting
4. Use project-based isolation for multi-tenant scenarios
5. Configure CORS appropriately
6. Never store sensitive data in metadata fields
7. Enable PII stripping for sensitive content

## Troubleshooting

### Common Issues

1. **InfinityDB not available on platform**
   - The service automatically falls back to a mock implementation
   - Full functionality is available on Linux x86_64

2. **Embedding model download fails**
   - Models are cached after first download
   - Ensure sufficient disk space (~400MB per model)

3. **LLM API errors**
   - Check API keys are correctly set
   - Verify model names match provider format
   - Use local models (Ollama) for offline operation

### Debug Mode

Enable debug logging:
```bash
HANZO_LOG_LEVEL=DEBUG uvicorn hanzo_memory.server:app
```

### Health Check

```bash
curl http://localhost:4000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "hanzo-memory",
  "version": "0.1.0"
}
```