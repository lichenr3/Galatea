"""
SQLAlchemy 基础配置

提供数据库引擎、会话工厂和基类。
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# 创建异步引擎
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # 生产环境设为 False
    pool_pre_ping=True,  # 连接池健康检查
    pool_size=5,
    max_overflow=10,
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


async def get_async_session() -> AsyncSession:
    """
    获取异步数据库会话（用于依赖注入）
    
    Usage:
        async with get_async_session() as session:
            ...
    
    或作为 FastAPI 依赖:
        session: AsyncSession = Depends(get_async_session)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库（创建所有表）
    
    注意：生产环境应使用 Alembic 迁移
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
