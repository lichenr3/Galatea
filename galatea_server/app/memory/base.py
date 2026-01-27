"""
记忆存储抽象接口

定义向量数据库的通用接口，便于切换不同实现。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryStore(ABC):
    """
    记忆存储抽象接口
    
    子类需要实现：
    - save_memory: 保存记忆
    - retrieve_relevant: 检索相关记忆
    - delete_memories: 删除记忆
    """
    
    @abstractmethod
    async def save_memory(
        self, 
        session_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        保存记忆到向量库
        
        Args:
            session_id: 会话ID，用于隔离不同会话的记忆
            content: 记忆内容（会被向量化）
            metadata: 可选的元数据（时间戳、角色、标签等）
        
        Returns:
            记忆ID
        """
        pass
    
    @abstractmethod
    async def retrieve_relevant(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆
        
        Args:
            query: 查询文本
            session_id: 可选，限定在某个会话内搜索
            k: 返回结果数量
        
        Returns:
            相关记忆列表，每个记忆包含 content 和 metadata
        """
        pass
    
    @abstractmethod
    async def delete_memories(self, session_id: str) -> int:
        """
        删除指定会话的所有记忆
        
        Args:
            session_id: 会话ID
        
        Returns:
            删除的记忆数量
        """
        pass
    
    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        按元数据搜索记忆（可选实现）
        
        Args:
            filters: 元数据过滤条件
            k: 返回结果数量
        
        Returns:
            匹配的记忆列表
        """
        raise NotImplementedError("search_by_metadata not implemented")
