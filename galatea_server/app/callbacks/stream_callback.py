"""
LangChain 流式输出回调处理器

将 LLM 事件转换为 WebSocket 消息格式。
注意：这是一个可选的实现方式，主要用于需要回调机制的场景。
当前 agent_service 使用 astream_events，不需要此回调。
"""
from langchain_core.callbacks import AsyncCallbackHandler
from typing import Any, Dict, Optional
from app.core.logger import get_logger

logger = get_logger(__name__)


class StreamCallbackHandler(AsyncCallbackHandler):
    """
    流式输出回调处理器
    
    可用于将 LLM 生成事件转换为其他格式。
    当前项目使用 astream_events 方式，此类作为备选方案保留。
    """
    
    def __init__(self):
        self.tokens = []
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """LLM 开始时调用"""
        logger.debug("🧠 LLM 开始生成...")
        self.tokens = []
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """LLM 生成新 token 时调用"""
        self.tokens.append(token)
    
    async def on_llm_end(self, response, **kwargs: Any) -> None:
        """LLM 结束时调用"""
        logger.debug(f"✅ LLM 生成完成，共 {len(self.tokens)} 个 token")
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """工具开始执行时调用"""
        tool_name = serialized.get("name", "unknown")
        logger.debug(f"🔧 工具开始执行: {tool_name}")
    
    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """工具执行结束时调用"""
        logger.debug(f"✅ 工具执行完成")
    
    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """工具执行出错时调用"""
        logger.error(f"❌ 工具执行错误: {error}")
