# Hanzo Memory SDK - Complete Usage Guide

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Memory Management](#memory-management)
6. [Knowledge Bases](#knowledge-bases)
7. [Chat History](#chat-history)
8. [Search Capabilities](#search-capabilities)
9. [LLM Integration](#llm-integration)
10. [Vector Databases](#vector-databases)
11. [API Client Usage](#api-client-usage)
12. [MCP Integration](#mcp-integration)
13. [Production Deployment](#production-deployment)
14. [Examples](#examples)
15. [API Reference](#api-reference)

## Overview

Hanzo Memory is a high-performance memory and knowledge management service for AI applications. It provides:

- **Semantic Memory**: Store and retrieve contextual memories using vector similarity
- **Knowledge Management**: Hierarchical knowledge bases with facts and relationships
- **Chat History**: Persistent conversation storage with semantic search
- **Vector Search**: Fast similarity search using local embeddings
- **LLM Integration**: Flexible LLM support via LiteLLM
- **Multi-tenancy**: User and project isolation
- **Cross-platform**: Works on Linux, macOS, Windows, and browsers

## Installation

### Install as a Service

```bash
# Install with uvx
uvx install hanzo-memory

# Run the service
hanzo-memory

# Or run directly without installing
uvx hanzo-memory
```

### Install as a Python Package

```bash
# Basic installation
pip install hanzo-memory

# With all features
pip install hanzo-memory[all]

# For development
pip install hanzo-memory[dev]
```

### Docker Installation

```bash
# Using docker-compose
docker-compose up

# Or with Docker directly
docker build -t hanzo-memory .
docker run -p 4000:4000 -v $(pwd)/data:/app/data hanzo-memory
```

## Quick Start

### Starting the Service

```python
# Start the memory service
import subprocess
service = subprocess.Popen(["hanzo-memory"])

# Or use programmatically
from hanzo_memory import MemoryService
service = MemoryService()
await service.start()
```

### Basic Client Usage

```python
from hanzo_memory.client import MemoryClient

# Initialize client
client = MemoryClient(
    base_url="http://localhost:4000",
    api_key="your-api-key"
)

# Store a memory
memory = await client.remember(
    content="The user prefers dark mode interfaces",
    user_id="user123",
    metadata={"category": "preferences"}
)

# Search memories
results = await client.search_memories(
    query="user interface preferences",
    user_id="user123",
    limit=10
)

# Use knowledge base
kb = await client.create_knowledge_base(
    name="Product Documentation",
    description="Internal product knowledge"
)

fact = await client.add_fact(
    kb_id=kb.id,
    content="The application supports OAuth2 authentication",
    metadata={"section": "auth", "version": "2.0"}
)
```

## Core Concepts

### Memory Types

1. **Episodic Memory**: Event-based memories with temporal context
2. **Semantic Memory**: Facts and knowledge without specific temporal context
3. **Working Memory**: Short-term context for active conversations

### Data Model

```python
from hanzo_memory.models import Memory, KnowledgeBase, Fact, ChatMessage
from datetime import datetime
from typing import Optional, Dict, Any

# Memory model
class Memory:
    id: str
    content: str
    embedding: Optional[list[float]]
    user_id: str
    project_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    accessed_at: datetime
    access_count: int

# Knowledge base model
class KnowledgeBase:
    id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]  # Hierarchical KBs
    metadata: Dict[str, Any]
    created_at: datetime

# Fact model
class Fact:
    id: str
    kb_id: str
    content: str
    embedding: Optional[list[float]]
    confidence: float = 1.0
    metadata: Dict[str, Any]
    created_at: datetime

# Chat message model
class ChatMessage:
    id: str
    session_id: str
    role: str  # "user", "assistant", "system"
    content: str
    embedding: Optional[list[float]]
    metadata: Dict[str, Any]
    created_at: datetime
```

## Memory Management

### Storing Memories

```python
# Simple memory storage
memory = await client.remember(
    content="Important information to remember",
    user_id="user123"
)

# With metadata and project context
memory = await client.remember(
    content="Customer prefers email communication",
    user_id="user123",
    project_id="project456",
    metadata={
        "type": "preference",
        "customer_id": "cust789",
        "confidence": 0.9
    }
)

# Batch memory storage
memories = await client.remember_batch([
    {
        "content": "Meeting scheduled for 3pm",
        "metadata": {"type": "event", "date": "2024-01-15"}
    },
    {
        "content": "Project deadline is next Friday",
        "metadata": {"type": "deadline", "project": "Alpha"}
    }
], user_id="user123")
```

### Retrieving Memories

```python
# Get specific memory
memory = await client.get_memory(memory_id="mem_123")

# List memories with filters
memories = await client.list_memories(
    user_id="user123",
    project_id="project456",
    limit=50,
    offset=0
)

# Semantic search
results = await client.search_memories(
    query="communication preferences",
    user_id="user123",
    threshold=0.7,  # Similarity threshold
    limit=10
)

# Advanced search with filters
results = await client.search_memories(
    query="project deadlines",
    user_id="user123",
    filters={
        "metadata.type": "deadline",
        "created_at": {"$gte": "2024-01-01"}
    },
    limit=20
)
```

### Memory Operations

```python
# Update memory
updated = await client.update_memory(
    memory_id="mem_123",
    content="Updated information",
    metadata={"edited": True, "editor": "user123"}
)

# Delete memory
await client.delete_memory(memory_id="mem_123")

# Forget memories (bulk delete)
deleted_count = await client.forget_memories(
    user_id="user123",
    filters={"metadata.type": "temporary"}
)

# Memory consolidation
consolidated = await client.consolidate_memories(
    user_id="user123",
    strategy="summarize",  # or "merge", "deduplicate"
    time_window="7d"
)
```

## Knowledge Bases

### Creating Knowledge Bases

```python
# Create root knowledge base
kb = await client.create_knowledge_base(
    name="Company Knowledge",
    description="Central repository of company information"
)

# Create child knowledge base
product_kb = await client.create_knowledge_base(
    name="Product Documentation",
    description="Product-specific knowledge",
    parent_id=kb.id,
    metadata={"version": "2.0", "public": True}
)

# Hierarchical structure
departments = await client.create_knowledge_base(
    name="Departments",
    parent_id=kb.id
)

engineering = await client.create_knowledge_base(
    name="Engineering",
    parent_id=departments.id
)
```

### Managing Facts

```python
# Add fact to knowledge base
fact = await client.add_fact(
    kb_id=engineering.id,
    content="The API uses REST architecture with JSON responses",
    metadata={
        "category": "architecture",
        "importance": "high",
        "last_updated": "2024-01-15"
    }
)

# Batch add facts
facts = await client.add_facts_batch(
    kb_id=product_kb.id,
    facts=[
        {
            "content": "Feature X improves performance by 40%",
            "metadata": {"feature": "X", "metric": "performance"}
        },
        {
            "content": "Feature Y reduces memory usage",
            "metadata": {"feature": "Y", "metric": "memory"}
        }
    ]
)

# Update fact
updated_fact = await client.update_fact(
    fact_id=fact.id,
    content="The API uses REST architecture with JSON and XML responses",
    metadata={"revised": True}
)

# Search facts
results = await client.search_facts(
    kb_id=engineering.id,
    query="API architecture",
    include_children=True,  # Search child KBs too
    limit=10
)
```

### Knowledge Base Operations

```python
# List knowledge bases
kbs = await client.list_knowledge_bases(
    parent_id=None,  # Get root KBs
    include_children=True
)

# Get KB with facts
kb_details = await client.get_knowledge_base(
    kb_id=kb.id,
    include_facts=True,
    include_children=True
)

# Update KB
updated_kb = await client.update_knowledge_base(
    kb_id=kb.id,
    name="Company Knowledge Base v2",
    metadata={"last_review": "2024-01-15"}
)

# Delete KB (and optionally its facts)
await client.delete_knowledge_base(
    kb_id=kb.id,
    cascade=True  # Delete all facts and child KBs
)

# Export KB
export_data = await client.export_knowledge_base(
    kb_id=kb.id,
    format="json",  # or "markdown", "yaml"
    include_embeddings=False
)

# Import KB
imported_kb = await client.import_knowledge_base(
    name="Imported Knowledge",
    data=export_data,
    parent_id=None
)
```

## Chat History

### Managing Chat Sessions

```python
# Create chat session
session = await client.create_chat_session(
    user_id="user123",
    metadata={
        "platform": "web",
        "version": "2.0"
    }
)

# Add messages to session
user_msg = await client.add_chat_message(
    session_id=session.id,
    role="user",
    content="What's the weather like?"
)

assistant_msg = await client.add_chat_message(
    session_id=session.id,
    role="assistant",
    content="I'd be happy to help with weather information. Could you tell me your location?"
)

# Get session history
messages = await client.get_chat_history(
    session_id=session.id,
    limit=50,
    include_system_messages=True
)

# Search across sessions
results = await client.search_chat_history(
    user_id="user123",
    query="weather information",
    limit=20
)
```

### Advanced Chat Features

```python
# Summarize conversation
summary = await client.summarize_chat_session(
    session_id=session.id,
    style="bullet_points"  # or "paragraph", "key_points"
)

# Extract insights from chat
insights = await client.extract_chat_insights(
    session_id=session.id,
    insight_types=["preferences", "issues", "questions"]
)

# Find similar conversations
similar = await client.find_similar_conversations(
    session_id=session.id,
    user_id="user123",
    threshold=0.8,
    limit=5
)

# Chat analytics
analytics = await client.get_chat_analytics(
    user_id="user123",
    time_range="30d",
    metrics=["message_count", "session_duration", "topics"]
)
```

## Search Capabilities

### Unified Search

```python
# Search across all data types
results = await client.unified_search(
    query="authentication methods",
    user_id="user123",
    search_types=["memories", "facts", "chats"],
    limit=30
)

# Structured results
for result in results:
    print(f"Type: {result.type}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print(f"Metadata: {result.metadata}")
```

### Advanced Search Features

```python
# Faceted search
results = await client.faceted_search(
    query="API documentation",
    facets={
        "type": ["fact", "memory"],
        "metadata.category": ["architecture", "authentication"],
        "created_at": {
            "ranges": [
                {"from": "2024-01-01", "to": "2024-06-30"},
                {"from": "2024-07-01", "to": "2024-12-31"}
            ]
        }
    }
)

# Hybrid search (keyword + semantic)
results = await client.hybrid_search(
    keyword_query="REST API",
    semantic_query="how to authenticate users",
    keyword_weight=0.3,
    semantic_weight=0.7
)

# Search with reranking
results = await client.search_with_rerank(
    query="best practices for API design",
    initial_results=50,
    rerank_top_k=10,
    rerank_model="cross-encoder"
)
```

## LLM Integration

### Content Processing

```python
# Summarize content before storing
summary_result = await client.process_content(
    content="Long document text...",
    operations=["summarize", "extract_facts", "remove_pii"]
)

memory = await client.remember(
    content=summary_result.summary,
    original_content=content,
    metadata={
        "facts": summary_result.facts,
        "pii_removed": summary_result.pii_removed
    }
)

# Generate knowledge from content
knowledge = await client.extract_knowledge(
    content="Technical documentation...",
    kb_id=kb.id,
    auto_add_facts=True
)

# Smart deduplication
deduplicated = await client.smart_deduplicate(
    user_id="user123",
    similarity_threshold=0.9,
    use_llm_verification=True
)
```

### LLM-Enhanced Search

```python
# Query expansion
expanded_results = await client.search_with_expansion(
    query="auth",
    expand_synonyms=True,
    expand_related=True,
    max_expansions=5
)

# Contextual search
contextual_results = await client.contextual_search(
    query="How do I implement this?",
    context="Previous conversation about OAuth2",
    user_id="user123"
)

# Answer generation
answer = await client.generate_answer(
    question="What are the authentication methods?",
    kb_ids=[kb.id],
    include_sources=True,
    max_facts_to_use=10
)
```

## Vector Databases

### LanceDB Configuration

```python
from hanzo_memory.db import LanceDBConfig

# Configure LanceDB
config = LanceDBConfig(
    path="data/lancedb",
    embedding_model="BAAI/bge-small-en-v1.5",
    distance_metric="cosine",  # or "l2", "dot"
    index_type="IVF_PQ",  # or "FLAT", "HNSW"
    nprobe=20,  # for IVF index
    refine_factor=10
)

# Initialize with config
service = MemoryService(db_config=config)
```

### InfinityDB Configuration

```python
from hanzo_memory.db import InfinityDBConfig

# Configure InfinityDB (Linux/Windows only)
config = InfinityDBConfig(
    path="data/infinity_db",
    embedding_dimension=384,
    distance_type="cosine",
    index_type="HNSW",
    ef_construction=200,
    ef_search=100
)
```

### Custom Embeddings

```python
from hanzo_memory.embeddings import EmbeddingService

# Use custom embedding model
embedding_service = EmbeddingService(
    model_name="sentence-transformers/all-mpnet-base-v2",
    device="cuda",  # or "cpu"
    batch_size=32
)

# Generate embeddings
embeddings = await embedding_service.embed_batch([
    "Text to embed 1",
    "Text to embed 2"
])

# Use with client
client = MemoryClient(
    base_url="http://localhost:4000",
    embedding_service=embedding_service
)
```

## API Client Usage

### Async Client

```python
import asyncio
from hanzo_memory.client import AsyncMemoryClient

async def main():
    async with AsyncMemoryClient(
        base_url="http://localhost:4000",
        api_key="your-api-key"
    ) as client:
        # All operations are async
        memory = await client.remember("Important info")
        results = await client.search_memories("important")
        
        # Batch operations
        memories = await client.remember_batch([
            {"content": "Memory 1"},
            {"content": "Memory 2"}
        ])

asyncio.run(main())
```

### Sync Client

```python
from hanzo_memory.client import SyncMemoryClient

# Synchronous client for non-async code
client = SyncMemoryClient(
    base_url="http://localhost:4000",
    api_key="your-api-key"
)

# All operations are synchronous
memory = client.remember("Important info")
results = client.search_memories("important")
```

### Client Configuration

```python
from hanzo_memory.client import MemoryClient, ClientConfig

# Advanced configuration
config = ClientConfig(
    base_url="http://localhost:4000",
    api_key="your-api-key",
    timeout=30,  # seconds
    max_retries=3,
    retry_backoff=2.0,
    verify_ssl=True,
    proxy="http://proxy.example.com:8080"
)

client = MemoryClient(config=config)

# With custom headers
client = MemoryClient(
    base_url="http://localhost:4000",
    api_key="your-api-key",
    headers={
        "X-User-ID": "user123",
        "X-Project-ID": "project456"
    }
)
```

## MCP Integration

### MCP Server Mode

```python
# Run as MCP server
from hanzo_memory.mcp import MemoryMCPServer

server = MemoryMCPServer(
    name="hanzo-memory",
    version="1.0.0"
)

# Register tools
server.register_tools([
    "remember",
    "search_memories",
    "manage_knowledge_base",
    "chat_history"
])

# Start server
await server.start()
```

### Using with Claude Desktop

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "hanzo-memory": {
      "command": "hanzo-memory",
      "args": ["--mcp"],
      "env": {
        "HANZO_API_KEY": "your-api-key"
      }
    }
  }
}
```

### MCP Tools

```python
# Available MCP tools
tools = {
    "remember": {
        "description": "Store information in memory",
        "parameters": {
            "content": "string",
            "metadata": "object"
        }
    },
    "search_memories": {
        "description": "Search stored memories",
        "parameters": {
            "query": "string",
            "limit": "number"
        }
    },
    "add_fact": {
        "description": "Add fact to knowledge base",
        "parameters": {
            "kb_name": "string",
            "content": "string"
        }
    }
}
```

## Production Deployment

### Environment Configuration

```bash
# Production .env file
# API Configuration
HANZO_API_KEY=strong-random-key
HANZO_DISABLE_AUTH=false
HANZO_CORS_ORIGINS=["https://app.example.com"]

# Database
HANZO_DB_BACKEND=lancedb
HANZO_LANCEDB_PATH=/data/lancedb
HANZO_DB_BACKUP_ENABLED=true
HANZO_DB_BACKUP_INTERVAL=3600

# LLM Configuration
HANZO_LLM_MODEL=gpt-4o-mini
HANZO_LLM_TEMPERATURE=0.3
HANZO_LLM_MAX_TOKENS=2000
OPENAI_API_KEY=your-openai-key

# Embedding Configuration
HANZO_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
HANZO_EMBEDDING_BATCH_SIZE=100
HANZO_EMBEDDING_DEVICE=cuda

# Performance
HANZO_WORKERS=4
HANZO_MAX_CONNECTIONS=1000
HANZO_CACHE_ENABLED=true
HANZO_CACHE_TTL=3600

# Monitoring
HANZO_METRICS_ENABLED=true
HANZO_METRICS_PORT=9090
HANZO_LOG_LEVEL=INFO
```

### Docker Compose Production

```yaml
version: '3.8'

services:
  hanzo-memory:
    image: hanzo/memory:latest
    ports:
      - "4000:4000"
      - "9090:9090"  # Metrics
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - HANZO_API_KEY=${HANZO_API_KEY}
      - HANZO_DB_BACKEND=lancedb
      - HANZO_WORKERS=4
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9091:9090"

volumes:
  redis_data:
  prometheus_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hanzo-memory
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hanzo-memory
  template:
    metadata:
      labels:
        app: hanzo-memory
    spec:
      containers:
      - name: hanzo-memory
        image: hanzo/memory:latest
        ports:
        - containerPort: 4000
        - containerPort: 9090
        env:
        - name: HANZO_API_KEY
          valueFrom:
            secretKeyRef:
              name: hanzo-secrets
              key: api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: hanzo-secrets
              key: openai-key
        volumeMounts:
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 4000
          initialDelaySeconds: 30
          periodSeconds: 30
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: hanzo-memory-data
```

### Monitoring Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hanzo-memory'
    static_configs:
      - targets: ['hanzo-memory:9090']
    metrics_path: '/metrics'
```

### Backup Strategy

```python
from hanzo_memory.backup import BackupService

# Configure automatic backups
backup_service = BackupService(
    source_path="/data/lancedb",
    backup_path="/backups",
    retention_days=30,
    compression="gzip"
)

# Schedule backups
backup_service.schedule_daily(hour=2, minute=0)

# Manual backup
backup_path = await backup_service.backup_now(
    description="Pre-deployment backup"
)

# Restore from backup
await backup_service.restore(
    backup_path=backup_path,
    target_path="/data/lancedb_restored"
)
```

## Examples

### AI Assistant with Memory

```python
class MemoryAgent:
    def __init__(self, memory_client, user_id):
        self.memory = memory_client
        self.user_id = user_id
        self.session_id = None
    
    async def start_session(self):
        session = await self.memory.create_chat_session(
            user_id=self.user_id
        )
        self.session_id = session.id
    
    async def process_message(self, message: str):
        # Store user message
        await self.memory.add_chat_message(
            session_id=self.session_id,
            role="user",
            content=message
        )
        
        # Search relevant memories
        memories = await self.memory.search_memories(
            query=message,
            user_id=self.user_id,
            limit=5
        )
        
        # Search knowledge base
        facts = await self.memory.search_facts(
            query=message,
            limit=5
        )
        
        # Generate response with context
        context = self._build_context(memories, facts)
        response = await self._generate_response(message, context)
        
        # Store assistant response
        await self.memory.add_chat_message(
            session_id=self.session_id,
            role="assistant",
            content=response
        )
        
        # Extract and store any new information
        await self._extract_and_store_info(message, response)
        
        return response
    
    async def _extract_and_store_info(self, user_msg: str, assistant_msg: str):
        # Extract important information
        extraction = await self.memory.extract_knowledge(
            content=f"User: {user_msg}\nAssistant: {assistant_msg}",
            auto_add_facts=False
        )
        
        # Store as memories
        for fact in extraction.facts:
            if fact.confidence > 0.7:
                await self.memory.remember(
                    content=fact.content,
                    user_id=self.user_id,
                    metadata={"source": "conversation", "confidence": fact.confidence}
                )
```

### Knowledge Base Builder

```python
class KnowledgeBuilder:
    def __init__(self, memory_client):
        self.memory = memory_client
        self.kb_cache = {}
    
    async def build_from_documents(self, documents: List[str], kb_name: str):
        # Create knowledge base
        kb = await self.memory.create_knowledge_base(
            name=kb_name,
            description=f"Knowledge extracted from {len(documents)} documents"
        )
        
        # Process each document
        for i, doc in enumerate(documents):
            print(f"Processing document {i+1}/{len(documents)}")
            
            # Extract knowledge
            knowledge = await self.memory.extract_knowledge(
                content=doc,
                kb_id=kb.id,
                auto_add_facts=True
            )
            
            # Store document as memory too
            await self.memory.remember(
                content=knowledge.summary,
                metadata={
                    "type": "document",
                    "kb_id": kb.id,
                    "doc_index": i
                }
            )
        
        # Build relationships
        await self._build_fact_relationships(kb.id)
        
        return kb
    
    async def _build_fact_relationships(self, kb_id: str):
        # Get all facts
        facts = await self.memory.list_facts(kb_id=kb_id, limit=1000)
        
        # Find related facts
        for fact in facts:
            similar = await self.memory.search_facts(
                kb_id=kb_id,
                query=fact.content,
                exclude_ids=[fact.id],
                limit=5,
                threshold=0.8
            )
            
            # Update fact with relationships
            if similar:
                await self.memory.update_fact(
                    fact_id=fact.id,
                    metadata={
                        **fact.metadata,
                        "related_facts": [f.id for f in similar]
                    }
                )
```

### Memory-Augmented RAG System

```python
class MemoryRAG:
    def __init__(self, memory_client, llm_service):
        self.memory = memory_client
        self.llm = llm_service
    
    async def query(self, question: str, user_id: str, kb_ids: List[str] = None):
        # Multi-stage retrieval
        stage1_results = await self._broad_retrieval(question, user_id, kb_ids)
        stage2_results = await self._focused_retrieval(question, stage1_results)
        
        # Build context
        context = await self._build_augmented_context(
            question, 
            stage2_results,
            user_id
        )
        
        # Generate answer
        answer = await self.llm.generate(
            prompt=self._build_prompt(question, context),
            temperature=0.3
        )
        
        # Store Q&A as memory
        await self.memory.remember(
            content=f"Q: {question}\nA: {answer}",
            user_id=user_id,
            metadata={
                "type": "qa",
                "sources": [r.id for r in stage2_results]
            }
        )
        
        return {
            "answer": answer,
            "sources": stage2_results,
            "confidence": self._calculate_confidence(stage2_results)
        }
    
    async def _broad_retrieval(self, query: str, user_id: str, kb_ids: List[str]):
        results = []
        
        # Search memories
        memories = await self.memory.search_memories(
            query=query,
            user_id=user_id,
            limit=20
        )
        results.extend(memories)
        
        # Search knowledge bases
        if kb_ids:
            for kb_id in kb_ids:
                facts = await self.memory.search_facts(
                    kb_id=kb_id,
                    query=query,
                    limit=20
                )
                results.extend(facts)
        
        return results
    
    async def _focused_retrieval(self, query: str, initial_results: List):
        # Rerank using cross-encoder
        reranked = await self.memory.rerank_results(
            query=query,
            results=initial_results,
            top_k=10
        )
        
        # Expand with related content
        expanded = []
        for result in reranked[:5]:
            if hasattr(result, 'metadata') and 'related_facts' in result.metadata:
                related = await self.memory.get_facts(result.metadata['related_facts'])
                expanded.extend(related)
        
        return reranked + expanded
```

## API Reference

### Client Methods

```python
# Memory operations
async def remember(content: str, user_id: str, **kwargs) -> Memory
async def get_memory(memory_id: str) -> Memory
async def search_memories(query: str, user_id: str, **kwargs) -> List[Memory]
async def update_memory(memory_id: str, **kwargs) -> Memory
async def delete_memory(memory_id: str) -> None
async def forget_memories(user_id: str, **kwargs) -> int

# Knowledge base operations
async def create_knowledge_base(name: str, **kwargs) -> KnowledgeBase
async def get_knowledge_base(kb_id: str, **kwargs) -> KnowledgeBase
async def list_knowledge_bases(**kwargs) -> List[KnowledgeBase]
async def update_knowledge_base(kb_id: str, **kwargs) -> KnowledgeBase
async def delete_knowledge_base(kb_id: str, cascade: bool = False) -> None

# Fact operations
async def add_fact(kb_id: str, content: str, **kwargs) -> Fact
async def get_fact(fact_id: str) -> Fact
async def search_facts(kb_id: str, query: str, **kwargs) -> List[Fact]
async def update_fact(fact_id: str, **kwargs) -> Fact
async def delete_fact(fact_id: str) -> None

# Chat operations
async def create_chat_session(user_id: str, **kwargs) -> ChatSession
async def add_chat_message(session_id: str, role: str, content: str, **kwargs) -> ChatMessage
async def get_chat_history(session_id: str, **kwargs) -> List[ChatMessage]
async def search_chat_history(user_id: str, query: str, **kwargs) -> List[ChatMessage]

# Advanced operations
async def unified_search(query: str, **kwargs) -> List[SearchResult]
async def extract_knowledge(content: str, **kwargs) -> KnowledgeExtraction
async def generate_answer(question: str, kb_ids: List[str], **kwargs) -> AnswerResult
```

### REST API Endpoints

```
# Memory endpoints
POST   /v1/remember
GET    /v1/memories/{memory_id}
GET    /v1/memories
POST   /v1/memories/search
PUT    /v1/memories/{memory_id}
DELETE /v1/memories/{memory_id}
POST   /v1/memories/forget

# Knowledge base endpoints
POST   /v1/kb
GET    /v1/kb/{kb_id}
GET    /v1/kb
PUT    /v1/kb/{kb_id}
DELETE /v1/kb/{kb_id}

# Fact endpoints
POST   /v1/kb/{kb_id}/facts
GET    /v1/facts/{fact_id}
POST   /v1/kb/{kb_id}/facts/search
PUT    /v1/facts/{fact_id}
DELETE /v1/facts/{fact_id}

# Chat endpoints
POST   /v1/chat/sessions
POST   /v1/chat/sessions/{session_id}/messages
GET    /v1/chat/sessions/{session_id}/messages
POST   /v1/chat/search

# Advanced endpoints
POST   /v1/search
POST   /v1/extract
POST   /v1/answer
```

## Best Practices

1. **Memory Hygiene**: Regularly consolidate and deduplicate memories
2. **Knowledge Organization**: Use hierarchical KBs for better organization
3. **Embedding Caching**: Cache embeddings for frequently accessed content
4. **Batch Operations**: Use batch APIs for better performance
5. **Security**: Always use API keys in production
6. **Monitoring**: Track memory usage and query performance
7. **Backup**: Regular backups of vector database
8. **Privacy**: Implement PII removal for sensitive data

## Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce embedding batch size or use smaller models
2. **Slow Searches**: Create indexes on vector columns
3. **API Timeouts**: Increase client timeout or use async operations
4. **Embedding Errors**: Check model compatibility and dimensions
5. **Database Corruption**: Restore from backup and check disk space

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Client with debug mode
client = MemoryClient(
    base_url="http://localhost:4000",
    api_key="your-api-key",
    debug=True
)

# Service with debug mode
HANZO_LOG_LEVEL=DEBUG hanzo-memory
```

For more help, see our [GitHub issues](https://github.com/hanzoai/memory/issues).