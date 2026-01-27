import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    # Base settings
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Galatea Server")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    # Directories
    CHARACTERS_DIR: Path = BASE_DIR / "app" / "characters"
    PROMPTS_DIR: Path = BASE_DIR / "app" / "prompts"
    LOGS_DIR: Path = BASE_DIR / "logs"
    DATA_DIR: Path = BASE_DIR / "data"

    # TTS Service settings
    TTS_API_HOST: str = os.getenv("TTS_API_HOST", "http://127.0.0.1")
    TTS_API_PORT: int = int(os.getenv("TTS_API_PORT", 9880))
    TTS_ROUTE: str = os.getenv("TTS_ROUTE", "../GPT-SoVITS-v2pro-20250604-nvidia50")

    # LLM settings
    LLM_API_KEY: str = os.getenv("LLM_API_KEY")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL")
    LLM_MODEL: str = os.getenv("LLM_MODEL")

    # Unity settings
    UNITY_EXE_PATH: str = os.getenv("UNITY_EXE_PATH", "../galatea_unity/Build/galatea.exe")

    # Memory settings (向量数据库)
    MEMORY_BACKEND: str = os.getenv("MEMORY_BACKEND", "chroma")  # chroma | qdrant | none
    CHROMA_PERSIST_DIR: Path = Path(os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma")))

    # LangGraph Checkpoint settings (会话状态持久化)
    CHECKPOINT_BACKEND: str = os.getenv("CHECKPOINT_BACKEND", "postgres")  # memory | sqlite | postgres
    CHECKPOINT_DB_PATH: Path = Path(os.getenv("CHECKPOINT_DB_PATH", str(BASE_DIR / "data" / "checkpoints" / "langgraph.db")))

    # Database settings (PostgreSQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/galatea"
    )
    # 同步版本的 URL（用于 Alembic 迁移）
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/galatea"
    )

    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

settings = Settings()
