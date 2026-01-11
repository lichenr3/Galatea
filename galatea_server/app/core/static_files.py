"""静态文件服务管理"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def mount_static_files(app: FastAPI) -> None:
    """
    挂载静态文件服务
    
    将 app/assets 目录挂载到 /static 路径，
    使前端可以通过 HTTP 访问头像、音频等资源
    
    Args:
        app: FastAPI 应用实例
    """
    static_dir = settings.BASE_DIR / "app" / "assets"
    
    if not static_dir.exists():
        logger.warning(f"⚠️  静态文件目录不存在: {static_dir}")
        logger.info(f"💡 提示: 请创建 {static_dir} 目录并放入资源文件")
        return
    
    try:
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"📁 静态文件服务: /static → {static_dir.name}/")
        
        # 列出可用的资源目录
        subdirs = [d.name for d in static_dir.iterdir() if d.is_dir()]
        if subdirs:
            logger.info(f"   └─ 可用目录: {', '.join(subdirs)}")
    except Exception as e:
        logger.error(f"❌ 挂载静态文件失败: {e}")


def get_static_file_path(relative_path: str) -> Path:
    """
    获取静态文件的绝对路径
    
    Args:
        relative_path: 相对于 assets 目录的路径，如 "images/avatar.png"
    
    Returns:
        静态文件的绝对路径
    """
    static_dir = settings.BASE_DIR / "app" / "assets"
    return static_dir / relative_path


def check_static_file_exists(relative_path: str) -> bool:
    """
    检查静态文件是否存在
    
    Args:
        relative_path: 相对于 assets 目录的路径
    
    Returns:
        文件是否存在
    """
    file_path = get_static_file_path(relative_path)
    return file_path.exists() and file_path.is_file()

