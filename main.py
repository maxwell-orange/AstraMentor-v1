"""
AstraMentor - 双Agent教学系统

主程序入口，实现整体工作流控制
"""

import logging
import sys
from pathlib import Path

from agents.teacher_agent import TeacherAgent
from agents.evaluation_agent import EvaluationAgent
from core.learner_state import LearnerState, KnowledgePoint
from utils.api_client import APIClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AstraMentor:
    """
    AstraMentor 主控制器
    
    协调Teacher Agent和Evaluation Agent的工作流
    """
    
    def __init__(self, state_file: str = "learner_state.json"):
        """
        初始化AstraMentor
        
        Args:
            state_file: 学习状态持久化文件路径
        """
        # 初始化共享的API客户端
        self.api_client = APIClient()
        
        # 初始化Agents
        self.teacher = TeacherAgent(api_client=self.api_client)
        self.evaluator = EvaluationAgent(api_client=self.api_client)
        
        # 初始化学习者状态
        self.learner_state = LearnerState(state_file=state_file)
        
        logger.info("AstraMentor 初始化完成")
    
    def start_learning(
        self,
        topic: str,
        target_mastery: float = 0.8,
        current_mastery: float = 0.0,
        note: str = ""
    ) -> None:
        """
        开始学习一个知识点
        
        Args:
            topic: 知识点名称
            target_mastery: 目标掌握度（B权重）
            current_mastery: 初始掌握度（A权重）
            note: 用户备注
        """
        print("\n" + "="*60)
        print(f"🎓 AstraMentor - AI教学助手")
        print("="*60)
        print(f"\n📚 开始学习: {topic}")
        print(f"📊 当前掌握度: {current_mastery:.1%}")
        print(f"🎯 目标掌握度: {target_mastery:.1%}")
        if note:
            print(f"📝 备注: {note}")
        print()
        
        # 添加或获取知识点
        kp = self.learner_state.add_knowledge_point(
            name=topic,
            target_mastery=target_mastery,
            note=note,
            initial_mastery=current_mastery
        )
        
        # 阶段1：生成教学计划
        plan = self._generate_and_confirm_plan(kp)
        if plan is None:
            print("\n👋 学习已取消，下次再见！")
            return
        
        # 阶段2：开始教学循环
        self._teaching_loop(kp)
        
        # 完成学习
        self._show_completion_summary(kp)
    
    def _generate_and_confirm_plan(
        self,
        knowledge_point: KnowledgePoint
    ) -> str | None:
        """
        生成教学计划并确认
        
        Args:
            knowledge_point: 知识点对象
            
        Returns:
            确认后的教学计划，取消返回None
        """
        while True:
            print("🔄 正在生成教学计划...")
            plan = self.teacher.generate_teaching_plan(knowledge_point)
            
            print("\n📋 教学计划:")
            print("-"*50)
            print(plan)
            print("-"*50)
            
            choice = input("\n请选择操作 [Y]接受 / [N]重新生成 / [Q]取消: ").strip().upper()
            
            if choice == "Y" or choice == "":
                return plan
            elif choice == "Q":
                return None
            elif choice == "N":
                note = input("请输入修改意见（直接回车跳过）: ").strip()
                if note:
                    knowledge_point.note = note
                continue
            else:
                print("⚠️ 无效输入，请重新选择")
    
    def _teaching_loop(self, knowledge_point: KnowledgePoint) -> None:
        """
        教学循环
        
        持续教学直到达到目标掌握度
        
        Args:
            knowledge_point: 知识点对象
        """
        iteration = 0
        max_iterations = 20  # 防止无限循环
        
        while not knowledge_point.is_mastered() and iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"📖 第 {iteration} 轮学习")
            print(f"{'='*60}")
            
            # 1. 教学
            print("\n🎓 正在讲解...")
            teaching_content = self.teacher.teach(knowledge_point)
            print("\n" + teaching_content)
            
            input("\n按回车继续进行知识检验...")
            
            # 2. 提问
            print("\n❓ 验证问题:")
            question = self.teacher.generate_question(knowledge_point)
            print(question)
            
            # 3. 获取用户回答
            print("\n请输入你的回答（输入多行时，输入空行结束）:")
            answer_lines = []
            while True:
                line = input()
                if line == "":
                    break
                answer_lines.append(line)
            answer = "\n".join(answer_lines)
            
            if not answer.strip():
                print("⚠️ 回答不能为空，请重新输入")
                continue
            
            # 4. 评估
            print("\n🔍 正在评估...")
            evaluation = self.evaluator.evaluate(
                knowledge_point=knowledge_point,
                question=question,
                answer=answer
            )
            
            # 5. 更新状态
            self.evaluator.update_learner_state(
                learner_state=self.learner_state,
                knowledge_point_name=knowledge_point.name,
                evaluation_result=evaluation
            )
            
            # 重新获取更新后的知识点
            knowledge_point = self.learner_state.get_knowledge_point(
                knowledge_point.name
            )
            
            # 6. 显示反馈
            feedback = self.evaluator.get_progress_feedback(
                evaluation_result=evaluation,
                knowledge_point=knowledge_point
            )
            print("\n" + feedback)
            
            # 7. 如果需要，解释答案
            if evaluation.score < 0.8:
                print("\n📝 答案解析:")
                explanation = self.teacher.explain_answer(
                    knowledge_point=knowledge_point,
                    question=question,
                    user_answer=answer,
                    correct_analysis=evaluation.analysis
                )
                print(explanation)
            
            # 检查是否达到目标
            if knowledge_point.is_mastered():
                print("\n🎉 恭喜！你已经掌握了这个知识点！")
                break
            
            # 继续下一轮
            choice = input("\n是否继续学习？[Y]继续 / [Q]退出: ").strip().upper()
            if choice == "Q":
                break
    
    def _show_completion_summary(self, knowledge_point: KnowledgePoint) -> None:
        """
        显示学习完成摘要
        
        Args:
            knowledge_point: 知识点对象
        """
        print("\n" + "="*60)
        print("📊 学习总结")
        print("="*60)
        print(f"知识点: {knowledge_point.name}")
        print(f"最终掌握度: {knowledge_point.actual_mastery:.1%}")
        print(f"目标掌握度: {knowledge_point.target_mastery:.1%}")
        print(f"学习轮数: {len(knowledge_point.history)}")
        
        if knowledge_point.is_mastered():
            print("\n✅ 恭喜！你已成功达到学习目标！")
        else:
            remaining = knowledge_point.target_mastery - knowledge_point.actual_mastery
            print(f"\n⏳ 继续加油！距离目标还差 {remaining:.1%}")
        
        # 显示整体进度
        summary = self.learner_state.get_progress_summary()
        print(f"\n📈 总体学习进度:")
        print(f"   已学知识点: {summary['total']} 个")
        print(f"   已掌握: {summary['mastered']} 个")
        print(f"   平均掌握度: {summary['average_mastery']:.1%}")


def main():
    """主函数"""
    print("="*60)
    print("  🌟 欢迎使用 AstraMentor - AI教学助手 🌟")
    print("="*60)
    
    # 测试API连接
    print("\n正在测试API连接...")
    client = APIClient()
    if not client.test_connection():
        print("❌ API连接失败，请检查配置")
        print("提示: 确保Antigravity代理服务正在运行（http://127.0.0.1:8045）")
        sys.exit(1)
    print("✅ API连接成功！")
    
    # 创建主程序
    mentor = AstraMentor()
    
    # 获取用户输入
    print("\n请输入学习信息:")
    topic = input("知识点名称: ").strip()
    if not topic:
        print("❌ 知识点名称不能为空")
        sys.exit(1)
    
    try:
        current = float(input("当前掌握度 (0.0-1.0，默认0.0): ").strip() or "0.0")
        target = float(input("目标掌握度 (0.0-1.0，默认0.8): ").strip() or "0.8")
    except ValueError:
        print("❌ 请输入有效的数字")
        sys.exit(1)
    
    note = input("备注（可选）: ").strip()
    
    # 开始学习
    mentor.start_learning(
        topic=topic,
        target_mastery=target,
        current_mastery=current,
        note=note
    )


if __name__ == "__main__":
    main()
