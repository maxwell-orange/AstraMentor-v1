import os
import json
import logging
from typing import Optional, Any, List, Dict

from google import genai
from google.genai import types
from config import get_config

logger = logging.getLogger(__name__)


class APIClient:
    """
    Google GenAI (new SDK) API客户端
    """

    def __init__(self, model_name: Optional[str] = None):
        config = get_config()

        self.model_name = model_name or config.api.model_name

        # ✅ 新 SDK：Client
        # 你原来的 transport / api_endpoint 这些在新 SDK 里不一定同名支持，
        # 最稳的做法是先只用 api_key 跑通；需要自定义 endpoint 再加。
        api_key = config.api.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing Gemini API key (config.api.api_key or GEMINI_API_KEY)")

        self.client = genai.Client(api_key=api_key, 
        http_options=types.HttpOptions(
        base_url=config.api.api_endpoint,   # ✅ 你的 endpoint 放这里
        # api_version="v1",                 # 可选：稳定版 v1（不写默认可能走 beta）
    ))

        logger.info(f"API客户端初始化完成（new SDK），使用模型: {self.model_name}")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        try:
            cfg = types.GenerateContentConfig(
                temperature=temperature,
            )
            if system_instruction:
                # 新 SDK 支持 system_instruction（字段名依版本可能略有差异，但这是主流写法）
                cfg.system_instruction = system_instruction

            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=cfg,
            )
            # 新 SDK 一般是 resp.text
            return getattr(resp, "text", "") or ""

        except Exception as e:
            logger.error(f"内容生成失败: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        output_schema: Optional[Any] = None
    ):
        """
        output_schema: Pydantic模型类（或 list[Model] / dict schema）
        返回：如果给 schema -> response.parsed（Pydantic实例/列表）；否则 -> dict
        """
        if output_schema:
            try:
                cfg = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=output_schema,   # ✅ 直接 Pydantic / list[Pydantic]
                    temperature=temperature,
                )
                if system_instruction:
                    cfg.system_instruction = system_instruction

                resp = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=cfg,
                )

                # ✅ parsed 是“已反序列化+校验”的结果
                return resp.parsed

            except Exception as e:
                logger.error(f"JSON生成失败: {e}")
                raise
        else:
            # 没 schema：走文本 -> json.loads
            text = self.generate(prompt, system_instruction, temperature)
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
                return {
                    "_error": f"JSON解析错误: {e}",
                    "_raw": text
                }

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        最稳的“兼容你现有 messages 结构”的写法：把 messages 转成 contents 直接 generate。
        如果你一定要 stateful chat/session，我们可以再升级到 session API。
        """
        try:
            # 把 {"role","content"} 转成 types.Content/Part
            contents = []
            for m in messages:
                role = m.get("role", "user")
                text = m.get("content", "")
                # 新 SDK 推荐用 types.Content
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=text)]
                    )
                )

            cfg = types.GenerateContentConfig(temperature=temperature)
            if system_instruction:
                cfg.system_instruction = system_instruction

            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=cfg,
            )
            return getattr(resp, "text", "") or ""

        except Exception as e:
            logger.error(f"对话生成失败: {e}")
            raise

    def test_connection(self) -> bool:
        try:
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents="Say 'OK' if you can hear me."
            )
            text = getattr(resp, "text", "") or ""
            return ("OK" in text) or (len(text) > 0)
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
