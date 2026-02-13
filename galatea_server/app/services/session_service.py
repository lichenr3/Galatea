from app.infrastructure.managers.session_manager import SessionManager
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.session import *
from app.schemas.common import UnifiedResponse
from app.core.logger import get_logger
from app.utils.path_utils import resolve_static_url
from app.schemas.tts import SwitchTTSModelRequest
from app.services.tts_model_service import switch_tts_model_service
import asyncio

logger = get_logger(__name__)


async def _switch_tts_model_in_background(request: SwitchTTSModelRequest, character_registry: CharacterRegistry):
    """
    后台异步切换 TTS 模型，不阻塞主流程
    """
    try:
        logger.info(f"🎤 [后台任务] 开始切换 TTS 模型: {request.character_id}")
        result = await switch_tts_model_service(request, character_registry)
        if result.code == 200:
            logger.info(f"✅ [后台任务] TTS 模型切换成功: {request.character_id}")
        else:
            logger.warning(f"⚠️ [后台任务] TTS 模型切换失败: {result.message}")
    except Exception as e:
        logger.error(f"❌ [后台任务] TTS 模型切换异常: {e}", exc_info=True)


async def create_session_service(
    request: CreateSessionRequest,
    session_manager: SessionManager,
    character_registry: CharacterRegistry,
    unity_manager: UnityConnectionManager,
    session_repo: SessionRepository,
    message_repo: MessageRepository,
) -> UnifiedResponse[CreateSessionResponse]:
    """创建新的会话服务实例"""
    character_id = request.character_id
    db_id: int | None = None
    session_id: str = ""
    created = False

    try:
        if not character_registry.character_exists(character_id):
            logger.error(f"❌ 角色不存在: {character_id}")
            return UnifiedResponse(code=404, message=f"角色 {character_id} 不存在", data=None)

        gala_info = character_registry.get_character(character_id)
        if gala_info is None:
            logger.error(f"❌ 角色配置非法: {character_id}")
            return UnifiedResponse(code=400, message=f"角色 {character_id} 配置非法", data=None)

        # 先持久化到数据库，拿到自增 ID
        db_id = await session_repo.create(character_id)
        session_id = str(db_id)

        # 创建会话（内存，用 str(id) 作为 key）
        session = session_manager.create_session(
            session_id=session_id, 
            character_id=character_id,
            language=request.language
        )
        created = True

        # 保存 system prompt 到消息表
        if session.history:
            await message_repo.save(db_id, "system", session.history[0]["content"])

        # 🆕 异步切换 TTS 模型（不阻塞会话创建）
        logger.info(f"🎤 准备异步切换 TTS 模型到角色: {character_id}")
        tts_switch_request = SwitchTTSModelRequest(character_id=character_id)
        
        # 使用 asyncio.create_task 在后台执行，不等待结果
        asyncio.create_task(_switch_tts_model_in_background(tts_switch_request, character_registry))

        # 注意：不在这里切换角色，而是在启动 Unity 时传递角色 ID
        # 避免 Unity 未启动时消息丢失

        # 使用工具函数优雅地解析头像 URL
        avatar_path = gala_info.avatar.image if gala_info.avatar else ""
        avatar_url = resolve_static_url(avatar_path)
        
        if avatar_url:
            logger.info(f"🖼️  头像 URL: {avatar_url}")
        else:
            logger.warning(f"⚠️  角色 {character_id} 没有配置头像")
        
        logger.info(f"✅ 创建会话成功: {session_id}")
        
        # 返回统一格式的响应
        response_data = CreateSessionResponse(session_id=session_id, avatar_url=avatar_url)
        return UnifiedResponse.success(message="创建会话成功", data=response_data)

    except Exception as e:
        # 回滚：删除内存中已创建的会话
        if created:
            try:
                session_manager.remove_session(session_id)
                logger.warning(f"⚠️ 已回滚内存会话: {session_id}")
            except Exception as rollback_error:
                logger.error(f"❌ 回滚内存会话失败: {rollback_error}")
        # 回滚：删除 DB 中已创建的记录
        if db_id is not None:
            try:
                await session_repo.delete(db_id)
                logger.warning(f"⚠️ 已回滚数据库会话: {db_id}")
            except Exception as rollback_error:
                logger.error(f"❌ 回滚数据库会话失败: {rollback_error}")
        
        logger.error(f"❌ 创建会话失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"创建会话失败: {str(e)}", data=None)
    
async def delete_session_service(
    session_id: str,
    session_manager: SessionManager,
    session_repo: SessionRepository,
) -> UnifiedResponse[bool]:
    """删除会话服务实例"""
    try:
        session_manager.remove_session(session_id)
        await session_repo.delete(int(session_id))
        logger.info(f"✅ 删除会话成功: {session_id}")
        return UnifiedResponse.success(message="删除会话成功", data=True)

    except Exception as e:
        logger.error(f"❌ 删除会话失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"删除会话失败: {str(e)}", data=None)


def get_contacts_service(
    session_manager: SessionManager,
    character_registry: CharacterRegistry,
    language: str = "zh"
) -> UnifiedResponse[ContactsResponse]:
    """
    获取通讯录（按角色分组的会话列表）
    
    返回格式：
    - 角色按最近交互排序
    - 每个角色下的会话也按最近交互排序
    
    Args:
        language: 语言代码（zh/en），用于返回对应语言的角色名称
    """
    try:
        # 获取按角色分组的会话
        contacts_dict = session_manager.get_contacts_grouped_by_character()
        
        contacts = []
        
        # 按角色顺序构建响应
        for character_id, sessions in contacts_dict.items():
            # 获取角色信息
            gala_info = character_registry.get_character(character_id)
            if not gala_info:
                logger.warning(f"⚠️ 角色 {character_id} 不存在于注册表中")
                continue
            
            # 解析头像 URL
            avatar_path = gala_info.avatar.image if gala_info.avatar else ""
            avatar_url = resolve_static_url(avatar_path)
            
            # 获取对应语言的角色名称
            character_name = gala_info.get_name(language)
            
            # 构建会话信息列表
            session_infos = []
            for session in sessions:
                session_infos.append(SessionInfo(
                    session_id=session.session_id,
                    last_active=session.last_active.isoformat(),
                    message_count=len(session.history) - 1  # 减去 system prompt
                ))
            
            # 添加角色联系人
            contacts.append(CharacterContact(
                character_id=character_id,
                character_name=character_name,
                avatar_url=avatar_url or "",
                sessions=session_infos
            ))
        
        response_data = ContactsResponse(contacts=contacts)
        logger.info(f"✅ 获取通讯录成功，共 {len(contacts)} 个角色 (语言: {language})")
        
        return UnifiedResponse.success(message="获取通讯录成功", data=response_data)
    
    except Exception as e:
        logger.error(f"❌ 获取通讯录失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"获取通讯录失败: {str(e)}", data=None)


def get_history_service(
    session_id: str,
    session_manager: SessionManager
) -> UnifiedResponse[GetHistoryResponse]:
    """获取会话历史记录"""
    try:
        if session_id not in session_manager.sessions:
            return UnifiedResponse(code=404, message=f"会话 {session_id} 不存在", data=None)
        
        session = session_manager.sessions[session_id]
        history = session.get_messages()
        
        # 转换格式
        chat_messages = [
            ChatMessage(role=msg["role"], content=msg["content"]) 
            for msg in history 
            if msg["role"] in {"user", "assistant"}
        ]
        
        return UnifiedResponse.success(
            message="获取历史记录成功",
            data=GetHistoryResponse(session_id=session_id, history=chat_messages)
        )
    except Exception as e:
        logger.error(f"❌ 获取历史记录失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"获取历史记录失败: {str(e)}", data=None)


def get_available_characters_service(
    character_registry: CharacterRegistry
) -> UnifiedResponse[list[CharacterInfo]]:
    """
    获取所有可用角色的完整信息（用于角色选择界面）
    """
    try:
        characters_list = []
        available_ids = character_registry.list_available_characters()
        
        for char_id in available_ids:
            try:
                # 加载角色配置
                char_config = character_registry.get_character(char_id)
                
                # 解析头像 URL
                avatar_path = char_config.avatar.image if char_config.avatar else ""
                avatar_url = resolve_static_url(avatar_path)
                
                # 处理角色名称（支持旧格式和新格式）
                if isinstance(char_config.name, dict):
                    name_dict = char_config.name
                else:
                    # 兼容旧格式：如果是字符串，转换为字典
                    name_dict = {"zh": char_config.name, "en": char_config.display_name or char_config.name}
                
                # 构建角色信息
                char_info = CharacterInfo(
                    id=char_config.id,
                    name=name_dict,
                    display_name=char_config.display_name,
                    description=char_config.description if hasattr(char_config, 'description') else {"zh": "", "en": ""},
                    avatar_url=avatar_url or "/images/default_avatar.png",
                    tags=char_config.metadata.tags if char_config.metadata and hasattr(char_config.metadata, 'tags') else []
                )
                
                characters_list.append(char_info)
                logger.info(f"✅ 加载角色: {name_dict.get('zh', char_config.id)} (头像: {avatar_url})")
            except Exception as e:
                # 跳过加载失败的角色
                logger.warning(f"⚠️ 跳过角色 {char_id}: {e}")
                continue
        
        logger.info(f"✅ 获取角色列表成功，共 {len(characters_list)} 个角色")
        return UnifiedResponse.success(
            message="获取角色列表成功",
            data=characters_list
        )
    except Exception as e:
        logger.error(f"❌ 获取角色列表失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"获取角色列表失败: {str(e)}", data=None)

