
from app.schemas.web_protocol import *
from app.agents.base import BaseAgent
from app.utils.message_utils import convert_dict_messages_to_langchain
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from app.core.logger import get_logger
from app.exceptions.base import InvalidDataException
from app.exceptions.session import SessionNotFoundException
from app.exceptions.llm import LLMException
import time
import uuid

logger = get_logger(__name__)


async def handle_user_message(
    session_id: str,
    session_repo: SessionRepository,
    message_repo: MessageRepository,
    agent: BaseAgent,
    msg: WebClientMessage,
):
    """处理用户聊天消息（生成器函数，用于流式响应）"""
    payload = msg.data
    user_text = payload.content
    
    if not user_text or not user_text.strip():
        raise InvalidDataException(message="消息内容不能为空")
    
    logger.info(f"用户消息: {user_text[:50]}...")
    
    db_session = await session_repo.get_by_id(int(session_id))
    if db_session is None:
        logger.info(f"会话不存在: {session_id}")
        raise SessionNotFoundException(message=f"会话 {session_id} 不存在或已过期")
    
    await session_repo.update_last_active(int(session_id))
    
    await message_repo.save(int(session_id), "user", user_text)
    
    yield WebServerMessage(
        type=WebServerMessageType.AI_STATUS,
        data=AIStatusPayload(status="thinking", message="思考中...").model_dump(),
        timestamp=time.time()
    )
    
    messages = await message_repo.get_recent_with_system(int(session_id))
    langchain_messages = convert_dict_messages_to_langchain([
        {"role": m.role, "content": m.content} for m in messages
    ])
    
    message_id = str(uuid.uuid4())
    full_response = ""
    
    try:
        async for text_chunk in agent.astream_chat(langchain_messages):
            full_response += text_chunk
            
            yield WebServerMessage(
                type=WebServerMessageType.AI_TEXT_STREAM,
                data=AITextStreamPayload(
                    text=text_chunk,
                    is_finish=False,
                    message_id=message_id
                ),
                timestamp=time.time()
            )
        
        logger.info(f"LLM 回复: {full_response[:50]}...")
        
        await message_repo.save(int(session_id), "assistant", full_response)
        
        yield WebServerMessage(
            type=WebServerMessageType.AI_TEXT_STREAM,
            data=AITextStreamPayload(
                text="",
                is_finish=True,
                message_id=message_id
            ),
            timestamp=time.time()
        )
        
        yield WebServerMessage(
            type=WebServerMessageType.AI_STATUS,
            data=AIStatusPayload(status="idle", message="").model_dump(),
            timestamp=time.time()
        )
    
    except Exception as e:
        logger.error(f"LLM 处理错误: {e}", exc_info=True)
        raise LLMException(message=f"获取 AI 回复失败: {str(e)}", details={"original_error": str(e)})
