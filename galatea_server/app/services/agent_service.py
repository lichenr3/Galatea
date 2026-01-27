"""
Agent 服务

处理用户消息，协调 LangGraph Agent、TTS 等服务。
"""
from langchain_core.messages import HumanMessage

from app.schemas.web_protocol import (
    WebServerMessage,
    WebServerMessageType,
    WebClientMessage,
    AIStatusPayload,
    AITextStreamPayload,
)
from app.infrastructure.managers.session_manager import SessionManager
from app.agents import chat_agent
from app.core.logger import get_logger
from app.exceptions.base import InvalidDataException
from app.utils.text_buffer import TextBuffer
from app.exceptions.session import SessionNotFoundException
from app.exceptions.llm import LLMException
import time
import uuid
import asyncio
from app.core.container import tts_service

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
    session_manager: SessionManager,
    msg: WebClientMessage
):
    """
    处理用户聊天消息（生成器函数，用于流式响应）
    
    使用 LangGraph Agent 处理消息，支持工具调用。
    
    Raises:
        InvalidDataException: 当消息内容为空时
        SessionNotFoundException: 当会话不存在时
        LLMException: 当 Agent 处理出错时
    """
    user_text = msg.data.content
    enable_audio = getattr(msg.data, 'enable_audio', True)
    
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
    
    # 初始化流式处理状态
    message_id = str(uuid.uuid4())
    full_response = ""
    text_buffer = TextBuffer()
    sentence_index = 0
    tts_queue = asyncio.Queue()
    tts_task = None
    
    # 启动 TTS 任务
    if enable_audio:
        logger.info("🔊 音频已启用，启动 TTS 处理任务")
        tts_task = asyncio.create_task(
            tts_service.process_queue(tts_queue, session.character)
        )
    else:
        logger.info("🔇 音频已禁用，跳过 TTS 生成")
    
    # 准备 Agent 输入
    input_state = {
        "messages": [HumanMessage(content=user_text)],
        "character_id": session.character,
        "language": "zh",  # TODO: 从 session 获取语言设置
        "enable_audio": enable_audio,
    }
    
    # LangGraph 配置（使用 session_id 作为 thread_id 实现会话隔离）
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }
    
    try:
        # 使用 astream_events 获取流式事件
        async for event in chat_agent.astream_events(input_state, config=config, version="v2"):
            event_type = event.get("event")
            
            # LLM 开始（已在开头发送 thinking 状态）
            if event_type == "on_chat_model_start":
                pass  # 已经发送了 thinking 状态
            
            # 工具开始执行
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "tool")
                logger.info(f"🔧 调用工具: {tool_name}")
                yield create_status_message("calling_tool", f"调用 {tool_name}...")
            
            # 工具执行完成
            elif event_type == "on_tool_end":
                logger.info("✅ 工具执行完成")
                yield create_status_message("thinking", "继续思考...")
            
            # LLM 流式输出
            elif event_type == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")
                
                if chunk and hasattr(chunk, "content") and chunk.content:
                    text_chunk = chunk.content
                    
                    # 过滤工具调用的中间输出
                    if isinstance(text_chunk, str) and text_chunk:
                        full_response += text_chunk
                        
                        # 发送文本片段到前端
                        yield create_text_stream_message(
                            text=text_chunk,
                            is_finish=False,
                            message_id=message_id
                        )
                        
                        # TTS 处理
                        if enable_audio:
                            completed_sentences = text_buffer.add_chunk(text_chunk)
                            for sentence in completed_sentences:
                                logger.info(f"🎤 检测到完整句子 [{sentence_index}]: {sentence[:30]}...")
                                await tts_queue.put({"index": sentence_index, "text": sentence})
                                sentence_index += 1
        
        logger.info(f"✅ Agent 回复完成: {full_response[:50]}...")
        
        # 处理 TTS 剩余文本
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
        
        # 保存 AI 回复到会话历史（用于前端显示，LangGraph 也会保存到 Checkpointer）
        if full_response:
            session.add_message("user", user_text)
            session.add_message("assistant", full_response)
        
        # 通知前端流式响应结束
        yield create_text_stream_message("", is_finish=True, message_id=message_id)
        yield create_status_message("idle")
    
    except Exception as e:
        logger.error(f"❌ Agent 处理错误: {e}", exc_info=True)
        if enable_audio and tts_task:
            await tts_queue.put(None)
        raise LLMException(
            message=f"获取 AI 回复失败: {str(e)}", 
            details={"original_error": str(e)}
        )
