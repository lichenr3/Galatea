// ==================== Unity 服务类型 ====================
export interface UnityStatusResponse {
    running: boolean;
    pid: number | null;
}

export interface UnityActionResponse {
    success: boolean;
    message: string;
    pid?: number | null;
}
