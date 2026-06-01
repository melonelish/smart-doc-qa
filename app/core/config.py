from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "SmartDocQA"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com"
    openai_model: str = "deepseek-v4-pro"
    openai_embedding_model: str = "local"
    local_embedding_model: str = "BAAI/bge-small-zh-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"
    openai_timeout: int = 60
    openai_proxy: str = ""
    conversation_ttl_seconds: int = 3600

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "smart_doc_qa"

    redis_host: str = "localhost"
    redis_port: int = 6379

    vector_store_path: str = str(_PROJECT_ROOT / "data" / "vector_store")
    hf_endpoint: str = ""
    allowed_extensions: str = ".pdf,.txt,.md,.docx,.csv"
    max_file_size_mb: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 200

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def database_url_no_db(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}"
            f"?charset=utf8mb4"
        )

    @property
    def allowed_file_extensions(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
