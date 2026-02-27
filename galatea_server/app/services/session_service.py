from app.infrastructure.managers.character_registry import CharacterRegistry
from app.schemas.session import *
from app.schemas.common import UnifiedResponse
from app.core.logger import get_logger
from app.utils.path_utils import resolve_static_url
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository

logger = get_logger(__name__)


async def create_session_service(
    request: CreateSessionRequest,
    session_repo: SessionRepository,
    character_registry: CharacterRegistry,
) -> UnifiedResponse[CreateSessionResponse]:
    """创建新会话（数据库）"""
    character_id = request.character_id

    try:
        if not character_registry.character_exists(character_id):
            logger.error(f"角色不存在: {character_id}")
            return UnifiedResponse(code=404, message=f"角色 {character_id} 不存在", data=None)

        gala_info = character_registry.get_character(character_id)
        if gala_info is None:
            logger.error(f"角色配置非法: {character_id}")
            return UnifiedResponse(code=400, message=f"角色 {character_id} 配置非法", data=None)

        session_id = await session_repo.create(character_id)
        session_id_str = str(session_id)

        avatar_path = gala_info.avatar.image if gala_info.avatar else ""
        avatar_url = resolve_static_url(avatar_path)
        
        logger.info(f"创建会话成功: {session_id_str}")
        
        response_data = CreateSessionResponse(session_id=session_id_str, avatar_url=avatar_url or "")
        return UnifiedResponse.success(message="创建会话成功", data=response_data)

    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"创建会话失败: {str(e)}", data=None)


async def delete_session_service(
    session_id: str,
    session_repo: SessionRepository,
) -> UnifiedResponse[bool]:
    """删除会话（数据库）"""
    try:
        await session_repo.delete(int(session_id))
        logger.info(f"删除会话成功: {session_id}")
        return UnifiedResponse.success(message="删除会话成功", data=True)

    except Exception as e:
        logger.error(f"删除会话失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"删除会话失败: {str(e)}", data=None)


async def get_contacts_service(
    session_repo: SessionRepository,
    message_repo: MessageRepository,
    character_registry: CharacterRegistry,
) -> UnifiedResponse[ContactsResponse]:
    """获取通讯录（数据库）"""
    try:
        contacts_dict = await session_repo.get_all_grouped_by_character()
        
        contacts = []
        
        for character_id, sessions in contacts_dict.items():
            gala_info = character_registry.get_character(character_id)
            if not gala_info:
                logger.warning(f"角色 {character_id} 不存在于注册表中")
                continue
            
            avatar_path = gala_info.avatar.image if gala_info.avatar else ""
            avatar_url = resolve_static_url(avatar_path)
            
            session_infos = []
            for session in sessions:
                last_msg = await message_repo.get_last_message(session.id)
                preview = last_msg.content[:50] if last_msg else ""
                message_count = await message_repo.count_by_session(session.id)
                
                session_infos.append(SessionInfo(
                    session_id=str(session.id),
                    message_count=message_count,
                    preview=preview,
                ))
            
            contacts.append(CharacterContact(
                character_id=character_id,
                character_name=gala_info.get_name(),
                avatar_url=avatar_url or "",
                sessions=session_infos
            ))
        
        response_data = ContactsResponse(contacts=contacts)
        logger.info(f"获取通讯录成功，共 {len(contacts)} 个角色")
        
        return UnifiedResponse.success(message="获取通讯录成功", data=response_data)
    
    except Exception as e:
        logger.error(f"获取通讯录失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"获取通讯录失败: {str(e)}", data=None)


async def get_history_service(
    session_id: str,
    session_repo: SessionRepository,
    message_repo: MessageRepository,
) -> UnifiedResponse[GetHistoryResponse]:
    """获取会话历史记录（数据库）"""
    try:
        session = await session_repo.get_by_id(int(session_id))
        if not session:
            return UnifiedResponse(code=404, message=f"会话 {session_id} 不存在", data=None)
        
        messages = await message_repo.get_by_session(int(session_id))
        
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content) 
            for msg in messages 
            if msg.role in {"user", "assistant"}
        ]
        
        return UnifiedResponse.success(
            message="获取历史记录成功",
            data=GetHistoryResponse(session_id=session_id, history=chat_messages)
        )
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}", exc_info=True)
        return UnifiedResponse(code=500, message=f"获取历史记录失败: {str(e)}", data=None)
