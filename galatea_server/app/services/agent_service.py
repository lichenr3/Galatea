"""
Agent Service — 处理用户消息的核心业务逻辑

使用 LangGraph 编排 LLM 对话流程，通过 stream_mode="messages" 实现 token 级流式输出。
Checkpointer 自动持久化对话状态；同时保留 message_repo 双写以支持自定义查询。
"""

from app.schemas.web_protocol import *
from app.infrastructure.managers.session_manager import SessionManager
from app.services.tts_service import TTSService
from app.repositories.message_repo import MessageRepository
from app.repositories.session_repo import SessionRepository
from app.core.logger import get_logger
from app.exceptions.base import InvalidDataException
from app.utils.text_buffer import TextBuffer
from app.exceptions.session import SessionNotFoundException
from app.exceptions.llm import LLMException
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AIMessageChunk
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


def _convert_history_to_langchain(history: list[dict]) -> list:
    """将 session_manager 的 dict 格式历史转为 langchain Message 对象"""
    messages = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


async def handle_user_message(
    session_id: str,
    session_manager: SessionManager,
    chat_graph,  # CompiledStateGraph — LangGraph 编译后的图
    tts_service: TTSService,
    message_repo: MessageRepository,
    session_repo: SessionRepository,
    msg: WebClientMessage
):
    """
    处理用户聊天消息（异步生成器，用于流式响应）

    流程：
    1. 验证输入 & 获取会话
    2. 构建 LangGraph 输入（首次消息含 system prompt，后续仅含新消息）
    3. 通过 graph.astream(stream_mode="messages") 获取 token 级流式输出
    4. 实时发送文本 + TTS 处理
    5. 持久化消息到自定义 messages 表（checkpointer 同时自动持久化图状态）

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

    # 获取并验证会话
    session = session_manager.get_session(session_id)
    if session is None:
        raise SessionNotFoundException(message=f"会话 {session_id} 不存在或已过期")

    session_manager.move_to_front(session_id)

    # 通知前端 AI 开始思考
    yield create_status_message("thinking", "思考中...")

    # ---- 构建 LangGraph 输入 ----
    graph_config = {"configurable": {"thread_id": session_id}}

    # 检查 checkpointer 是否已有该会话的状态
    state_snapshot = await chat_graph.aget_state(graph_config)
    has_graph_state = bool(state_snapshot.values and state_snapshot.values.get("messages"))

    if not has_graph_state:
        # 首次调用（新会话或重启后恢复的会话）：
        # 将 session_manager 中的完整历史转为 langchain 消息，
        # 附加新的用户消息一起传入，让 checkpointer 建立初始状态。
        input_messages = _convert_history_to_langchain(session.history)
        input_messages.append(HumanMessage(content=user_text))
        logger.info(f"🔄 初始化图状态 (历史消息: {len(input_messages) - 1} 条 + 新消息)")
    else:
        # 后续调用：checkpointer 自动加载历史，只需传入新消息
        input_messages = [HumanMessage(content=user_text)]

    # 记录用户消息（内存 + 自定义 DB 表）
    db_session_id = int(session_id)
    session.add_message("user", user_text)
    await message_repo.save(db_session_id, "user", user_text)

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
            tts_service.process_queue(tts_queue, session.character)
        )
    else:
        logger.info("🔇 音频已禁用，跳过 TTS 生成")

    try:
        # ---- LangGraph 流式生成 ----
        async for msg_chunk, metadata in chat_graph.astream(
            {"messages": input_messages},
            config=graph_config,
            stream_mode="messages",
        ):
            # 只处理 AI 生成的 token（过滤掉输入消息等其他事件）
            if isinstance(msg_chunk, AIMessageChunk) and msg_chunk.content:
                text_chunk = msg_chunk.content
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

        # 保存 AI 回复（内存 + 自定义 DB 表；checkpointer 已自动持久化图状态）
        session.add_message("assistant", full_response)
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
