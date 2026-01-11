"""Web 客户端专用协议"""
from enum import Enum
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# ==================== 1. Web → Server (上行请求) ====================

class WebClientMessageType(str, Enum):
    """前端发给后端的类型"""
    USER_MESSAGE = "user_message"      # 用户说话
    HEARTBEAT = "heartbeat"            # 心跳保活

# --- 上行载荷定义 (先定义 Payload) ---

class UserMessagePayload(BaseModel):
    """用户消息载荷"""
    content: str
    # 配合通讯录功能，告诉后端我在跟谁说话
    target_character_id: Optional[str] = None
    # 是否启用音频（控制 TTS 生成）
    enable_audio: bool = True 

# --- 上行消息定义 (后定义 Message) ---

class WebClientMessage(BaseModel):
    """上行消息基类"""
    type: WebClientMessageType
    # session_id 放在顶层，方便 Router 路由
    session_id: str 
    
    # ✨ 改造点：使用 Union 明确 data 的类型
    # Heartbeat 通常是空字典，所以加上 Dict[str, Any] 作为兜底，或者 Optional
    data: Union[UserMessagePayload, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="根据 type 不同，data 结构不同"
    )
    
    timestamp: float


# ==================== 2. Server → Web (下行推送) ====================

class WebServerMessageType(str, Enum):
    """后端推给前端的类型"""
    AI_TEXT_STREAM = "ai_text_stream" # 流式文本
    AI_STATUS = "ai_status"           # 状态变化
    HEARTBEAT = "heartbeat"             # 心跳保活
    ERROR = "error"                   # 报错
    AUDIO_CHUNK = "audio_chunk"       # 音频数据（前端播放）

# --- 下行载荷定义 (先定义 Payload) ---

class AITextStreamPayload(BaseModel):
    """AI 流式文本载荷"""
    text: str
    is_finish: bool
    message_id: str
    character_id: Optional[str] = None

class AIStatusPayload(BaseModel):
    """AI 状态载荷"""
    status: str  # "thinking" | "idle" | "listening"
    message: str = ""

class ErrorPayload(BaseModel):
    """错误信息载荷"""
    code: int  # 错误码（3位数）
    message: str
    details: Dict[str, Any] = {}

class AudioChunkPayload(BaseModel):
    """音频数据载荷（前端播放用）"""
    sentence_index: int              # 句子索引
    audio_data: str                  # Base64 编码的 WAV 数据
    sample_rate: int = 32000         # 采样率
    duration: float                  # 音频时长（秒）

# --- 下行消息定义 (后定义 Message) ---

class WebServerMessage(BaseModel):
    """下行消息基类"""
    type: WebServerMessageType
    
    # ✨ 改造点：强类型 Union
    # 这里的 data 必须是这几种 Payload 之一
    data: Union[AIStatusPayload, AITextStreamPayload, ErrorPayload, AudioChunkPayload, Dict[str, Any]] = Field(
        ..., 
        description="Payload 数据"
    )
    
    timestamp: float