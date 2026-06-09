# ⚠️ MUST be first: fix Intel MKL / torch C-extension crash on Windows
import os as _os
_os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_os.environ.setdefault("OMP_NUM_THREADS", "1")
_os.environ.setdefault("MKL_THREADING_LAYER", "GNU")
_os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import sys
import uuid
from pathlib import Path

_project_root = Path(__file__).parent.parent.resolve()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import uvicorn
from sqlalchemy import create_engine, text
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import get_settings
from app.db.database import engine, Base
from app.exceptions import AppException
from app.api import documents, qa, knowledge_bases
from app.api import auth, model_configs  # noqa: auth modules
from app.models import document  # noqa: ensure models are loaded
from app.models import user, model_config  # noqa: auth models
from app.services.progress_ws import progress_tracker
from app.utils.log_util import setup_logging, get_logger, set_request_id, clear_request_id

settings = get_settings()

# ── Initialise logging (BEFORE anything else) ──
setup_logging(
    level=settings.log_level,
    log_dir=settings.log_dir,
    app_name=settings.app_name,
)
logger = get_logger(__name__)


STATIC_DIR = Path(__file__).parent / "static"


def create_database_if_not_exists():
    engine_no_db = create_engine(settings.database_url_no_db)
    with engine_no_db.connect() as conn:
        conn.execute(text("COMMIT"))
        result = conn.execute(
            text(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = :db_name"
            ),
            {"db_name": settings.mysql_database},
        )
        if not result.fetchone():
            conn.execute(
                text(
                    f"CREATE DATABASE `{settings.mysql_database}` "
                    "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            logger.info("数据库 '%s' 自动创建成功", settings.mysql_database)
        else:
            logger.info("数据库 '%s' 已存在", settings.mysql_database)
    engine_no_db.dispose()


def create_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表初始化完成")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="智能文档问答助手 —— 上传文档，与文档进行智能对话",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request tracing middleware (inject X-Request-ID) ──
    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        set_request_id(req_id)
        logger.info("[%s] %s %s", req_id, request.method, request.url.path)
        response = await call_next(request)
        clear_request_id()
        return response

    # ── No-cache headers on static files via raw ASGI ──
    from starlette.types import ASGIApp, Scope, Receive, Send

    class NoCacheStaticMiddleware:
        def __init__(self, app: ASGIApp):
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send):
            path = scope["path"]
            if scope["type"] == "http" and (path.startswith("/static") or path.startswith("/assets")):
                async def send_wrapper(message):
                    if message["type"] == "http.response.start":
                        headers = [(k, v) for k, v in message.get("headers", []) if k != b"cache-control"]
                        headers.append((b"cache-control", b"no-cache, no-store, must-revalidate"))
                        message["headers"] = headers
                    await send(message)
                await self.app(scope, receive, send_wrapper)
            else:
                await self.app(scope, receive, send)

    app.add_middleware(NoCacheStaticMiddleware)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(documents.router)
    app.include_router(qa.router)
    app.include_router(knowledge_bases.router)
    app.include_router(auth.router)
    app.include_router(model_configs.router)

    # ── Serve new Vue frontend build ──
    _VUE_DIST = _project_root / "frontend" / "dist"
    if _VUE_DIST.is_dir():
        logger.info("Serving Vue frontend from %s", _VUE_DIST)
        app.mount("/assets", StaticFiles(directory=str(_VUE_DIST / "assets")), name="vue_assets")

    # ── Global exception handlers ───────────────────────

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "detail": exc.detail,
                "type": type(exc).__name__,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"error": "参数错误", "detail": str(exc)},
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        return JSONResponse(
            status_code=500,
            content={"error": "服务运行时错误", "detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def catchall_handler(request: Request, exc: Exception):
        # Don't catch AppException subclasses again
        if isinstance(exc, AppException):
            raise exc
        return JSONResponse(
            status_code=500,
            content={
                "error": "服务器内部错误",
                "detail": "发生未预期的错误，请检查日志",
                "type": type(exc).__name__,
            },
        )

    @app.websocket("/ws/progress/{doc_id}")
    async def ws_progress(doc_id: str, websocket: WebSocket):
        """WebSocket 端点 —— 客户端连接后实时接收文档处理进度。"""
        await websocket.accept()
        await progress_tracker.subscribe(doc_id, websocket)
        try:
            while True:
                await websocket.receive_text()  # keep-alive
        except Exception:
            pass
        finally:
            await progress_tracker.unsubscribe(doc_id, websocket)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/debug/vector-store/{kb_id}")
    async def debug_vector_store(kb_id: str):
        from pathlib import Path
        from app.core.config import get_settings
        s = get_settings()
        store_dir = Path(s.vector_store_path) / f"kb_{kb_id}"
        idx = store_dir / "index.faiss"
        return {
            "vector_store_path": repr(s.vector_store_path),
            "store_dir": str(store_dir),
            "store_dir_exists": store_dir.exists(),
            "idx_exists": idx.exists(),
            "store_contents": [str(p.name) for p in store_dir.iterdir()] if store_dir.exists() else [],
        }

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """SPA fallback: serve Vue app index.html for any non-API route."""
        if path.startswith(("api/", "ws/", "static/", "assets/", "debug/", "health", "docs", "redoc", "openapi")):
            return JSONResponse(status_code=404, content={"error": "Not found"})

        _vue_index = _project_root / "frontend" / "dist" / "index.html"
        if _vue_index.is_file():
            return FileResponse(
                str(_vue_index),
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

        # Fallback to old static frontend
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()

# ── Load active model config from database on startup ──
@app.on_event("startup")
async def _load_active_model_config():
    """Read the user's active model config and apply it to the LLM client."""
    try:
        from app.db.database import SessionLocal
        from app.models.model_config import ModelConfig
        from app.services.qa_service import set_active_model_config
        from app.api.model_configs import _decrypt
        _db = SessionLocal()
        try:
            _active = _db.query(ModelConfig).filter(ModelConfig.is_active == True).first()
            if _active:
                _key = _decrypt(_active.api_key_encrypted)
                set_active_model_config(_active.base_url, _key, _active.model_name)
                print(f"[startup] Loaded active model config: {_active.model_name}")
            else:
                print("[startup] No active model config found in database")
        finally:
            _db.close()
    except Exception as _e:
        print(f"[startup] Failed to load active model config: {_e}")


if __name__ == "__main__":
    create_database_if_not_exists()
    create_tables()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        reload_dirs=[str(_project_root / "app")] if settings.app_debug else [],
    )
