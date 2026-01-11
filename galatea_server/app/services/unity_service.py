from app.core.container import unity_process
from app.schemas.common import UnifiedResponse
from app.schemas.unity_protocol import UnityActionResponse, UnityStatusResponse
from app.core.logger import get_logger

logger = get_logger(__name__)

def launch_unity_service() -> UnifiedResponse[UnityActionResponse]:
    """启动 Unity 客户端服务"""
    try:
        result = unity_process.start()
        
        # 无论成功与否，都返回 200，具体的业务成功状态由 data.success 决定
        # 如果是系统级错误（如异常），则在 except 中捕获
        
        if not result["success"]:
            logger.warning(f"⚠️ Unity 启动失败: {result['message']}")
            return UnifiedResponse.success(
                message="Unity 启动操作已执行（结果失败）",
                data=UnityActionResponse(**result)
            )
        
        logger.info(f"✅ Unity 启动成功 (PID: {result.get('pid')})")
        return UnifiedResponse.success(
            message="Unity 启动成功",
            data=UnityActionResponse(**result)
        )
        
    except Exception as e:
        logger.error(f"❌ Unity 启动服务异常: {e}", exc_info=True)
        # 这里返回 500，表示服务层发生了未预期的错误
        return UnifiedResponse(
            code=500, 
            message=f"Unity 启动服务异常: {str(e)}", 
            data=None
        )

def shutdown_unity_service() -> UnifiedResponse[UnityActionResponse]:
    """关闭 Unity 客户端服务"""
    try:
        result = unity_process.stop()
        
        if not result["success"]:
            logger.warning(f"⚠️ Unity 关闭失败: {result['message']}")
            return UnifiedResponse.success(
                message="Unity 关闭操作已执行（结果失败）",
                data=UnityActionResponse(**result)
            )
        
        logger.info("✅ Unity 关闭成功")
        return UnifiedResponse.success(
            message="Unity 关闭成功",
            data=UnityActionResponse(**result)
        )
        
    except Exception as e:
        logger.error(f"❌ Unity 关闭服务异常: {e}", exc_info=True)
        return UnifiedResponse(
            code=500, 
            message=f"Unity 关闭服务异常: {str(e)}", 
            data=None
        )

def get_unity_status_service() -> UnifiedResponse[UnityStatusResponse]:
    """获取 Unity 客户端状态服务"""
    try:
        status = unity_process.get_status()
        logger.debug(f"Unity status queried: {status}")
        return UnifiedResponse.success(
            message="获取 Unity 状态成功",
            data=UnityStatusResponse(**status)
        )
    except Exception as e:
        logger.error(f"❌ 获取 Unity 状态失败: {e}", exc_info=True)
        return UnifiedResponse(
            code=500,
            message=f"获取 Unity 状态失败: {str(e)}",
            data=None
        )
