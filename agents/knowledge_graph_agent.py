"""
KnowledgeGraph Agent - 知识星图生成器
生成topic下的知识节点及依赖关系
"""

import logging
from typing import Dict, Any, List

from utils.api_client import APIClient
from models.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class KnowledgeGraphAgent:
    """
    知识星图生成Agent
    """

    SYSTEM_INSTRUCTION = """你是一位专业的知识星图架构师。

你的任务是：根据用户的学习主题、目标和当前水平，生成一个结构化的知识星图。

输出要求：
1. 使用 JSON Schema 定义的 KnowledgeGraph 格式
2. graph.topic 必须填写用户的学习主题
3. graph.name 设置为 "{主题} 学习路线图" 的格式
4. nodes 包含 5-15 个知识节点，每个节点需要：
   - id: 唯一标识符（如 "node_1", "node_2"）
   - name: 知识点名称（简洁明确）
   - attributes.weight_A: 根据用户当前水平设置（0.0-1.0）
     * 如果用户可能已掌握该知识点，设置为 0.6-0.9
     * 如果用户完全不懂，设置为 0.0-0.2
   - attributes.weight_B: 根据用户目标设置（0.0-1.0）
     * 如果该知识点对达成目标很重要，设置为 0.8-0.95
     * 如果该知识点只需了解即可，设置为 0.5-0.7
   - attributes.description: 1-2句话描述该知识点的核心内容和学习要点
   - attributes.user_note: 留空（用于用户后续填写个性化备注）
5. links 定义节点间的依赖关系：
   - source: 前置知识节点ID
   - target: 后续知识节点ID  
   - reason: 清晰说明为什么存在这个依赖
   - weight: 依赖强度（0.0-1.0）

设计原则：
- 节点粒度适中：每个节点是独立的教学单元
- 依赖清晰：确保是DAG（有向无环图）
- 个性化：根据用户的当前水平和目标，合理设置每个节点的 weight_A 和 weight_B
- 循序渐进：确保学习路径符合认知规律（先易后难）
"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        logger.info("KnowledgeGraphAgent 初始化完成")

    def generate_knowledge_graph(
        self,
        topic: str,
        learning_goal: str = "",
        current_level: str = "零基础",
        target_level: str = "掌握核心概念",
    ) -> Dict[str, Any]:
        """
        生成知识星图

        Args:
            topic: 学习主题（如"Python异步编程"）
            learning_goal: 学习目的（如"用于开发高性能Web服务"）
            current_level: 当前水平描述（如"零基础"、"了解基础语法"、"有一定项目经验"）
            target_level: 目标水平描述（如"掌握核心概念"、"能独立开发项目"、"达到专家水平"）

        Returns:
            图谱数据字典（从 Pydantic 模型转换）
        """
        # 构建用户输入上下文（只包含用户信息，不包含规则）
        prompt = f"""学习主题：{topic}

学习目的：{learning_goal if learning_goal else "系统学习该主题"}

我的当前水平：{current_level}

我的目标水平：{target_level}

请为我生成个性化的知识星图。"""

        logger.info(f"正在为主题 '{topic}' 生成知识星图...")

        try:
            # 使用结构化输出
            graph_model = self.api_client.generate_json(
                prompt=prompt,
                system_instruction=self.SYSTEM_INSTRUCTION,
                temperature=0.7,
                output_schema=KnowledgeGraph,
            )

            # 转换为字典（保持向后兼容）
            graph_data = graph_model.model_dump()

            logger.info(f"✅ 知识星图生成成功，包含 {len(graph_data['nodes'])} 个节点")
            return graph_data

        except Exception as e:
            logger.error(f"❌ 知识星图生成失败: {e}")
            raise

    def get_learning_path(self, graph_data: Dict[str, Any]) -> List[str]:
        """
        拓扑排序生成学习路径

        Returns:
            节点ID的排序列表
        """
        from collections import defaultdict, deque

        nodes = graph_data["nodes"]
        links = graph_data.get("links", [])  # 使用新的 links 字段

        # 构建图
        graph = defaultdict(list)
        in_degree = {node["id"]: 0 for node in nodes}

        for link in links:
            graph[link["source"]].append(link["target"])
            in_degree[link["target"]] += 1

        # Kahn算法
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        path = []

        while queue:
            current = queue.popleft()
            path.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return path

    def format_graph_summary(self, graph_data: Dict[str, Any]) -> str:
        """
        生成图谱的文字摘要

        Returns:
            可读的摘要文字
        """
        nodes = graph_data["nodes"]
        links = graph_data.get("links", [])

        summary = f"📊 知识星图包含 {len(nodes)} 个知识点，{len(links)} 个依赖关系\n\n"

        # 列出所有节点
        summary += "📚 知识节点：\n"
        for i, node in enumerate(nodes, 1):
            summary += f"  {i}. {node['name']}\n"

        return summary
