"""Unity 客户端管理 API 端点

提供 Unity 客户端进程的启动、关闭和状态查询功能
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.logger import get_logger
from app.schemas.common import UnifiedResponse
from app.schemas.unity_protocol import UnityActionResponse, UnityStatusResponse
from app.schemas.unity import LaunchUnityRequest, SwitchCharacterRequest
from app.services.unity_service import launch_unity_service, shutdown_unity_service, get_unity_status_service
from app.api.deps import get_unity_manager, get_unity_process
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.infrastructure.processes.unity_process import UnityProcess

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status", response_model=UnifiedResponse[UnityStatusResponse])
async def get_unity_status(
    unity_process: UnityProcess = Depends(get_unity_process)
):
    """获取 Unity 进程状态
    
    Returns:
        UnifiedResponse[UnityStatusResponse]: Unity 运行状态信息
    """
    try:
        return get_unity_status_service(unity_process)
    except Exception as e:
        raise e


@router.post("/launch", response_model=UnifiedResponse[UnityActionResponse])
async def launch_unity(
    request: LaunchUnityRequest = LaunchUnityRequest(),
    unity_manager: UnityConnectionManager = Depends(get_unity_manager),
    unity_process: UnityProcess = Depends(get_unity_process),
):
    """启动 Unity 客户端
    
    Args:
        request: 启动请求，可选包含要加载的角色ID
        unity_manager: Unity连接管理器
        
    Returns:
        UnifiedResponse[UnityActionResponse]: 启动操作结果
        
    Raises:
        HTTPException: 如果启动失败
    """
    character_id = request.character_id
    
    if character_id:
        logger.info(f"🔵 Received request to launch Unity with character: {character_id}")
        # 保存待加载的角色ID，Unity连接后自动发送
        unity_manager.pending_character_id = character_id
        logger.info(f"💾 已保存待加载角色: {character_id}")
    else:
        logger.info("🔵 Received request to launch Unity (no character specified)")
    
    try:
        result = launch_unity_service(unity_process)
        return result
    except Exception as e:
        raise e


@router.post("/shutdown", response_model=UnifiedResponse[UnityActionResponse])
async def shutdown_unity(
    unity_process: UnityProcess = Depends(get_unity_process)
):
    """关闭 Unity 客户端
    
    Returns:
        UnifiedResponse[UnityActionResponse]: 关闭操作结果
    """
    logger.info("🔴 Received request to shutdown Unity")
    try:
        return shutdown_unity_service(unity_process)
    except Exception as e:
        raise e


@router.post("/switch-character", response_model=UnifiedResponse[bool])
async def switch_character(
    request: SwitchCharacterRequest,
    unity_manager: UnityConnectionManager = Depends(get_unity_manager)
):
    """切换 Unity 中显示的角色（独立接口）
    
    Args:
        request: 包含要切换到的角色 ID
        
    Returns:
        UnifiedResponse[bool]: 切换操作结果
    """
    logger.info(f"🎭 Received request to switch character to: {request.character_id}")
    try:
        await unity_manager.notify_character_switch(request.character_id)
        return UnifiedResponse.success(
            message=f"已发送切换角色指令: {request.character_id}",
            data=True
        )
    except Exception as e:
        logger.error(f"❌ 切换角色失败: {e}", exc_info=True)
        return UnifiedResponse(
            code=500,
            message=f"切换角色失败: {str(e)}",
            data=False
        )
