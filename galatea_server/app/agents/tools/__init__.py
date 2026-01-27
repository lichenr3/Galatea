"""
Agent 工具模块

使用 @tool 装饰器定义工具，然后在 get_all_tools() 中注册。
"""
from typing import List
from langchain_core.tools import BaseTool


def get_all_tools() -> List[BaseTool]:
    """获取所有可用工具"""
    # TODO: 在 Phase 3 中添加工具
    return []
