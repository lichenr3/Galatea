from app.schemas.web_protocol import *
from app.agents.base import BaseAgent
from app.utils.message_utils import convert_dict_messages_to_langchain
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from app.core.logger import get_logger
from app.exceptions.base import InvalidDataException
from app.exceptions.session import SessionNotFoundException
from app.exceptions.llm import LLMException
from app.utils.text_buffer import TextBuffer
import time
import uuid

logger = get_logger(__name__)


import asyncio
from app.api.deps.services import get_mini_llm, get_embeddings, get_tts_service
from app.api.deps.database import get_memory_repo
from app.api.deps.infrastructure import get_character_registry
from app.services.memory_service import run_memory_extraction

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


import asyncio
from app.api.deps.services import get_mini_llm, get_embeddings
from app.api.deps.database import get_memory_repo
from app.api.deps.infrastructure import get_character_registry
from app.services.memory_service import run_memory_extraction

async def _trigger_memory_extraction(
    session_id: int,
    character_id: str,
    session_repo: SessionRepository,
    message_repo: MessageRepository,
):
    """后台任务：触发记忆提取"""
    try:
        db_session = await session_repo.get_by_id(session_id)
        if not db_session:
            return

        registry = get_character_registry()
        character = registry.get_character(character_id)
        character_name = character.name if character else character_id

        # 获取完整的最新对话历史
        messages = await message_repo.get_recent_with_system(session_id)
        history = [{"role": m.role, "content": m.content} for m in messages]

        new_index = await run_memory_extraction(
            session_id=session_id,
            character_id=character_id,
            character_name=character_name,
            session_history=history,
            last_extracted_index=db_session.last_extracted_index,
            extract_llm=get_mini_llm(),
            embeddings=get_embeddings(),
            memory_repo=get_memory_repo(),
        )

        if new_index > db_session.last_extracted_index:
            await session_repo.update_last_extracted_index(session_id, new_index)

    except Exception as e:
        logger.error(f"后台记忆提取任务失败: {e}", exc_info=True)


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
    
    character_id = db_session.character_id
    
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
    
    # 初始化流式处理所需的状态
    enable_audio = getattr(msg.data, 'enable_audio', True)  # 默认启用音频
    text_buffer = TextBuffer()
    sentence_index = 0
    tts_queue = asyncio.Queue()
    tts_task = None
    tts_service = get_tts_service()

    # 只在启用音频时启动 TTS 任务
    if enable_audio and tts_service:
        logger.info("🔊 音频已启用，启动 TTS 处理任务")
        tts_task = asyncio.create_task(
            tts_service.process_queue(tts_queue, character_id)
        )
    else:
        logger.info("🔇 音频已禁用或服务未初始化，跳过 TTS 生成")
        
    try:
        async for text_chunk in agent.astream_chat(langchain_messages, character_id=character_id):
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
            
            # 只在启用音频时检测句子并加入 TTS 队列
            if enable_audio and tts_service:
                completed_sentences = text_buffer.add_chunk(text_chunk)
                for sentence in completed_sentences:
                    logger.info(f"🎤 检测到完整句子 [{sentence_index}]: {sentence[:30]}...")
                    await tts_queue.put({"index": sentence_index, "text": sentence})
                    sentence_index += 1
        
        logger.info(f"LLM 回复: {full_response[:50]}...")
        
        # 只在启用音频时处理剩余文本
        if enable_audio and tts_service:
            remaining = text_buffer.flush()
            if remaining:
                logger.info(f"🎤 处理剩余文本 [{sentence_index}]: {remaining[:30]}...")
                try:
                    await tts_queue.put({"index": sentence_index, "text": remaining})
                except Exception as e:
                    logger.error(f"❌ 剩余文本入队失败: {e}")

            # 发送结束信号到 TTS 队列
            await tts_queue.put(None)
            
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
        if enable_audio and tts_task:
            await tts_queue.put(None)  # 确保 TTS 任务退出
        raise LLMException(message=f"获取 AI 回复失败: {str(e)}", details={"original_error": str(e)})
    finally:
        # 在返回后触发后台记忆提取
        asyncio.create_task(
            _trigger_memory_extraction(
                session_id=int(session_id),
                character_id=character_id,
                session_repo=session_repo,
                message_repo=message_repo,
            )
        )
