"""路径工具函数"""
from typing import Optional
from app.core.config import settings


def resolve_static_url(path: Optional[str]) -> str:
    """
    将配置中的路径转换为前端可访问的 URL
    
    支持的格式：
    - "/images/avatars/yanagi.png" → "/static/images/avatars/yanagi.png"
    - "static://images/avatars/yanagi.png" → "/static/images/avatars/yanagi.png"
    - "/static/images/avatars/yanagi.png" → "/static/images/avatars/yanagi.png" (已经是完整路径)
    - "https://cdn.example.com/avatar.png" → "https://cdn.example.com/avatar.png" (外部 URL)
    
    Args:
        path: 配置文件中的路径字符串
    
    Returns:
        前端可访问的 HTTP URL
    """
    if not path:
        return ""
    
    # 如果已经是完整的 HTTP/HTTPS URL，直接返回
    if path.startswith(("http://", "https://")):
        return path
    
    # 如果使用了 static:// 协议前缀，移除它
    if path.startswith("static://"):
        path = "/" + path.replace("static://", "", 1)
    
    # 如果已经包含 /static/ 前缀，直接返回
    if path.startswith("/static/"):
        return path
    
    # 否则，添加 /static/ 前缀
    if path.startswith("/"):
        return f"/static{path}"
    else:
        return f"/static/{path}"


def resolve_file_path(path: Optional[str]) -> str:
    """
    将配置中的路径转换为服务器文件系统路径
    
    支持的格式：
    - "/images/avatars/yanagi.png" → "BASE_DIR/app/assets/images/avatars/yanagi.png"
    - "static://images/avatars/yanagi.png" → "BASE_DIR/app/assets/images/avatars/yanagi.png"
    
    Args:
        path: 配置文件中的路径字符串
    
    Returns:
        服务器文件系统的绝对路径
    """
    if not path:
        return ""
    
    # 外部 URL 无法转换为文件路径
    if path.startswith(("http://", "https://")):
        raise ValueError(f"Cannot resolve external URL to file path: {path}")
    
    # 处理 static:// 前缀
    if path.startswith("static://"):
        path = "/" + path.replace("static://", "", 1)
    
    # 移除 /static/ 前缀（如果有）
    if path.startswith("/static/"):
        path = path.replace("/static/", "", 1)
    elif path.startswith("/"):
        path = path[1:]
    
    # 拼接完整路径
    assets_dir = settings.BASE_DIR / "app" / "assets"
    full_path = assets_dir / path
    
    return str(full_path)

