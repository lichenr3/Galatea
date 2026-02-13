"""
Base Agent — Agent 基类
~~~~~~~~~~~~~~~~~~~~~~~~

定义所有 Agent 的公共接口。
具体 Agent（如 GalateaAgent）继承此类并实现 build_graph。
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from app.core.logger import get_logger
from langchain_core.messages import AIMessageChunk

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.graph = self._build_graph()
        logger.info(f"✅ {self.__class__.__name__} initialized")

    @abstractmethod
    def _build_graph(self):
        """
        构建并编译 LangGraph 工作流。子类必须实现。

        Returns:
            CompiledStateGraph
        """
        ...

    async def astream_chat(
        self,
        messages: list[BaseMessage],
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天：传入完整消息历史，逐 token 返回 AI 回复文本。

        Args:
            messages: 完整的 langchain Message 列表（含 system prompt + 历史 + 新消息）

        Yields:
            str: AI 生成的文本片段（token 级）
        """

        async for msg_chunk, metadata in self.graph.astream(
            {"messages": messages},
            stream_mode="messages",
        ):
            if isinstance(msg_chunk, AIMessageChunk) and msg_chunk.content:
                yield msg_chunk.content
