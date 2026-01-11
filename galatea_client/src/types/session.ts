import type { ChatMessage } from './message';

// UI Model
export interface SessionInfo {
    sessionId: string;
    messageCount: number;
    preview?: string;
}

export interface ChatSession {
    sessionId: string;
    messages: ChatMessage[];
}

// API DTOs
export interface CreateSessionRequest {
    character_id: string;
}

export interface CreateSessionResponse {
    session_id: string;
    avatar_url: string;
}

export interface DeleteSessionRequest {
    session_id: string;
}

export interface ApiSessionInfo {
    session_id: string;
    message_count: number;
    preview?: string;
}
