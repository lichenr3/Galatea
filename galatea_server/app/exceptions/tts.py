from .base import GalateaException
from app.core.constants import ErrorCode
from typing import Any, Dict, Optional

class TTSException(GalateaException):
    """TTS 服务基础异常"""
    default_code = ErrorCode.TTS_ERROR

class TTSProcessException(TTSException):
    """TTS 子进程管理错误"""
    default_code = ErrorCode.TTS_PROCESS_ERROR

class TTSAudioGenException(TTSException):
    """TTS 音频生成失败"""
    default_code = ErrorCode.TTS_AUDIO_GEN_ERROR
