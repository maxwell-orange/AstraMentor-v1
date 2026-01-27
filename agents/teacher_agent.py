"""
Teacher Agent 模块

负责教学功能，包括生成教学计划、按计划教学和提问验证
"""

import logging
from typing import Optional

from core.learner_state import KnowledgePoint
from core.prompts import (
    get_teaching_prompt,
    get_teaching_plan_prompt,
    get_question_prompt
)
from utils.api_client import APIClient


logger = logging.getLogger(__name__)


class TeacherAgent:
    """
    教学Agent
    
    负责：
    1. 根据知识点和用户状态生成教学计划
    2. 按计划逐步教学
    3. 每次讲解后生成验证问题
    """
    
    def __init__(self, api_client: Optional[APIClient] = None):
        """
        初始化Teacher Agent
        
        Args:
            api_client: API客户端，为None时自动创建
        """
        self.api_client = api_client or APIClient()
        logger.info("Teacher Agent 初始化完成")
    
    def generate_teaching_plan(
        self,
        knowledge_point: KnowledgePoint
    ) -> str:
        """
        生成教学计划
        
        Args:
            knowledge_point: 知识点对象
            
        Returns:
            教学计划文本
        """
        prompt = get_teaching_plan_prompt(
            topic=knowledge_point.name,
            current_score=knowledge_point.actual_mastery,
            target_score=knowledge_point.target_mastery,
            note=knowledge_point.note
        )
        
        system_instruction = """
你是AstraMentor，一位专业的AI编程教育专家。
你的任务是为学习者制定个性化的教学计划。
请确保计划循序渐进，适合学习者当前的水平。
"""
        
        plan = self.api_client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.7
        )
        
        logger.info(f"已生成知识点 '{knowledge_point.name}' 的教学计划")
        return plan
    
    def teach(
        self,
        knowledge_point: KnowledgePoint,
        context: str = ""
    ) -> str:
        """
        进行教学
        
        根据知识点的掌握程度选择合适的教学风格
        
        Args:
            knowledge_point: 知识点对象
            context: 额外的上下文信息
            
        Returns:
            教学内容
        """
        # 获取教学阶段
        stage = knowledge_point.get_teaching_stage()
        
        # 获取对应阶段的教学提示词
        system_instruction = get_teaching_prompt(
            stage=stage,
            topic=knowledge_point.name,
            current_score=knowledge_point.actual_mastery
        )
        
        # 构建用户提示
        user_prompt = f"请讲解知识点：{knowledge_point.name}"
        if knowledge_point.note:
            user_prompt += f"\n\n用户备注：{knowledge_point.note}"
        if context:
            user_prompt += f"\n\n补充说明：{context}"
        
        # 生成教学内容
        teaching_content = self.api_client.generate(
            prompt=user_prompt,
            system_instruction=system_instruction,
            temperature=0.7
        )
        
        logger.info(
            f"已完成知识点 '{knowledge_point.name}' 的阶段{stage}教学"
        )
        return teaching_content
    
    def generate_question(
        self,
        knowledge_point: KnowledgePoint
    ) -> str:
        """
        生成验证问题
        
        根据当前教学阶段生成适合的验证问题
        
        Args:
            knowledge_point: 知识点对象
            
        Returns:
            问题内容
        """
        stage = knowledge_point.get_teaching_stage()
        
        prompt = get_question_prompt(
            topic=knowledge_point.name,
            stage=stage,
            current_score=knowledge_point.actual_mastery
        )
        
        system_instruction = """
你是AstraMentor的提问助手。
请根据学习者的当前水平，生成一个适合的验证问题。
问题应该能够准确评估学习者对知识点的掌握程度。
直接输出问题内容，不要有多余的前缀或解释。
"""
        
        question = self.api_client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.6
        )
        
        logger.info(f"已生成知识点 '{knowledge_point.name}' 的验证问题")
        return question.strip()
    
    def explain_answer(
        self,
        knowledge_point: KnowledgePoint,
        question: str,
        user_answer: str,
        correct_analysis: str
    ) -> str:
        """
        解释正确答案
        
        当用户回答不够完美时，提供详细的解释
        
        Args:
            knowledge_point: 知识点对象
            question: 原问题
            user_answer: 用户的回答
            correct_analysis: 评分分析
            
        Returns:
            答案解释
        """
        stage = knowledge_point.get_teaching_stage()
        
        system_instruction = get_teaching_prompt(
            stage=stage,
            topic=knowledge_point.name,
            current_score=knowledge_point.actual_mastery
        )
        
        prompt = f"""
【问题】{question}

【用户的回答】{user_answer}

【分析】{correct_analysis}

请基于以上信息，为用户详细解释正确的答案或更好的解法。
保持鼓励的语气，帮助用户理解自己的不足之处。
"""
        
        explanation = self.api_client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.7
        )
        
        return explanation
