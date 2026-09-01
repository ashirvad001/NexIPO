# Backend main entry point
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from collections import defaultdict
import asyncio
import logging
import time
import threading
import shutil

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.security import (
    SecurityHeadersMiddleware,
    RequestIdMiddleware,
    limiter,
    validate_secret_key,
)
from app.core.logging_config import setup_logging
from app.db.database import Base, engine
from app.api.routes import ipos, files, ml, auth, volatility, allotment, model_accuracy
from app.api import websockets

settings = get_settings()

# Initialize structured logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("nexipo")


# ── In-Memory Metrics Collector ────────────────────────────────────────────

class MetricsCollector:
    """Thread-safe in-memory metrics for API observability."""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.total_errors = 0
        self.requests_by_endpoint = defaultdict(int)
        self.errors_by_endpoint = defaultdict(int)
        self.latencies = []  # list of (path, latency_ms)
        self._max_latencies = 10000  # keep last N for percentile calculation

    def record_request(self, path: str, latency_ms: float, status_code: int):
        with self._lock:
            self.total_requests += 1
            self.requests_by_endpoint[path] += 1
            if status_code >= 400:
                self.total_errors += 1
                self.errors_by_endpoint[path] += 1
            self.latencies.append(latency_ms)
            if len(self.latencies) > self._max_latencies:
                self.latencies = self.latencies[-self._max_latencies:]

    def get_percentile(self, p: float) -> float:
        with self._lock:
            if not self.latencies:
                return 0.0
            sorted_lat = sorted(self.latencies)
            idx = int(len(sorted_lat) * p / 100)
            idx = min(idx, len(sorted_lat) - 1)
            return round(sorted_lat[idx], 2)

    def get_summary(self) -> dict:
        with self._lock:
            error_rate = (
                round(self.total_errors / max(self.total_requests, 1) * 100, 2)
            )
            return {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate_pct": error_rate,
                "latency_p50_ms": self.get_percentile(50),
                "latency_p95_ms": self.get_percentile(95),
                "latency_p99_ms": self.get_percentile(99),
                "top_endpoints": dict(
                    sorted(
                        self.requests_by_endpoint.items(),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:10]
                ),
            }


metrics = MetricsCollector()


# ── Application Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    logger.info("Starting NexIPO...", extra={"path": "/startup"})
    logger.info(
        f"Environment: {'Development' if settings.DEBUG else 'Production'}",
        extra={"path": "/startup"},
    )

    # Validate secret key
    validate_secret_key(settings.SECRET_KEY, settings.DEBUG)
    
    # Initialize NLTK
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        logger.info("NLTK initialized")
    except Exception as e:
        logger.warning(f"NLTK initialization warning: {e}")
    
    # Initialize database
    try:
        # We no longer use Base.metadata.create_all(bind=engine)
        # Database schema is now managed by Alembic. 
        # Run `alembic upgrade head` before starting the application.
        logger.info("Database schema should be initialized via Alembic.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Load ML model
    try:
        from app.ml_service.inference.risk_predictor import get_predictor
        predictor = get_predictor()
        if predictor.classifier.is_fitted:
            logger.info("ML model loaded successfully")
        else:
            logger.warning("ML model not trained yet")
    except Exception as e:
        logger.warning(f"ML model loading warning: {e}")
    
    # Start background IPO sync (DISABLED for local SQLite to prevent locks)
    # sync_task = asyncio.create_task(_background_ipo_sync())
    # logger.info("Background IPO sync started")
    
    yield
    
    # Shutdown
    # sync_task.cancel()
    logger.info("Shutting down NexIPO...")


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


# ── Rate Limiter Registration ─────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Security Middleware ────────────────────────────────────────────────────

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)


# ── CORS middleware configuration ─────────────────────────────────────────

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


# ── Request Timing & Metrics Middleware ────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header and record metrics for all requests."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    latency_ms = round(process_time * 1000, 2)

    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    # Record metrics
    path = request.url.path
    metrics.record_request(path, latency_ms, response.status_code)

    # Structured log for requests (skip health checks and static assets)
    if not path.startswith("/health") and not path.startswith("/favicon"):
        request_id = getattr(request.state, "request_id", "N/A")
        logger.info(
            f"{request.method} {path} -> {response.status_code} ({latency_ms}ms)",
            extra={
                "request_id": request_id,
                "path": path,
                "method": request.method,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )

    return response


# ── Global Exception Handler ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# ── Health Check Endpoints ─────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Shallow health check endpoint for load balancers.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/health/deep", tags=["Health"])
async def deep_health_check():
    """
    Deep health check that validates all downstream dependencies.
    Returns per-component status with overall healthy/degraded assessment.
    """
    checks = {}

    # 1. Database check
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            checks["database"] = {"status": "ok", "type": "postgres"}
        finally:
            db.close()
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}

    # 2. Redis check
    try:
        from app.core.cache import cache
        if cache.enabled:
            cache.client.ping()
            checks["redis"] = {"status": "ok"}
        else:
            checks["redis"] = {"status": "disabled", "note": "Redis not available"}
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)}

    # 3. ML model check
    try:
        from app.ml_service.inference.risk_predictor import get_predictor
        predictor = get_predictor()
        checks["ml_model"] = {
            "status": "ok" if predictor.classifier.is_fitted else "not_trained",
            "is_fitted": predictor.classifier.is_fitted,
        }
    except Exception as e:
        checks["ml_model"] = {"status": "error", "error": str(e)}

    # 4. Disk space check
    try:
        usage = shutil.disk_usage("/")
        free_gb = round(usage.free / (1024**3), 2)
        checks["disk_space"] = {
            "status": "ok" if free_gb > 1.0 else "warning",
            "free_gb": free_gb,
        }
    except Exception as e:
        checks["disk_space"] = {"status": "error", "error": str(e)}

    # Overall status
    statuses = [v.get("status") for v in checks.values()]
    if all(s in ("ok", "disabled", "not_trained") for s in statuses):
        overall = "healthy"
    elif any(s == "error" for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    return {"status": overall, "checks": checks}


# ── Metrics Endpoint ───────────────────────────────────────────────────────

@app.get("/metrics", tags=["Observability"])
async def get_metrics():
    """
    API metrics endpoint exposing request counts, error rates, and latency percentiles.
    """
    return metrics.get_summary()


# ── Root Endpoint ──────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to NexIPO API",
        "version": settings.VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "health_deep": "/health/deep",
        "metrics": "/metrics",
    }


# ── Include Routers ───────────────────────────────────────────────────────

logger.info(f"API_V1_PREFIX: {settings.API_V1_PREFIX}")
app.include_router(ipos.router, prefix=settings.API_V1_PREFIX)
app.include_router(files.router, prefix=settings.API_V1_PREFIX)
app.include_router(ml.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(websockets.router, prefix=settings.API_V1_PREFIX)
app.include_router(volatility.router, prefix=settings.API_V1_PREFIX)
app.include_router(allotment.router, prefix=settings.API_V1_PREFIX)
app.include_router(model_accuracy.router, prefix=settings.API_V1_PREFIX)
logger.info("All routers included")

@app.get("/inspect_routes")
def inspect_routes():
    return [{"path": route.path, "name": route.name} for route in app.routes]



async def _background_ipo_sync():
    """
    Background task that syncs IPO data on startup and every 30 minutes.
    """
    from app.db.database import SessionLocal
    from app.services.ipo_scraper import sync_ipos

    # Initial sync after a short delay to let the app fully start
    await asyncio.sleep(5)
    try:
        db = SessionLocal()
        try:
            summary = await sync_ipos(db)
            logger.info(
                f"Initial IPO sync: {summary['added']} added, "
                f"{summary['updated']} updated, {summary['total_scraped']} scraped"
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Initial IPO sync failed: {e}")

    # Periodic sync every 30 minutes
    while True:
        try:
            await asyncio.sleep(30 * 60)  # 30 minutes
            db = SessionLocal()
            try:
                summary = await sync_ipos(db)
                logger.info(
                    f"Periodic IPO sync: {summary['added']} added, "
                    f"{summary['updated']} updated"
                )
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Periodic IPO sync failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )