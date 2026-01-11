from enum import IntEnum

class ErrorCode(IntEnum):
    """
    错误码定义（3位数）
    - 1xx: 通用/基础错误
    - 2xx: 会话相关错误
    - 3xx: LLM 相关错误
    - 4xx: TTS 相关错误
    """
    
    # --- 通用错误 (100-199) ---
    INTERNAL_ERROR = 100
    INVALID_DATA = 101
    DATA_NOT_FOUND = 102
    UNAUTHORIZED = 103
    
    # --- 会话错误 (200-299) ---
    SESSION_ERROR = 200
    SESSION_NOT_FOUND = 201
    SESSION_EXPIRED = 202
    
    # --- LLM 错误 (300-399) ---
    LLM_ERROR = 300
    LLM_PROVIDER_ERROR = 301
    LLM_TIMEOUT = 302
    
    # --- TTS 错误 (400-499) ---
    TTS_ERROR = 400
    TTS_PROCESS_ERROR = 401
    TTS_AUDIO_GEN_ERROR = 402

# 错误码对应的默认消息
ERROR_MESSAGES = {
    ErrorCode.INTERNAL_ERROR: "系统内部错误",
    ErrorCode.INVALID_DATA: "数据格式非法或校验失败",
    ErrorCode.DATA_NOT_FOUND: "请求的数据或资源未找到",
    ErrorCode.UNAUTHORIZED: "未经授权的访问",
    
    ErrorCode.SESSION_ERROR: "会话异常",
    ErrorCode.SESSION_NOT_FOUND: "会话不存在",
    ErrorCode.SESSION_EXPIRED: "会话已过期",
    
    ErrorCode.LLM_ERROR: "大模型服务异常",
    ErrorCode.LLM_PROVIDER_ERROR: "大模型供应商接口错误",
    ErrorCode.LLM_TIMEOUT: "大模型请求超时",
    
    ErrorCode.TTS_ERROR: "语音合成服务异常",
    ErrorCode.TTS_PROCESS_ERROR: "TTS 子进程启动或管理失败",
    ErrorCode.TTS_AUDIO_GEN_ERROR: "音频生成失败",
}
