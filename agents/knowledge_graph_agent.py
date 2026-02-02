"""
KnowledgeGraph Agent - 知识图谱生成器
生成topic下的知识节点及依赖关系
"""

import logging
from typing import Dict, Any, List

from utils.api_client import APIClient

logger = logging.getLogger(__name__)


class KnowledgeGraphAgent:
    """
    知识图谱生成Agent
    只负责生成图谱结构，不负责教学计划
    """

    SYSTEM_INSTRUCTION = """你是知识图谱架构师。

分析学习主题，拆分成5-15个可独立学习的知识节点。

输出JSON格式：
{
  "nodes": [
    {
      "id": "n1",
      "name": "知识点名称",
      "description": "1-2句话描述学习内容",
      "level": 0,              // 0=基础, 1=进阶, 2=高级, 3=专家
      "difficulty": "初级",     // 初级/中级/高级/专家
      "prerequisites": []       // 前置节点ID数组
    }
  ],
  "edges": [
    {"source": "n1", "target": "n2"}  // n1是n2的前置知识
  ]
}

要求：
1. 节点粒度适中：每个节点是独立的教学单元（可单独讲解+出题）
2. 依赖清晰：确保是DAG（有向无环图）
3. 层级递进：level从0开始，逐层增加
4. 难度合理：初级→中级→高级→专家
"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        logger.info("KnowledgeGraphAgent 初始化完成")

    def generate_knowledge_graph(
        self, topic: str, user_note: str = ""
    ) -> Dict[str, Any]:
        """
        生成知识图谱

        Args:
            topic: 学习主题（如"Python异步编程"）
            user_note: 用户备注（可选）

        Returns:
            图谱JSON数据
            {
                "nodes": [...],
                "edges": [...]
            }
        """
        prompt = f"""请为以下主题生成知识图谱：

主题：{topic}
"""
        if user_note:
            prompt += f"用户需求：{user_note}\n"

        prompt += "\n请严格按照JSON格式输出。"

        logger.info(f"正在为主题 '{topic}' 生成知识图谱...")

        try:
            graph_data = self.api_client.generate_json(
                prompt=prompt,
                system_instruction=self.SYSTEM_INSTRUCTION,
                temperature=0.7,
            )

            # 验证数据
            if not self._validate_graph(graph_data):
                raise ValueError("图谱数据格式不正确")

            logger.info(f"✅ 知识图谱生成成功，包含 {len(graph_data['nodes'])} 个节点")
            return graph_data

        except Exception as e:
            logger.error(f"❌ 知识图谱生成失败: {e}")
            raise

    def _validate_graph(self, data: Dict[str, Any]) -> bool:
        """验证图谱数据格式"""
        if not isinstance(data, dict):
            return False

        if "nodes" not in data or "edges" not in data:
            return False

        # 验证节点
        node_ids = set()
        for node in data["nodes"]:
            required_fields = ["id", "name", "level", "difficulty"]
            if not all(field in node for field in required_fields):
                return False
            node_ids.add(node["id"])

        # 验证边
        for edge in data["edges"]:
            if "source" not in edge or "target" not in edge:
                return False
            if edge["source"] not in node_ids or edge["target"] not in node_ids:
                return False

        return True

    def get_learning_path(self, graph_data: Dict[str, Any]) -> List[str]:
        """
        拓扑排序生成学习路径

        Returns:
            节点ID的排序列表
        """
        from collections import defaultdict, deque

        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # 构建图
        graph = defaultdict(list)
        in_degree = {node["id"]: 0 for node in nodes}

        for edge in edges:
            graph[edge["source"]].append(edge["target"])
            in_degree[edge["target"]] += 1

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
        edges = graph_data["edges"]

        summary = f"📊 知识图谱包含 {len(nodes)} 个知识点，{len(edges)} 个依赖关系\n\n"

        # 按层级分组
        levels = {}
        for node in nodes:
            level = node.get("level", 0)
            if level not in levels:
                levels[level] = []
            levels[level].append(node["name"])

        summary += "🎓 学习路径：\n"
        level_names = ["🔰 基础层", "📚 进阶层", "🚀 高级层", "🌟 专家层"]
        for level in sorted(levels.keys()):
            name = level_names[min(level, 3)]
            summary += f"  {name}: {' → '.join(levels[level])}\n"

        return summary
