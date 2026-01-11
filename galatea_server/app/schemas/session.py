from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class CreateSessionRequest(BaseModel):
    character_id: str = Field(..., description="角色 ID")
    language: str = Field("zh", description="会话语言 (zh/en)")

class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    avatar_url: str = Field(..., description="头像 URL")


# 通讯录相关 Schema
class SessionInfo(BaseModel):
    """单个会话信息"""
    session_id: str = Field(..., description="会话 ID")
    message_count: int = Field(..., description="消息数量（不含 system prompt）")
    preview: str = Field("", description="最后一条消息预览")

class CharacterContact(BaseModel):
    """单个角色的联系人信息"""
    character_id: str = Field(..., description="角色 ID")
    character_name: str = Field(..., description="角色名称")
    avatar_url: str = Field(..., description="头像 URL")
    sessions: List[SessionInfo] = Field(..., description="该角色下的所有会话（按最近活跃排序）")

class ContactsResponse(BaseModel):
    """通讯录响应"""
    contacts: List[CharacterContact] = Field(..., description="所有角色联系人（按最近交互排序）")


class ChatMessage(BaseModel):
    role: str = Field(..., description="角色 (system, user, assistant)")
    content: str = Field(..., description="消息内容")


class GetHistoryResponse(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    history: List[ChatMessage] = Field(..., description="聊天记录")


# 角色信息 Schema
class CharacterInfo(BaseModel):
    """角色完整信息（用于角色选择界面）"""
    id: str = Field(..., description="角色 ID")
    name: Dict[str, str] = Field(..., description="角色名称（多语言）")
    display_name: str = Field(..., description="角色显示名称（英文）")
    description: Dict[str, str] = Field(..., description="角色描述（多语言）")
    avatar_url: str = Field(..., description="头像 URL")
    tags: List[str] = Field(default_factory=list, description="角色标签")

