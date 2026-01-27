"""
Agent 图节点实现

每个节点是一个函数，接收 AgentState，返回状态更新。
"""
from langchain_core.messages import SystemMessage
from app.agents.state import AgentState
from app.utils.prompts import load_persona
from app.core.container import character_registry
from app.core.logger import get_logger

logger = get_logger(__name__)


def chat_node(state: AgentState, llm) -> dict:
    """
    聊天节点：调用 LLM 生成回复
    
    职责:
    1. 加载角色 system prompt
    2. 构建完整消息列表
    3. 调用 LLM
    4. 返回新消息（会自动追加到 state.messages）
    
    Args:
        state: 当前 Agent 状态
        llm: LangChain LLM 实例（已绑定工具）
    
    Returns:
        状态更新字典，包含新消息
    """
    character_id = state["character_id"]
    language = state.get("language", "zh")
    
    # 加载角色人设作为 system prompt
    system_prompt = load_persona(character_id, character_registry, language=language)
    
    # 构建完整消息列表（system prompt + 历史消息）
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    
    logger.debug(f"🧠 调用 LLM (角色: {character_id}, 消息数: {len(messages)})")
    
    # 调用 LLM
    response = llm.invoke(messages)
    
    # 返回新消息（LangGraph 会自动追加到 messages 列表）
    return {"messages": [response]}


def respond_node(state: AgentState) -> dict:
    """
    响应节点：最终回复处理（后处理钩子）
    
    职责:
    1. 可在此处做后处理
    2. 返回最终状态
    
    未来扩展（Phase 6）:
    - 提取对话要点存入向量库
    - 更新用户画像
    - 记录分析日志
    
    Args:
        state: 当前 Agent 状态
    
    Returns:
        状态（不做修改）
    """
    # 目前直接透传状态
    # Phase 6 可在此处添加记忆提取逻辑
    return {}
