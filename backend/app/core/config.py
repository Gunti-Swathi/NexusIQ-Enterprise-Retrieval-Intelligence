from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "local"
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_generation_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "NexusIQ"

    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    chroma_path: Path = Path("data/chroma")
    sqlite_path: Path = Path("data/app.sqlite")
    embedding_cache_path: Path = Path("data/embedding_cache.sqlite")

    max_upload_files: int = 15
    chunk_size: int = 1200
    chunk_overlap: int = 180
    semantic_top_k: int = 10
    keyword_top_k: int = 10
    hybrid_top_k: int = 8
    recommendation_top_k: int = 5
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    value = Settings()
    value.ensure_directories()
    return value


settings = get_settings()
