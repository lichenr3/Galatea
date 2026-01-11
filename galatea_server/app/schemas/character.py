from __future__ import annotations

from typing import List, Literal, Optional, Dict, Union

from pydantic import BaseModel, Field


class PersonaConfig(BaseModel):
    file: str = Field(..., description="角色 persona 文件路径（通常相对角色目录）")
    type: Literal["toml", "json", "txt"] = Field("toml", description="persona 文件类型")


class VoiceConfig(BaseModel):
    gpt_model: str = Field(..., description="GPT 权重路径")
    sovits_model: str = Field(..., description="SoVITS 权重路径")
    reference_audio: str = Field(..., description="参考音频路径")
    prompt_text: str = Field("", description="参考音频对应的文本（为空则自动识别）")
    language: str = Field("zh", description="默认语言")
    speed: float = Field(1.0, description="语速")
    pitch: float = Field(0, description="音高偏移")


class ExpressionsConfig(BaseModel):
    file: str = Field(..., description="表情映射配置文件路径")
    default: str = Field("neutral", description="默认表情")


class AvatarConfig(BaseModel):
    image: str = Field("", description="头像图片路径/URL")
    model: str = Field("", description="Unity 模型标识（如 unity://...）")


class MetadataConfig(BaseModel):
    author: str = Field("", description="作者")
    created: str = Field("", description="创建日期（字符串）")
    tags: List[str] = Field(default_factory=list, description="标签")


class CharacterConfig(BaseModel):
    id: str = Field(..., description="角色 ID")
    name: Union[str, Dict[str, str]] = Field(..., description="角色名称（支持字符串或多语言对象）")
    display_name: str = Field("", description="展示名")
    version: str = Field("", description="版本号")
    description: Optional[Dict[str, str]] = Field(default_factory=dict, description="角色描述（多语言）")

    persona: PersonaConfig
    voice: VoiceConfig
    expressions: Optional[ExpressionsConfig] = None
    avatar: Optional[AvatarConfig] = None
    metadata: Optional[MetadataConfig] = None
    
    def get_name(self, language: str = "zh") -> str:
        """获取指定语言的角色名称"""
        if isinstance(self.name, dict):
            return self.name.get(language, self.name.get("zh", self.name.get("en", "")))
        return self.name


