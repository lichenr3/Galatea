"""Unity 相关的请求/响应 Schema"""
from pydantic import BaseModel
from typing import Optional


class LaunchUnityRequest(BaseModel):
    """启动 Unity 请求"""
    character_id: Optional[str] = None  # 要显示的角色 ID
    

class SwitchCharacterRequest(BaseModel):
    """切换角色请求"""
    character_id: str  # 要切换到的角色 ID

