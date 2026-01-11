# app/core/error_handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions.base import BusinessException
from app.core.logger import get_logger

logger = get_logger(__name__)

def register_exception_handlers(app: FastAPI):
    
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """
        因为 DataNotFoundException 等都继承自 BusinessException，
        所以这一个函数就能捕获所有子类异常！
        """
        logger.error(f"业务异常: {exc.code} - {exc.message}", extra={
            "path": request.url.path,
            "method": request.method
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
            }
        )

    # 2. 捕获未知的系统级异常 (兜底)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"系统崩溃: {str(exc)}", exc_info=True, extra={
            "path": request.url.path
        })
        
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "系统内部错误，请联系管理员"
            }
        )
