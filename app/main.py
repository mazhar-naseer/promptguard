import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.logging_config import setup_logging, logger, request_id_ctx
from app.core.rate_limit import limiter
from app.db.database import Base, engine, SessionLocal
from app.db.seed import run_all_seeds
from app.services.rule_engine import rule_engine
from app.api import routes_analyze, routes_admin, routes_auth, routes_pages

setup_logging()

app = FastAPI(title="PromptGuard", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(routes_pages.router)
app.include_router(routes_auth.router)
app.include_router(routes_analyze.router)
app.include_router(routes_admin.router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    rid = str(uuid.uuid4())
    request_id_ctx.set(rid)
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    response.headers["X-Request-ID"] = rid
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_all_seeds(db)
        rule_engine.reload(db)
    finally:
        db.close()
    logger.info(f"PromptGuard started in {settings.app_env} mode")
