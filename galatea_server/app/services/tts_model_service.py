"""TTS 模型切换服务"""
import httpx
from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.tts import SwitchTTSModelRequest, SwitchTTSModelResponse
from app.schemas.common import UnifiedResponse
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.utils.path_utils import resolve_file_path

logger = get_logger(__name__)


async def switch_tts_model_service(
    request: SwitchTTSModelRequest,
    character_registry: CharacterRegistry
) -> UnifiedResponse[SwitchTTSModelResponse]:
    """
    切换 TTS 模型服务
    
    根据角色 ID 获取对应的 GPT 和 SoVITS 模型路径，
    调用 GPT-SoVITS API 进行模型切换
    
    Args:
        request: 包含 character_id 的请求
        character_registry: 角色注册表
    
    Returns:
        UnifiedResponse[SwitchTTSModelResponse]
    """
    character_id = request.character_id
    
    try:
        # 1. 从 character_registry 获取角色配置
        if not character_registry.character_exists(character_id):
            logger.error(f"❌ 角色不存在: {character_id}")
            return UnifiedResponse(
                code=404, 
                message=f"角色 {character_id} 不存在", 
                data=None
            )
        
        character = character_registry.get_character(character_id)
        if not character or not character.voice:
            logger.error(f"❌ 角色配置非法: {character_id}")
            return UnifiedResponse(
                code=400, 
                message=f"角色 {character_id} 配置非法或缺少 voice 配置", 
                data=None
            )
        
        voice_config = character.voice
        
        # 2. 解析模型文件路径（从相对路径转换为绝对路径）
        gpt_model_relative = voice_config.gpt_model
        sovits_model_relative = voice_config.sovits_model
        
        gpt_model_path = resolve_file_path(gpt_model_relative)
        sovits_model_path = resolve_file_path(sovits_model_relative)
        
        logger.info(f"🎤 准备切换 TTS 模型:")
        logger.info(f"   角色: {character.name} ({character_id})")
        logger.info(f"   GPT 模型: {gpt_model_path}")
        logger.info(f"   SoVITS 模型: {sovits_model_path}")
        
        # 3. 调用 GPT-SoVITS API 切换模型
        base_url = f"http://{settings.TTS_API_HOST}:{settings.TTS_API_PORT}"
        timeout = 30.0
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 3.1 切换 GPT 模型
            logger.info(f"📡 调用 API: GET {base_url}/set_gpt_weights")
            gpt_response = await client.get(
                f"{base_url}/set_gpt_weights",
                params={"weights_path": gpt_model_path}
            )
            
            if gpt_response.status_code != 200:
                error_msg = f"GPT 模型切换失败: {gpt_response.status_code} - {gpt_response.text}"
                logger.error(f"❌ {error_msg}")
                return UnifiedResponse(
                    code=500,
                    message=error_msg,
                    data=None
                )
            
            logger.info(f"✅ GPT 模型切换成功")
            
            # 3.2 切换 SoVITS 模型
            logger.info(f"📡 调用 API: GET {base_url}/set_sovits_weights")
            sovits_response = await client.get(
                f"{base_url}/set_sovits_weights",
                params={"weights_path": sovits_model_path}
            )
            
            if sovits_response.status_code != 200:
                error_msg = f"SoVITS 模型切换失败: {sovits_response.status_code} - {sovits_response.text}"
                logger.error(f"❌ {error_msg}")
                return UnifiedResponse(
                    code=500,
                    message=error_msg,
                    data=None
                )
            
            logger.info(f"✅ SoVITS 模型切换成功")
        
        # 4. 返回成功响应
        response_data = SwitchTTSModelResponse(
            character_id=character_id,
            character_name=character.name,
            gpt_model_path=gpt_model_path,
            sovits_model_path=sovits_model_path,
            success=True,
            message=f"成功切换到 {character.name} 的 TTS 模型"
        )
        
        logger.info(f"🎉 TTS 模型切换完成: {character.name}")
        return UnifiedResponse.success(
            message=f"成功切换到 {character.name} 的 TTS 模型",
            data=response_data
        )
    
    except httpx.TimeoutException:
        error_msg = "TTS API 调用超时"
        logger.error(f"❌ {error_msg}")
        return UnifiedResponse(code=504, message=error_msg, data=None)
    
    except Exception as e:
        error_msg = f"切换 TTS 模型失败: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return UnifiedResponse(code=500, message=error_msg, data=None)

