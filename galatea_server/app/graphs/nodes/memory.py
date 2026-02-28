"""
Memory Node — 记忆检索节点

在 LLM 生成回复前，根据用户最新消息检索相关的历史记忆，
将结果写入 state.memory_context 供 generation 节点注入 system prompt。
"""
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.graphs.state import AgentState
from app.repositories.memory_repo import MemoryRepository

from app.core.logger import get_logger

logger = get_logger(__name__)


def create_retrieve_memory_node(
    mini_llm: ChatOpenAI,
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

        # Extract last 3 turns of conversation
        recent_messages = []
        for m in state["messages"][-6:]:
            if isinstance(m, HumanMessage):
                recent_messages.append(f"User: {m.content}")
            elif isinstance(m, AIMessage):
                recent_messages.append(f"AI: {m.content}")

        conversation_history = "\n".join(recent_messages)

        user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
        if not user_messages:
            return {"memory_context": ""}

        # Rewrite query to make it context-independent and optimized for vector search
        rewrite_prompt = f"""You are an expert at optimizing search queries for a vector database.
The user is talking to an AI character. 
Here is the recent conversation history:
{conversation_history}

Please rewrite the user's latest query to be a standalone, highly descriptive search query that can be used to search for relevant long-term memories in the vector database.
- If the user uses pronouns (e.g., "he", "it"), replace them with what they refer to.
- If the user's latest query is a simple agreement or meaningless chatter (e.g., "ok", "yes", "haha"), reply with exactly "SKIP_SEARCH"
- Only output the rewritten query string, nothing else.

Latest user query: {user_messages[-1].content}
Rewritten query:"""

        try:
            rewrite_response = await mini_llm.ainvoke(rewrite_prompt)
            rewritten_query = rewrite_response.content.strip()

            if rewritten_query == "SKIP_SEARCH" or not rewritten_query:
                logger.debug("retrieve_memory: Query rewrite returned SKIP_SEARCH, skipping retrieval.")
                return {"memory_context": ""}

            logger.info(f"retrieve_memory: Rewrote query -> '{rewritten_query}'")
            query_embedding = await embeddings.aembed_query(rewritten_query)

            memories = await memory_repo.search_similar(
                character_id=character_id,
                query_embedding=query_embedding,
                top_k=5,
                min_importance=3,
                max_distance=0.45,  # Add a reasonable threshold for cosine distance
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
