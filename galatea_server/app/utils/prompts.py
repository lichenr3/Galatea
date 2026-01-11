"""
Prompt 加载工具
支持从 TOML 文件加载角色人设 - 适配 v2.0 驱动型架构
"""
import tomllib
from app.core.config import settings
from typing import Dict, Any
from app.core.logger import get_logger
from app.infrastructure.managers.character_registry import CharacterRegistry

logger = get_logger(__name__)

def _format_examples(data: Dict[str, Any]) -> str:
    """辅助函数：格式化 few-shot 对话示例"""
    examples_str = ""
    # 检查是否存在 interaction_examples.case 结构
    if "interaction_examples" in data and "case" in data["interaction_examples"]:
        for case in data["interaction_examples"]["case"]:
            examples_str += (
                f"User Situation: {case['situation']}\n"
                f"Assistant Response: {case['response']}\n"
                f"---\n"
            )
    return examples_str

def load_persona(character: str, character_registry: CharacterRegistry, language: str = "zh") -> str:
    """
    从 TOML 文件加载角色人设并构建 prompt
    
    Args:
        character: 角色名称
        character_registry: 角色注册表实例
        language: 会话语言 (zh/en)
        
    Returns:
        构建好的完整 prompt 字符串
    """
    # 获取基础文件名
    filename = character_registry.get_character(character).persona.file
    
    # 如果是英文，尝试加载 _en 后缀的文件
    if language == "en":
        base_name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename_en = f"{base_name}_en.{ext}" if ext else f"{base_name}_en"
        toml_path = settings.CHARACTERS_DIR / character / filename_en
        # 如果英文版不存在，回退到默认
        if not toml_path.exists():
            logger.warning(f"⚠️ 角色 {character} 的英文 Prompt 文件 {filename_en} 不存在，将使用默认版本")
            toml_path = settings.CHARACTERS_DIR / character / filename
    else:
        toml_path = settings.CHARACTERS_DIR / character / filename
    
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
            
        char = data["character"]
        
        # 兼容性处理：支持多种字段名结构
        world_view_data = char.get("world_view", {})
        world_view = world_view_data.get("reality_definition") or world_view_data.get("perspective") or ""
        
        cognitive_data = char.get("cognitive_model", {})
        cognitive_model = cognitive_data.get("motivation") or cognitive_data.get("mentality") or ""
        
        persona_data = char.get("persona", {})
        traits = persona_data.get("traits") or persona_data.get("demeanor") or ""
        
        rules_data = char.get("interaction_guidelines", {})
        rules = rules_data.get("rules") or ""
        
        # 2. 格式化示例
        examples_block = _format_examples(data)

        # 3. 构建最终的 System Prompt
        if language == "en":
            final_prompt = f"""
            [Role Definition]
            Name: {char['name']}
            Source: {char.get('source', 'Unknown')}
            Role: {char['role']}

            [World View & Perception]
            {world_view}

            [Cognitive Model & Motivation]
            {cognitive_model}

            [Personality Traits]
            {traits}

            [Interaction Guidelines]
            {rules}

            [Reference Examples (Strict Style Adherence)]
            {examples_block}

            [System Instruction]
            You are NOT an AI assistant. You are the character defined above. 
            Immerse yourself fully in the 'World View'. 
            Respond only in English. Use natural, character-appropriate language.
            """
        else:
            final_prompt = f"""
            [Role Definition]
            Name: {char['name']}
            Source: {char.get('source', 'Unknown')}
            Role: {char['role']}

            [World View & Perception]
            {world_view}

            [Cognitive Model & Motivation]
            {cognitive_model}

            [Personality Traits]
            {traits}

            [Interaction Guidelines]
            {rules}

            [Reference Examples (Strict Style Adherence)]
            {examples_block}

            [System Instruction]
            你不是一个 AI 助手。你就是上面定义的那个角色。
            请完全沉浸在你的“世界观”中。
            请只使用中文回复。使用自然、符合角色性格的语言。
            """
        
        logger.info(f"✅ 成功加载角色: {char['name']} ({character}) [{language}]")
        return final_prompt.strip()

    except FileNotFoundError:
        logger.error(f"❌ Prompt 文件未找到: {toml_path}")
        return f"System Error: Prompt file '{filename}' not found."
    
    except KeyError as e:
        logger.error(f"❌ Prompt 文件格式不匹配 (V2 架构): 缺少字段 {e}")
        # 这里可以返回一个默认的错误提示，或者抛出异常
        return "System Error: Invalid prompt file format. Please update TOML to V2 schema."
        
    except Exception as e:
        logger.error(f"⚠️ Prompt 加载失败: {e}", exc_info=True)
        return f"You are a helpful AI assistant."
