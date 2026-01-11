import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    获取或创建logger实例
    
    Args:
        name: logger名称 (通常使用 __name__)
        level: 日志级别 (默认INFO)
    
    Returns:
        配置好的logger实例
    """
    # 延迟导入，避免循环依赖
    from app.core.config import settings
    
    # 确保日志目录存在
    settings.LOGS_DIR.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False  # 避免日志重复
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. 通用日志文件 (滚动日志，每个10MB，保留5个备份)
    file_handler = RotatingFileHandler(
        settings.LOGS_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 3. 错误日志单独记录
    error_handler = RotatingFileHandler(
        settings.LOGS_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger
