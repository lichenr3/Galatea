export const WebMessageType = {
    // 发送
    USER_MESSAGE: "user_message",
    HEARTBEAT: "heartbeat",
    
    // 接收
    AI_TEXT_STREAM: "ai_text_stream",
    AI_STATUS: "ai_status",
    ERROR: "error",
    AUDIO_CHUNK: "audio_chunk"  // 新增：音频数据
} as const;

export type WebMessageType = typeof WebMessageType[keyof typeof WebMessageType];


// 2. 定义基础消息结构 (对应 Python 的 WebClientMessage/WebServerMessage)
export interface WebBaseMessage<T = any> {
  type: WebMessageType;
  session_id?: string; // 发送消息时需要带上
  data: T;
  timestamp: number;
}

// 3. 定义具体的数据载荷 (对应 Python 的 Payload classes)

// 用户发送的消息
export interface UserMessagePayload {
  content: string;
  target_character_id?: string;
  enable_audio?: boolean;  // 是否启用音频（默认 true）
}

// AI 流式返回的文本
export interface AITextStreamPayload {
  text: string;
  is_finish: boolean;
  message_id: string;
  character_id?: string;
}

// AI 的状态 (思考中/空闲)
export interface AIStatusPayload {
  status: "thinking" | "idle" | "listening" | "error";
  message: string;
}

// 错误信息
export interface ErrorPayload {
  code: number; // 改为 number (3位数错误码)
  message: string;
  details?: Record<string, any>;
}

// 音频数据载荷
export interface AudioChunkPayload {
  sentence_index: number;
  audio_data: string;  // Base64 编码的 WAV 数据
  sample_rate: number;
  duration: number;    // 音频时长（秒）
}
