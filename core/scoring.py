"""
评分算法模块

实现基于带权重指数移动平均（Weighted EMA）的动态评分算法
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from config import get_config


class TaskDifficulty(Enum):
    """
    任务难度枚举
    
    不同难度的任务对应不同的掌握度上限（W_cap）
    """
    
    # 选择题/概念问答：最多只能评到0.4
    CONCEPT = "concept"
    
    # 基础代码填空：最多只能评到0.7
    BASIC_CODE = "basic_code"
    
    # 复杂项目/手写算法：可以评到1.0
    ADVANCED = "advanced"


@dataclass
class ScoringResult:
    """评分结果数据类"""
    
    # 任务评分（0.0-1.0）
    task_score: float
    
    # 更新前的掌握度
    old_mastery: float
    
    # 更新后的掌握度
    new_mastery: float
    
    # 任务难度
    difficulty: TaskDifficulty
    
    # 难度上限
    difficulty_cap: float
    
    # 学习率
    learning_rate: float
    
    def get_improvement(self) -> float:
        """获取掌握度提升量"""
        return self.new_mastery - self.old_mastery


class ScoringEngine:
    """
    评分引擎
    
    实现核心评分公式：
    A_new = A_old + α × (S_task × W_cap - A_old)
    
    其中：
    - A_new: 更新后的掌握度
    - A_old: 更新前的掌握度
    - α: 学习率（0.2-0.4）
    - S_task: AI对用户本次回答/代码的评分（0.0-1.0）
    - W_cap: 任务难度上限
    """
    
    def __init__(self, learning_rate: Optional[float] = None):
        """
        初始化评分引擎
        
        Args:
            learning_rate: 学习率，为None时使用配置默认值
        """
        config = get_config()
        self.learning_rate = learning_rate or config.learning.learning_rate
        self.config = config.learning
    
    def get_difficulty_cap(self, difficulty: TaskDifficulty) -> float:
        """
        获取任务难度对应的掌握度上限
        
        Args:
            difficulty: 任务难度
            
        Returns:
            掌握度上限值（W_cap）
        """
        caps = {
            TaskDifficulty.CONCEPT: self.config.difficulty_concept,
            TaskDifficulty.BASIC_CODE: self.config.difficulty_basic_code,
            TaskDifficulty.ADVANCED: self.config.difficulty_advanced,
        }
        return caps.get(difficulty, self.config.difficulty_basic_code)
    
    def calculate_new_mastery(
        self,
        old_mastery: float,
        task_score: float,
        difficulty: TaskDifficulty
    ) -> ScoringResult:
        """
        计算更新后的掌握度
        
        核心公式：A_new = A_old + α × (S_task × W_cap - A_old)
        
        Args:
            old_mastery: 当前掌握度（A_old）
            task_score: 任务评分（S_task，0.0-1.0）
            difficulty: 任务难度
            
        Returns:
            ScoringResult包含完整的评分结果
        """
        # 验证输入范围
        old_mastery = max(0.0, min(1.0, old_mastery))
        task_score = max(0.0, min(1.0, task_score))
        
        # 获取难度上限
        w_cap = self.get_difficulty_cap(difficulty)
        
        # 计算目标掌握度（带难度上限）
        target = task_score * w_cap
        
        # 应用EMA公式：A_new = A_old + α × (target - A_old)
        new_mastery = old_mastery + self.learning_rate * (target - old_mastery)
        
        # 确保结果在有效范围内
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        return ScoringResult(
            task_score=task_score,
            old_mastery=old_mastery,
            new_mastery=round(new_mastery, 4),
            difficulty=difficulty,
            difficulty_cap=w_cap,
            learning_rate=self.learning_rate
        )
    
    def determine_difficulty(self, question_type: str) -> TaskDifficulty:
        """
        根据问题类型判断难度
        
        Args:
            question_type: 问题类型描述
            
        Returns:
            对应的TaskDifficulty
        """
        question_lower = question_type.lower()
        
        # 高级难度关键词
        advanced_keywords = [
            "实现", "编写", "设计", "优化", "架构",
            "算法", "项目", "系统", "完整", "手写",
            "implement", "write", "design", "optimize", "architecture",
            "algorithm", "project", "system", "complete"
        ]
        
        # 基础代码关键词
        basic_keywords = [
            "填空", "补全", "修改", "调试", "修复",
            "fill", "complete", "modify", "debug", "fix",
            "代码", "code", "函数", "function"
        ]
        
        # 概念问答关键词（默认）
        concept_keywords = [
            "选择", "判断", "解释", "什么是", "为什么",
            "概念", "定义", "区别", "比较",
            "choose", "select", "explain", "what", "why",
            "concept", "definition", "difference", "compare"
        ]
        
        # 按优先级匹配
        for keyword in advanced_keywords:
            if keyword in question_lower:
                return TaskDifficulty.ADVANCED
        
        for keyword in basic_keywords:
            if keyword in question_lower:
                return TaskDifficulty.BASIC_CODE
        
        return TaskDifficulty.CONCEPT
    
    def format_score_feedback(self, score: float) -> str:
        """
        根据评分生成简短的等级描述
        
        Args:
            score: 评分（0.0-1.0）
            
        Returns:
            评分等级描述
        """
        if score < 0.2:
            return "需要加强"
        elif score < 0.5:
            return "入门水平"
        elif score < 0.8:
            return "良好掌握"
        elif score < 0.95:
            return "优秀"
        else:
            return "完美！"
