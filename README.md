<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Google_AI-Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<h1 align="center">🌟 AstraMentor</h1>

<p align="center">
  <strong>基于多Agent架构的AI编程教学系统</strong>
</p>

<p align="center">
  让AI像真正的导师一样，为你量身打造学习路线，提供个性化教学与实时指导
</p>

---

## ✨ 特性亮点

<table>
<tr>
<td width="50%">

### 🌌 知识星图 (New!)
根据你的目标和水平，自动生成可视化的知识依赖图谱，规划最佳学习路径

</td>
<td width="50%">

### 💬 交互式教学 (New!)
不再是单向输出，支持在教学过程中随时提问、讨论，直到彻底理解

</td>
</tr>
<tr>
<td width="50%">

### 🎓 智能分阶段教学
根据用户掌握度自动调整教学风格，从生活类比到源码级讲解，循序渐进

</td>
<td width="50%">

### 📊 动态评分算法
采用增强型带权重指数移动平均(EMA)算法，精准追踪学习进度

</td>
</tr>
<tr>
<td width="50%">

### 🤖 多Agent协作
Knowledge Agent规划路线，Teacher Agent负责教学，Evaluation Agent负责评估

</td>
<td width="50%">

### 💾 状态持久化
自动保存学习进度和图谱数据，支持断点续学

</td>
</tr>
</table>

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      AstraMentor 主控制器                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────┐         ┌─────────────────────┐      │
│   │  🌌 Knowledge Agent │         │  📝 Evaluation Agent│      │
│   │                     │         │                     │      │
│   │  • 生成知识星图     │         │  • 评估用户回答     │      │
│   │  • 规划学习路径     │         │  • 计算评分         │      │
│   │  • 依赖关系分析     │         │  • 更新掌握度       │      │
│   └─────────────────────┘         └─────────────────────┘      │
│             ▲                                  ▲               │
│             │                                  │               │
│             ▼                                  ▼               │
│   ┌─────────────────────────────────────────────────────┐      │
│   │                 🎓 Teacher Agent                    │      │
│   │                                                     │      │
│   │  • 生成教学计划    • 分阶段智能教学    • 答疑解惑   │      │
│   │  • 生成验证问题    • 解释正确答案      • 互动讨论   │      │
│   └─────────────────────────────────────────────────────┘      │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              📚 LearnerState 学习者状态管理              │  │
│   │   知识点管理  •  掌握度跟踪  •  历史记录  •  自动持久化   │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 分阶段教学策略

系统会根据用户当前的掌握度（A权重）自动选择最适合的教学风格：

| 阶段 | 掌握度 | 教学角色 | 教学特点 |
|:----:|:------:|:--------:|:---------|
| **阶段0** | 0.0 ~ 0.2 | 🌱 科普老师 | 用生活类比解释概念，禁用专业术语，消除恐惧 |
| **阶段1** | 0.2 ~ 0.5 | 📝 编程导师 | 语法讲解，提供Hello World示例，逐行解释 |
| **阶段2** | 0.5 ~ 0.8 | 💼 高级工程师 | 原理剖析，Error Handling，技术对比 |
| **阶段3** | 0.8 ~ 1.0 | 🎯 架构师 | 源码级理解，手写实现，SOTA技术探讨 |

---

## 📐 评分算法（增强版）

采用 **增强型带权重指数移动平均** 算法，融合BKT和IRT的优秀特性：

```
A_new = A_old × β + α(stage) × (S_task × W_cap - A_old × β) × γ
```

### 核心特性

| 特性 | 说明 |
|:----:|:-----|
| **自适应学习率** | 初期学习快(α=0.4)，后期精进慢(α=0.15) |
| **时间遗忘** | 超过7天未练习，每天衰减2%掌握度 |
| **失误保护** | 高手(>70%)答错，惩罚减半（可能是失误） |
| **猜对抑制** | 新手(<30%)答对，奖励打6折（可能是猜的） |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Google Gemini API Key

### 1️⃣ 克隆项目

```bash
git clone https://github.com/your-repo/AstraMentor-v1.git
cd AstraMentor-v1
```

### 2️⃣ 准备环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3️⃣ 配置

复制 `.env.example` 为 `.env` 并填入 API Key：

```env
ASTRA_API_KEY=your-api-key-here
# 可选：配置代理或其他模型
# ASTRA_API_ENDPOINT=http://127.0.0.1:8045
```

### 4️⃣ 运行

```bash
python main.py
```

---

## 📁 项目结构

```
AstraMentor-v1/
│
├── 📄 main.py                  # 主程序入口，工作流控制
├── 📄 config.py                # 配置管理
├── 📂 agents/                  # Agent 智能体
│   ├── teacher_agent.py        # 🎓 教学 Agent
│   ├── evaluation_agent.py     # 📝 评估 Agent
│   └── knowledge_graph_agent.py # 🌌 知识图谱 Agent
│
├── 📂 core/                    # 核心逻辑
│   ├── learner_state.py        # 状态管理
│   ├── scoring.py              # 评分算法
│   └── prompts.py              # Prompt 模板
│
├── 📂 test_data/               # 数据存储
│   └── knowledge_graph_*.json  # 生成的知识星图
│
└── 📄 learner_state.json       # 学习状态持久化文件
```

---

## 🔄 交互流程

1.  **初始设置**：输入学习主题（如 "Python 装饰器"）和当前/目标水平。
2.  **生成星图**：系统生成知识点依赖图谱，并推荐最佳学习路径。
3.  **选择节点**：从图谱中选择一个知识点开始学习。
4.  **教学阶段**：
    *   AI 导师进行讲解。
    *   **💬 互动讨论**：你可以随时提问，直到搞懂为止。
5.  **测验评估**：AI 出题（选择/代码填空/实操），你作答。
6.  **反馈更新**：系统评估回答，更新掌握度，并给出详细解析。
7.  **循环进阶**：掌握当前节点后，解锁下一节点。

---

## 📝 许可证

本项目采用 [MIT License](LICENSE) 开源协议。
