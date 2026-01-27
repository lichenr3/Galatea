"""
LangGraph Checkpointer 适配

提供会话状态持久化功能。
支持 Memory（开发）、SQLite 和 PostgreSQL（生产）三种模式。
"""
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, Any
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class CheckpointerManager:
    """
    Checkpointer 管理器
    
    管理 LangGraph Checkpointer 的生命周期。
    支持 memory、sqlite、postgres 三种后端。
    """
    
    def __init__(self):
        self._checkpointer = None
        self._backend = settings.CHECKPOINT_BACKEND
        self._pool = None  # PostgreSQL 连接池
    
    async def _get_postgres_checkpointer(self):
        """获取 PostgreSQL Checkpointer"""
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        
        # 构建 PostgreSQL 连接字符串（psycopg 格式）
        # 从 asyncpg 格式转换
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        if self._pool is None:
            self._pool = AsyncConnectionPool(conninfo=db_url)
            await self._pool.open()
        
        checkpointer = AsyncPostgresSaver(self._pool)
        await checkpointer.setup()
        return checkpointer
    
    @asynccontextmanager
    async def get_checkpointer(self) -> AsyncGenerator[Any, None]:
        """
        获取 Checkpointer（异步上下文管理器）
        
        Usage:
            async with checkpointer_manager.get_checkpointer() as checkpointer:
                agent = create_chat_agent(checkpointer=checkpointer)
        """
        if self._backend == "memory":
            from langgraph.checkpoint.memory import MemorySaver
            yield MemorySaver()
        
        elif self._backend == "sqlite":
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
            import aiosqlite
            
            # 确保目录存在
            db_path = settings.CHECKPOINT_DB_PATH
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建异步 SQLite 连接
            async with aiosqlite.connect(str(db_path)) as conn:
                checkpointer = AsyncSqliteSaver(conn)
                await checkpointer.setup()
                logger.debug(f"📝 SQLite Checkpointer 已连接: {db_path}")
                yield checkpointer
        
        elif self._backend == "postgres":
            checkpointer = await self._get_postgres_checkpointer()
            logger.debug("📝 PostgreSQL Checkpointer 已连接")
            yield checkpointer
        
        else:
            logger.warning(f"⚠️ 未知的 CHECKPOINT_BACKEND: {self._backend}，使用内存模式")
            from langgraph.checkpoint.memory import MemorySaver
            yield MemorySaver()
    
    def get_sync_checkpointer(self):
        """
        获取同步 Checkpointer（用于应用启动时创建 Agent）
        
        注意：这只返回 MemorySaver，因为 SQLite/PostgreSQL 需要异步上下文。
        生产环境应在异步上下文中使用 get_checkpointer()。
        """
        if self._backend == "memory":
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()
        else:
            logger.info(f"📝 启动时使用内存 Checkpointer，运行时切换到 {self._backend}")
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()
    
    async def close(self):
        """关闭连接池"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("📝 Checkpointer 连接池已关闭")


# 全局 Checkpointer 管理器
checkpointer_manager = CheckpointerManager()
