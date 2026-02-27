"""
Memory Service — 记忆提取

职责：
1. should_extract(): 按轮次判断是否需要触发记忆提取（每 5 轮对话提取一次）
2. extract_and_save_memories(): 从对话中提取事实/偏好/事件，去重后存入向量库
3. run_memory_extraction(): 组合 1+2 的完整异步流程（fire-and-forget）
"""
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.repositories.memory_repo import MemoryRepository
from app.core.logger import get_logger

logger = get_logger(__name__)

# 每隔多少轮对话触发一次记忆提取（1 轮 = 1 条 user + 1 条 assistant = 2 条消息）
EXTRACTION_INTERVAL_ROUNDS = 5

# ============================================================
# Prompt 模板
# ============================================================

EXTRACT_MEMORY_PROMPT = """你是记忆管理专家。分析角色「{character_name}」与用户的对话，提取值得长期记住的信息。

## 已有记忆
{existing_memories}

## 新对话内容
{conversation_text}

## 输出要求
以 JSON 格式输出：
{{
  "memories": [
    {{
      "action": "new",
      "text": "具体事实",
      "type": "fact 或 preference 或 event",
      "importance": 1到10的整数
    }},
    {{
      "action": "update",
      "target_id": 已有记忆的编号,
      "text": "更新后的事实",
      "type": "fact 或 preference 或 event",
      "importance": 1到10的整数
    }}
  ],
  "session_summary": "一句话概括这段对话"
}}

规则：
- "new": 全新信息，已有记忆中不存在
- "update": 已有记忆需要修正或补充（如"用户在学Python" -> "用户从Python转向学Rust"）
- 与已有记忆重复的信息直接忽略，不要输出
- importance: 个人身份信息=8, 明确偏好=7, 一般经历=5, 闲聊=忽略
- 没有值得记忆的内容时返回空 memories 数组
- 只输出 JSON，不要有其他内容"""


# ============================================================
# 轮次判断
# ============================================================

def should_extract(
    session_history: list[dict[str, str]],
    last_extracted_index: int,
) -> bool:
    """
    判断是否应触发记忆提取：自上次提取以来，新增的非系统消息
    达到 EXTRACTION_INTERVAL_ROUNDS 轮（每轮 2 条）时返回 True。

    Args:
        session_history: 完整会话历史（含 system prompt）
        last_extracted_index: 上次提取时 history 的位置

    Returns:
        True 表示已积累足够轮次，应触发记忆提取
    """
    new_messages = session_history[last_extracted_index:]
    non_system_count = sum(1 for m in new_messages if m["role"] != "system")
    needed = EXTRACTION_INTERVAL_ROUNDS * 2  # 5 轮 = 10 条消息
    if non_system_count >= needed:
        logger.info(f"轮次触发记忆提取: 新增 {non_system_count} 条非系统消息 (阈值 {needed})")
        return True
    logger.debug(f"轮次未达阈值: {non_system_count}/{needed}, 跳过记忆提取")
    return False


# ============================================================
# 记忆提取与存储
# ============================================================

def _format_messages_as_text(messages: list[dict[str, str]]) -> str:
    """将消息列表格式化为可读文本（排除 system prompt）"""
    lines = []
    for m in messages:
        if m["role"] == "system":
            continue
        role_label = "用户" if m["role"] == "user" else "角色"
        lines.append(f"{role_label}: {m['content']}")
    return "\n".join(lines)


def _format_existing_memories(memories: list) -> str:
    """将已有记忆格式化为带编号的列表"""
    if not memories:
        return "（暂无已有记忆）"
    lines = []
    for m in memories:
        text = m.summary or m.content
        lines.append(f"[{m.id}] ({m.memory_type}) {text}")
    return "\n".join(lines)


async def extract_and_save_memories(
    session_id: int,
    character_id: str,
    character_name: str,
    messages: list[dict[str, str]],
    memory_repo: MemoryRepository,
    llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings,
) -> int:
    """
    从对话片段中提取记忆并存入向量库。

    流程：
    1. 获取该角色已有的记忆（用于去重）
    2. 调用 LLM 提取新事实 + 判断需要更新的旧事实
    3. 对每条新/更新记忆做 embedding 后写入 DB

    Args:
        session_id: 会话 ID（用于追溯来源）
        character_id: 角色 ID
        character_name: 角色显示名称
        messages: 待提取的对话片段
        memory_repo: 记忆数据访问层
        llm: 用于提取的 LLM（可以是主 LLM 也可以是小模型）
        embeddings: 向量化模型

    Returns:
        本次提取保存/更新的记忆条数
    """
    conversation_text = _format_messages_as_text(messages)
    if not conversation_text.strip():
        return 0

    # 1. 获取已有记忆（用于去重）
    existing_memories = await memory_repo.get_by_character(character_id, limit=30)
    existing_text = _format_existing_memories(existing_memories)

    # 2. 调用 LLM 提取
    prompt = EXTRACT_MEMORY_PROMPT.format(
        character_name=character_name,
        existing_memories=existing_text,
        conversation_text=conversation_text,
    )

    try:
        response = await llm.ainvoke(prompt)
        raw = response.content.strip()

        # 清理可能的 markdown 代码块包裹
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]  # 去掉第一行 ```json
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        extracted = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"记忆提取 JSON 解析失败: {e}\n原始输出: {raw[:500]}")
        return 0
    except Exception as e:
        logger.error(f"记忆提取 LLM 调用失败: {e}", exc_info=True)
        return 0

    memories_data = extracted.get("memories", [])
    session_summary = extracted.get("session_summary", "")
    saved_count = 0

    # 建立已有记忆的 ID 索引（用于 update 操作）
    existing_by_id = {m.id: m for m in existing_memories}

    # 3. 逐条处理
    for item in memories_data:
        action = item.get("action", "new")
        text = item.get("text", "").strip()
        mem_type = item.get("type", "fact")
        importance = item.get("importance", 5)

        if not text:
            continue

        # 确保 importance 在合法范围内
        importance = max(1, min(10, int(importance)))

        try:
            # 生成 embedding
            embedding = await embeddings.aembed_query(text)

            if action == "update":
                target_id = item.get("target_id")
                if target_id and target_id in existing_by_id:
                    await memory_repo.update_memory(
                        memory_id=target_id,
                        content=text,
                        summary=text,
                        embedding=embedding,
                        importance=importance,
                    )
                    logger.debug(f"记忆更新: id={target_id}, text={text[:50]}")
                    saved_count += 1
                else:
                    # target_id 无效，降级为 new
                    action = "new"

            if action == "new":
                await memory_repo.save(
                    character_id=character_id,
                    session_id=session_id,
                    content=text,
                    summary=text,
                    embedding=embedding,
                    memory_type=mem_type,
                    importance=importance,
                )
                logger.debug(f"记忆新增: type={mem_type}, text={text[:50]}")
                saved_count += 1

        except Exception as e:
            logger.error(f"记忆保存失败 ({action}): {e}", exc_info=True)
            continue

    # 4. 保存会话摘要（如果有）
    if session_summary:
        try:
            summary_embedding = await embeddings.aembed_query(session_summary)
            await memory_repo.save(
                character_id=character_id,
                session_id=session_id,
                content=session_summary,
                summary=session_summary,
                embedding=summary_embedding,
                memory_type="conversation",
                importance=4,
            )
            saved_count += 1
        except Exception as e:
            logger.error(f"会话摘要保存失败: {e}", exc_info=True)

    logger.info(f"记忆提取完成: character={character_id}, session={session_id}, saved={saved_count}")
    return saved_count


# ============================================================
# 组合入口（fire-and-forget）
# ============================================================

async def run_memory_extraction(
    session_id: int,
    character_id: str,
    character_name: str,
    session_history: list[dict[str, str]],
    last_extracted_index: int,
    extract_llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings,
    memory_repo: MemoryRepository,
) -> int:
    """
    完整的异步记忆提取流程（设计为 asyncio.create_task 调用）。

    1. 按轮次判断是否达到提取阈值（每 5 轮对话提取一次）
    2. 如果达到，提取 [last_extracted_index : 当前] 范围的对话
    3. 返回新的 last_extracted_index（无论是否保存到记忆库）

    Args:
        session_history: 完整会话历史（含 system prompt）
        last_extracted_index: 上次提取时 history 的位置

    Returns:
        新的 last_extracted_index（调用方负责更新 ChatSession）
        如果未触发提取，返回原始 last_extracted_index
    """
    current_index = len(session_history)

    # 没有新消息，跳过
    if current_index <= last_extracted_index:
        return last_extracted_index

    try:
        # 1. 轮次判断（每 5 轮对话触发一次）
        if not should_extract(session_history, last_extracted_index):
            return last_extracted_index

        # 2. 提取范围：上次提取位置到当前位置
        segment = session_history[last_extracted_index:current_index]

        # 3. 执行提取
        saved = await extract_and_save_memories(
            session_id=session_id,
            character_id=character_id,
            character_name=character_name,
            messages=segment,
            memory_repo=memory_repo,
            llm=extract_llm,
            embeddings=embeddings,
        )

        if saved <= 0:
            logger.info(
                f"记忆提取完成但未保存: character={character_id}, session={session_id}"
            )
        return current_index

    except Exception as e:
        logger.error(f"run_memory_extraction 异常: {e}", exc_info=True)
        return last_extracted_index
