"""
Agent Service — 处理用户消息的核心业务逻辑

使用 LangGraph 编排 LLM 对话流程，通过 stream_mode="messages" 实现 token 级流式输出。
Graph 为无状态模式（不使用 checkpointer），每次调用从 DB 加载完整历史。
消息持久化由 message_repo / session_repo 负责，不依赖任何内存状态。
"""

from app.schemas.web_protocol import *
from app.services.tts_service import TTSService
from app.repositories.message_repo import MessageRepository
from app.repositories.session_repo import SessionRepository
from app.core.logger import get_logger
from app.exceptions.base import InvalidDataException
from app.utils.text_buffer import TextBuffer
from app.exceptions.session import SessionNotFoundException
from app.exceptions.llm import LLMException
from app.agents.base import BaseAgent
from app.utils.message_utils import convert_db_messages_to_langchain
import time
import uuid
import asyncio

logger = get_logger(__name__)


def create_status_message(status: str, message: str = "") -> WebServerMessage:
    """创建 AI 状态消息"""
    return WebServerMessage(
        type=WebServerMessageType.AI_STATUS,
        data=AIStatusPayload(status=status, message=message).model_dump(),
        timestamp=time.time()
    )


def create_text_stream_message(text: str, is_finish: bool, message_id: str) -> WebServerMessage:
    """创建文本流消息"""
    return WebServerMessage(
        type=WebServerMessageType.AI_TEXT_STREAM,
        data=AITextStreamPayload(
            text=text,
            is_finish=is_finish,
            message_id=message_id
        ),
        timestamp=time.time()
    )


async def handle_user_message(
    session_id: str,
    agent: BaseAgent,
    tts_service: TTSService,
    message_repo: MessageRepository,
    session_repo: SessionRepository,
    msg: WebClientMessage
):
    """
    处理用户聊天消息（异步生成器，用于流式响应）

    流程：
    1. 验证输入 & 从 DB 查询会话
    2. 保存用户消息到 DB → 从 DB 加载完整历史（滑动窗口）→ 转为 langchain Message
    3. 通过 agent.astream_chat() 获取 token 级流式输出
    4. 实时发送文本 + TTS 处理
    5. 保存 AI 回复到 DB

    Raises:
        InvalidDataException: 当消息内容为空时
        SessionNotFoundException: 当会话不存在时
        LLMException: 当 LLM 服务出错时
    """
    user_text = msg.data.content
    enable_audio = getattr(msg.data, 'enable_audio', True)  # 默认启用音频

    # 验证输入
    if not user_text or not user_text.strip():
        raise InvalidDataException(message="消息内容不能为空")

    logger.info(f"📩 用户消息: {user_text[:50]}... (音频: {'开启' if enable_audio else '关闭'})")

    # 从 DB 验证会话并获取角色 ID
    db_session_id = int(session_id)
    character_id = await session_repo.get_character_id(db_session_id)
    if character_id is None:
        raise SessionNotFoundException(message=f"会话 {session_id} 不存在或已过期")

    # 通知前端 AI 开始思考
    yield create_status_message("thinking", "思考中...")

    # ---- 保存用户消息到 DB ----
    await message_repo.save(db_session_id, "user", user_text)

    # ---- 从 DB 加载完整历史（system prompt + 最近 N 条，含刚存的用户消息）----
    db_messages = await message_repo.get_recent_with_system(db_session_id, limit=20)
    input_messages = convert_db_messages_to_langchain(db_messages)

    # 初始化流式处理所需的状态
    message_id = str(uuid.uuid4())
    full_response = ""
    text_buffer = TextBuffer()
    sentence_index = 0
    tts_queue = asyncio.Queue()
    tts_task = None

    # 只在启用音频时启动 TTS 任务
    if enable_audio:
        logger.info("🔊 音频已启用，启动 TTS 处理任务")
        tts_task = asyncio.create_task(
            tts_service.process_queue(tts_queue, character_id)
        )
    else:
        logger.info("🔇 音频已禁用，跳过 TTS 生成")

    try:
        # ---- Agent 流式生成 ----
        async for text_chunk in agent.astream_chat(input_messages):
            full_response += text_chunk

            # 实时发送文本片段到前端
            yield create_text_stream_message(text_chunk, is_finish=False, message_id=message_id)

            # 只在启用音频时检测句子并加入 TTS 队列
            if enable_audio:
                completed_sentences = text_buffer.add_chunk(text_chunk)
                for sentence in completed_sentences:
                    logger.info(f"🎤 检测到完整句子 [{sentence_index}]: {sentence[:30]}...")
                    await tts_queue.put({"index": sentence_index, "text": sentence})
                    sentence_index += 1

        logger.info(f"✅ LLM 回复完成: {full_response[:50]}...")

        # 只在启用音频时处理剩余文本
        if enable_audio:
            remaining = text_buffer.flush()
            if remaining:
                logger.info(f"🎤 处理剩余文本 [{sentence_index}]: {remaining[:30]}...")
                try:
                    await tts_queue.put({"index": sentence_index, "text": remaining})
                except Exception as e:
                    logger.error(f"❌ 剩余文本入队失败: {e}")

            # 发送结束信号到 TTS 队列
            await tts_queue.put(None)

        # 保存 AI 回复到 DB
        await message_repo.save(db_session_id, "assistant", full_response)
        await session_repo.update_last_active(db_session_id)

        # 通知前端流式响应结束
        yield create_text_stream_message("", is_finish=True, message_id=message_id)
        yield create_status_message("idle")

    except Exception as e:
        logger.error(f"❌ LLM 处理错误: {e}", exc_info=True)
        if enable_audio and tts_task:
            await tts_queue.put(None)  # 确保 TTS 任务退出
        raise LLMException(
            message=f"获取 AI 回复失败: {str(e)}",
            details={"original_error": str(e)}
        )
