"""
Generation Node — LLM 对话生成
====================================

功能：
1. 将 memory_context 注入到 system prompt
2. 调用 LLM 生成回复

memory_context 会被插入到 system 消息之前，作为背景信息。
"""
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from app.graphs.state import AgentState
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_generation_node(llm: ChatOpenAI):
    """
    工厂函数：创建绑定到指定 LLM 的生成节点。

    通过闭包捕获 llm 实例，使节点函数签名符合 LangGraph 要求。
    """

    async def generation(state: AgentState, config: RunnableConfig) -> dict:
        """
        调用 LLM 生成回复，返回增量 messages 更新。
        如果有 memory_context，会将其注入到消息前面。
        """
        # 1. 构建消息列表（注入记忆上下文）
        memory_context = state.get("memory_context", "")
        
        # 保留原有的 system 消息（人设 prompt）
        system_messages = [m for m in state["messages"] if isinstance(m, SystemMessage)]
        non_system_messages = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        
        if memory_context:
            # 将记忆作为 system 消息插入
            context_msg = SystemMessage(content=memory_context)
            # 组合: 原有 system 消息 + 记忆 context + 非 system 消息
            full_messages = system_messages + [context_msg] + non_system_messages
            logger.debug(f"Generation: injected memory_context ({len(memory_context)} chars)")
        else:
            # 保持原有消息顺序
            full_messages = state["messages"]

        # 2. 调用 LLM
        response = await llm.ainvoke(full_messages, config)
        return {"messages": [response]}

    return generation
