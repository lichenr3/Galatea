export const translations = {
  zh: {
    // Header
    status_thinking: '正在思考...',
    status_online: '在线',
    status_offline: '连接断开',
    
    // Tooltips
    tooltip_refresh: '刷新',
    tooltip_unity: 'Unity 控制',
    tooltip_audio: '音频开关',
    tooltip_pet_mode: '桌宠模式',
    tooltip_minimize: '收起聊天框',
    tooltip_send: '发送',
    
    // Contact List
    new_chat: '开启新会话',
    no_conversations: '暂无会话记录',
    delete_session: '删除会话',
    confirm_delete: '确定要删除这个会话吗？',
    new_conversation_preview: '新的对话',
    
    // Add Contact Modal
    modal_title: '选择对话角色',
    loading: '加载中...',
    start_new_chat: '开始新的对话',
    cancel: '取消',
    confirm: '开始对话',
    
    // Input
    input_placeholder: '和你的桌宠聊聊天...',
    input_placeholder_disabled: '请先选择一个角色开始会话...',
    
    // Characters
    char_yanagi_name: '月城柳',
    char_yanagi_desc: '游戏《绝区零》中的角色',
    
    // Language
    lang_toggle: 'English'
  },
  en: {
    // Header
    status_thinking: 'Thinking...',
    status_online: 'Online',
    status_offline: 'Disconnected',
    
    // Tooltips
    tooltip_refresh: 'Refresh',
    tooltip_unity: 'Unity Control',
    tooltip_audio: 'Audio Toggle',
    tooltip_pet_mode: 'Pet Mode',
    tooltip_minimize: 'Minimize',
    tooltip_send: 'Send',
    
    // Contact List
    new_chat: 'New chat',
    no_conversations: 'No conversations',
    delete_session: 'Delete Session',
    confirm_delete: 'Are you sure you want to delete this session?',
    new_conversation_preview: 'New conversation',
    
    // Add Contact Modal
    modal_title: 'Select Character',
    loading: 'Loading...',
    start_new_chat: 'Start a new chat',
    cancel: 'Cancel',
    confirm: 'Confirm',
    
    // Input
    input_placeholder: 'Chat with your pet...',
    input_placeholder_disabled: 'Please select a character first...',
    
    // Characters
    char_yanagi_name: 'Yanagi',
    char_yanagi_desc: 'A character from the game Zenless Zone Zero',
    
    // Language
    lang_toggle: '中文'
  }
};

export type Language = 'zh' | 'en';
export type TranslationKeys = keyof typeof translations.zh;

