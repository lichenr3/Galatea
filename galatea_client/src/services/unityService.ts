import config from '../config';
import type { UnityActionResponse, UnityStatusResponse } from '../types';

// ==================== Unity 控制 API ====================

/**
 * 获取 Unity 进程状态
 */
export const getUnityStatus = async (): Promise<UnityStatusResponse> => {
    try {
        const response = await fetch(`${config.API_URL}/unity/status`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const json = await response.json();
        return json.data; // 返回 UnifiedResponse.data
    } catch (error) {
        console.error('❌ 获取 Unity 状态失败:', error);
        throw error;
    }
};

/**
 * 启动 Unity 客户端
 * @param characterId 要加载的角色ID（可选，后端会在Unity连接后自动加载）
 */
export const launchUnity = async (characterId?: string): Promise<UnityActionResponse> => {
    try {
        console.log('🚀 发起启动 Unity 请求', characterId ? `(角色: ${characterId})` : '');

        const response = await fetch(`${config.API_URL}/unity/launch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                character_id: characterId || null,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const json = await response.json();
        console.log('📨 Unity 启动响应:', json);

        return json.data; // 返回 UnifiedResponse.data
    } catch (error) {
        console.error('❌ 启动 Unity 请求失败:', error);
        throw error;
    }
};

/**
 * 切换 Unity 中显示的角色
 * @param characterId 要切换到的角色 ID
 */
export const switchCharacter = async (characterId: string): Promise<boolean> => {
    try {
        console.log('🎭 发起切换角色请求:', characterId);

        const response = await fetch(`${config.API_URL}/unity/switch-character`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                character_id: characterId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const json = await response.json();
        console.log('📨 切换角色响应:', json);

        return json.data; // 返回 UnifiedResponse.data (boolean)
    } catch (error) {
        console.error('❌ 切换角色请求失败:', error);
        throw error;
    }
};

/**
 * 关闭 Unity 客户端
 */
export const shutdownUnity = async (): Promise<UnityActionResponse> => {
    try {
        console.log('🛑 发起关闭 Unity 请求');

        const response = await fetch(`${config.API_URL}/unity/shutdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const json = await response.json();
        console.log('📨 Unity 关闭响应:', json);

        return json.data; // 返回 UnifiedResponse.data
    } catch (error) {
        console.error('❌ 关闭 Unity 请求失败:', error);
        throw error;
    }
};
