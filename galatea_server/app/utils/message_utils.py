"""
消息格式转换工具
"""
from typing import Dict, List
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


def convert_dict_messages_to_langchain(dict_messages: List[Dict[str, str]]) -> list[BaseMessage]:
    """
    将 dict 格式的消息列表转为 langchain Message 对象。

    Args:
        dict_messages: 字典列表，每个字典包含 "role" 和 "content" 键

    Returns:
        langchain BaseMessage 列表
    """
    messages = []
    for msg in dict_messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages
