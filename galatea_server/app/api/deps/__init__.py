"""
Application Dependency Injection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

按领域拆分为子模块，本文件统一导出所有 provider 和生命周期函数。
外部代码仍然使用 `from app.api.deps import xxx` 即可。
"""
from app.core.config import settings

# Re-export: Database
from app.api.deps.database import (
    get_database,
    get_session_repo,
    get_message_repo,
    get_memory_repo,
)

# Re-export: Infrastructure
from app.api.deps.infrastructure import (
    get_web_manager,
    get_unity_manager,
    get_character_registry,
)

# Re-export: Services
from app.api.deps.services import (
    get_tts_server,
    get_unity_process,
    get_tts_service,
    get_llm,
    get_agent,
    get_embeddings,
    get_mini_llm,
)



# 子模块引用（供 init/shutdown 使用）
from app.api.deps import database as _db_deps
from app.api.deps import infrastructure as _infra_deps
from app.api.deps import services as _svc_deps


async def init_dependencies() -> None:
    """
    初始化所有应用级单例。在 app lifespan startup 阶段调用一次。
    """
    # 1. Database + Repositories
    await _db_deps.init_database(settings.DATABASE_URL)

    # 2. Infrastructure（连接管理器、角色注册表、会话管理器）
    _infra_deps.init_infrastructure()

    # 3. Services（LLM、Agent、TTS、Unity 进程）
    _svc_deps.init_services(
        character_registry=_infra_deps.get_character_registry(),
        unity_manager=_infra_deps.get_unity_manager(),
        web_manager=_infra_deps.get_web_manager(),
        llm_model=settings.LLM_MODEL,
        llm_api_key=settings.LLM_API_KEY,
        llm_base_url=settings.LLM_BASE_URL,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_api_key=settings.EMBEDDING_API_KEY or settings.LLM_API_KEY,
        embedding_base_url=settings.EMBEDDING_BASE_URL or settings.LLM_BASE_URL,
        mini_llm_model=settings.MINI_LLM_MODEL,
        mini_llm_api_key=settings.MINI_LLM_API_KEY,
        mini_llm_base_url=settings.MINI_LLM_BASE_URL,
    )


async def shutdown_dependencies() -> None:
    """清理资源。在 app lifespan shutdown 阶段调用。"""
    await _db_deps.shutdown_database()
