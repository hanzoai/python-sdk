"""Hanzo UI Registry Server — FastAPI service serving cached component data.

Deploy at ui.hanzo.ai. Pre-fetches all components from hanzoai/ui on GitHub,
serves instant cached responses. Refreshes every 15 minutes in background.

Run:
    python -m hanzo_tools.ui.registry
    # or
    uvicorn hanzo_tools.ui.registry.server:app --port 8787
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse

from .cache import RegistryCache

logger = logging.getLogger(__name__)

# Configuration
FRAMEWORKS = os.environ.get("REGISTRY_FRAMEWORKS", "hanzo").split(",")
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "900"))

# Global cache instance
_cache: RegistryCache | None = None


def get_cache() -> RegistryCache:
    assert _cache is not None, "Cache not initialized"
    return _cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cache
    _cache = RegistryCache(frameworks=FRAMEWORKS, refresh_interval=REFRESH_INTERVAL)

    logger.info("Starting initial cache refresh...")
    await _cache.refresh()
    logger.info("Initial refresh complete, starting background refresh loop")
    _cache.start()

    yield

    _cache.stop()
    logger.info("Registry server shutting down")


app = FastAPI(
    title="Hanzo UI Registry",
    description="Cached component registry for Hanzo UI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --- API Endpoints ---


@app.get("/api/health")
async def health():
    cache = get_cache()
    return cache.health


@app.get("/api/components")
async def list_components(framework: str = Query(default="hanzo")):
    cache = get_cache()
    components = cache.get_components(framework)
    return {"framework": framework, "total": len(components), "components": components}


@app.get("/api/components/{name}")
async def get_component(name: str, framework: str = Query(default="hanzo")):
    cache = get_cache()
    comp = cache.get_component(name, framework)
    if comp is None:
        raise HTTPException(404, detail={"error": "Component not found", "name": name})
    return comp


@app.get("/api/components/{name}/source")
async def get_component_source(name: str, framework: str = Query(default="hanzo")):
    cache = get_cache()
    source = cache.get_component_source(name, framework)
    if source is None:
        raise HTTPException(404, detail={"error": "Component not found", "name": name})
    return {"name": name, "source": source}


@app.get("/api/components/{name}/demo")
async def get_component_demo(name: str, framework: str = Query(default="hanzo")):
    cache = get_cache()
    demo = cache.get_component_demo(name, framework)
    if demo is None:
        raise HTTPException(
            404, detail={"error": "Demo not found", "name": name}
        )
    return {"name": name, "demo": demo}


@app.get("/api/components/{name}/metadata")
async def get_component_metadata(name: str, framework: str = Query(default="hanzo")):
    cache = get_cache()
    metadata = cache.get_component_metadata(name, framework)
    if metadata is None:
        raise HTTPException(404, detail={"error": "Component not found", "name": name})
    return {"name": name, "metadata": metadata}


@app.get("/api/blocks")
async def list_blocks(framework: str = Query(default="hanzo")):
    cache = get_cache()
    blocks = cache.get_blocks(framework)
    return {"framework": framework, "total": len(blocks), "blocks": blocks}


@app.get("/api/blocks/{name}")
async def get_block(name: str, framework: str = Query(default="hanzo")):
    cache = get_cache()
    block = cache.get_block(name, framework)
    if block is None:
        raise HTTPException(404, detail={"error": "Block not found", "name": name})
    return block


@app.get("/api/search")
async def search_components(
    q: str = Query(..., min_length=1), framework: str = Query(default="hanzo")
):
    cache = get_cache()
    results = cache.search(q, framework)
    return {"query": q, "framework": framework, "results": results}


@app.get("/api/structure")
async def get_structure(
    path: str = Query(default=""), framework: str = Query(default="hanzo")
):
    cache = get_cache()
    structure = cache.get_structure(path, framework)
    if structure is None:
        raise HTTPException(
            404, detail={"error": "Path not found in cache", "path": path}
        )
    return structure


@app.get("/registry/index.json")
async def registry_index(framework: str = Query(default="hanzo")):
    """Full registry manifest — all components with source in one payload."""
    cache = get_cache()
    index = cache.build_index(framework)
    return JSONResponse(content=index)


@app.get("/")
async def root():
    return {
        "service": "Hanzo UI Registry",
        "docs": "/docs",
        "health": "/api/health",
        "components": "/api/components",
        "index": "/registry/index.json",
    }
