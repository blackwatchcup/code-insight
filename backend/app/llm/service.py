import os
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

import openai

from app.core.config import settings


@dataclass
class LLMConfig:
    model: str = "deepseek-chat"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: str = "You are a helpful code assistant."


class LLMService:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        # 优先使用config中的api_key和base_url
        # 然后使用settings中的配置
        # 最后尝试从环境变量中读取
        # 支持DEEPSEEK_API_KEY和OPENAI_API_KEY环境变量
        self.api_key = (
            self.config.api_key or 
            settings.OPENAI_API_KEY or
            os.getenv("DEEPSEEK_API_KEY") or 
            os.getenv("OPENAI_API_KEY")
        )
        self.base_url = (
            self.config.base_url or 
            settings.OPENAI_BASE_URL or
            os.getenv("DEEPSEEK_BASE_URL") or 
            os.getenv("OPENAI_BASE_URL")
        )
        # 确保模型设置正确
        if not self.config.model:
            self.config.model = settings.OPENAI_MODEL

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self._client = openai.OpenAI(**client_kwargs)
        self._async_client = openai.AsyncOpenAI(**client_kwargs)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = self._build_messages(prompt, system_prompt, history)

        response = await self._async_client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        return response.choices[0].message.content

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(prompt, system_prompt, history)

        stream = await self._async_client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = self._build_messages(prompt, system_prompt, history)

        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        return response.choices[0].message.content

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt or self.config.system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": prompt})

        return messages

    def count_tokens(self, text: str) -> int:
        import tiktoken

        encoding = tiktoken.encoding_for_model(self.config.model)
        return len(encoding.encode(text))
