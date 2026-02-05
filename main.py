"""
AstraMentor - 双Agent教学系统

主程序入口，实现整体工作流控制
"""

import logging
import sys
from pathlib import Path

from agents.teacher_agent import TeacherAgent
from agents.evaluation_agent import EvaluationAgent
from agents.knowledge_graph_agent import KnowledgeGraphAgent
from core.learner_state import LearnerState, KnowledgePoint
from utils.api_client import APIClient
import json


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        self.knowledge_graph = KnowledgeGraphAgent(api_client=self.api_client)
        self.teacher = TeacherAgent(api_client=self.api_client)
        self.evaluator = EvaluationAgent(api_client=self.api_client)

        # 初始化学习者状态
        self.learner_state = LearnerState(state_file=state_file)

        logger.info("AstraMentor 初始化完成")

    def generate_knowledge_graph(self, topic: str, user_note: str = "") -> dict | None:
        """
        生成知识图谱

        Args:
            topic: 学习主题
            user_note: 用户备注

        Returns:
            图谱数据，失败或取消返回None
        """
        print("\n" + "=" * 60)
        print(f"🎓 AstraMentor - 知识图谱生成器")
        print("=" * 60)
        print(f"\n📚 主题: {topic}")
        if user_note:
            print(f"📝 备注: {user_note}")
        print()

        # 生成知识图谱
        print("🌟 正在生成知识图谱...")
        try:
            graph_data = self.knowledge_graph.generate_knowledge_graph(
                topic=topic, user_note=user_note
            )
        except Exception as e:
            print(f"❌ 知识图谱生成失败: {e}")
            print("请检查API配置或稍后重试")
            return None

        # 保存图谱到文件
        test_data_dir = Path("test_data")
        graph_filename = (
            f"knowledge_graph_{topic.replace(' ', '_').replace('/', '_')}.json"
        )
        graph_file = test_data_dir / graph_filename
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 知识图谱已保存到: {graph_file}")

        # 显示图谱摘要
        summary = self.knowledge_graph.format_graph_summary(graph_data)
        print("\n" + summary)

        # 用户确认图谱
        choice = (
            input("\n请选择操作 [Y]确认图谱 / [R]重新生成 / [Q]退出: ").strip().upper()
        )
        if choice == "Q":
            print("\n👋 已取消")
            return None
        elif choice == "R":
            # 递归重新生成
            return self.generate_knowledge_graph(topic, user_note)

        return graph_data

    def start_learning(
        self,
        node_name: str,
        node_description: str = "",
        user_note: str = "",
        target_mastery: float = 0.8,
        current_mastery: float = 0.0,
    ) -> None:
        """
        开始学习一个知识节点

        Args:
            node_name: 知识节点名称
            node_description: 节点描述（AI生成）
            user_note: 用户备注（个性化需求）
            target_mastery: 目标掌握度（B权重）
            current_mastery: 初始掌握度（A权重）
        """
        print("\n" + "=" * 60)
        print(f"🎓 AstraMentor - AI教学助手")
        print("=" * 60)
        print(f"\n📖 开始学习: {node_name}")
        if node_description:
            print(f"📝 描述: {node_description}")
        if user_note:
            print(f"💬 你的需求: {user_note}")
        print(f"📊 当前掌握度: {current_mastery:.1%}")
        print(f"🎯 目标掌握度: {target_mastery:.1%}")
        print()

        # 合并描述和用户备注
        combined_note = node_description
        if user_note:
            combined_note = (
                f"{node_description}\n\n用户需求: {user_note}"
                if node_description
                else user_note
            )

        # 添加或获取知识点
        kp = self.learner_state.add_knowledge_point(
            name=node_name,
            target_mastery=target_mastery,
            note=combined_note,
            initial_mastery=current_mastery,
        )

        # 阶段1：生成教学计划
        plan = self._generate_and_confirm_plan(kp)
        if plan is None:
            print("\n👋 学习已取消，下次再见！")
            return
        # 这个plan 没有被用到，应该可以用来更细致的做教学的步骤
        # good to make this a list of todos for the teaching loop
        
        # 阶段2：开始教学循环
        self._teaching_loop(kp)

        # 完成学习
        self._show_completion_summary(kp)

    def _generate_and_confirm_plan(self, knowledge_point: KnowledgePoint) -> str | None:
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
            print("-" * 50)
            print(plan)
            print("-" * 50)

            choice = (
                input("\n请选择操作 [Y]接受 / [N]重新生成 / [Q]取消: ").strip().upper()
            )

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
            
            
            # 1.5 这里应该有一个讨论环节：跟据内容允许答疑，直到用户满意为止
            current_discussion_round = 0
            max_discussion_rounds = 10
            
            discussion_history = []

            while current_discussion_round < max_discussion_rounds:
                print("\n💬 讨论环节:")
                # He should be able to use the knowledge as context, answer questions, etc.
                print("你可以就刚才的内容提出问题或讨论！")
                question = input("请输入你的问题（直接回车跳过讨论环节）: ").strip()
                if question:
                    discussion_response = self.teacher.discuss(
                        knowledge_point=knowledge_point, teaching_content= teaching_content,question=question, discussion_history = discussion_history
                    )
                    print("\n" + discussion_response)
                    discussion_history.append({
                        "question": question,
                        "response": discussion_response
                    })
                    
                    
                else:
                    print("跳过讨论环节。")
                    break
                
                
                if current_discussion_round % 3 == 2:
                    user_input = input(f"\n你有信心进入测试，来检测你对当前知识点的掌握程度吗？[(Yes)进入测试/(No)继续学习]: ").strip()
                    if user_input == "Yes" or user_input == "进入测试":
                        break
                    elif user_input == "No" or user_input == "继续学习":
                        print("\n🎓 继续讲解...")
                        current_discussion_round += 1
                    else:
                        print("无效输入，请输入 '继续' 或 '退出'")
                current_discussion_round += 1
            # 2. 提问/Quiz, check that the user is mastering the content
            print("\n❓ 测试问题，用来检验你的掌握情况:")
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
                knowledge_point=knowledge_point, question=question, answer=answer
            )

            # 5. 更新状态
            self.evaluator.update_learner_state(
                learner_state=self.learner_state,
                knowledge_point_name=knowledge_point.name,
                evaluation_result=evaluation,
            )

            # 重新获取更新后的知识点
            knowledge_point = self.learner_state.get_knowledge_point(
                knowledge_point.name
            )

            # 6. 显示反馈
            feedback = self.evaluator.get_progress_feedback(
                evaluation_result=evaluation, knowledge_point=knowledge_point
            )
            print("\n" + feedback)

            # 7. 如果需要，解释答案
            if evaluation.score < 0.8:
                print("\n📝 答案解析:")
                explanation = self.teacher.explain_answer(
                    knowledge_point=knowledge_point,
                    question=question,
                    user_answer=answer,
                    correct_analysis=evaluation.analysis,
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
        print("\n" + "=" * 60)
        print("📊 学习总结")
        print("=" * 60)
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
    print("=" * 60)
    print("  🌟 欢迎使用 AstraMentor - AI教学助手 🌟")
    print("=" * 60)

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
    print("\n请输入学习主题:")
    topic = input("主题名称: ").strip()
    if not topic:
        print("❌ 主题名称不能为空")
        sys.exit(1)

    note = input("备注（可选）: ").strip()

    # 第一步：生成知识图谱
    graph_data = mentor.generate_knowledge_graph(topic=topic, user_note=note)
    if graph_data is None:
        print("\n👋 已退出")
        sys.exit(0)

    # 第二步：选择要学习的节点
    learning_path = mentor.knowledge_graph.get_learning_path(graph_data)
    print(
        f"\n建议学习顺序: {' → '.join([n['name'] for n in graph_data['nodes'] if n['id'] in learning_path[:3]])}..."
    )
    print("\n可用的知识节点：")
    for i, node in enumerate(graph_data["nodes"], 1):
        level_icon = ["🔰", "📚", "🚀", "🌟"][min(node.get("level", 0), 3)]
        print(f"  {i}. {level_icon} {node['name']} ({node.get('difficulty', '中级')})")

    node_choice = input("\n请选择要学习的节点编号（直接回车选择第一个）: ").strip()
    if not node_choice:
        selected_node = graph_data["nodes"][0]
    else:
        try:
            idx = int(node_choice) - 1
            selected_node = graph_data["nodes"][idx]
        except (ValueError, IndexError):
            print("❌ 无效的选择，自动选择第一个节点")
            selected_node = graph_data["nodes"][0]

    print(f"\n已选择: {selected_node['name']}")
    if selected_node.get("description"):
        print(f"描述: {selected_node['description']}")

    # 第三步：添加个性化备注
    print("\n你可以为这个知识点添加个性化需求（可选）：")
    print("例如: '我想了解实际项目应用'、'重点讲解性能优化'、'需要更多代码示例'等")
    user_note = input("备注: ").strip()

    # 第四步：设置学习参数
    try:
        current = float(input("\n当前掌握度 (0.0-1.0，默认0.0): ").strip() or "0.0")
        target = float(input("目标掌握度 (0.0-1.0，默认0.8): ").strip() or "0.8")
    except ValueError:
        print("❌ 请输入有效的数字")
        sys.exit(1)

    # 第五步：开始学习
    mentor.start_learning(
        node_name=selected_node["name"],
        node_description=selected_node.get("description", ""),
        user_note=user_note,
        target_mastery=target,
        current_mastery=current,
    )


if __name__ == "__main__":
    main()
