"""应用启动配置模块"""
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def print_startup_banner() -> None:
    """打印启动横幅"""
    banner = f"""
╔══════════════════════════════════════════════════╗
║                                                  ║
║          🌸 Galatea Server v1.0.0 🌸             ║
║                                                  ║
║  AI Desktop Pet Backend Service                 ║
║                                                  ║
╚══════════════════════════════════════════════════╝

🚀 服务器配置:
   • Host: {settings.HOST}
   • Port: {settings.PORT}
   • API: {settings.API_V1_STR}
   
📦 模块状态:
"""
    print(banner)


def print_available_endpoints() -> None:
    """打印可用的端点"""
    endpoints = [
        ("🌐 Web WebSocket", f"ws://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/ws/web"),
        ("🎮 Unity WebSocket", f"ws://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/ws/unity"),
        ("📝 Session API", f"http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/session/create"),
        ("🖼️  Static Files", f"http://{settings.HOST}:{settings.PORT}/static/"),
    ]
    
    logger.info("🔗 可用端点:")
    for name, url in endpoints:
        logger.info(f"   {name}: {url}")

