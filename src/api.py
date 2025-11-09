"""FastAPI REST API for Discord RAG Bot Web Interface.

This module provides a REST API to interact with the Discord RAG Bot
through a web interface.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import FilterLevel, get_settings
from src.logging_config import get_logger
from src.models import QueryRequest
from src.services import (
    ConfigService,
    LLMService,
    SupabaseService,
    VectorStoreService,
)

# Initialize FastAPI
app = FastAPI(
    title="Discord RAG Bot API",
    description="REST API for Discord RAG Bot with web interface",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
logger = get_logger(settings)

supabase_service = SupabaseService(settings=settings, logger=logger)
vectorstore_service = VectorStoreService(
    settings=settings,
    logger=logger,
    supabase_service=supabase_service,
)
llm_service = LLMService(
    settings=settings,
    logger=logger,
    vectorstore_service=vectorstore_service,
)
config_service = ConfigService(settings=settings, logger=logger)


# ============================================================================
# Request/Response Models
# ============================================================================


class QueryRequestModel(BaseModel):
    """Query request model."""

    question: str = Field(..., min_length=1, max_length=1000)
    filter_level: str = Field(default="moderado")


class QueryResponseModel(BaseModel):
    """Query response model."""

    answer: str
    sources: list[str]
    duration: float
    timestamp: str


class StatusResponseModel(BaseModel):
    """Status response model."""

    bot_online: bool
    rag_loaded: bool
    llm_model: str
    cache_enabled: bool
    cache_stats: Optional[dict] = None
    documents_count: int
    timestamp: str


# ============================================================================
# API Endpoints
# ============================================================================


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("Starting API server", action="STARTUP")

    try:
        await vectorstore_service.load()
        logger.info("Vector store loaded", action="SUCCESS")
    except Exception as e:
        logger.error("Failed to load vector store", action="ERROR", exc_info=True)


@app.get("/")
async def root() -> FileResponse:
    """Serve the web interface."""
    return FileResponse("web/index.html")


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/status", response_model=StatusResponseModel)
async def get_status() -> StatusResponseModel:
    """Get bot status and statistics."""
    try:
        # Get cache stats if enabled
        cache_stats = None
        if settings.cache_enabled:
            from src.cache import get_cache

            cache = get_cache()
            cache_stats = cache.stats

        # Count documents (if possible)
        documents_count = 0
        try:
            # This is a placeholder - implement actual document counting
            documents_count = 0
        except Exception:
            pass

        return StatusResponseModel(
            bot_online=True,
            rag_loaded=vectorstore_service.is_loaded,
            llm_model=settings.openrouter_model,
            cache_enabled=settings.cache_enabled,
            cache_stats=cache_stats,
            documents_count=documents_count,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Error getting status", action="ERROR", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponseModel)
async def process_query(request: QueryRequestModel) -> QueryResponseModel:
    """Process a query and return response."""
    start_time = datetime.now()

    try:
        # Validate filter level
        try:
            filter_level = FilterLevel(request.filter_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter level: {request.filter_level}",
            )

        # Create query request
        query_request = QueryRequest(
            question=request.question,
            guild_id=None,
            user_id="web_interface",
            query_type="Web API",
        )

        # Process query
        result = await llm_service.process_query(query_request, filter_level)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Get source names
        source_names = result.get_source_names(max_sources=5)

        logger.info(
            "Query processed",
            action="SUCCESS",
            duration=duration,
            sources_count=len(source_names),
        )

        return QueryResponseModel(
            answer=result.answer,
            sources=source_names,
            duration=duration,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Error processing query", action="ERROR", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Static Files
# ============================================================================

# Mount static files with existence checks
css_dir = Path("web/css")
js_dir = Path("web/js")
assets_dir = Path("web/assets")

if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
else:
    logger.warning(f"CSS directory not found: {css_dir}")

if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
else:
    logger.warning(f"JS directory not found: {js_dir}")

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
else:
    logger.warning(f"Assets directory not found: {assets_dir}")


# ============================================================================
# Main Entry Point
# ============================================================================


def run_api_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the API server.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn

    logger.info(
        "Starting API server",
        action="STARTUP",
        host=host,
        port=port,
    )

    uvicorn.run(
        "src.api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    run_api_server()
