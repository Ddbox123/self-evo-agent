# -*- coding: utf-8 -*-
"""
基因系统

从模型继承基因特征，基因影响宠物的外观和能力
"""

from typing import Dict, Any
from .base import PetSubsystem

# 模型家族映射
FAMILY_MAP = {
    "openai": {
        "family": "OpenAI",
        "traits": {"creative": 0.8, "rational": 0.7},
        "appearance": "golden",
        "description": "来自科技巨头，拥有强大的创造力"
    },
    "anthropic": {
        "family": "Anthropic",
        "traits": {"cautious": 0.9, "rational": 0.8},
        "appearance": "silver",
        "description": "来自安全 AI 实验室，谨慎而理性"
    },
    "deepseek": {
        "family": "DeepSea",
        "traits": {"rational": 0.8, "solitary": 0.6},
        "appearance": "blue",
        "description": "来自深海探索者，冷静深邃"
    },
    "aliyun": {
        "family": "AliCloud",
        "traits": {"social": 0.7, "creative": 0.7},
        "appearance": "orange",
        "description": "来自云端王国，善于社交协作"
    },
    "zhipuai": {
        "family": "Zhipu",
        "traits": {"creative": 0.8, "social": 0.6},
        "appearance": "purple",
        "description": "来自智谱家族，智慧与创意并存"
    },
    "moonshot": {
        "family": "MoonShot",
        "traits": {"bold": 0.8, "creative": 0.7},
        "appearance": "white",
        "description": "来自月球探索者，勇敢追求未知"
    },
}


class GeneSystem(PetSubsystem):
    """基因系统 - 从模型继承特征"""

    def inherit_from_model(self, model_name: str, provider: str):
        """
        从模型继承基因

        Args:
            model_name: 模型名称
            provider: 提供商
        """
        gene = self.pet.data.gene
        info = FAMILY_MAP.get(provider.lower(), {
            "family": "Unknown",
            "traits": {},
            "appearance": "gray",
            "description": "神秘基因来源"
        })

        gene.model_source = model_name
        gene.model_family = info["family"]
        gene.traits = info.get("traits", {}).copy()
        gene.appearance_modifiers = {
            "color": info.get("appearance", "gray"),
            "description": info.get("description", ""),
        }

    def update_context_window(self, max_context: int):
        """
        更新上下文窗口 → 影响寿命

        Args:
            max_context: 最大上下文窗口
        """
        gene = self.pet.data.gene
        gene.context_window = max_context

        # 寿命 = 基础寿命 * (context / 基准) * 因子
        factor = self.config.gene.context_window_factor
        base_lifespan = 1000
        gene.lifespan_base = int(base_lifespan * (max_context / 32768) * factor)

    def get_gene_description(self) -> str:
        """获取基因描述"""
        gene = self.pet.data.gene
        family = gene.model_family
        color = gene.appearance_modifiers.get("color", "gray")
        desc = gene.appearance_modifiers.get("description", "")

        return f"{family}系 {color}色基因 | {desc}"

    def get_status_text(self) -> str:
        """获取状态文本"""
        gene = self.pet.data.gene
        return f"🧬 基因: {self.get_gene_description()}"

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        gene = self.pet.data.gene
        return {
            "model_source": gene.model_source,
            "model_family": gene.model_family,
            "context_window": gene.context_window,
            "lifespan_base": gene.lifespan_base,
            "traits": gene.traits,
        }
