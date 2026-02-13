"""
Galatea Agent — 主角色聊天 Agent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当前为最基础的聊天 Agent（START → generation → END）。
后续扩展：
  - 加入 retrieve_memory / extract_memory 节点
  - 绑定 tools（搜索、知识库查询等）
  - 支持 checkpointer（多步 agent 状态恢复）
"""
from langchain_openai import ChatOpenAI
from app.agents.base import BaseAgent
from app.graphs.workflow_graph import build_chat_graph


class GalateaAgent(BaseAgent):
    """角色聊天 Agent"""

    def __init__(self, llm: ChatOpenAI):
        super().__init__(llm)

    def _build_graph(self):
        """构建聊天 Graph: START → generation → END"""
        return build_chat_graph(self.llm)
