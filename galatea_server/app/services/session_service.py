from app.infrastructure.managers.character_registry import CharacterRegistry
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.session import *
from app.schemas.common import UnifiedResponse
from app.core.logger import get_logger
from app.utils.path_utils import resolve_static_url
from app.utils.prompts import load_persona
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
    character_registry: CharacterRegistry,
    unity_manager: UnityConnectionManager,
    session_repo: SessionRepository,
    message_repo: MessageRepository,
) -> UnifiedResponse[CreateSessionResponse]:
    """创建新的会话服务实例"""
    character_id = request.character_id
    db_id: int | None = None

    try:
        if not character_registry.character_exists(character_id):
            logger.error(f"❌ 角色不存在: {character_id}")
            return UnifiedResponse(code=404, message=f"角色 {character_id} 不存在", data=None)

        gala_info = character_registry.get_character(character_id)
        if gala_info is None:
            logger.error(f"❌ 角色配置非法: {character_id}")
            return UnifiedResponse(code=400, message=f"角色 {character_id} 配置非法", data=None)

        # 持久化到数据库，拿到自增 ID
        db_id = await session_repo.create(character_id)
        session_id = str(db_id)

        # 生成 system prompt 并保存到消息表
        persona = load_persona(character_id, character_registry, language=request.language)
        await message_repo.save(db_id, "system", persona)

        # 异步切换 TTS 模型（不阻塞会话创建）
        logger.info(f"🎤 准备异步切换 TTS 模型到角色: {character_id}")
        tts_switch_request = SwitchTTSModelRequest(character_id=character_id)
        asyncio.create_task(_switch_tts_model_in_background(tts_switch_request, character_registry))

        # 解析头像 URL
        avatar_path = gala_info.avatar.image if gala_info.avatar else ""
        avatar_url = resolve_static_url(avatar_path)
        
        if avatar_url:
            logger.info(f"🖼️  头像 URL: {avatar_url}")
        else:
            logger.warning(f"⚠️  角色 {character_id} 没有配置头像")
        
        logger.info(f"✅ 创建会话成功: {session_id}")
        
        response_data = CreateSessionResponse(session_id=session_id, avatar_url=avatar_url)
        return UnifiedResponse.success(message="创建会话成功", data=response_data)

    except Exception as e:
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
    session_repo: SessionRepository,
) -> UnifiedResponse[bool]:
    """删除会话服务实例"""
    try:
        await session_repo.delete(int(session_id))
        logger.info(f"✅ 删除会话成功: {session_id}")
        return UnifiedResponse.success(message="删除会话成功", data=True)

    except Exception as e:
        logger.error(f"❌ 删除会话失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"删除会话失败: {str(e)}", data=None)


async def get_contacts_service(
    session_repo: SessionRepository,
    message_repo: MessageRepository,
    character_registry: CharacterRegistry,
    language: str = "zh"
) -> UnifiedResponse[ContactsResponse]:
    """
    获取通讯录（按角色分组的会话列表）— 完全从 DB 读取
    
    返回格式：
    - 角色按最近交互排序（由 DB last_active 决定）
    - 每个角色下的会话也按最近交互排序
    
    Args:
        language: 语言代码（zh/en），用于返回对应语言的角色名称
    """
    try:
        # 从 DB 获取所有会话（已按 last_active DESC 排序）
        db_sessions = await session_repo.get_all_ordered()

        # 按角色分组（保持插入顺序 = 最近交互在前）
        grouped: dict[str, list] = {}
        for db_sess in db_sessions:
            grouped.setdefault(db_sess.character_id, []).append(db_sess)

        contacts = []

        for character_id, sessions in grouped.items():
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
            for db_sess in sessions:
                msg_count = await message_repo.count_by_session(db_sess.id)
                session_infos.append(SessionInfo(
                    session_id=str(db_sess.id),
                    last_active=db_sess.last_active.isoformat(),
                    message_count=msg_count
                ))
            
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


async def get_history_service(
    session_id: str,
    message_repo: MessageRepository,
) -> UnifiedResponse[GetHistoryResponse]:
    """获取会话历史记录（从 DB 读取）"""
    try:
        db_session_id = int(session_id)
        db_messages = await message_repo.get_by_session(db_session_id)

        if not db_messages:
            return UnifiedResponse(code=404, message=f"会话 {session_id} 不存在或无消息", data=None)

        # 只返回 user / assistant 消息（过滤 system prompt）
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content)
            for msg in db_messages
            if msg.role in {"user", "assistant"}
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

