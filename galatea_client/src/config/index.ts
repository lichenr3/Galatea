const config = {
    // WebSocket URL (用于实时通信)
    WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws/web',
    
    // API Base URL (用于 HTTP 请求，如创建会话)
    API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    
    // 后端服务器地址（用于拼接静态资源 URL）
    SERVER_URL: import.meta.env.VITE_SERVER_URL || 'http://localhost:8000',
    
    // App Info
    APP_TITLE: import.meta.env.VITE_APP_TITLE || 'AI Galatea',
    APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
    
    // 环境检查
    isDevelopment: import.meta.env.DEV,
    isProduction: import.meta.env.PROD,
} as const;

export default config;