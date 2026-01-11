"""TTS 模型切换相关的 Schema"""
from pydantic import BaseModel
from typing import Optional


class SwitchTTSModelRequest(BaseModel):
    """切换 TTS 模型请求"""
    character_id: str


class SwitchTTSModelResponse(BaseModel):
    """切换 TTS 模型响应"""
    character_id: str
    character_name: str
    gpt_model_path: str
    sovits_model_path: str
    success: bool
    message: str

