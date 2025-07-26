# Memory API Documentation

## Introduction

Memory API provides long-term memory and contextual knowledge capabilities for AI applications, enabling systems to:

* **Remember past interactions** with users
* **Maintain context** across sessions
* **Retrieve relevant information** from previous conversations or a dedicated knowledge base

These capabilities support more personalized, contextually aware, and human-like AI experiences.

### Authentication

* **Production**: All endpoints require an API key provided via the `x-hanzo-api-key` HTTP header or set in the `HANZO_API_KEY` environment variable.
* **Local Development**: Authentication can be disabled when running locally by setting `DISABLE_AUTH=true` or omitting the header.

> **Note:** All endpoints are RESTful and expect JSON request bodies with **lowercase** key names (e.g., `userid`, `messagecontent`). The `userid` parameter is **mandatory** for most endpoints; it partitions data per user to ensure multi-tenancy and security.

## Core Memory API

### 1. POST /v1/remember

**Retrieve & Store Memories**

* **Description:** Retrieves relevant memories for the incoming message, enqueues the message for storage, and optionally filters results via an LLM.
* **Authentication:** API key required in header `Authorization: Bearer <apikey>` or JSON field `apikey`.

#### Request Parameters

| Name                | Type    | Required | Description                                                  |
| ------------------- | ------- | -------- | ------------------------------------------------------------ |
| `apikey`            | string  | Yes      | Your API key.                                                |
| `userid`            | string  | Yes      | Unique user identifier.                                      |
| `messagecontent`    | string  | Yes      | Message text for retrieval and storage.                      |
| `additionalcontext` | string  | No       | Extra context to improve retrieval or LLM filtering.         |
| `strippii`          | boolean | No       | Anonymize PII during storage (default: false).               |
| `filterresults`     | boolean | No       | Use LLM to filter to top 3 memories (default: false).        |
| `includememoryid`   | boolean | No       | Return objects with `content` & `memoryId` (default: false). |

#### Example Request

```json
POST /v1/remember
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "userid": "user-123",
  "messagecontent": "I prefer dark mode interfaces",
  "filterresults": true,
  "includememoryid": true
}
```

#### Example Response

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "userid": "user-123",
  "relevant_memories": [
    {"content": "User previously chose dark theme.", "memory_id": "mem_abc123"}
  ],
  "memory_stored": true,
  "usage_info": {"current": 15, "limit": 1000}
}
```

---

### 2. POST /v1/memories/add

**Add Explicit Memories**

* **Description:** Directly adds one or more memory strings, bypassing importance analysis.

#### Request Parameters

| Name            | Type         | Required | Description                               |
| --------------- | ------------ | -------- | ----------------------------------------- |
| `apikey`        | string       | Yes      | Your API key.                             |
| `userid`        | string       | Yes      | Unique user identifier.                   |
| `memoriestoadd` | string/array | Yes      | Single string or array of strings to add. |

#### Example Request

```json
POST /v1/memories/add
{
  "apikey": "YOUR_API_KEY",
  "userid": "user-123",
  "memoriestoadd": [
    "User likes chocolate ice cream",
    "User is allergic to nuts"
  ]
}
```

#### Example Response

```json
HTTP/1.1 200 OK
{
  "userid": "user-123",
  "added_count": 2,
  "memory_ids": ["mem_001", "mem_002"],
  "usage_info": {"current": 17, "limit": 1000}
}
```

---

### 3. POST /v1/memories/get

**Retrieve Stored Memories**

* **Description:** Fetches a single memory by ID or a paginated list for a user.

#### Request Parameters

| Name         | Type    | Required | Description                                        |
| ------------ | ------- | -------- | -------------------------------------------------- |
| `apikey`     | string  | Yes      | Your API key.                                      |
| `userid`     | string  | Yes      | Unique user identifier.                            |
| `memoryid`   | string  | No       | Specific memory ID (ignores `limit`/`startafter`). |
| `limit`      | integer | No       | Maximum memories to return (default: 50).          |
| `startafter` | string  | No       | Memory ID to start after (for pagination).         |

#### Example Response (List)

```json
HTTP/1.1 200 OK
{
  "userid": "user-123",
  "memories": [
    {
      "memory_id": "mem_001",
      "content": "User likes chocolate ice cream",
      "timestamp": "2025-07-22T14:23:01Z"
    }
  ],
  "pagination": {"has_more": false, "last_id": "mem_001"},
  "usage_info": {"current": 20, "limit": 1000}
}
```

---

### 4. POST /v1/memories/delete

**Delete a Specific Memory**

* **Description:** Removes a single memory by its ID.

#### Request Parameters

| Name       | Type   | Required | Description                 |
| ---------- | ------ | -------- | --------------------------- |
| `apikey`   | string | Yes      | Your API key.               |
| `userid`   | string | Yes      | Unique user identifier.     |
| `memoryid` | string | Yes      | ID of the memory to delete. |

#### Example Response

```json
HTTP/1.1 200 OK
{
  "message": "Memory deleted successfully",
  "memory_id": "mem_001",
  "userid": "user-123"
}
```

---

### 5. POST /v1/user/delete

**Delete All Memories for a User**

* **Description:** Permanently deletes all memories for a given user. Requires explicit confirmation.

#### Request Parameters

| Name            | Type    | Required | Description                         |
| --------------- | ------- | -------- | ----------------------------------- |
| `apikey`        | string  | Yes      | Your API key.                       |
| `userid`        | string  | Yes      | Unique user identifier.             |
| `confirmdelete` | boolean | Yes      | Must be `true` to confirm deletion. |

#### Example Response

```json
HTTP/1.1 200 OK
{
  "message": "All user memories deleted",
  "userid": "user-123",
  "deleted_count": 42
}
```

---

## MCP Server API

The MCP Server API exposes Memory and Fact operations via the Model Context Protocol. Use your dedicated MCP URL (including `:userid`) and authenticate with a Bearer token or `x-api-key`.

### POST /v1/mcp/\:userid

**All Tools Endpoint**: Access both Core Memory and Fact APIs, plus Knowledge tools

#### Available MCP Tools

* `addMemories`, `getMemories`, `deleteMemory`
* `addKnowledge`, `getKnowledge`, `deleteKnowledge`
* `addFacts`, `getFacts`, `deleteFact`

#### Example Request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "addMemories",
    "arguments": {"memoriesToAdd": ["dark mode", "vegan user"]}
  }
}
```

---

### POST /v1/mcp/memory/\:userid

**Memory-Only Tools**: `addMemories`, `getMemories`, `deleteMemory`

---

### POST /v1/mcp/knowledge/\:userid

**Knowledge-Only Tools**: `addKnowledge`, `getKnowledge`, `deleteKnowledge`, `listSources`

---

## Knowledge API (Multi-Base Graph)

The Knowledge API handles structured knowledge—individual facts—organized into one or more **knowledge bases** per user. Each knowledge base is a separate namespace, and within each, facts are stored as nodes in a directed graph in a SQL backend. Facts can be linked via parent–child relationships to model hierarchies or networks.

### Data Model

A typical SQL schema:

```sql
-- Knowledge bases (namespaces)
CREATE TABLE knowledge_bases (
  kb_id      VARCHAR PRIMARY KEY,
  userid     VARCHAR NOT NULL,
  name       TEXT,
  metadata   JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact nodes
CREATE TABLE facts (
  fact_id    VARCHAR PRIMARY KEY,
  kb_id      VARCHAR REFERENCES knowledge_bases(kb_id),
  content    TEXT NOT NULL,
  metadata   JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships between facts
CREATE TABLE fact_relations (
  parent_fact_id VARCHAR REFERENCES facts(fact_id),
  child_fact_id  VARCHAR REFERENCES facts(fact_id),
  relation_type  VARCHAR,
  PRIMARY KEY(parent_fact_id, child_fact_id)
);
```

* **knowledge\_bases**: Namespaces for facts. A user can own multiple bases.
* **facts**: Individual fact nodes within a base (`kb_id`).
* **fact\_relations**: Directed edges modeling parent → child links.

### Key Concepts

* **Multiple Knowledge Bases**: Create, list, and delete bases to partition knowledge.
* **Fact Nodes**: Store `content` plus optional JSON `metadata` per fact.
* **Edges**: Build rich fact networks via `fact_relations`.
* **Recursive Traversal**: Use SQL CTEs for subtree queries.

### Endpoints

All endpoints require `userid` and either the `x-hanzo-api-key` header or `HANZO_API_KEY` environment variable (unless `DISABLE_AUTH=true`).

#### 1. POST /v1/knowledge/bases/create

**Create a new knowledge base**

| Field   | Type   | Required | Description                            |
| ------- | ------ | -------- | -------------------------------------- |
| `name`  | string | Yes      | Display name for the base.             |
| `kb_id` | string | No       | Custom ID (auto-generated if omitted). |

**Response:**

```json
{ "success": true, "kb_id": "kb_123", "name": "Engineering Knowledge" }
```

#### 2. POST /v1/knowledge/bases/list

**List knowledge bases for a user**

| Field    | Type   | Required | Description      |
| -------- | ------ | -------- | ---------------- |
| `userid` | string | Yes      | User identifier. |

**Response:**

```json
{ "bases": [ { "kb_id": "kb_123", "name": "Engineering Knowledge", "created_at": "2025-07-22T..." } ] }
```

#### 3. POST /v1/knowledge/add

**Add facts to a knowledge base**

| Field    | Type         | Required | Description                                                          |
| -------- | ------------ | -------- | -------------------------------------------------------------------- |
| `userid` | string       | Yes      | User identifier.                                                     |
| `kb_id`  | string       | Yes      | Target knowledge base.                                               |
| `facts`  | array of obj | Yes      | List of facts: `{ fact_id?(auto), content, metadata?, parent_id? }`. |

**Behavior:** Inserts into `facts` and, if `parent_id` provided, into `fact_relations`.

**Response:**

```json
{ "success": true, "inserted": 5 }
```

#### 4. POST /v1/knowledge/get

**Retrieve facts**

| Field     | Type    | Required | Description                                    |
| --------- | ------- | -------- | ---------------------------------------------- |
| `userid`  | string  | Yes      | User identifier.                               |
| `kb_id`   | string  | Yes      | Knowledge base ID.                             |
| `fact_id` | string  | No       | Single fact ID to fetch.                       |
| `subtree` | boolean | No       | If true, fetch this fact plus all descendants. |
| `query`   | string  | No       | Full-text search on `content`.                 |
| `limit`   | integer | No       | Max facts to return (default: 50).             |

**Behavior:**

* With `fact_id` + `subtree=true`, uses a SQL recursive CTE to traverse descendants.
* Otherwise, returns matching nodes.

**Response:**

```json
{ "facts": [ { "fact_id":"f_1","content":"...","metadata":{} } ], "pagination": {...} }
```

#### 5. POST /v1/knowledge/delete

**Delete facts**

| Field     | Type    | Required | Description                                |
| --------- | ------- | -------- | ------------------------------------------ |
| `userid`  | string  | Yes      | User identifier.                           |
| `kb_id`   | string  | Yes      | Knowledge base ID.                         |
| `fact_id` | string  | Yes      | Fact node to delete.                       |
| `cascade` | boolean | No       | If true, also delete all descendant facts. |

#### 6. POST /v1/knowledge/ingest

**Configure GCS ingestion**

| Field         | Type            | Required | Description                                  |
| ------------- | --------------- | -------- | -------------------------------------------- |
| `userid`      | string          | Yes      | User identifier.                             |
| `kb_id`       | string          | Yes      | Target knowledge base.                       |
| `details`     | object          | Yes      | Must include `bucketUri` (e.g., `gs://...`). |
| `projecttags` | array of string | No       | Tags applied to all ingested facts.          |

**Behavior:** Sets up nightly sync from GCS into the specified base.

---

For more information, see the online docs at [https://your-api-domain.com/docs](https://your-api-domain.com/docs)
