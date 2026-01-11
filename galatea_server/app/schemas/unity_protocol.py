"""Unity 客户端专用协议"""
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class UnityMessageType(str, Enum):
    """Unity 客户端消息类型"""
    # Server → Unity
    PLAY_ANIMATION = "play_animation"
    SET_EXPRESSION = "set_expression"
    SPEAK = "speak"
    IDLE = "idle"
    SWITCH_CHARACTER = "switch_character"  # 🆕 切换角色
    
    # Server → Unity (音频)
    AUDIO_START = "audio_start"      # 音频流开始（已废弃）
    AUDIO_CHUNK = "audio_chunk"      # 音频数据块（已废弃）
    AUDIO_END = "audio_end"          # 音频流结束（已废弃）
    AUDIO_COMPLETE = "audio_complete"  # 完整音频（推荐）
    
    # Unity → Server (反馈)
    ANIMATION_COMPLETE = "animation_complete"
    STATE_UPDATE = "state_update"
    HEARTBEAT = "heartbeat"


class UnityActionResponse(BaseModel):
    """Unity 操作响应"""
    success: bool
    message: str
    pid: int | None = None


class UnityStatusResponse(BaseModel):
    """Unity 状态响应"""
    running: bool
    pid: int | None


class UnityBaseMessage(BaseModel):
    """Unity 消息基础结构"""
    type: UnityMessageType
    data: Dict[str, Any] = {}
    timestamp: float


# ==================== Server → Unity 指令 ====================

class PlayAnimationPayload(BaseModel):
    """播放动画载荷"""
    animation_name: str
    transition_duration: float = 0.3
    loop: bool = False


class SetExpressionPayload(BaseModel):
    """设置表情载荷"""
    expression: str  # "happy", "sad", "angry", "neutral", etc.
    intensity: float = 1.0  # 0.0 ~ 1.0


class SpeakPayload(BaseModel):
    """说话指令载荷"""
    text: str  # 完整的 AI 回复文本
    emotion: str = "neutral"
    duration: Optional[float] = None


class IdlePayload(BaseModel):
    """待机指令载荷"""
    idle_type: str = "normal"  # "normal", "bored", "excited", etc.


class SwitchCharacterPayload(BaseModel):
    """切换角色载荷"""
    character_id: str  # 角色ID，如 "yanagi", "SilverWolf"


# ==================== Unity → Server 反馈 ====================

class AnimationCompletePayload(BaseModel):
    """动画完成反馈"""
    animation_name: str
    success: bool
    error_message: Optional[str] = None


class StateUpdatePayload(BaseModel):
    """状态更新反馈"""
    current_animation: str
    current_expression: str
    is_busy: bool


# ==================== 音频传输载荷 ====================

class AudioStartPayload(BaseModel):
    """音频流开始标记"""
    sentence_index: int              # 句子索引（从0开始）
    text: str                        # 原文本内容
    sample_rate: int = 32000         # 采样率
    format: str = "wav"              # 音频格式


class AudioChunkPayload(BaseModel):
    """音频数据块"""
    sentence_index: int              # 句子索引
    chunk_index: int                 # 音频块索引（从0开始）
    audio_data: str                  # Base64编码的音频数据
    sample_rate: int                 # 采样率
    chunk_size: int                  # 原始字节数


class AudioEndPayload(BaseModel):
    """音频流结束标记"""
    sentence_index: int              # 句子索引
    total_chunks: int                # 总音频块数
    total_bytes: int                 # 总字节数


class AudioCompletePayload(BaseModel):
    """完整音频数据（推荐使用）"""
    sentence_index: int              # 句子索引（从0开始）
    text: str                        # 原文本内容
    audio_data: str                  # Base64编码的完整音频数据（WAV格式）
    sample_rate: int = 32000         # 采样率
    total_bytes: int                 # 音频字节数

