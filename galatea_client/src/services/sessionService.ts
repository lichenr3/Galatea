import config from '../config';
import type { 
    CharacterContact,
    CharacterInfo,
    ApiCharacterInfo,
    ChatMessage,
    CreateSessionResponse,
    UnifiedResponse,
    ApiContactsResponse,
    ApiGetHistoryResponse
} from '../types';

// ==================== 接口响应类型 ====================
// Types imported from ../types


// API Response Types for Contacts
// Types imported from ../types


// API Response Types for History
// Types imported from ../types


// ==================== 工具函数 ====================

/**
 * 将后端返回的相对 URL 转换为完整 URL
 */
export const resolveAvatarUrl = (avatarUrl: string): string => {
    if (!avatarUrl) return '';
    
    // 如果已经是完整 URL，直接返回
    if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
        return avatarUrl;
    }
    
    // 拼接服务器地址
    return `${config.SERVER_URL}${avatarUrl}`;
};

// ==================== API 函数 ====================

/**
 * 创建新会话
 */
export const createSession = async (characterId: string, language: string = 'zh'): Promise<CreateSessionResponse> => {
    console.log('📡 发起创建会话请求:', { character_id: characterId, language });
    
    try {
        const response = await fetch(`${config.API_URL}/session/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                character_id: characterId,
                language: language
            }),
        });

        const result: UnifiedResponse<CreateSessionResponse> = await response.json();
        console.log('📨 收到服务器响应:', result);
        
        // 检查业务状态码
        if (result.code !== 200) {
            console.error('❌ 业务错误:', result);
            throw new Error(result.message || '创建会话失败');
        }
        
        // 检查 data 是否存在
        if (!result.data) {
            console.error('❌ 响应数据为空:', result);
            throw new Error('服务器返回的数据为空');
        }
        
        // 转换头像 URL 为完整路径
        const sessionData = result.data;
        const originalUrl = sessionData.avatar_url;
        sessionData.avatar_url = resolveAvatarUrl(sessionData.avatar_url);
        
        console.log('🖼️  头像 URL 转换:', {
            原始: originalUrl,
            转换后: sessionData.avatar_url
        });
        console.log('✅ 创建会话成功:', sessionData);
        
        return sessionData;
    } catch (error) {
        console.error('❌ 创建会话失败:', error);
        throw error;
    }
};

/**
 * 删除会话
 */
export const deleteSession = async (sessionId: string): Promise<void> => {
    console.log('🗑️ 发起删除会话请求:', { session_id: sessionId });
    
    try {
        const response = await fetch(`${config.API_URL}/session/delete/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const result: UnifiedResponse<null> = await response.json();
        
        if (result.code !== 200) {
            console.error('❌ 删除会话失败:', result);
            throw new Error(result.message || '删除会话失败');
        }
        
        console.log('✅ 删除会话成功');
    } catch (error) {
        console.error('❌ 删除会话请求异常:', error);
        throw error;
    }
};

/**
 * 获取可用角色列表（完整信息）
 */
export const getAvailableCharacters = async (language: string = 'zh'): Promise<CharacterInfo[]> => {
    console.log('📡 发起获取角色列表请求');
    
    try {
        const response = await fetch(`${config.API_URL}/session/characters`);
        const result: UnifiedResponse<ApiCharacterInfo[]> = await response.json();
        
        console.log('📨 收到角色列表响应:', result);
        
        if (result.code !== 200) {
            console.error('❌ 获取角色列表失败:', result);
            throw new Error(result.message || '获取角色列表失败');
        }
        
        // 转换 API 响应为前端模型
        const characters: CharacterInfo[] = (result.data || []).map(apiChar => ({
            id: apiChar.id,
            name: apiChar.name,
            displayName: apiChar.display_name,
            description: apiChar.description || { zh: '', en: '' },
            avatarUrl: resolveAvatarUrl(apiChar.avatar_url),
            tags: apiChar.tags || []
        }));
        
        console.log('✅ 获取角色列表成功:', characters);
        return characters;
    } catch (error) {
        console.error('❌ 获取角色列表异常:', error);
        // 降级方案：返回空数组
        return [];
    }
};

/**
 * 获取通讯录
 */
export const getContacts = async (language: string = 'zh'): Promise<CharacterContact[]> => {
    try {
        const response = await fetch(`${config.API_URL}/session/contacts?language=${language}`);
        const result: UnifiedResponse<ApiContactsResponse> = await response.json();
        
        if (result.code !== 200) {
            throw new Error(result.message || '获取通讯录失败');
        }

        return result.data.contacts.map(contact => ({
            characterId: contact.character_id,
            characterName: contact.character_name,
            avatarUrl: resolveAvatarUrl(contact.avatar_url),
            sessions: contact.sessions.map(session => ({
                sessionId: session.session_id,
                messageCount: session.message_count,
                preview: session.preview
            }))
        }));
    } catch (error) {
        console.error('❌ 获取通讯录失败:', error);
        throw error;
    }
};

/**
 * 获取会话历史记录
 */
export const getHistory = async (sessionId: string): Promise<ChatMessage[]> => {
    try {
        const response = await fetch(`${config.API_URL}/session/history/${sessionId}`);
        const result: UnifiedResponse<ApiGetHistoryResponse> = await response.json();

        if (result.code !== 200) {
            throw new Error(result.message || '获取历史记录失败');
        }

        return result.data.history.map((msg, index) => ({
            id: `${sessionId}-${index}-${Date.now()}`, // Generate a temporary ID
            role: msg.role === 'user' ? 'user' : 'ai',
            content: msg.content,
            timestamp: Date.now(), // We don't have timestamp in history yet, use current
            status: 'finished'
        }));
    } catch (error) {
        console.error('❌ 获取历史记录失败:', error);
        throw error;
    }
};

/**
 * 切换 TTS 模型
 */
export const switchTTSModel = async (characterId: string): Promise<boolean> => {
    console.log('🎤 发起 TTS 模型切换请求:', { character_id: characterId });
    
    try {
        const response = await fetch(`${config.API_URL}/tts/switch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ character_id: characterId }),
        });

        const result: UnifiedResponse<any> = await response.json();
        
        if (result.code !== 200) {
            console.error('❌ TTS 模型切换失败:', result);
            throw new Error(result.message || 'TTS 模型切换失败');
        }
        
        console.log('✅ TTS 模型切换成功:', result.data);
        return true;
    } catch (error) {
        console.error('❌ TTS 模型切换请求异常:', error);
        // 不抛出错误，只记录日志，避免影响用户体验
        return false;
    }
};

