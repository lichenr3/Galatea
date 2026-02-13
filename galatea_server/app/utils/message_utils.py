"""
消息格式转换工具
"""
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage


def convert_db_messages_to_langchain(db_messages) -> list[BaseMessage]:
    """
    将 DBMessage 列表转为 langchain Message 对象。

    Args:
        db_messages: DBMessage 对象列表（需有 .role 和 .content 属性）

    Returns:
        langchain BaseMessage 列表
    """
    messages = []
    for msg in db_messages:
        if msg.role == "system":
            messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
    return messages
