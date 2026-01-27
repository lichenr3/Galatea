"""
Agent 图构建

使用 LangGraph 构建 ReAct 风格的 Agent。
"""
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.agents.nodes import chat_node, respond_node
from app.agents.tools import get_all_tools
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def _should_use_tools(state: AgentState) -> str:
    """
    路由函数：判断是否需要调用工具
    
    检查 LLM 返回的最后一条消息是否包含工具调用请求。
    
    Returns:
        "tools" - 需要调用工具
        "respond" - 直接响应
    """
    messages = state["messages"]
    if not messages:
        return "respond"
    
    last_message = messages[-1]
    
    # 检查是否有工具调用
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "respond"


def create_chat_agent(checkpointer=None):
    """
    创建聊天 Agent（ReAct 风格）
    
    流程:
    1. START → chat: 调用 LLM
    2. chat → router: 判断是否需要工具
       - 需要工具 → tools → chat（循环）
       - 不需要 → respond → END
    
    Args:
        checkpointer: LangGraph Checkpointer，用于状态持久化
                     None 表示使用内存（开发模式）
    
    Returns:
        编译后的 LangGraph Agent
    """
    tools = get_all_tools()
    
    # 创建 LLM 并绑定工具
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        streaming=True,
        temperature=0.7
    )
    
    # 如果有工具，绑定到 LLM
    if tools:
        llm = llm.bind_tools(tools)
        logger.info(f"🔧 已绑定 {len(tools)} 个工具到 LLM")
    
    # 构建图
    graph = StateGraph(AgentState)
    
    # 添加节点
    # chat_node 需要 llm 参数，使用 lambda 包装
    graph.add_node("chat", lambda state: chat_node(state, llm))
    graph.add_node("respond", respond_node)
    
    # 如果有工具，添加工具节点
    if tools:
        graph.add_node("tools", ToolNode(tools))
    
    # 添加边
    graph.add_edge(START, "chat")
    
    if tools:
        # 有工具时：chat → 条件路由
        graph.add_conditional_edges("chat", _should_use_tools, {
            "tools": "tools",
            "respond": "respond"
        })
        # 工具执行后回到 chat 继续推理
        graph.add_edge("tools", "chat")
    else:
        # 无工具时：chat → respond
        graph.add_edge("chat", "respond")
    
    graph.add_edge("respond", END)
    
    # 编译（使用提供的 checkpointer 或默认内存）
    if checkpointer is None:
        checkpointer = MemorySaver()
        logger.info("📝 使用内存 Checkpointer（开发模式）")
    
    compiled = graph.compile(checkpointer=checkpointer)
    logger.info("✅ Chat Agent 编译完成")
    
    return compiled


# 创建默认 Agent 实例（使用内存 Checkpointer）
# 生产环境应使用 SQLite Checkpointer
chat_agent = create_chat_agent()
