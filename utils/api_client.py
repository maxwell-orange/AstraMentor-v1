"""
API客户端封装模块

封装Google Generative AI的调用逻辑
"""

import json
import logging
from typing import Optional

import google.generativeai as genai

from config import get_config


logger = logging.getLogger(__name__)


class APIClient:
    """
    Google Generative AI API客户端
    
    封装模型初始化和内容生成逻辑
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        初始化API客户端
        
        Args:
            model_name: 模型名称，为None时使用配置默认值
        """
        config = get_config()
        
        # 配置API
        genai.configure(
            api_key=config.api.api_key,
            transport=config.api.transport,
            client_options={"api_endpoint": config.api.api_endpoint}
        )
        
        # 初始化模型
        self.model_name = model_name or config.api.model_name
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"API客户端初始化完成，使用模型: {self.model_name}")
    
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        生成内容
        
        Args:
            prompt: 用户提示词
            system_instruction: 系统指令
            temperature: 温度参数
            
        Returns:
            生成的文本内容
        """
        try:
            # 如果有系统指令，创建带系统指令的模型
            if system_instruction:
                model = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            # 生成内容
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"内容生成失败: {e}")
            raise
    
    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3
    ) -> dict:
        """
        生成JSON格式的内容
        
        Args:
            prompt: 用户提示词
            system_instruction: 系统指令
            temperature: 温度参数（JSON生成使用较低温度）
            
        Returns:
            解析后的JSON字典
        """
        text = self.generate(prompt, system_instruction, temperature)
        
        # 清理可能的Markdown代码块标记
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}\n原始文本: {text}")
            # 返回默认值
            return {
                "score": 0.5,
                "feedback": "评分解析失败，请重试",
                "analysis": f"JSON解析错误: {e}"
            }
    
    def chat(
        self,
        messages: list[dict],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        多轮对话
        
        Args:
            messages: 消息列表，每条消息包含role和content
            system_instruction: 系统指令
            temperature: 温度参数
            
        Returns:
            助手回复内容
        """
        try:
            # 创建带系统指令的模型
            if system_instruction:
                model = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            # 开始对话
            chat = model.start_chat(history=[])
            
            # 发送历史消息
            for msg in messages[:-1]:
                if msg["role"] == "user":
                    chat.send_message(msg["content"])
            
            # 发送最后一条消息并获取回复
            last_message = messages[-1]["content"] if messages else ""
            response = chat.send_message(last_message)
            
            return response.text
            
        except Exception as e:
            logger.error(f"对话生成失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            response = self.model.generate_content("Say 'OK' if you can hear me.")
            return "OK" in response.text or len(response.text) > 0
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
