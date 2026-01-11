// UI Model
export interface ChatMessage {
    id: string;
    role: 'user' | 'ai';
    content: string;
    timestamp: number;
    status?: 'streaming' | 'finished';
}

// API DTOs
export interface ApiChatMessage {
    role: string;
    content: string;
}

export interface ApiGetHistoryResponse {
    session_id: string;
    history: ApiChatMessage[];
}
