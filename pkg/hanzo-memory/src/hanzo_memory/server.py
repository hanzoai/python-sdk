"""FastAPI server for Hanzo Memory Service."""

import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from structlog import get_logger

from .api.auth import get_or_verify_user_id, require_auth, security
from .config import settings
from .db import get_db_client
from .models import (
    AddKnowledgeRequest,
    AddMemoriesRequest,
    ChatMessageCreate,
    ChatSessionCreate,
    CreateKnowledgeBaseRequest,
    DeleteKnowledgeRequest,
    DeleteMemoryRequest,
    DeleteUserRequest,
    GetKnowledgeRequest,
    GetMemoriesRequest,
    MemoryListResponse,
    MemoryResponse,
    RememberRequest,
    UpdateMemoryRequest,
)
from .services import get_embedding_service, get_memory_service

logger = get_logger()

# Global service instances
db_client = None
embedding_service = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global db_client, embedding_service

    # Startup
    logger.info("Starting Hanzo Memory Service")
    settings.ensure_paths()

    # Initialize services
    db_client = get_db_client()
    embedding_service = get_embedding_service()
    if db_client:
        db_client.create_projects_table()
        db_client.create_knowledge_bases_table()

    yield

    # Shutdown
    logger.info("Shutting down Hanzo Memory Service")
    if db_client:
        db_client.close()


# Create FastAPI app
app = FastAPI(
    title="Hanzo Memory Service",
    description="AI memory and knowledge management service",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hanzo-memory",
        "version": "0.1.0",
    }


@app.post("/v1/remember")
async def remember(
    request: RememberRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> MemoryResponse:
    """
    Retrieve relevant memories and store new memory.

    This endpoint:
    1. Searches for relevant memories based on the message content
    2. Optionally filters results using LLM
    3. Stores the incoming message as a new memory
    4. Returns relevant memories
    """
    # Check auth
    request.apikey or require_auth(req, credentials)

    memory_service = get_memory_service()

    # Get or create default project for user
    project_id = f"project_{request.userid}_default"

    # Search for relevant memories
    memories = memory_service.search_memories(
        user_id=request.userid,
        query=request.messagecontent,
        project_id=project_id,
        limit=10,
        filter_with_llm=request.filterresults,
        additional_context=request.additionalcontext,
    )

    # Store the new memory
    memory_service.create_memory(
        user_id=request.userid,
        project_id=project_id,
        content=request.messagecontent,
        metadata={
            "additional_context": request.additionalcontext,
        },
        strip_pii=request.strippii,
    )

    # Format response
    relevant_memories: list[str | dict[str, str]]
    if request.includememoryid:
        relevant_memories = [
            {"content": m.content, "memoryId": m.memory_id} for m in memories
        ]
    else:
        relevant_memories = [m.content for m in memories]

    # Usage info based on returned memories
    usage_info = {
        "current": len(memories),
        "limit": settings.max_memories_per_user,
    }

    return MemoryResponse(
        user_id=request.userid,
        relevant_memories=relevant_memories,
        memory_stored=True,
        usage_info=usage_info,
    )


@app.post("/v1/memories/add")
async def add_memories(
    request: AddMemoriesRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Add explicit memories without importance analysis."""
    # Check auth
    request.apikey or require_auth(req, credentials)

    memory_service = get_memory_service()

    # Get or create default project
    project_id = f"project_{request.userid}_default"

    # Normalize memories to list
    memories_to_add = (
        [request.memoriestoadd]
        if isinstance(request.memoriestoadd, str)
        else request.memoriestoadd
    )

    # Add memories
    memory_ids = []
    for content in memories_to_add:
        memory = memory_service.create_memory(
            user_id=request.userid,
            project_id=project_id,
            content=content,
            importance=5.0,  # Default importance for explicit adds
        )
        memory_ids.append(memory.memory_id)

    return {
        "userid": request.userid,
        "added_count": len(memory_ids),
        "memory_ids": memory_ids,
        "usage_info": {
            "current": len(memory_ids),
            "limit": settings.max_memories_per_user,
        },
    }


@app.post("/v1/memories/get")
async def get_memories(
    request: GetMemoriesRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> MemoryListResponse:
    """Retrieve stored memories."""
    # Check auth
    request.apikey or require_auth(req, credentials)

    memory_service = get_memory_service()

    # Specific memory ID is required
    if not request.memoryid:
        raise HTTPException(
            status_code=400,
            detail="Memory ID is required. Use /v1/memories/search for querying memories.",
        )

    memory = memory_service.get_memory(request.userid, request.memoryid)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )
    memories = [memory]

    return MemoryListResponse(
        user_id=request.userid,
        memories=memories,
        pagination={
            "has_more": False,
            "last_id": memories[-1].memory_id if memories else None,
        },
        usage_info={
            "current": len(memories),
            "limit": settings.max_memories_per_user,
        },
    )


@app.post("/v1/memories/update")
async def update_memory_endpoint(
    request: UpdateMemoryRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Update a specific memory."""
    # Check auth
    request.apikey or require_auth(req, credentials)

    memory_service = get_memory_service()

    # Prepare update parameters
    update_params = {}
    if request.content is not None:
        update_params["content"] = request.content
    if request.importance is not None:
        update_params["importance"] = request.importance
    if request.metadata is not None:
        update_params["metadata"] = request.metadata

    # Perform the update
    updated_memory = memory_service.update_memory(
        user_id=request.userid,
        memory_id=request.memoryid,
        project_id=request.projectid,
        **update_params
    )

    if not updated_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )

    return {
        "message": "Memory updated successfully",
        "memory_id": request.memoryid,
        "userid": request.userid,
        "updated_fields": list(update_params.keys()),
    }


@app.post("/v1/memories/delete")
async def delete_memory(
    request: DeleteMemoryRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Delete a specific memory."""
    # Check auth
    request.apikey or require_auth(req, credentials)

    memory_service = get_memory_service()

    success = memory_service.delete_memory(request.userid, request.memoryid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )

    return {
        "message": "Memory deleted successfully",
        "memory_id": request.memoryid,
        "userid": request.userid,
    }


@app.post("/v1/user/delete")
async def delete_user(
    request: DeleteUserRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Delete all memories for a user."""
    # Check auth
    request.apikey or require_auth(req, credentials)

    if not request.confirmdelete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="confirmdelete must be true",
        )

    memory_service = get_memory_service()

    deleted_count = memory_service.delete_user_memories(request.userid)

    return {
        "message": "All user memories deleted",
        "userid": request.userid,
        "deleted_count": deleted_count,
    }


# Knowledge Base Management Endpoints


@app.post("/v1/kb/create")
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Create a new knowledge base."""
    try:
        # Get or verify user ID
        user_id = await get_or_verify_user_id(request.userid, credentials, req)

        # Get default project if not specified
        project_id = getattr(request, "project_id", None)
        if not project_id:
            # Create or get default project for user
            project_id = f"default-{user_id}"
            try:
                if db_client:
                    db_client.create_project(
                        project_id=project_id,
                        user_id=user_id,
                        name="Default Project",
                        description="Automatically created default project",
                    )
            except Exception:
                pass  # Project may already exist

        # Create knowledge base
        kb_id = request.kb_id or str(uuid.uuid4())
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")
        db_client.create_knowledge_base(
            kb_id=kb_id,
            user_id=user_id,
            project_id=project_id,
            name=request.name,
            description=getattr(request, "description", ""),
        )

        return {
            "kb_id": kb_id,
            "message": f"Knowledge base '{request.name}' created successfully",
        }
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/kb/list")
async def list_knowledge_bases(
    req: Request,
    userid: str = Query(...),
    project_id: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """List knowledge bases for a user."""
    try:
        # Get or verify user ID
        user_id = await get_or_verify_user_id(userid, credentials, req)

        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Query knowledge bases from the database
        kbs = db_client.get_knowledge_bases(project_id or user_id)

        return {
            "userid": user_id,
            "knowledge_bases": kbs,
            "total": len(kbs),
        }
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/kb/facts/add")
async def add_facts(
    request: AddKnowledgeRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Add facts to a knowledge base."""
    try:
        # Get or verify user ID
        await get_or_verify_user_id(request.userid, credentials, req)

        # Process each fact
        added_facts = []
        for fact_data in request.facts:
            # Generate embedding for fact content
            content = fact_data.get("content", "")
            if not embedding_service:
                raise HTTPException(
                    status_code=503, detail="Embedding service not initialized"
                )
            embedding = embedding_service.embed_text(content)[0]

            # Add fact to database
            fact_id = fact_data.get("fact_id") or str(uuid.uuid4())
            if not db_client:
                raise HTTPException(status_code=503, detail="Database not initialized")
            db_client.add_fact(
                fact_id=fact_id,
                kb_id=request.kb_id,
                content=content,
                embedding=embedding,
                parent_id=fact_data.get("parent_id"),
                metadata=fact_data.get("metadata", {}),
            )

            added_facts.append(
                {
                    "fact_id": fact_id,
                    "content": content,
                }
            )

        return {
            "kb_id": request.kb_id,
            "facts_added": len(added_facts),
            "facts": added_facts,
        }
    except Exception as e:
        logger.error(f"Error adding facts: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/kb/facts/get")
async def get_facts(
    request: GetKnowledgeRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Get facts from a knowledge base."""
    try:
        # Get or verify user ID
        await get_or_verify_user_id(request.userid, credentials, req)

        # Search facts if query provided
        if request.query:
            # Generate query embedding
            if not embedding_service:
                raise HTTPException(
                    status_code=503, detail="Embedding service not initialized"
                )
            query_embedding = embedding_service.embed_text(request.query)[0]

            # Search facts
            if not db_client:
                raise HTTPException(status_code=503, detail="Database not initialized")
            results_df = db_client.search_facts(
                kb_id=request.kb_id,
                query_embedding=query_embedding,
                limit=request.limit,
                parent_id=request.fact_id if request.subtree else None,
            )

            # Convert results
            facts = []
            if not results_df.is_empty():
                for row in results_df.to_dicts():
                    facts.append(
                        {
                            "fact_id": row["fact_id"],
                            "content": row["content"],
                            "parent_id": row.get("parent_id"),
                            "metadata": json.loads(row.get("metadata", "{}")),
                            "similarity_score": row.get("_similarity", 0.0),
                        }
                    )

            return {
                "kb_id": request.kb_id,
                "facts": facts,
                "total": len(facts),
            }
        else:
            # Query is required for searching facts
            raise HTTPException(
                status_code=400,
                detail="Query parameter is required to search facts. Provide a search query.",
            )
    except Exception as e:
        logger.error(f"Error getting facts: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/kb/facts/delete")
async def delete_fact_endpoint(
    request: DeleteKnowledgeRequest,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Delete a fact from a knowledge base."""
    try:
        # Get or verify user ID
        await get_or_verify_user_id(request.userid, credentials, req)

        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Delete fact from database
        deleted = db_client.delete_fact(request.fact_id, request.kb_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Fact '{request.fact_id}' not found in knowledge base '{request.kb_id}'",
            )

        return {
            "kb_id": request.kb_id,
            "fact_id": request.fact_id,
            "deleted": True,
            "cascade": request.cascade,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting fact: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Chat Management Endpoints


@app.post("/v1/chat/sessions/create")
async def create_chat_session(
    request: ChatSessionCreate,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Create a new chat session."""
    try:
        # Get or verify user ID
        user_id = await get_or_verify_user_id(request.userid, credentials, req)

        # Create session ID
        session_id = request.session_id or str(uuid.uuid4())

        # Get or create default project
        project_id = request.project_id or f"default-{user_id}"

        # Ensure user's chat table exists
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")
        db_client.create_chats_table(user_id)

        return {
            "session_id": session_id,
            "userid": user_id,
            "project_id": project_id,
            "created": True,
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/chat/messages/add")
async def add_chat_message(
    request: ChatMessageCreate,
    req: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Add a message to a chat session."""
    try:
        # Get or verify user ID
        user_id = await get_or_verify_user_id(request.userid, credentials, req)

        # Generate embedding for message content
        if not embedding_service:
            raise HTTPException(
                status_code=503, detail="Embedding service not initialized"
            )
        embedding = embedding_service.embed_text(request.content)[0]

        # Check for duplicate messages
        # Search for similar messages in the same session
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")
        search_results = db_client.search_chats(
            user_id=user_id,
            query_embedding=embedding,
            session_id=request.session_id,
            limit=5,
        )

        # Check if this is a duplicate
        is_duplicate = False
        if not search_results.is_empty():
            for row in search_results.to_dicts():
                if (
                    row["content"] == request.content
                    and row["role"] == request.role
                    and row.get("_similarity", 0) > 0.99
                ):
                    is_duplicate = True
                    chat_id = row["chat_id"]
                    break

        if not is_duplicate:
            # Add new message
            chat_id = str(uuid.uuid4())
            if not db_client:
                raise HTTPException(status_code=503, detail="Database not initialized")
            db_client.add_chat_message(
                chat_id=chat_id,
                user_id=user_id,
                project_id=request.project_id or f"default-{user_id}",
                session_id=request.session_id,
                role=request.role,
                content=request.content,
                embedding=embedding,
                metadata=request.metadata or {},
            )

        return {
            "chat_id": chat_id,
            "session_id": request.session_id,
            "duplicate": is_duplicate,
        }
    except Exception as e:
        logger.error(f"Error adding chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    req: Request,
    userid: str = Query(...),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Get messages for a chat session."""
    try:
        # Get or verify user ID
        user_id = await get_or_verify_user_id(userid, credentials, req)

        # Get chat history
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")
        history_df = db_client.get_chat_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
        )

        # Convert to messages
        messages = []
        if not history_df.is_empty():
            # Sort by created_at timestamp
            sorted_df = history_df.sort("created_at")

            for row in sorted_df.to_dicts():
                messages.append(
                    {
                        "chat_id": row["chat_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "metadata": json.loads(row.get("metadata", "{}")),
                        "created_at": row["created_at"],
                    }
                )

        return {
            "session_id": session_id,
            "messages": messages,
            "total": len(messages),
        }
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/chat/search")
async def search_chat_messages(
    req: Request,
    query: str = Query(...),
    userid: str = Query(...),
    project_id: str | None = Query(None),
    session_id: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Search across chat messages."""
    try:
        # Get or verify user ID
        user_id = await get_or_verify_user_id(userid, credentials, req)

        # Generate query embedding
        if not embedding_service:
            raise HTTPException(
                status_code=503, detail="Embedding service not initialized"
            )
        query_embedding = embedding_service.embed_text(query)[0]

        # Search chats
        if not db_client:
            raise HTTPException(status_code=503, detail="Database not initialized")
        results_df = db_client.search_chats(
            user_id=user_id,
            query_embedding=query_embedding,
            project_id=project_id,
            session_id=session_id,
            limit=limit,
        )

        # Convert results
        messages = []
        if not results_df.is_empty():
            for row in results_df.to_dicts():
                messages.append(
                    {
                        "chat_id": row["chat_id"],
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "similarity_score": row.get("_similarity", 0.0),
                        "created_at": row["created_at"],
                    }
                )

        return {
            "query": query,
            "messages": messages,
            "total": len(messages),
        }
    except Exception as e:
        logger.error(f"Error searching chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def run() -> None:
    """Run the server."""
    import uvicorn

    uvicorn.run(
        "hanzo_memory.server:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
