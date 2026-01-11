"""
LLM 服务
无状态的 API 调用层，不保存会话历史
"""
from openai import AsyncOpenAI
from app.core.config import settings
from typing import AsyncGenerator, List, Dict
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    LLM API 调用服务（无状态）
    不保存对话历史，历史由 SessionService 管理
    """
    
    def __init__(self):
        # 打印配置信息
        logger.info(f"🧠 LLM Service 初始化:")
        logger.info(f"   - Model: {settings.LLM_MODEL}")

        # 初始化 OpenAI 客户端
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = settings.LLM_MODEL

    async def chat_stream(
        self, 
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        流式对话（无状态）
        
        Args:
            messages: 完整的消息历史（包括 system prompt）
            temperature: 温度参数（0.7 适合角色扮演）
            
        Yields:
            LLM 生成的文本片段
        """
        try:
            logger.debug(f"🧠 发送请求到 LLM (消息数: {len(messages)})")
            
            # 调用 LLM API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=temperature
            )

            logger.debug("🧠 LLM 连接建立，开始接收数据...")

            # 流式返回
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content

            logger.debug("✅ LLM 响应完成")

        except Exception as e:
            logger.error(f"❌ LLM 调用错误: {e}", exc_info=True)
            yield f"[系统错误: {str(e)}]"


# 单例导出
llm_service = LLMService()