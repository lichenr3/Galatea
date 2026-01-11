"""文本缓冲工具"""
from typing import List


class TextBuffer:
    """增量文本缓冲器，用于检测句子边界"""
    
    def __init__(self):
        self.buffer = ""
        # 中文和英文的句子分隔符
        self.sentence_delimiters = ["。", "！", "？", ".", "!", "?", "\n\n"]
        self.min_chunk_length = 5  # 最小句子长度，避免过短的片段
    
    def add_chunk(self, text: str) -> List[str]:
        """
        添加文本块，返回完成的句子列表
        
        Args:
            text: 新增的文本片段
            
        Returns:
            List[str]: 已完成的句子列表
        """
        self.buffer += text
        completed = []
        
        while True:
            # 找到第一个分隔符
            earliest_pos = -1
            earliest_delimiter = None
            
            for delimiter in self.sentence_delimiters:
                pos = self.buffer.find(delimiter)
                if pos != -1 and (earliest_pos == -1 or pos < earliest_pos):
                    earliest_pos = pos
                    earliest_delimiter = delimiter
            
            if earliest_pos == -1:
                break
            
            # 提取句子（包含分隔符）
            sentence = self.buffer[:earliest_pos + len(earliest_delimiter)].strip()
            
            # 移除已处理的部分
            self.buffer = self.buffer[earliest_pos + len(earliest_delimiter):]
            
            # 过滤过短的片段
            if len(sentence) >= self.min_chunk_length:
                completed.append(sentence)
        
        return completed
    
    def flush(self) -> str:
        """
        获取剩余的文本（在LLM结束时调用）
        
        Returns:
            str: 剩余文本，如果太短则返回None
        """
        remaining = self.buffer.strip()
        self.buffer = ""
        
        if remaining and len(remaining) >= self.min_chunk_length:
            return remaining
        return None
    
    def clear(self):
        """清空缓冲区"""
        self.buffer = ""
