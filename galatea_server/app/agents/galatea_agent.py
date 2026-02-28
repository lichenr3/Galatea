"""
Galatea Agent — 主角色聊天 Agent
=====================================

功能：
- START → retrieve_memory → generation → END
- retrieve_memory: 根据用户消息检索历史记忆
- generation: 生成回复（注入记忆到 system prompt）

设计说明：
- 记忆提取（extract_memory）是 fire-and-forget 异步任务，由调用方在每轮对话后触发
- 记忆检索在 graph 内部完成，每次生成前自动执行
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.agents.base import BaseAgent
from app.graphs.workflow_graph import build_chat_graph
from app.repositories.memory_repo import MemoryRepository


class GalateaAgent(BaseAgent):
    """角色聊天 Agent（含记忆检索）"""

    def __init__(
        self,
        llm: ChatOpenAI,
        mini_llm: ChatOpenAI,
        embeddings: OpenAIEmbeddings,
        memory_repo: MemoryRepository,
    ):
        # 先设置属性，再调用父类（父类会调用 _build_graph）
        self.mini_llm = mini_llm

        self.embeddings = embeddings
        self.memory_repo = memory_repo
        super().__init__(llm)

    def _build_graph(self):
        """构建聊天 Graph: START → retrieve_memory → generation → END"""
        return build_chat_graph(
            llm=self.llm,
            mini_llm=self.mini_llm,
            embeddings=self.embeddings,
            memory_repo=self.memory_repo,
        )
