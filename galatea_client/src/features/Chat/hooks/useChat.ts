import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketService } from '../../../services/websocketService';
import { createSession, getContacts, getHistory, deleteSession, switchTTSModel } from '../../../services/sessionService';
import type { ChatMessage, ChatSession, CharacterContact } from '../../../types';
import { WebMessageType } from '../../../types/protocol';
import type { 
  WebBaseMessage, 
  AITextStreamPayload, 
  AIStatusPayload,
  AudioChunkPayload
} from '../../../types/protocol';
import { useLanguage } from '../../../i18n/LanguageContext';

export const useChat = () => {
  const { language } = useLanguage();
  
  // 会话管理
  const [contacts, setContacts] = useState<CharacterContact[]>([]);
  const [sessions, setSessions] = useState<Record<string, ChatSession>>({});
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  
  // WebSocket 状态
  const [isConnected, setIsConnected] = useState(false);
  const [aiStatus, setAiStatus] = useState<"idle" | "thinking" | "error">("idle");
  
  // 🆕 追踪当前激活的角色 ID
  const [currentCharacterId, setCurrentCharacterId] = useState<string | null>(null);
  
  // 使用 Ref 避免闭包问题
  const activeSessionIdRef = useRef<string | null>(null);
  const sessionsRef = useRef<Record<string, ChatSession>>({});
  const currentCharacterIdRef = useRef<string | null>(null);
  
  // ✨ 使用 Ref 保存最新的消息处理函数，避免闭包陷阱
  const handleServerMessageRef = useRef<((msg: WebBaseMessage) => void) | null>(null);
  
  // 同步 Ref 和 State
  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
    sessionsRef.current = sessions;
    currentCharacterIdRef.current = currentCharacterId;
  }, [activeSessionId, sessions, currentCharacterId]);
  
  // 加载历史会话
  useEffect(() => {
    const loadContacts = async () => {
      try {
        console.log('📥 加载会话列表...');
        const charContacts = await getContacts(language);
        console.log('✅ 会话列表加载完成:', charContacts.length);
        setContacts(charContacts);
      } catch (error) {
        console.error('❌ 加载会话列表失败:', error);
      }
    };
    
    loadContacts();
  }, [language]); // 依赖语言，当语言改变时重新加载

  // 初始化 WebSocket（只在组件挂载时执行一次）
  useEffect(() => {
    console.log('🔌 初始化 WebSocket 连接');
    
    webSocketService.connect(
      (msg) => {
        // 使用 Ref 中的最新回调函数
        if (handleServerMessageRef.current) {
          handleServerMessageRef.current(msg);
        }
      },
      (status) => setIsConnected(status)
    );

    return () => {
      console.log('🔌 清理 WebSocket 连接');
      webSocketService.disconnect();
    };
  }, []); // 空依赖数组：只在挂载和卸载时执行

  // 🆕 音频播放队列管理
  const audioQueueRef = useRef<Array<{ base64Data: string; sentenceIndex: number }>>([]);
  const isPlayingAudioRef = useRef(false);

  // 🆕 播放音频函数（带队列管理）
  const playAudioFromBase64 = useCallback((base64Data: string, sentenceIndex: number = 0) => {
    // 添加到队列
    audioQueueRef.current.push({ base64Data, sentenceIndex });
    console.log(`🎵 音频加入队列 [${sentenceIndex}]，队列长度: ${audioQueueRef.current.length}`);
    
    // 如果当前没有播放，立即开始播放队列
    if (!isPlayingAudioRef.current) {
      playNextInQueue();
    }
  }, []);

  // 🆕 播放队列中的下一个音频
  const playNextInQueue = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingAudioRef.current = false;
      console.log('📋 播放队列为空');
      return;
    }

    const { base64Data, sentenceIndex } = audioQueueRef.current.shift()!;
    isPlayingAudioRef.current = true;
    
    console.log(`🔊 开始播放音频 [${sentenceIndex}]，剩余队列: ${audioQueueRef.current.length}`);

    try {
      // Base64 → ArrayBuffer
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      // 创建 Blob
      const blob = new Blob([bytes], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);
      
      // 创建 Audio 对象并播放
      const audio = new Audio(url);
      
      // 播放结束后清理资源并播放下一个
      audio.onended = () => {
        URL.revokeObjectURL(url);
        console.log(`✅ 音频播放完成 [${sentenceIndex}]`);
        
        // 播放队列中的下一个
        playNextInQueue();
      };
      
      // 播放错误处理
      audio.onerror = (err) => {
        console.error(`❌ 音频播放错误 [${sentenceIndex}]:`, err);
        URL.revokeObjectURL(url);
        
        // 继续播放下一个
        playNextInQueue();
      };
      
      // 开始播放
      audio.play().catch(err => {
        console.error(`❌ 音频播放失败 [${sentenceIndex}]:`, err);
        URL.revokeObjectURL(url);
        
        // 继续播放下一个
        playNextInQueue();
      });
    } catch (error) {
      console.error(`❌ 音频处理失败 [${sentenceIndex}]:`, error);
      
      // 继续播放下一个
      playNextInQueue();
    }
  }, []);

  // 处理服务器消息（将最新的函数保存到 Ref）
  const handleServerMessage = useCallback((msg: WebBaseMessage) => {
    console.log('📩 收到服务器消息:', msg.type, msg);
    
    switch (msg.type) {
      case WebMessageType.AI_STATUS:
        const statusPayload = msg.data as AIStatusPayload;
        console.log('🎯 AI 状态更新:', statusPayload.status);
        setAiStatus(statusPayload.status as any);
        break;

      case WebMessageType.AI_TEXT_STREAM:
        const streamPayload = msg.data as AITextStreamPayload;
        console.log('📝 收到文本流:', { 
          text: streamPayload.text, 
          is_finish: streamPayload.is_finish,
          message_id: streamPayload.message_id 
        });
        
        // 更新对应会话的消息列表
        setSessions((prev) => {
          // 优先使用 Ref 中的最新值避免闭包问题
          const sessionId = activeSessionIdRef.current;
          console.log('🔍 当前活跃会话:', sessionId);
          
          if (!sessionId) {
            console.warn('⚠️ 没有活跃会话，消息被丢弃');
            return prev;
          }

          const session = prev[sessionId];
          if (!session) {
            console.warn('⚠️ 会话不存在:', sessionId);
            return prev;
          }

          const messages = session.messages;
          const lastMsg = messages[messages.length - 1];

          let updatedMessages: ChatMessage[];
          if (lastMsg && lastMsg.role === 'ai' && lastMsg.id === streamPayload.message_id) {
            // 追加到现有消息
            console.log('📌 追加到现有消息:', lastMsg.id);
            updatedMessages = messages.slice(0, -1).concat({
              ...lastMsg,
              content: lastMsg.content + streamPayload.text,
              status: streamPayload.is_finish ? 'finished' : 'streaming'
            } as ChatMessage);
          } else {
            // 新消息
            console.log('✨ 创建新 AI 消息');
            const newMessage: ChatMessage = {
              id: streamPayload.message_id,
              role: 'ai' as const,
              content: streamPayload.text,
              timestamp: Date.now(),
              status: streamPayload.is_finish ? 'finished' : 'streaming'
            };
            updatedMessages = [...messages, newMessage];
          }

          console.log('💾 更新后的消息列表:', updatedMessages.length, '条');

          // 更新联系人的最后消息
          if (streamPayload.is_finish && streamPayload.text) {
            updateContactLastMessage(sessionId, updatedMessages[updatedMessages.length - 1].content);
          }

          return {
            ...prev,
            [sessionId]: {
              ...session,
              messages: updatedMessages
            }
          };
        });
        break;

      case WebMessageType.ERROR:
        console.error("❌ 服务器错误:", msg.data);
        setAiStatus('error');
        break;
      
      case WebMessageType.AUDIO_CHUNK:
        const audioPayload = msg.data as AudioChunkPayload;
        console.log('🔊 收到音频数据:', { 
          sentence_index: audioPayload.sentence_index, 
          duration: audioPayload.duration 
        });
        playAudioFromBase64(audioPayload.audio_data, audioPayload.sentence_index);
        break;
      
      default:
        console.log('📭 未处理的消息类型:', msg.type);
    }
  }, []); // 空依赖数组，因为我们使用 Ref 访问最新状态
  
  // 将最新的 handleServerMessage 保存到 Ref
  useEffect(() => {
    handleServerMessageRef.current = handleServerMessage;
  }, [handleServerMessage]);

  // 更新联系人最后消息
  const updateContactLastMessage = (sessionId: string, message: string) => {
    setContacts(prev => prev.map(char => {
      const sessionIndex = char.sessions.findIndex(s => s.sessionId === sessionId);
      if (sessionIndex !== -1) {
        const newSessions = [...char.sessions];
        newSessions[sessionIndex] = {
          ...newSessions[sessionIndex],
          preview: message.substring(0, 50) + (message.length > 50 ? '...' : '')
        };
        return { ...char, sessions: newSessions };
      }
      return char;
    }));
  };

  // 创建新会话
  const handleCreateSession = useCallback(async (characterId: string, language: string = 'zh') => {
    try {
      console.log('🔨 正在创建会话，角色:', characterId, '语言:', language);
      const response = await createSession(characterId, language);
      const { session_id, avatar_url } = response;
      console.log('✅ 会话创建成功:', session_id);

      // 🆕 更新当前角色 ID（创建会话时后端已经切换了 TTS 模型）
      setCurrentCharacterId(characterId);

      // 添加到联系人列表
      setContacts(prev => {
        const newContacts = [...prev];
        const charIndex = newContacts.findIndex(c => c.characterId === characterId);
        
        if (charIndex >= 0) {
          // 添加到现有角色
          const char = { ...newContacts[charIndex] };
          char.sessions = [{
            sessionId: session_id,
            messageCount: 0,
            preview: ''
          }, ...char.sessions];
          newContacts[charIndex] = char;
        } else {
          // 新角色
          newContacts.push({
            characterId,
            characterName: characterId,
            avatarUrl: avatar_url,
            sessions: [{
              sessionId: session_id,
              messageCount: 0,
              preview: ''
            }]
          });
        }
        return newContacts;
      });

      // 创建会话消息列表
      setSessions(prev => {
        const newSessions = {
          ...prev,
          [session_id]: {
            sessionId: session_id,
            messages: []
          }
        };
        console.log('💼 创建会话对象，当前会话数:', Object.keys(newSessions).length);
        return newSessions;
      });

      // 设置为当前活跃会话
      setActiveSessionId(session_id);
      console.log('🎯 设置活跃会话为:', session_id);

      return session_id;
    } catch (err) {
      console.error('❌ 创建会话失败:', err);
      throw err;
    }
  }, []);

  // 删除会话
  const handleDeleteSession = useCallback(async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      
      setContacts(prev => prev.map(char => ({
        ...char,
        sessions: char.sessions.filter(s => s.sessionId !== sessionId)
      })).filter(char => char.sessions.length > 0));

      setSessions(prev => {
        const next = { ...prev };
        delete next[sessionId];
        return next;
      });

      if (activeSessionIdRef.current === sessionId) {
        setActiveSessionId(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  }, []);

  // 切换会话
  const handleSelectSession = useCallback(async (sessionId: string) => {
    const prevSessionId = activeSessionIdRef.current;
    
    // 🆕 获取新会话的角色 ID
    const newCharacterId = contacts.find(c => 
      c.sessions.some(s => s.sessionId === sessionId)
    )?.characterId;
    
    const prevCharacterId = currentCharacterIdRef.current;
    
    // 🆕 如果角色发生变化，切换 TTS 模型
    if (newCharacterId && newCharacterId !== prevCharacterId) {
      console.log('🎤 检测到角色切换:', {
        从: prevCharacterId,
        到: newCharacterId
      });
      
      // 异步调用 TTS 切换，不阻塞会话切换
      switchTTSModel(newCharacterId).then(success => {
        if (success) {
          console.log('✅ TTS 模型已切换到:', newCharacterId);
          setCurrentCharacterId(newCharacterId);
        } else {
          console.warn('⚠️  TTS 模型切换失败，但不影响使用');
        }
      }).catch(err => {
        console.error('❌ TTS 模型切换异常:', err);
      });
    }
    
    // 自动删除空会话逻辑
    if (prevSessionId && prevSessionId !== sessionId) {
      const prevSession = sessionsRef.current[prevSessionId];
      // 如果前一个会话存在且没有消息，则自动删除
      if (prevSession && prevSession.messages.length === 0) {
        console.log('🗑️ 自动删除空会话:', prevSessionId);
        // 不等待删除完成，直接继续切换，避免UI卡顿
        deleteSession(prevSessionId).catch(e => console.error('Auto-delete failed', e));
        
        // 更新 UI 状态移除该会话
        setContacts(prev => prev.map(char => ({
          ...char,
          sessions: char.sessions.filter(s => s.sessionId !== prevSessionId)
        })).filter(char => char.sessions.length > 0));
        
        setSessions(prev => {
          const next = { ...prev };
          delete next[prevSessionId];
          return next;
        });
      }
    }

    setActiveSessionId(sessionId);
    
    // 如果该会话还没有消息记录，尝试加载历史
    if (!sessionsRef.current[sessionId] || sessionsRef.current[sessionId].messages.length === 0) {
      try {
        console.log('📜 加载会话历史:', sessionId);
        const history = await getHistory(sessionId);
        
        setSessions(prev => ({
          ...prev,
          [sessionId]: {
            sessionId,
            messages: history
          }
        }));
      } catch (error) {
        console.error('❌ 加载历史失败:', error);
      }
    }
  }, [contacts]);

  // 发送消息
  const sendMessage = useCallback((text: string, enableAudio: boolean = true) => {
    const currentSessionId = activeSessionIdRef.current;
    const currentSessions = sessionsRef.current;
    
    console.log('📤 准备发送消息:', { 
      text: text.substring(0, 20), 
      sessionId: currentSessionId,
      enableAudio 
    });
    
    if (!text.trim() || !currentSessionId) {
      console.warn('⚠️ 无法发送：', { hasText: !!text.trim(), hasSession: !!currentSessionId });
      return;
    }

    const session = currentSessions[currentSessionId];
    if (!session) {
      console.error('❌ 会话不存在:', currentSessionId);
      return;
    }

    // 添加用户消息到当前会话
    const tempId = Date.now().toString();
    const newMsg: ChatMessage = {
      id: tempId,
      role: 'user' as const,
      content: text,
      timestamp: Date.now(),
      status: 'finished'
    };

    setSessions(prev => {
      const updated = {
        ...prev,
        [currentSessionId]: {
          ...session,
          messages: [...session.messages, newMsg]
        }
      };
      console.log('💾 用户消息已添加到会话');
      return updated;
    });

    // 更新联系人最后消息
    updateContactLastMessage(currentSessionId, text);

    // 发送给后端（带上 session_id 和 enable_audio）
    const messageToSend = {
      type: WebMessageType.USER_MESSAGE,
      session_id: currentSessionId,
      data: { 
        content: text,
        enable_audio: enableAudio  // 🆕 添加音频开关
      },
      timestamp: Date.now() / 1000
    };
    console.log('📡 发送消息到后端:', messageToSend);
    webSocketService.sendMessage(messageToSend);
  }, []);

  // 自动选中第一个会话（如果当前没有选中且有会话）
  useEffect(() => {
    if (!activeSessionId && contacts.length > 0) {
      const firstChar = contacts[0];
      if (firstChar.sessions.length > 0) {
        const firstSessionId = firstChar.sessions[0].sessionId;
        console.log('🔄 自动选中最新会话:', firstSessionId);
        handleSelectSession(firstSessionId);
      }
    }
  }, [contacts, activeSessionId, handleSelectSession]);

  // 获取当前活跃会话的消息
  const currentMessages = activeSessionId && sessions[activeSessionId] 
    ? sessions[activeSessionId].messages 
    : [];

  // 聊天框是否可用（需要有活跃会话）
  const isChatActive = activeSessionId !== null && isConnected;

  return { 
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
  };
};
