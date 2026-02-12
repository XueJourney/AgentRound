"""
API客户端模块 / API Client Module

功能说明 / Functionality:
这个模块封装了与 OpenAI API 的交互，包括模型列表获取、聊天完成请求等。
This module encapsulates interactions with the OpenAI API, including
model list retrieval, chat completion requests, etc.

实现细节 / Implementation Details:
- 使用 openai 官方 Python SDK
- 支持自定义 base_url 以兼容其他 API 提供商
- 实现重试机制和错误处理
- 支持并发请求
- Uses official openai Python SDK
- Supports custom base_url for compatibility with other API providers
- Implements retry mechanism and error handling
- Supports concurrent requests

设计理由 / Design Rationale:
将 API 交互逻辑封装在独立模块中，便于测试和维护，也方便未来切换到其他 API。
Encapsulating API interaction logic in a separate module facilitates testing
and maintenance, and makes it easier to switch to other APIs in the future.

已知问题 / Known Issues:
- 当前未实现自动重试机制，网络错误会直接抛出
- Currently no automatic retry mechanism, network errors are thrown directly

TODO:
- 添加请求重试机制
- 添加请求速率限制
- 支持流式响应
- Add request retry mechanism
- Add request rate limiting
- Support streaming responses
"""

import logging
import random
from typing import List, Dict, Any, Tuple, Optional
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed


class APIClient:
    """
    API客户端类 / API Client Class

    这个类封装了所有与 OpenAI API 的交互。
    This class encapsulates all interactions with the OpenAI API.
    """

    def __init__(self, base_url: str, api_key: str,
                 temperature_min: float = 0.4, temperature_max: float = 1.2,
                 max_workers: int = 5):
        """
        初始化API客户端 / Initialize API Client

        Args:
            base_url: API 基础 URL / API base URL
            api_key: API 密钥 / API key
            temperature_min: 最小温度参数 / Minimum temperature
            temperature_max: 最大温度参数 / Maximum temperature
            max_workers: 最大并发工作线程数 / Maximum concurrent workers
        """
        self.base_url = base_url
        self.api_key = api_key
        self.temperature_min = temperature_min
        self.temperature_max = temperature_max
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

        # 初始化 OpenAI 客户端 / Initialize OpenAI client
        self.client = openai.Client(base_url=base_url, api_key=api_key)

        self.logger.info(
            "API客户端初始化完成 / API client initialized: base_url=%s",
            base_url
        )

    def get_available_models(self, custom_models: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        获取可用模型列表 / Get Available Model List

        Args:
            custom_models: 自定义模型列表，如果提供则直接使用
                          Custom model list, use directly if provided

        Returns:
            List[Dict[str, str]]: 模型列表，每个模型包含 'id' 字段
                                 Model list, each model contains 'id' field

        实现说明 / Implementation Notes:
        如果提供了自定义模型列表，直接使用；否则从 API 获取。
        If custom model list provided, use directly; otherwise fetch from API.
        """
        if custom_models:
            # 使用自定义模型列表 / Use custom model list
            models = [{"id": model} for model in custom_models]
            self.logger.info(
                "使用自定义模型列表: %s / Using custom model list: %s",
                custom_models, custom_models
            )
            return models

        # 从 API 获取模型列表 / Fetch model list from API
        try:
            self.logger.info("正在从 API 获取模型列表... / Fetching model list from API...")
            response = self.client.models.list()
            models = [{"id": model.id} for model in response.data]
            self.logger.info(
                "成功获取 %d 个模型 / Successfully fetched %d models",
                len(models), len(models)
            )
            return models
        except Exception as e:
            self.logger.error(
                "获取模型列表失败 / Failed to fetch model list: %s",
                e
            )
            raise

    def get_chat_completion(self, messages: List[Dict[str, Any]], model_id: str,
                           max_tokens: int = 2048) -> Tuple[str, int, int]:
        """
        获取聊天完成响应 / Get Chat Completion Response

        Args:
            messages: 消息列表 / Message list
            model_id: 模型 ID / Model ID
            max_tokens: 最大生成 token 数 / Maximum tokens to generate

        Returns:
            Tuple[str, int, int]: (响应内容, prompt tokens, completion tokens)
                                 (Response content, prompt tokens, completion tokens)

        实现说明 / Implementation Notes:
        - 使用随机温度参数增加回复多样性
        - 捕获并记录所有异常
        - 返回 token 使用统计
        - Uses random temperature to increase response diversity
        - Catches and logs all exceptions
        - Returns token usage statistics
        """
        # 生成随机温度参数 / Generate random temperature
        temperature = random.uniform(self.temperature_min, self.temperature_max)

        self.logger.debug(
            "发起聊天请求 / Initiating chat request: model=%s, temperature=%.2f, max_tokens=%d",
            model_id, temperature, max_tokens
        )

        try:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens

            self.logger.info(
                "聊天请求成功 / Chat request successful: model=%s, "
                "prompt_tokens=%d, completion_tokens=%d",
                model_id, prompt_tokens, completion_tokens
            )

            return content, prompt_tokens, completion_tokens

        except Exception as e:
            self.logger.error(
                "聊天请求失败 / Chat request failed: model=%s, error=%s",
                model_id, e
            )
            raise

    def get_batch_completions(self, requests: List[Tuple[List[Dict[str, Any]], str, int]]) -> Dict[str, Tuple[str, int, int]]:
        """
        批量获取聊天完成响应（并发）/ Get Batch Chat Completions (Concurrent)

        Args:
            requests: 请求列表，每个请求是 (messages, model_id, max_tokens) 元组
                     Request list, each request is (messages, model_id, max_tokens) tuple

        Returns:
            Dict[str, Tuple[str, int, int]]: 模型ID到响应的映射
                                            Mapping from model ID to response

        实现说明 / Implementation Notes:
        使用 ThreadPoolExecutor 实现并发请求，提高效率。
        Uses ThreadPoolExecutor for concurrent requests to improve efficiency.
        """
        results = {}

        self.logger.info(
            "开始批量请求 / Starting batch requests: %d 个请求 / %d requests",
            len(requests), len(requests)
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务 / Submit all tasks
            future_to_model = {
                executor.submit(self.get_chat_completion, messages, model_id, max_tokens): model_id
                for messages, model_id, max_tokens in requests
            }

            # 收集结果 / Collect results
            for future in as_completed(future_to_model):
                model_id = future_to_model[future]
                try:
                    content, pt, ct = future.result()
                    results[model_id] = (content, pt, ct)
                    self.logger.debug(
                        "模型 %s 完成 / Model %s completed",
                        model_id, model_id
                    )
                except Exception as e:
                    self.logger.warning(
                        "模型 %s 请求失败 / Model %s request failed: %s",
                        model_id, model_id, e
                    )
                    results[model_id] = (f"[请求失败: {e}]", 0, 0)

        self.logger.info(
            "批量请求完成 / Batch requests completed: %d/%d 成功 / %d/%d successful",
            len([r for r in results.values() if not r[0].startswith("[请求失败")]),
            len(requests),
            len([r for r in results.values() if not r[0].startswith("[请求失败")]),
            len(requests)
        )

        return results
