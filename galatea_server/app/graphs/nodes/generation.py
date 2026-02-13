"""
Generation Node — LLM 对话生成

当前为最基础的单轮生成节点。
后续扩展：可加入 tool_calling、structured output 等能力。
"""
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from app.graphs.state import AgentState


def create_generation_node(llm: ChatOpenAI):
    """
    工厂函数：创建绑定到指定 LLM 的生成节点。

    通过闭包捕获 llm 实例，使节点函数签名符合 LangGraph 要求。
    """

    async def generation(state: AgentState, config: RunnableConfig) -> dict:
        """调用 LLM 生成回复，返回增量 messages 更新。"""
        response = await llm.ainvoke(state["messages"], config)
        return {"messages": [response]}

    return generation
