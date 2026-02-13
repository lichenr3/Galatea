"""
Database Connection Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供 async SQLAlchemy engine 和 session factory。
在 init_dependencies() 中创建，lifespan shutdown 时关闭。
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from app.core.logger import get_logger

logger = get_logger(__name__)


class Database:
    """Async database connection manager"""

    def __init__(self, url: str, echo: bool = False):
        self.engine: AsyncEngine = create_async_engine(url, echo=echo)
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine, expire_on_commit=False
        )
        logger.info("🗄️  Database engine created")

    async def init_db(self) -> None:
        """
        初始化数据库：启用 pgvector 扩展 + 创建所有表。
        仅用于开发环境，生产环境请使用 Alembic 迁移。
        """
        from app.models import Base  # noqa: 确保所有 model 被导入

        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables initialized (pgvector enabled)")

    async def close(self) -> None:
        """关闭数据库连接池"""
        await self.engine.dispose()
        logger.info("🗄️  Database engine disposed")
