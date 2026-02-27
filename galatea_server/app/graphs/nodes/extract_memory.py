"""
Extract Memory Node — 记忆提取节点

在 LLM 生成回复后，判断是否需要提取记忆并存储。
每隔 CONVERSATION_TURNS_THRESHOLD 轮触发一次总结。
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from app.graphs.state import AgentState
from app.repositories.memory_repo import MemoryRepository
from app.core.logger import get_logger

logger = get_logger(__name__)

CONVERSATION_TURNS_THRESHOLD = 5


def create_extract_memory_node(
    llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings,
    memory_repo: MemoryRepository,
):
    """
    工厂函数：创建记忆提取节点。
    """

    async def extract_memory(state: AgentState, config: RunnableConfig) -> dict:
        """判断是否需要提取记忆，并执行提取"""
        character_id = config["configurable"].get("character_id", "")
        session_id_str = config["configurable"].get("session_id", "")
        
        if not character_id:
            logger.warning("extract_memory: character_id 未设置")
            return {"should_store_memory": False}

        conversation_turns = state.get("conversation_turns", 0)
        
        if conversation_turns == 0 or conversation_turns % CONVERSATION_TURNS_THRESHOLD != 0:
            return {"should_store_memory": False}

        messages = state["messages"]
        
        recent_messages = []
        for msg in messages[-11:]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                recent_messages.append(f"{role}: {msg.content}")
        
        if len(recent_messages) < 2:
            return {"should_store_memory": False}

        conversation_text = "\n".join(recent_messages[-10:])

        prompt = f"""你是一个角色的记忆管理系统。请分析以下对话，提取关于用户的重要信息。

对话内容：
{conversation_text}

请以 JSON 数组格式输出你观察到的关于用户的重要信息。每个元素格式如下：
{{
  "content": "具体信息内容",
  "type": "preference/fact/event",
  "importance": 1-10 的整数
}}

规则：
- 只提取与用户相关的信息
- importance >= 7 的信息才会被存储
- 如果没有重要信息，返回空数组 []
- content 最多 100 字

请直接输出 JSON，不要其他内容："""

        try:
            response = await llm.ainvoke([
                HumanMessage(content=prompt)
            ])
            
            import json
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            items = json.loads(content)
            
            if not isinstance(items, list) or len(items) == 0:
                logger.info(f"extract_memory: 无重要信息需要存储")
                return {"should_store_memory": False}

            session_id = int(session_id_str) if session_id_str else None
            
            for item in items:
                if item.get("importance", 0) >= 7:
                    summary = item.get("content", "")
                    embedding = await embeddings.aembed_query(summary)
                    
                    await memory_repo.save(
                        character_id=character_id,
                        session_id=session_id,
                        content=item.get("content", ""),
                        summary=summary,
                        embedding=embedding,
                        memory_type=item.get("type", "fact"),
                        importance=item.get("importance", 5),
                    )
            
            logger.info(f"extract_memory: 存储了 {len([i for i in items if i.get('importance', 0) >= 7])} 条记忆")
            
            return {"should_store_memory": True}

        except Exception as e:
            logger.error(f"extract_memory 失败: {e}", exc_info=True)
            return {"should_store_memory": False}

    return extract_memory
