import type { SessionInfo, ApiSessionInfo } from './session';

// UI Model - 角色联系人（用于会话列表）
export interface CharacterContact {
    characterId: string;
    characterName: string;
    avatarUrl: string;
    sessions: SessionInfo[];
}

// UI Model - 角色完整信息（用于角色选择界面）
export interface CharacterInfo {
    id: string;
    name: {
        zh: string;
        en: string;
    };
    displayName: string;
    description: {
        zh: string;
        en: string;
    };
    avatarUrl: string;
    tags: string[];
}

// API DTOs
export interface ApiCharacterContact {
    character_id: string;
    character_name: string;
    avatar_url: string;
    sessions: ApiSessionInfo[];
}

export interface ApiContactsResponse {
    contacts: ApiCharacterContact[];
}

export interface ApiCharacterInfo {
    id: string;
    name: {
        zh: string;
        en: string;
    };
    display_name: string;
    description: {
        zh: string;
        en: string;
    };
    avatar_url: string;
    tags: string[];
}

