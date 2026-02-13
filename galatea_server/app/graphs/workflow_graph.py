"""
Workflow Graph — 组装和编译 LangGraph 工作流
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当前结构（Phase 1）:
    START → generation → END

后续扩展（Phase 3）:
    START → retrieve_memory → generation → extract_memory → END

当前为无状态图（不使用 checkpointer），
对话历史由 messages 表管理，每次调用从 DB 加载完整上下文。
后续如需多步 agent 的中间状态恢复，可重新绑定 checkpointer。
"""
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from app.graphs.state import AgentState
from app.graphs.nodes.generation import create_generation_node
from app.core.logger import get_logger

logger = get_logger(__name__)


def build_chat_graph(llm: ChatOpenAI):
    """
    构建并编译聊天 Graph（无状态）。

    Args:
        llm: LangChain ChatModel 实例

    Returns:
        编译后的 CompiledStateGraph，可直接调用 astream / ainvoke
    """
    graph_builder = StateGraph(AgentState)

    # ---- 节点 ----
    graph_builder.add_node("generation", create_generation_node(llm))

    # ---- 边 ----
    graph_builder.add_edge(START, "generation")
    graph_builder.add_edge("generation", END)

    compiled = graph_builder.compile()
    logger.info("✅ Chat graph compiled (START → generation → END)")
    return compiled
