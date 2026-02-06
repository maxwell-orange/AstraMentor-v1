"""
业务常量定义

包含学习程度、难度等级等业务相关的枚举值
"""

from typing import Dict, List


class LearningLevel:
    """学习水平定义"""

    # 当前水平选项
    CURRENT_LEVELS: Dict[str, str] = {
        "1": "零基础",
        "2": "了解基础概念",
        "3": "有一定实践经验",
        "4": "比较熟练",
    }

    # 目标水平选项
    TARGET_LEVELS: Dict[str, str] = {
        "1": "了解基本概念",
        "2": "掌握核心知识",
        "3": "能独立完成项目",
        "4": "达到专家水平",
    }

    # 默认值
    DEFAULT_CURRENT = "零基础"
    DEFAULT_TARGET = "掌握核心知识"

    @classmethod
    def get_current_level(cls, choice: str) -> str:
        """获取当前水平描述"""
        return cls.CURRENT_LEVELS.get(choice, cls.DEFAULT_CURRENT)

    @classmethod
    def get_target_level(cls, choice: str) -> str:
        """获取目标水平描述"""
        return cls.TARGET_LEVELS.get(choice, cls.DEFAULT_TARGET)

    @classmethod
    def display_current_options(cls) -> List[str]:
        """返回当前水平选项列表（用于显示）"""
        return [f"{k}. {v}" for k, v in cls.CURRENT_LEVELS.items()]

    @classmethod
    def display_target_options(cls) -> List[str]:
        """返回目标水平选项列表（用于显示）"""
        return [f"{k}. {v}" for k, v in cls.TARGET_LEVELS.items()]
