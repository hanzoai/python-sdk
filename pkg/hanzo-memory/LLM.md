# Hanzo Memory Service - LLM Context

## Project Overview

Hanzo Memory Service is a high-performance AI memory and knowledge management system built with:
- **InfinityDB**: Embedded vector database for fast similarity search
- **FastEmbed**: Local embedding generation (no API calls)
- **LiteLLM**: Universal LLM interface supporting 100+ providers
- **FastAPI**: Modern async web framework

## Key Architecture Decisions

### 1. InfinityDB over PostgreSQL/pgvector
- Embedded database (no separate server process)
- Optimized for vector similarity search
- Lightweight deployment with file-based storage
- Direct support for multimodal embeddings

### 2. FastEmbed for Local Embeddings
- No dependency on external embedding APIs
- Fast local inference using ONNX runtime
- Default model: BAAI/bge-small-en-v1.5 (384 dimensions)
- Supports custom models via model registry

### 3. LiteLLM for LLM Flexibility
- Single interface for all LLM providers
- Supports OpenAI, Anthropic, Ollama, Azure, etc.
- Easy switching between cloud and local models
- Automatic retry and fallback handling

## Core Components

### Database Schema (InfinityDB Tables)

1. **Projects Database**
   - `projects` table: User projects with metadata

2. **Memories Database**
   - `memories_{user_id}` tables: Per-user memory storage
   - Columns: memory_id, content, embedding, metadata, importance

3. **Knowledge Database**
   - `knowledge_bases` table: Knowledge base definitions
   - `facts_{kb_id}` tables: Facts with parent-child relationships

4. **Chats Database**
   - `chats_{user_id}` tables: Conversation history with embeddings

### Service Layer

1. **EmbeddingService**
   - Manages FastEmbed model lifecycle
   - Batch processing for efficiency
   - Similarity computation (cosine, dot, euclidean)

2. **LLMService**
   - LiteLLM integration for all LLM operations
   - Summarization with knowledge extraction
   - JSON-mode for structured outputs
   - PII stripping capabilities

3. **MemoryService**
   - Memory CRUD operations
   - Semantic search with optional LLM filtering
   - Importance scoring and metadata management

## API Design Patterns

### Authentication
- Bearer token or x-hanzo-api-key header
- Optional apikey field in JSON body (legacy support)
- DISABLE_AUTH environment variable for development

### Request/Response Models
- Lowercase field names for compatibility (userid, messagecontent)
- Pydantic models for validation and documentation
- Consistent error responses with status codes

### Unified Search
- Query embeddings generated locally
- Vector similarity search in InfinityDB
- Optional LLM re-ranking for relevance
- Project and session-based filtering

## Testing Strategy

### Unit Tests
- Service layer testing with mocked dependencies
- Embedding generation and similarity tests
- LLM response parsing and error handling

### Integration Tests
- FastAPI TestClient for endpoint testing
- InfinityDB operations with temporary databases
- End-to-end memory storage and retrieval

### Test Fixtures
- Temporary database paths
- Sample embeddings and content
- Mock LLM responses for deterministic tests

## Performance Optimizations

1. **Local Operations**
   - Embeddings generated in-process
   - No network latency for vector operations
   - Batch processing where possible

2. **Caching Strategy**
   - Optional Redis integration
   - Embedding cache for repeated content
   - LLM response caching for common queries

3. **Async Operations**
   - FastAPI async endpoints
   - Non-blocking database operations
   - Concurrent request handling

## Deployment Considerations

### Docker Deployment
- Multi-stage build for smaller images
- Non-root user for security
- Health checks for orchestration
- Volume mounting for data persistence

### Configuration Management
- Environment variables with HANZO_ prefix
- .env file support for local development
- Sensible defaults for all settings
- Model selection via environment

### Scaling Options
1. **Vertical Scaling**: Larger instances for more memory/CPU
2. **Horizontal Scaling**: Multiple instances with shared storage
3. **Edge Deployment**: Fully offline operation with local models

## Future Enhancements

1. **MCP Server Implementation**
   - Full Model Context Protocol support
   - Tool definitions for memory/knowledge operations
   - Integration with Claude Desktop and other MCP clients

2. **Advanced Features**
   - Multi-modal embeddings (images, audio)
   - Incremental learning and memory consolidation
   - Federated memory sharing between instances
   - Advanced graph operations for knowledge bases

3. **Performance Improvements**
   - GPU acceleration for embeddings
   - Streaming responses for large result sets
   - Distributed vector indices

## Common Patterns

### Adding New Endpoints
1. Define Pydantic models in `models/`
2. Implement service logic in `services/`
3. Add FastAPI endpoint in `server.py`
4. Write tests in `tests/`

### Extending Embedding Support
1. Update FastEmbed model in config
2. Adjust embedding dimensions
3. Regenerate existing embeddings if needed

### Custom LLM Integration
1. Configure LiteLLM model string
2. Set appropriate API base/key
3. Adjust temperature and token limits
4. Test JSON mode compatibility