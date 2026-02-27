"""
Database 依赖注入
"""
from app.infrastructure.database import Database
from app.repositories import SessionRepository, MessageRepository, MemoryRepository

_database: Database | None = None
_session_repo: SessionRepository | None = None
_message_repo: MessageRepository | None = None
_memory_repo: MemoryRepository | None = None


async def init_database(database_url: str) -> None:
    """初始化数据库及 Repository"""
    global _database, _session_repo, _message_repo, _memory_repo

    _database = Database(database_url)
    await _database.init_db()

    _session_repo = SessionRepository(_database.session_factory)
    _message_repo = MessageRepository(_database.session_factory)
    _memory_repo = MemoryRepository(_database.session_factory)


async def shutdown_database() -> None:
    """关闭数据库连接"""
    if _database:
        await _database.close()


def get_database() -> Database:
    return _database


def get_session_repo() -> SessionRepository:
    return _session_repo


def get_message_repo() -> MessageRepository:
    return _message_repo


def get_memory_repo() -> MemoryRepository:
    return _memory_repo
