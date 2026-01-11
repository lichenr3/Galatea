from .base import GalateaException
from app.core.constants import ErrorCode
from typing import Any, Dict, Optional

class LLMException(GalateaException):
    """LLM 服务基础异常"""
    default_code = ErrorCode.LLM_ERROR

class LLMProviderException(LLMException):
    """LLM 供应商 (OpenAI/Gemini等) 接口错误"""
    default_code = ErrorCode.LLM_PROVIDER_ERROR

class LLMTimeoutException(LLMException):
    """LLM 请求超时"""
    status_code = 504
    default_code = ErrorCode.LLM_TIMEOUT
