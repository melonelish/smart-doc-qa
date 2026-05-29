import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.resolve()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import uvicorn
from sqlalchemy import create_engine, text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.db.database import engine, SessionLocal, Base
from app.api import documents, qa

settings = get_settings()

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
            print(f"[OK] 数据库 '{settings.mysql_database}' 自动创建成功")
        else:
            print(f"[OK] 数据库 '{settings.mysql_database}' 已存在")
    engine_no_db.dispose()


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表初始化完成")


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

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(documents.router)
    app.include_router(qa.router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/")
    async def serve_frontend():
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    create_database_if_not_exists()
    create_tables()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
