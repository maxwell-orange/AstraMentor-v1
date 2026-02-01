class KnowledgeState:
    def __init__(self, topic_name, target_mastery=0.8):
        """
        初始化知识点状态
        :param topic_name: 知识点名称
        :param target_mastery: 用户期望达到的掌握程度 (E), 默认 0.8
        """
        self.topic = topic_name
        self.target_mastery = target_mastery  # E: 期望值
        self.actual_mastery = 0.0             # A: 实际值 (初始为0)
        
        # 记录学习历史，用于后续分析
        self.history = [] 

    def get_learning_phase(self):
        """
        根据当前实际掌握度，返回对应的 Prompt Level Key
        """
        if self.actual_mastery < 0.2:
            return "level_0"
        elif self.actual_mastery < 0.5:
            return "level_1"
        elif self.actual_mastery < 0.8:
            return "level_2"
        else:
            return "level_3"

    def update_mastery(self, task_type, ai_score):
        """
        核心算法：更新用户的掌握度
        :param task_type: 任务类型 ('quiz', 'code_basic', 'code_project')
        :param ai_score: AI 评分器打出的分数 (0.0 - 1.0)
        :return: 更新后的 actual_mastery
        """
        
        # --- 1. 定义任务难度天花板 (Weight Cap) ---
        # 逻辑：简单的题做全对，也不能证明你是专家。
        # quiz: 概念选择题/问答 -> 上限 0.4
        # code_basic: 基础代码填空 -> 上限 0.7
        # code_project: 复杂逻辑/完整实现 -> 上限 1.0
        caps = {
            'quiz': 0.4,
            'code_basic': 0.7,
            'code_project': 1.0
        }
        w_cap = caps.get(task_type, 0.5)

        # --- 2. 动态学习率 (Alpha) ---
        # 逻辑：
        # - 如果是新手(mastery < 0.5)，知识增长应该快，alpha 大 (0.3)
        # - 如果是高手(mastery >= 0.5)，分数增长应该稳健，避免波动，alpha 小 (0.15)
        alpha = 0.3 if self.actual_mastery < 0.5 else 0.15

        # --- 3. 计算“有效表现分” (Effective Score) ---
        # 基础公式：用户的表现 * 题目的难度上限
        effective_score = ai_score * w_cap
        
        # --- 4. 高手保护机制 (Expert Protection Logic) ---
        # 场景：用户已经是 0.8 的高手了，回头做了一个简单的 quiz (cap 0.4)。
        # 即使他全对 (ai_score 1.0)，effective_score 也就 0.4。
        # 如果直接用 EMA 更新，会将他的 0.8 拉低。这不合理。
        
        if self.actual_mastery > w_cap:
            if ai_score >= 0.8:
                # 情况A：高手做简单题且做对了。
                # 策略：不降分，只给予极微小的奖励 (0.005) 或者保持不变。
                print(f"[Info] 高手做基础题({task_type})表现良好，分数保持稳定。")
                self.actual_mastery += 0.005
            else:
                # 情况B：高手做简单题竟然做错了 (ai_score < 0.8)。
                # 策略：惩罚。说明基础不牢，需要扣分，但稍微降低 alpha 避免扣太狠。
                print(f"[Info] 高手做基础题({task_type})翻车，给予适当惩罚。")
                penalty_alpha = 0.1 # 较小的惩罚系数
                # 此时 effective_score 很低，会把均值往下拉
                self.actual_mastery = self.actual_mastery + penalty_alpha * (effective_score - self.actual_mastery)
        else:
            # --- 5. 正常学习曲线逻辑 ---
            # 场景：用户水平低于题目上限，这是正常的学习攀升过程。
            # 公式：New = Old + Alpha * (Target - Old)
            self.actual_mastery = self.actual_mastery + alpha * (effective_score - self.actual_mastery)

        # --- 6. 边界裁剪 ---
        self.actual_mastery = max(0.0, min(1.0, self.actual_mastery))
        
        # 记录历史
        self.history.append({
            'type': task_type,
            'ai_score': ai_score,
            'new_mastery': self.actual_mastery
        })

        return self.actual_mastery