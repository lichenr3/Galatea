"""
Agent State 定义

LangGraph 使用 State 在图节点间传递数据。
这里定义 AgentState，继承自 MessagesState，添加项目特定的字段。
"""
from langgraph.graph import MessagesState
from typing import Optional, List


class AgentState(MessagesState):
    """
    Agent 状态，由 LangGraph 管理
    
    继承自 MessagesState，自动包含:
    - messages: list[BaseMessage]  对话历史（自动累积）
    
    扩展字段:
    - character_id: 当前角色 ID
    - language: 会话语言 (zh/en)
    - enable_audio: 是否启用 TTS
    
    未来扩展（Phase 6）:
    - retrieved_memories: 从向量库检索的相关记忆
    """
    character_id: str
    language: str = "zh"
    enable_audio: bool = True
    # Phase 6 扩展:
    # retrieved_memories: Optional[List[str]] = None
