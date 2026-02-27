"""
Memory Node — 记忆检索节点

在 LLM 生成回复前，根据用户最新消息检索相关的历史记忆，
将结果写入 state.memory_context 供 generation 节点注入 system prompt。
"""
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from app.graphs.state import AgentState
from app.repositories.memory_repo import MemoryRepository
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_retrieve_memory_node(
    embeddings: OpenAIEmbeddings,
    memory_repo: MemoryRepository,
):
    """
    工厂函数：创建绑定到 embedding 模型和 memory_repo 的检索节点。

    通过 config["configurable"]["character_id"] 获取角色 ID。
    """

    async def retrieve_memory(state: AgentState, config: RunnableConfig) -> dict:
        """检索与当前用户消息相关的历史记忆"""
        character_id = config["configurable"].get("character_id", "")
        if not character_id:
            logger.warning("retrieve_memory: character_id 未设置，跳过记忆检索")
            return {"memory_context": ""}

        user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
        if not user_messages:
            return {"memory_context": ""}

        query = user_messages[-1].content
        if not query or not query.strip():
            return {"memory_context": ""}

        try:
            query_embedding = await embeddings.aembed_query(query)

            memories = await memory_repo.search_similar(
                character_id=character_id,
                query_embedding=query_embedding,
                top_k=5,
                min_importance=3,
            )

            if not memories:
                logger.debug(f"retrieve_memory: 未找到相关记忆 (character={character_id})")
                return {"memory_context": ""}

            await memory_repo.update_last_accessed([m.id for m in memories])

            lines = []
            for m in memories:
                text = m.summary or m.content
                lines.append(f"- {text}")

            context = "你记得以下关于用户的信息：\n" + "\n".join(lines)
            logger.info(f"retrieve_memory: 召回 {len(memories)} 条记忆 (character={character_id})")
            return {"memory_context": context}

        except Exception as e:
            logger.error(f"retrieve_memory 失败: {e}", exc_info=True)
            return {"memory_context": ""}

    return retrieve_memory
