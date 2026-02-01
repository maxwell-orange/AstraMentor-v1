"""
Evaluation Agent 模块

负责评估用户回答并更新学习程度
"""

import logging
from dataclasses import dataclass
from typing import Optional

from core.learner_state import KnowledgePoint, LearnerState
from core.scoring import ScoringEngine, TaskDifficulty, ScoringResult
from core.prompts import get_evaluation_prompt
from utils.api_client import APIClient


logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """评估结果数据类"""
    
    # AI评分（0.0-1.0）
    score: float
    
    # 给用户的反馈
    feedback: str
    
    # 系统分析
    analysis: str
    
    # 评分计算结果
    scoring_result: Optional[ScoringResult] = None
    
    # 是否已达到目标
    mastery_achieved: bool = False


class EvaluationAgent:
    """
    评估Agent
    
    负责：
    1. 评估用户对问题的回答（0.0-1.0评分）
    2. 根据评分更新学习程度（使用EMA公式）
    3. 生成反馈和分析
    """
    
    def __init__(
        self,
        api_client: Optional[APIClient] = None,
        scoring_engine: Optional[ScoringEngine] = None
    ):
        """
        初始化Evaluation Agent
        
        Args:
            api_client: API客户端，为None时自动创建
            scoring_engine: 评分引擎，为None时自动创建
        """
        self.api_client = api_client or APIClient()
        self.scoring_engine = scoring_engine or ScoringEngine()
        logger.info("Evaluation Agent 初始化完成")
    
    def evaluate(
        self,
        knowledge_point: KnowledgePoint,
        question: str,
        answer: str,
        question_type: str = ""
    ) -> EvaluationResult:
        """
        评估用户回答
        
        Args:
            knowledge_point: 知识点对象
            question: 问题内容
            answer: 用户回答
            question_type: 问题类型（用于判断难度）
            
        Returns:
            EvaluationResult评估结果
        """
        # 1. 使用AI进行评分
        ai_result = self._get_ai_evaluation(
            topic=knowledge_point.name,
            question=question,
            answer=answer,
            current_score=knowledge_point.actual_mastery
        )
        
        # 2. 确定任务难度
        if question_type:
            difficulty = self.scoring_engine.determine_difficulty(question_type)
        else:
            difficulty = self.scoring_engine.determine_difficulty(question)
        
        # 3. 获取上次练习时间（用于时间遗忘计算）
        last_practice_time = knowledge_point.get_last_practice_time()
        
        # 4. 计算新的掌握度（使用增强版算法）
        scoring_result = self.scoring_engine.calculate_new_mastery(
            old_mastery=knowledge_point.actual_mastery,
            task_score=ai_result["score"],
            difficulty=difficulty,
            last_practice_time=last_practice_time,
            use_enhanced=True
        )
        
        # 4. 检查是否达到目标
        mastery_achieved = (
            scoring_result.new_mastery >= knowledge_point.target_mastery
        )
        
        logger.info(
            f"知识点 '{knowledge_point.name}' 评估完成: "
            f"评分={ai_result['score']:.2f}, "
            f"掌握度 {scoring_result.old_mastery:.2f} -> {scoring_result.new_mastery:.2f}"
        )
        
        return EvaluationResult(
            score=ai_result["score"],
            feedback=ai_result["feedback"],
            analysis=ai_result["analysis"],
            scoring_result=scoring_result,
            mastery_achieved=mastery_achieved
        )
    
    def _get_ai_evaluation(
        self,
        topic: str,
        question: str,
        answer: str,
        current_score: float
    ) -> dict:
        """
        使用AI获取评分
        
        Args:
            topic: 知识点名称
            question: 问题
            answer: 用户回答
            current_score: 当前掌握度
            
        Returns:
            包含score、feedback、analysis的字典
        """
        prompt = get_evaluation_prompt(
            topic=topic,
            question=question,
            answer=answer,
            current_score=current_score
        )
        
        result = self.api_client.generate_json(
            prompt=prompt,
            temperature=0.3  # 使用较低温度保证评分稳定性
        )
        
        # 确保返回值格式正确
        return {
            "score": float(result.get("score", 0.5)),
            "feedback": str(result.get("feedback", "评估完成")),
            "analysis": str(result.get("analysis", "无详细分析"))
        }
    
    def update_learner_state(
        self,
        learner_state: LearnerState,
        knowledge_point_name: str,
        evaluation_result: EvaluationResult
    ) -> bool:
        """
        更新学习者状态
        
        Args:
            learner_state: 学习者状态对象
            knowledge_point_name: 知识点名称
            evaluation_result: 评估结果
            
        Returns:
            是否更新成功
        """
        if evaluation_result.scoring_result is None:
            logger.error("评估结果中缺少scoring_result")
            return False
        
        return learner_state.update_mastery(
            name=knowledge_point_name,
            new_mastery=evaluation_result.scoring_result.new_mastery,
            score=evaluation_result.score,
            feedback=evaluation_result.feedback
        )
    
    def get_progress_feedback(
        self,
        evaluation_result: EvaluationResult,
        knowledge_point: KnowledgePoint
    ) -> str:
        """
        生成进度反馈信息
        
        Args:
            evaluation_result: 评估结果
            knowledge_point: 知识点对象
            
        Returns:
            进度反馈文本
        """
        sr = evaluation_result.scoring_result
        if sr is None:
            return evaluation_result.feedback
        
        # 构建进度信息
        score_desc = self.scoring_engine.format_score_feedback(
            evaluation_result.score
        )
        
        improvement = sr.get_improvement()
        if improvement > 0:
            progress_text = f"📈 掌握度提升了 {improvement:.1%}"
        elif improvement < 0:
            progress_text = f"📉 掌握度下降了 {abs(improvement):.1%}"
        else:
            progress_text = "➡️ 掌握度保持不变"
        
        # 目标进度
        current = sr.new_mastery
        target = knowledge_point.target_mastery
        if current >= target:
            goal_text = "🎉 恭喜！你已达到学习目标！"
        else:
            remaining = target - current
            goal_text = f"🎯 距离目标还差 {remaining:.1%}"
        
        return f"""
**本次表现**: {score_desc}（{evaluation_result.score:.2f}分）
{evaluation_result.feedback}

**学习进度**: 
{progress_text}
当前掌握度: {current:.1%} | 目标: {target:.1%}
{goal_text}
""".strip()
