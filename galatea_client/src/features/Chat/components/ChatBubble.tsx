import React from 'react';
import type { ChatMessage } from '../../../types/index';
import { useTypewriter } from '../hooks/useTypewriter';
import './ChatBubble.css';

interface Props {
  message: ChatMessage;
}

export const ChatBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';
  
  // 只有 AI 的消息，且正在流式传输时才启用打字机
  // 这样刷新页面或切换会话时（status 为 finished 或 undefined）就不会有打字机效果
  const shouldAnimate = !isUser && message.status === 'streaming';
  const displayedContent = useTypewriter(message.content, 20, shouldAnimate);
  
  // 判断是否正在打字：是 AI 消息，且显示的内容还没追上实际内容
  const isTyping = shouldAnimate && displayedContent.length < message.content.length;
  // 或者后端状态是 streaming
  const isStreaming = message.status === 'streaming';

  return (
    <div className={`bubble-container ${isUser ? 'user' : 'ai'}`}>
      <div className="bubble-content">
        <div className="bubble-text">
          {isUser ? message.content : displayedContent}
          {(isTyping || isStreaming) && <span className="cursor-blink"></span>}
        </div>
      </div>
    </div>
  );
};