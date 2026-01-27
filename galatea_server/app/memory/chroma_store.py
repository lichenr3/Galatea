"""
Chroma 向量数据库实现

使用 Chroma 嵌入式模式，数据持久化到本地文件。
优点：无需额外服务，部署简单。
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.memory.base import MemoryStore
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class ChromaMemoryStore(MemoryStore):
    """
    Chroma 向量数据库实现
    
    使用嵌入式模式，数据持久化到本地目录。
    适合单机部署，数据量中等的场景。
    """
    
    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "galatea_memories"):
        """
        初始化 Chroma 存储
        
        Args:
            persist_directory: 数据持久化目录，默认使用配置
            collection_name: 集合名称
        """
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        persist_dir = persist_directory or str(settings.CHROMA_PERSIST_DIR)
        
        # 确保目录存在
        settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        
        # 创建持久化客户端
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Galatea conversation memories"}
        )
        
        logger.info(f"✅ Chroma 向量库已初始化: {persist_dir}")
        logger.info(f"   集合: {collection_name}, 当前记忆数: {self.collection.count()}")
    
    async def save_memory(
        self, 
        session_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存记忆到 Chroma"""
        memory_id = str(uuid.uuid4())
        
        # 构建元数据
        meta = metadata.copy() if metadata else {}
        meta["session_id"] = session_id
        meta["created_at"] = datetime.now().isoformat()
        
        # 添加到集合（Chroma 会自动生成嵌入向量）
        self.collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[meta]
        )
        
        logger.debug(f"💾 保存记忆: {memory_id[:8]}... (会话: {session_id})")
        return memory_id
    
    async def retrieve_relevant(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """从 Chroma 检索相关记忆"""
        # 构建过滤条件
        where_filter = {"session_id": session_id} if session_id else None
        
        # 查询
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        memories = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })
        
        logger.debug(f"🔍 检索到 {len(memories)} 条相关记忆 (查询: {query[:30]}...)")
        return memories
    
    async def delete_memories(self, session_id: str) -> int:
        """删除指定会话的所有记忆"""
        # 先查询该会话的所有记忆
        results = self.collection.get(
            where={"session_id": session_id},
            include=["metadatas"]
        )
        
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            count = len(results["ids"])
            logger.info(f"🗑️ 删除 {count} 条记忆 (会话: {session_id})")
            return count
        
        return 0
    
    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """按元数据搜索记忆"""
        results = self.collection.get(
            where=filters,
            limit=k,
            include=["documents", "metadatas"]
        )
        
        memories = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                memories.append({
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })
        
        return memories
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_memories": self.collection.count(),
            "collection_name": self.collection.name,
            "persist_directory": str(settings.CHROMA_PERSIST_DIR)
        }
