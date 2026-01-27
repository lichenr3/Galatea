"""
CRUD 基类

提供通用的 CRUD 操作模板。
"""
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)


class BaseCRUD(Generic[ModelType]):
    """
    通用 CRUD 基类
    
    提供基本的 CRUD 操作，子类可以扩展特定的查询方法。
    
    Usage:
        class SessionCRUD(BaseCRUD[Session]):
            def __init__(self, session: AsyncSession):
                super().__init__(Session, session)
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """创建记录"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据 ID 获取记录"""
        return await self.session.get(self.model, id)
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """获取所有记录（分页）"""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_by_id(self, id: Any, **kwargs) -> Optional[ModelType]:
        """根据 ID 更新记录"""
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.session.flush()
            await self.session.refresh(instance)
        return instance
    
    async def delete_by_id(self, id: Any) -> bool:
        """根据 ID 删除记录"""
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
    
    async def exists(self, id: Any) -> bool:
        """检查记录是否存在"""
        instance = await self.get_by_id(id)
        return instance is not None
