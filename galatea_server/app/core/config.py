from pathlib import Path
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base settings
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = "Galatea Server"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # Directories（不从 .env 读取，由 BASE_DIR 派生）
    CHARACTERS_DIR: Path = BASE_DIR / "app" / "characters"
    PROMPTS_DIR: Path = BASE_DIR / "app" / "prompts"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # TTS Service settings
    TTS_API_HOST: str = "http://127.0.0.1"
    TTS_API_PORT: int = 9880
    TTS_ROUTE: str = "../GPT-SoVITS-v2pro-20250604-nvidia50"

    # LLM settings
    LLM_API_KEY: str = Field(default="", description="LLM API Key")
    LLM_BASE_URL: str = Field(default="", description="LLM Base URL")
    LLM_MODEL: str = Field(default="", description="LLM Model Name")

    # Unity settings
    UNITY_EXE_PATH: str = "../galatea_unity/Build/galatea.exe"

    # Database (PostgreSQL + pgvector)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "galatea"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """asyncpg 连接字符串（用于 SQLAlchemy async）"""
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def DATABASE_URL_PSYCOPG(self) -> str:
        """psycopg 连接字符串（用于 LangGraph Checkpointer / langchain-postgres）"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
