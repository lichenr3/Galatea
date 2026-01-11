from typing import Any, Dict, Optional
from app.core.constants import ErrorCode, ERROR_MESSAGES

class GalateaException(Exception):
    """
    所有业务异常的基类
    """
    status_code: int = 400
    default_code: int = ErrorCode.INTERNAL_ERROR

    def __init__(
        self, 
        message: Optional[str] = None, 
        code: Optional[int] = None, 
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        self.code = code if code is not None else self.default_code
        self.message = message or ERROR_MESSAGES.get(self.code, "未知错误")
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }

class BusinessException(GalateaException):
    """基础业务异常"""
    default_code = ErrorCode.INTERNAL_ERROR

class InvalidDataException(BusinessException):
    """数据格式非法或校验失败"""
    default_code = ErrorCode.INVALID_DATA

class DataNotFoundException(BusinessException):
    """请求的数据或资源未找到"""
    status_code = 404
    default_code = ErrorCode.DATA_NOT_FOUND

class UnauthorizedException(BusinessException):
    """未经授权的访问"""
    status_code = 401
    default_code = ErrorCode.UNAUTHORIZED
