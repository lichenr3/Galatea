import { useState, useEffect, useRef } from 'react';

/**
 * 自定义 Hook：实现打字机效果
 * @param text 目标文本
 * @param speed 基础打字速度（毫秒/字符）
 * @param isEnabled 是否启用打字机效果（通常只对 AI 消息启用）
 * @returns 当前显示的文本
 */
export const useTypewriter = (text: string, speed: number = 30, isEnabled: boolean = true) => {
  const [displayedText, setDisplayedText] = useState('');
  const indexRef = useRef(0);

  useEffect(() => {
    if (!isEnabled) {
      setDisplayedText(text);
      return;
    }

    // 如果目标文本变短了（比如重置），或者完全变了，重置状态
    if (text.length < displayedText.length || !text.startsWith(displayedText)) {
      setDisplayedText('');
      indexRef.current = 0;
    }

    // 如果已经显示完了，就不做任何事
    if (indexRef.current >= text.length) {
      return;
    }

    const timer = setInterval(() => {
      if (indexRef.current < text.length) {
        // 动态调整速度：如果落后太多，就一次多打几个字
        const distance = text.length - indexRef.current;
        const step = distance > 50 ? 5 : distance > 20 ? 2 : 1;
        
        indexRef.current += step;
        setDisplayedText(text.slice(0, indexRef.current));
      } else {
        clearInterval(timer);
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed, isEnabled, displayedText]);

  return displayedText;
};
