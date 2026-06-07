from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import time
import os

from core.config import settings
from db.database import init_db
from models.db import CandidateRecord
from api import system, candidates, chat, auth
from services.embedding import get_embedding_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    # Initialize the database
    await init_db()
    # Skip preloading embedding model to avoid Render port binding timeouts
    # Model will be loaded on-demand during the first request
    print("Database initialized, skipping model preload for fast boot")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions to prevent 500 stack traces leaking."""
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error.", "code": "INTERNAL_ERROR"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTP exceptions into the standard envelope."""
    detail = exc.detail
    if isinstance(detail, dict) and "status" in detail:
        content = detail
    else:
        content = {"status": "error", "message": str(detail), "code": "HTTP_ERROR"}
    return JSONResponse(status_code=exc.status_code, content=content)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format validation errors into the standard envelope."""
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid request parameters.", "code": "VALIDATION_ERROR"}
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update with deployment URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to inject processing time in milliseconds into headers and responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time_ms, 2))
    return response

# Get the absolute path to the frontend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML file."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(system.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1/candidates")
app.include_router(auth.router)
