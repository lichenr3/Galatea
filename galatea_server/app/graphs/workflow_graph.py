"""
Workflow Graph — 组装和编译 LangGraph 工作流
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当前结构（Phase 1）:
    START → generation → END

后续扩展（Phase 3）:
    START → retrieve_memory → generation → extract_memory → END
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_openai import ChatOpenAI
from app.graphs.state import AgentState
from app.graphs.nodes.generation import create_generation_node
from app.core.logger import get_logger

logger = get_logger(__name__)


def build_chat_graph(llm: ChatOpenAI, checkpointer: BaseCheckpointSaver):
    """
    构建并编译聊天 Graph。

    Args:
        llm: LangChain ChatModel 实例
        checkpointer: LangGraph checkpointer（用于持久化对话状态）

    Returns:
        编译后的 CompiledStateGraph，可直接调用 astream / ainvoke
    """
    graph_builder = StateGraph(AgentState)

    # ---- 节点 ----
    graph_builder.add_node("generation", create_generation_node(llm))

    # ---- 边 ----
    graph_builder.add_edge(START, "generation")
    graph_builder.add_edge("generation", END)

    compiled = graph_builder.compile(checkpointer=checkpointer)
    logger.info("✅ Chat graph compiled (START → generation → END)")
    return compiled
