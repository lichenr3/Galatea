from pydantic import BaseModel, Field
from typing import Optional, TypeVar, Generic, List


class BaseModelStrip(BaseModel):
    """
    基础模型, 自动将所有空值转换为 None
    """
    def __init__(self, **data):
        data = {k: self._convert_empty_to_none(v) for k, v in data.items()}
        super().__init__(**data)

    @staticmethod
    def _convert_empty_to_none(value):
        if isinstance(value, dict):
            if not value:
                return None
            return {k: BaseModelStrip._convert_empty_to_none(v) for k, v in value.items()}
        elif isinstance(value, list):
            if not value:
                return None
            return [BaseModelStrip._convert_empty_to_none(v) for v in value]
        elif isinstance(value, str):
            if value == "":
                return None
            return value
        else:
            return value


T = TypeVar('TItem')


class Page(BaseModel, Generic[T]):
    """
    通用分页结构
    用于聊天历史记录、角色列表等长列表场景
    """
    total: int = Field(..., description="总条数")
    pageNum: int = Field(1, description="当前页码")
    pageSize: int = Field(20, description="每页大小")
    pages: int = Field(0, description="总页数")
    items: List[T] = Field(..., description="当前页的数据列表")
    
    @classmethod
    def create(cls, items: List[T], total: int, pageNum: int, pageSize: int):
        import math
        return cls(
            items=items,
            total=total,
            pageNum=pageNum,
            pageSize=pageSize,
            pages=math.ceil(total / pageSize) if pageSize > 0 else 0
        )


class UnifiedResponse(BaseModel, Generic[T]):
    """
    统一的API响应结构。
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据体")

    @classmethod
    def success(cls, message: str = "success", data: T = None):
        return cls(code=200, message=message, data=data)
