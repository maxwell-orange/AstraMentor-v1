"""
AstraMentor 配置管理模块

包含API配置、模型配置和学习参数配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# 加载.env文件中的环境变量
try:
    from dotenv import load_dotenv
    # 查找项目根目录下的.env文件
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # 如果没有安装python-dotenv，则跳过


@dataclass
class APIConfig:
    """API配置类"""
    
    # Antigravity 代理地址
    api_endpoint: str = "http://127.0.0.1:8045"
    
    # API密钥（必须从环境变量读取）
    api_key: str = field(
        default_factory=lambda: os.getenv("ASTRA_API_KEY", "")
    )
    
    # 传输方式
    transport: str = "rest"
    
    # 默认模型
    model_name: str = "gemini-3-flash"


@dataclass
class LearningConfig:
    """学习参数配置类"""
    
    # 学习率（α），决定练习对总成绩的影响程度
    # 通常取值 0.2 - 0.4
    learning_rate: float = 0.3
    
    # 任务难度上限配置
    # 选择题/概念问答
    difficulty_concept: float = 0.4
    # 基础代码填空
    difficulty_basic_code: float = 0.7
    # 复杂项目/手写算法
    difficulty_advanced: float = 1.0
    
    # 默认期望掌握度
    default_target_mastery: float = 0.8


@dataclass
class Config:
    """全局配置类"""
    
    api: APIConfig = field(default_factory=APIConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)


# 全局配置实例
config = Config()


def get_config() -> Config:
    """获取全局配置实例"""
    return config
