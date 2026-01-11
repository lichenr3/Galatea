"""TTS 模型切换相关的 API 端点"""
from fastapi import APIRouter, Depends
from app.schemas.tts import SwitchTTSModelRequest, SwitchTTSModelResponse
from app.schemas.common import UnifiedResponse
from app.services.tts_model_service import switch_tts_model_service
from app.api.deps import get_character_registry
from app.infrastructure.managers.character_registry import CharacterRegistry

router = APIRouter()


@router.post("/switch", response_model=UnifiedResponse[SwitchTTSModelResponse])
async def switch_tts_model_endpoint(
    request: SwitchTTSModelRequest,
    character_registry: CharacterRegistry = Depends(get_character_registry)
):
    """
    切换 TTS 模型
    
    根据角色 ID 切换 GPT-SoVITS 的模型权重文件
    
    **调用时机**：
    - 用户创建新会话时（如果角色与当前模型不同）
    - 用户切换到不同角色的会话时
    
    **Args**:
    - character_id: 角色 ID（如 "yanagi"）
    
    **Returns**:
    - UnifiedResponse[SwitchTTSModelResponse]: 包含切换结果和模型路径信息
    
    **Example**:
    ```json
    POST /api/v1/tts/switch
    {
        "character_id": "yanagi"
    }
    ```
    
    **Response**:
    ```json
    {
        "code": 200,
        "message": "成功切换到 月城柳 的 TTS 模型",
        "data": {
            "character_id": "yanagi",
            "character_name": "月城柳",
            "gpt_model_path": "/path/to/gpt_weights/柳-e10.ckpt",
            "sovits_model_path": "/path/to/sovits_weights/柳_e10_s590_l32.pth",
            "success": true,
            "message": "成功切换到 月城柳 的 TTS 模型"
        }
    }
    ```
    """
    return await switch_tts_model_service(request, character_registry)

