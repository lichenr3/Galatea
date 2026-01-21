import React, { useState, useRef, useEffect } from 'react';
import { useChat } from './hooks/useChat';
import { ChatBubble } from './components/ChatBubble';
import { ContactList } from './components/ContactList';
import { AddContactModal } from './components/AddContactModal';
import { WindowControls } from '../../components/WindowControls';
import { launchUnity, shutdownUnity, getUnityStatus, switchCharacter } from '../../services/unityService';
import { useLanguage } from '../../i18n/LanguageContext';
import './ChatLayout.css';

export const ChatLayout: React.FC = () => {
  const {
    contacts,
    activeSessionId,
    currentMessages,
    isConnected,
    aiStatus,
    isChatActive,
    handleCreateSession,
    handleSelectSession,
    handleDeleteSession,
    sendMessage
  } = useChat();

  const { language, setLanguage, t } = useLanguage();

  const [inputValue, setInputValue] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const langMenuRef = useRef<HTMLDivElement>(null);

  // Unity 控制状态
  const [isUnityLoading, setIsUnityLoading] = useState(false);
  const [isUnityLaunched, setIsUnityLaunched] = useState(false);
  
  // 音频开关状态（默认关闭）
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);

  // 🆕 桌宠模式状态 (每次启动都使用默认值 false)
  const [isPetMode, setIsPetMode] = useState(false);

  // 🆕 最小化（收起）状态 (每次启动都使用默认值 false)
  const [isMinimized, setIsMinimized] = useState(false);

  // 同步窗口尺寸的辅助函数
  const syncWindowSize = (petMode: boolean, minimized: boolean) => {
    try {
      const electron = (window as any).require ? (window as any).require('electron') : null;
      const ipc = electron?.ipcRenderer || (window as any).ipcRenderer;
      if (ipc) {
        ipc.send('set-window-pet-mode', petMode, minimized);
      }
    } catch (e) {
      console.error('Failed to sync window size', e);
    }
  };

  // 页面加载时或模式切换时同步尺寸
  useEffect(() => {
    syncWindowSize(isPetMode, isMinimized);
  }, [isPetMode, isMinimized]);

  // 🆕 记录是否为首次加载，用于控制滚动效果
  const isInitialLoadRef = useRef(true);

  // 自动滚动到底部
  useEffect(() => {
    if (currentMessages.length > 0) {
      const scrollBehavior = isInitialLoadRef.current ? 'auto' : 'smooth';
      
      const timer = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: scrollBehavior, block: 'end' });
        isInitialLoadRef.current = false;
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [currentMessages, aiStatus, isPetMode, isMinimized]);

  // 当切换会话或切换模式时，重置首次加载标记，实现"闪现到底部"
  useEffect(() => {
    isInitialLoadRef.current = true;
  }, [activeSessionId, isPetMode, isMinimized]);

  // 当切换会话时，如果 Unity 已启动，自动切换角色
  useEffect(() => {
    const characterId = activeCharacter?.characterId;
    if (isUnityLaunched && characterId) {
      console.log('🎭 会话切换，通知 Unity 切换角色:', characterId);
      switchCharacter(characterId).catch(err => {
        console.error('Failed to switch character on session change:', err);
      });
    }
  }, [activeSessionId, isUnityLaunched]);

  // 初始化检查 Unity 状态
  useEffect(() => {
    // 确保初次加载时窗口尺寸正确
    syncWindowSize(isPetMode, isMinimized);
    
    const checkUnityStatus = async () => {
      try {
        const status = await getUnityStatus();
        if (status && status.running) {
          setIsUnityLaunched(true);
        }
      } catch (err) {
        console.error('Unity status check failed', err);
      }
    };
    checkUnityStatus();
  }, []);

  const handleSend = () => {
    if (!inputValue.trim() || !isChatActive) return;
    sendMessage(inputValue, isAudioEnabled);
    setInputValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleLaunchUnity = async () => {
    console.log('🚀 [DEBUG] 开始启动 Unity');
    console.log('🚀 [DEBUG] 当前角色ID:', activeCharacter?.characterId);
    
    setIsUnityLoading(true);
    try {
      const characterId = activeCharacter?.characterId;
      
      // 启动 Unity，并告诉后端要加载的角色
      const result = await launchUnity(characterId);
      console.log('✅ [DEBUG] Unity 启动结果:', result);
      
      // 无论成功与否，只要后端返回了运行状态或成功启动，就同步状态
      if (result.success || result.pid) {
        setIsUnityLaunched(true);
        console.log('✅ Unity 启动成功，后端将在连接后自动加载角色:', characterId);
      }
    } catch (err) {
      console.error('Failed to launch Unity:', err);
    } finally {
      setIsUnityLoading(false);
    }
  };

  const handleShutdownUnity = async () => {
    setIsUnityLoading(true);
    try {
      await shutdownUnity();
      // 无论关闭是否成功（可能已经手动关闭了），点击了关闭就应该取消高亮
      setIsUnityLaunched(false);
    } catch (err) {
      console.error('Failed to shutdown Unity:', err);
      // 报错也取消高亮，防止状态卡死
      setIsUnityLaunched(false);
    } finally {
      setIsUnityLoading(false);
    }
  };

  const togglePetMode = () => {
    setIsPetMode(!isPetMode);
  };

  const toggleMinimized = () => {
    setIsMinimized(!isMinimized);
  };

  const handleLanguageSelect = (lang: 'zh' | 'en') => {
    setLanguage(lang);
    setIsLangMenuOpen(false);
  };

  // 点击外部关闭语言菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (langMenuRef.current && !langMenuRef.current.contains(event.target as Node)) {
        setIsLangMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleRefresh = () => {
    window.location.reload();
  };

  const activeCharacter = contacts.find(char => 
    char.sessions.some(s => s.sessionId === activeSessionId)
  );

  // 🆕 悬浮球视图 (分离拖拽区和点击区)
  if (isMinimized) {
    return (
      <div className="floating-ball-container">
        {/* 1. 拖拽区：整个头像圆球 */}
        <div className="floating-ball" title="按住拖动">
          <div className="ball-content">
            {activeCharacter ? (
              <img src={activeCharacter.avatarUrl} alt="avatar" />
            ) : (
              <div className="ball-icon">💬</div>
            )}
            {aiStatus === 'thinking' && <div className="ball-status-dot" />}
          </div>
        </div>
        
        {/* 2. 点击区：专门的展开按钮，no-drag 确保可点击 */}
        <button 
          className="ball-restore-btn" 
          onClick={toggleMinimized} 
          title="展开聊天框"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 3 21 3 21 9"></polyline>
            <polyline points="9 21 3 21 3 15"></polyline>
            <line x1="21" y1="3" x2="14" y2="10"></line>
            <line x1="3" y1="21" x2="10" y2="14"></line>
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className={`chat-layout ${isPetMode ? 'pet-mode' : ''}`}>
      {!isPetMode && (
        <ContactList
          contacts={contacts}
          activeSessionId={activeSessionId}
          onSelectContact={handleSelectSession}
          onAddContact={() => setIsModalOpen(true)}
          onDeleteSession={handleDeleteSession}
        />
      )}

      <div className="chat-main">
        <header className="chat-header">
          <div className="header-left">
            {!isPetMode && <h2>Galatea</h2>}
            {isPetMode && activeCharacter && (
              <div className="active-avatar">
                <img 
                  src={activeCharacter.avatarUrl} 
                  alt={t(`${activeCharacter.characterId}` as any) || activeCharacter.characterName} 
                />
              </div>
            )}
          </div>
          <div className="header-right">
            <div className="status-badge">
              <span className={`status-dot ${isConnected ? 'online' : 'offline'}`} />
              {!isPetMode && (isConnected ? (aiStatus === 'thinking' ? t('status_thinking') : t('status_online')) : t('status_offline'))}
            </div>
            {!isPetMode && (
              <div className="lang-dropdown-container" ref={langMenuRef}>
                <button 
                  className="lang-toggle-btn" 
                  onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
                >
                  Lang: {language === 'zh' ? '中' : 'En'}
                  <svg 
                    className={`chevron-icon ${isLangMenuOpen ? 'expanded' : ''}`} 
                    width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                  >
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>
                {isLangMenuOpen && (
                  <div className="lang-menu">
                    <button 
                      className={`lang-menu-item ${language === 'en' ? 'active' : ''}`}
                      onClick={() => handleLanguageSelect('en')}
                    >
                      English
                    </button>
                    <button 
                      className={`lang-menu-item ${language === 'zh' ? 'active' : ''}`}
                      onClick={() => handleLanguageSelect('zh')}
                    >
                      简体中文
                    </button>
                  </div>
                )}
              </div>
            )}
            {!isPetMode && <WindowControls isPetMode={isPetMode} />}
          </div>
        </header>

        <div className="messages-list">
          {currentMessages.map((msg) => (
            <div key={msg.id} className="chat-bubble-wrapper">
              <ChatBubble message={msg} />
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <footer className="input-area">
          <div className="input-container">
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isChatActive ? t('input_placeholder') : t('input_placeholder_disabled')}
              disabled={!isChatActive}
              className="chat-input"
            />
            <div className="input-toolbar">
              <div className="toolbar-left">
                <button 
                  className="tool-btn refresh-btn" 
                  onClick={handleRefresh} 
                  disabled={!isChatActive}
                  title={t('tooltip_refresh')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <polyline points="1 20 1 14 7 14"></polyline>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                  </svg>
                </button>

                {/* <button className="tool-btn" title="添加文件">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                </button> */}
                
                <button 
                  className={`tool-btn unity-btn ${isUnityLaunched ? 'active' : ''}`}
                  onClick={() => {
                    console.log('Unity 按钮点击, 当前状态:', isUnityLaunched);
                    if (isUnityLaunched) {
                      handleShutdownUnity();
                    } else {
                      handleLaunchUnity();
                    }
                  }}
                  disabled={!isChatActive || isUnityLoading}
                  title={t('tooltip_unity')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                    <line x1="12" y1="22.08" x2="12" y2="12"></line>
                  </svg>
                </button>
                
                <button 
                  className={`tool-btn audio-btn ${isAudioEnabled ? 'active' : ''}`}
                  onClick={() => setIsAudioEnabled(!isAudioEnabled)}
                  disabled={!isChatActive}
                  title={t('tooltip_audio')}
                >
                  {isAudioEnabled ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                      <line x1="23" y1="9" x2="17" y2="15"></line>
                      <line x1="17" y1="9" x2="23" y2="15"></line>
                    </svg>
                  )}
                </button>

                <button 
                  className={`tool-btn pet-toggle-btn ${isPetMode ? 'active' : ''}`}
                  onClick={togglePetMode}
                  disabled={!isChatActive}
                  title={t('tooltip_pet_mode')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                    <line x1="9" y1="21" x2="9" y2="9"></line>
                  </svg>
                </button>

                <button 
                  className="tool-btn minimize-btn"
                  onClick={toggleMinimized}
                  disabled={!isChatActive}
                  title={t('tooltip_minimize')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                  </svg>
                </button>
              </div>
              
              <div className="toolbar-right">
                <button 
                  onClick={handleSend} 
                  disabled={!isChatActive || !inputValue.trim()} 
                  className="send-btn"
                  title={t('tooltip_send')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </footer>
      </div>

      <AddContactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSelectCharacter={(id) => handleCreateSession(id, language)}
      />
    </div>
  );
};
