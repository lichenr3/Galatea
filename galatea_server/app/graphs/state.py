"""
LangGraph Agent State
~~~~~~~~~~~~~~~~~~~~~

定义 Agent 的全局状态结构。
messages 字段使用 add_messages reducer：
  - 新消息追加到列表末尾
  - 同 ID 消息替换已有条目（用于更新）
"""
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """聊天 Agent 的状态"""
    messages: Annotated[list[BaseMessage], add_messages]
