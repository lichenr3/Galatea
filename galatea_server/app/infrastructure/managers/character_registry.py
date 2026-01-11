from typing import Dict, Optional
import json
from pydantic import ValidationError

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.character import CharacterConfig

logger = get_logger(__name__)

class CharacterRegistry:
    """角色注册表 - 懒加载模式"""
    
    def __init__(self):
        self.characters_dir = settings.CHARACTERS_DIR
        self._cache: Dict[str, CharacterConfig] = {}  # 缓存已加载的角色（强类型）
    
    def get_character(self, char_id: str) -> Optional[CharacterConfig]:
        """
        根据 ID 获取角色配置（懒加载）
        
        Args:
            char_id: 角色 ID (如 "yanagi")
        
        Returns:
            角色配置字典，如果不存在返回 None
        """
        # 1. 先检查缓存
        if char_id in self._cache:
            logger.debug(f"📦 从缓存加载角色: {char_id}")
            return self._cache[char_id]
        
        # 2. 尝试从文件系统加载
        char_dir = self.characters_dir / char_id
        config_file = char_dir / "config.json"
        
        if not config_file.exists():
            logger.warning(f"⚠️ 角色不存在: {char_id}")
            return None
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                raw = json.load(f)

            config = CharacterConfig.model_validate(raw)

            # 3. 加入缓存
            self._cache[char_id] = config
            logger.info(f"✅ 加载角色: {char_id}")
            return config

        except ValidationError as e:
            logger.error(f"❌ 角色配置校验失败 {char_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 加载角色 {char_id} 失败: {e}")
            return None
    
    def character_exists(self, char_id: str) -> bool:
        """检查角色是否存在（不加载完整配置）"""
        char_dir = self.characters_dir / char_id
        return (char_dir / "config.json").exists()
    
    def list_available_characters(self) -> list:
        """
        列出所有可用角色（只扫描文件夹名，不加载配置）
        用于展示角色列表时使用
        """
        available = []
        for char_dir in self.characters_dir.iterdir():
            if char_dir.is_dir() and not char_dir.name.startswith('_'):
                if (char_dir / "config.json").exists():
                    available.append(char_dir.name)
        return available
    
    def reload_character(self, char_id: str) -> Optional[CharacterConfig]:
        """强制重新加载角色配置（忽略缓存）"""
        if char_id in self._cache:
            del self._cache[char_id]
        return self.get_character(char_id)
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("🗑️ 清空角色缓存")
