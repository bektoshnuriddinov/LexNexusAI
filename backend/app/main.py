from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import logging

from app.config import get_settings
from app.routers import auth, threads, chat, documents, admin
from app.routers import settings as settings_router

# Configure logging - write to both console and file
import os
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "rag_debug.log"

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),  # Write to file
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"📝 Logging to file: {log_file}")

settings = get_settings()

app = FastAPI(
    title="RAG Masterclass API",
    description="Backend API for the RAG Masterclass application",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Starting RAG Masterclass API")

    # Import langsmith module to trigger initialization and test trace
    try:
        from app.services import langsmith
        logger.info("✅ LangSmith module loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load LangSmith: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return proper JSON response with CORS headers."""
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers
app.include_router(auth.router)
app.include_router(threads.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(settings_router.router)
app.include_router(admin.router)
