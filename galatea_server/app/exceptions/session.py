from .base import GalateaException
from app.core.constants import ErrorCode
from typing import Any, Dict, Optional

class SessionException(GalateaException):
    """会话相关基础异常"""
    default_code = ErrorCode.SESSION_ERROR

class SessionNotFoundException(SessionException):
    """找不到指定的会话"""
    status_code = 404
    default_code = ErrorCode.SESSION_NOT_FOUND

class SessionExpiredException(SessionException):
    """会话已过期"""
    status_code = 401
    default_code = ErrorCode.SESSION_EXPIRED
