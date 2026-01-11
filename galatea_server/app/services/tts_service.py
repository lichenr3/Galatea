"""TTS服务
无状态的TTS API调用层，通过HTTP调用TTS服务
"""
import httpx
import asyncio
import base64
from typing import AsyncGenerator, Tuple, Optional, TYPE_CHECKING
from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.unity_protocol import (
    UnityBaseMessage,
    UnityMessageType,
    AudioCompletePayload
)
from app.schemas.web_protocol import (
    WebServerMessage,
    WebServerMessageType,
    AudioChunkPayload
)
from app.utils.audio_utils import fix_wav_header
import time

if TYPE_CHECKING:
    from app.infrastructure.managers.character_registry import CharacterRegistry
    from app.infrastructure.managers.unity_connection import UnityConnectionManager
    from app.infrastructure.managers.web_connection import WebConnectionManager

logger = get_logger(__name__)


class TTSService:
    """
    TTS 服务（无状态）
    通过HTTP调用已启动的TTS服务（由TTSServer进程管理）
    """
    
    def __init__(self, character_registry: 'CharacterRegistry', unity_manager: Optional['UnityConnectionManager'] = None, web_manager: Optional['WebConnectionManager'] = None):
        self.base_url = f"http://{settings.TTS_API_HOST}:{settings.TTS_API_PORT}"
        self.timeout = 60.0
        self.character_registry = character_registry
        self.unity_manager = unity_manager
        self.web_manager = web_manager
        
        logger.info(f"🎤 TTS Service 初始化: {self.base_url}")
    
    async def synthesize_streaming(
        self, 
        text: str, 
        character_id: str = "yanagi"
    ) -> AsyncGenerator[Tuple[bytes, int], None]:
        """
        流式TTS合成
        
        Args:
            text: 要合成的文本（单个句子）
            character_id: 角色ID
        
        Yields:
            Tuple[audio_chunk: bytes, sample_rate: int]
        
        Raises:
            Exception: TTS服务错误
        """
        # 从 character_registry 获取角色配置
        character = self.character_registry.get_character(character_id)
        if not character:
            logger.error(f"❌ 角色不存在: {character_id}")
            raise Exception(f"角色不存在: {character_id}")
        
        voice_config = character.voice
        
        # 构建参考音频的完整路径
        # 配置文件中是相对路径如 "/audio/yanagi.wav"
        # 需要转换为 BASE_DIR/assets/audio/yanagi.wav
        ref_audio_path = voice_config.reference_audio
        if ref_audio_path.startswith("/"):
            ref_audio_path = str(settings.BASE_DIR / "app" / "assets" / ref_audio_path.lstrip("/"))
        
        params = {
            "text": text,
            "text_lang": voice_config.language,
            "ref_audio_path": ref_audio_path,
            "prompt_lang": voice_config.language,
            "streaming_mode": 1,  # 1=最佳质量流式
            "media_type": "wav",
            "batch_size": 1,
            "speed_factor": voice_config.speed,
            "temperature": 1.0,
            "top_p": 1.0,
            "top_k": 5,
        }
        
        # 如果提供了 prompt_text，则添加到参数中
        if voice_config.prompt_text:
            params["prompt_text"] = voice_config.prompt_text
        
        logger.debug(f"🎤 TTS请求参数: {params}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "GET", 
                    f"{self.base_url}/tts", 
                    params=params
                ) as response:
                    # 检查响应状态
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"❌ TTS服务错误 {response.status_code}: {error_text}")
                        raise Exception(f"TTS服务错误 {response.status_code}")
                    
                    sample_rate = 32000  # GPT-SoVITS默认采样率
                    chunk_count = 0
                    
                    # 流式读取音频块
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        if chunk:
                            chunk_count += 1
                            yield (chunk, sample_rate)
                    
                    logger.debug(f"✅ TTS完成: {text[:30]}... ({chunk_count} 个音频块)")
        
        except httpx.TimeoutException:
            logger.error(f"❌ TTS服务超时: {text[:30]}...")
            raise Exception("TTS服务超时")
        except Exception as e:
            logger.error(f"❌ TTS服务调用失败: {e}")
            raise
    
    async def process_queue(
        self,
        queue: asyncio.Queue, 
        character_id: str
    ):
        """
        后台处理TTS队列，并将音频流发送给Unity
        
        Args:
            queue: TTS任务队列
            character_id: 角色ID
        """
        while True:
            item = await queue.get()
            
            # 检查哨兵值（结束标记）
            if item is None:
                logger.info("✅ TTS队列处理完成")
                break
            
            sentence_index = item["index"]
            text = item["text"]
            
            logger.info(f"🎵 TTS [{sentence_index}]: {text[:30]}...")
            
            try:
                await self._process_single_sentence(sentence_index, text, character_id)
            
            except Exception as e:
                logger.error(f"❌ TTS失败 [{sentence_index}]: {e}", exc_info=True)
                # 继续处理队列中的其他任务，不中断整个流程
    
    async def _process_single_sentence(
        self,
        sentence_index: int,
        text: str,
        character_id: str
    ):
        """
        处理单个句子的TTS合成和音频传输（发送完整音频到Unity）
        
        Args:
            sentence_index: 句子索引
            text: 文本内容
            character_id: 角色ID
        """
        sample_rate = 32000  # 默认采样率
        
        # 收集完整音频数据
        audio_buffer = bytearray()
        
        logger.info(f"🎤 开始生成音频 [{sentence_index}]: {text[:30]}...")
        
        # 流式接收音频块并缓存到内存
        chunk_count = 0
        async for audio_chunk, sample_rate in self.synthesize_streaming(text, character_id):
            chunk_count += 1
            chunk_size = len(audio_chunk)
            audio_buffer.extend(audio_chunk)
            logger.debug(f"📦 收到音频块 {chunk_count}: {chunk_size} bytes")
        
        # 转换为 bytes
        complete_audio = bytes(audio_buffer)
        total_bytes = len(complete_audio)
        
        logger.info(f"✅ 音频生成完成 [{sentence_index}]: {total_bytes} bytes @ {sample_rate}Hz")
        
        # 修复 WAV header
        fixed_audio = fix_wav_header(complete_audio, sample_rate)
        fixed_total_bytes = len(fixed_audio)
        
        # Base64 编码（使用修复后的音频）
        audio_b64 = base64.b64encode(fixed_audio).decode('utf-8')
        
        # ✅ 优先发送音频到前端（立即播放）
        if self.web_manager and self.web_manager.has_active_client:
            duration = fixed_total_bytes / (sample_rate * 2)  # 16-bit = 2 bytes per sample
            
            web_audio_message = WebServerMessage(
                type=WebServerMessageType.AUDIO_CHUNK,
                data=AudioChunkPayload(
                    sentence_index=sentence_index,
                    audio_data=audio_b64,
                    sample_rate=sample_rate,
                    duration=duration
                ).model_dump(),
                timestamp=time.time()
            )
            await self.web_manager.broadcast(web_audio_message)
            logger.info(f"🔊 [优先] 音频已发送到前端 [{sentence_index}]: {duration:.2f}秒")
        
        # 发送完整音频到 Unity（用于口型同步）
        if self.unity_manager and self.unity_manager.has_active_client:
            complete_message = UnityBaseMessage(
                type=UnityMessageType.AUDIO_COMPLETE,
                data=AudioCompletePayload(
                    sentence_index=sentence_index,
                    text=text,
                    audio_data=audio_b64,
                    sample_rate=sample_rate,
                    total_bytes=fixed_total_bytes
                ).model_dump(),
                timestamp=time.time()
            )
            await self.unity_manager.broadcast(complete_message)
            logger.debug(f"📤 音频已发送到 Unity [{sentence_index}]")
        
        logger.info(f"✅ TTS 完成 [{sentence_index}]")

