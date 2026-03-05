 # Backend main entry point
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import time

from app.core.config import get_settings
from app.db.database import Base, engine
from app.api.routes import ipos, files, ml, auth
from app.api import websockets

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    print("[START] Starting NexIPO...")
    print(f"[ENV] Environment: {'Development' if settings.DEBUG else 'Production'}")
    
    # Initialize NLTK
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        print("[OK] NLTK initialized")
    except Exception as e:
        print(f"[WARN] NLTK initialization warning: {e}")
    
    # Initialize database
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        raise
    
    # Load ML model
    try:
        from app.ml_service.inference.risk_predictor import get_predictor
        predictor = get_predictor()
        if predictor.classifier.is_fitted:
            print("[OK] ML model loaded successfully")
        else:
            print("[WARN] ML model not trained yet")
    except Exception as e:
        print(f"[WARN] ML model loading warning: {e}")
    
    # Start background IPO sync
    sync_task = asyncio.create_task(_background_ipo_sync())
    print("[SYNC] Background IPO sync started")
    
    yield
    
    # Shutdown
    sync_task.cancel()
    print("[STOP] Shutting down NexIPO...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ML-Powered NexIPO Platform with Red Flag Detection",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# CORS middleware configuration
import json

# Ensure BACKEND_CORS_ORIGINS is a list (env may supply a JSON string or comma-separated)
origins = settings.BACKEND_CORS_ORIGINS
if isinstance(origins, str):
    try:
        parsed = json.loads(origins)
        if isinstance(parsed, str):
            origins = [parsed]
        elif isinstance(parsed, list):
            origins = parsed
        else:
            origins = [str(parsed)]
    except Exception:
        origins = [o.strip() for o in origins.split(',') if o.strip()]
if not isinstance(origins, list):
    origins = [origins]

if settings.DEBUG:
    # In development allow all origins to avoid CORS friction.
    # When using wildcard origins, do not allow credentials (browsers block wildcard + credentials).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header to all requests"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to NexIPO API",
        "version": settings.VERSION,
        "docs": "/api/docs",
        "health": "/health"
    }


# Include routers
app.include_router(ipos.router, prefix=settings.API_V1_PREFIX)
app.include_router(files.router, prefix=settings.API_V1_PREFIX)
app.include_router(ml.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(websockets.router, prefix=settings.API_V1_PREFIX)


async def _background_ipo_sync():
    """
    Background task that syncs IPO data on startup and every 30 minutes.
    """
    logger = logging.getLogger("ipo_sync")
    from app.db.database import SessionLocal
    from app.services.ipo_scraper import sync_ipos

    # Initial sync after a short delay to let the app fully start
    await asyncio.sleep(5)
    try:
        db = SessionLocal()
        try:
            summary = await sync_ipos(db)
            logger.info(
                f"[OK] Initial IPO sync: {summary['added']} added, "
                f"{summary['updated']} updated, {summary['total_scraped']} scraped"
            )
            print(
                f"[OK] Initial IPO sync: {summary['added']} added, "
                f"{summary['updated']} updated, {summary['total_scraped']} scraped"
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[ERROR] Initial IPO sync failed: {e}")
        print(f"[ERROR] Initial IPO sync failed: {e}")

    # Periodic sync every 30 minutes
    while True:
        try:
            await asyncio.sleep(30 * 60)  # 30 minutes
            db = SessionLocal()
            try:
                summary = await sync_ipos(db)
                logger.info(
                    f"[SYNC] Periodic IPO sync: {summary['added']} added, "
                    f"{summary['updated']} updated"
                )
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[ERROR] Periodic IPO sync failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )