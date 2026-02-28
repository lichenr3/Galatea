"""
Workflow Graph — 组装和编译 LangGraph 工作流
======================================================

当前结构（Phase 1 + Memory）:
    START → retrieve_memory → generation → END

记忆流程：
  1. retrieve_memory: 根据用户最新消息检索相关历史记忆
  2. generation: 生成回复时注入记忆到 system prompt

注意：记忆提取（extract_memory）是 fire-and-forget 异步任务，
不在 graph 流程中，由调用方在每轮对话后触发。
"""
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.graphs.state import AgentState
from app.graphs.nodes.generation import create_generation_node
from app.graphs.nodes.memory import create_retrieve_memory_node
from app.repositories.memory_repo import MemoryRepository
from app.core.logger import get_logger

logger = get_logger(__name__)


def build_chat_graph(
    llm: ChatOpenAI,
    mini_llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings,
    memory_repo: MemoryRepository,
):

    """
    构建并编译聊天 Graph（含记忆检索）。

    Args:
        llm: LangChain ChatModel 实例
        embeddings: OpenAI Embeddings 实例（用于向量检索）
        memory_repo: MemoryRepository 实例

    Returns:
        编译后的 CompiledStateGraph，可直接调用 astream / ainvoke
    """
    graph_builder = StateGraph(AgentState)

    # ---- 节点 ----
    graph_builder.add_node("retrieve_memory", create_retrieve_memory_node(mini_llm, embeddings, memory_repo))

    graph_builder.add_node("generation", create_generation_node(llm))

    # ---- 边 ----
    graph_builder.add_edge(START, "retrieve_memory")
    graph_builder.add_edge("retrieve_memory", "generation")
    graph_builder.add_edge("generation", END)

    compiled = graph_builder.compile()
    logger.info("✅ Chat graph compiled (START → retrieve_memory → generation → END)")
    return compiled
