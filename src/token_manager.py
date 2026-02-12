"""
Token管理模块 / Token Management Module

功能说明 / Functionality:
这个模块负责计算消息的token数量，并管理对话历史的裁剪以适应上下文限制。
This module is responsible for counting message tokens and managing
conversation history trimming to fit context limits.

实现细节 / Implementation Details:
- 使用 tiktoken 库进行 token 计数
- 实现智能历史裁剪算法，保留 system 消息
- 支持多种模型的 token 计算
- Uses tiktoken library for token counting
- Implements smart history trimming algorithm, preserving system messages
- Supports token calculation for multiple models

设计理由 / Design Rationale:
准确的 token 计数对于避免 API 调用失败和控制成本至关重要。
裁剪策略优先保留最近的消息和 system 消息，确保对话连贯性。
Accurate token counting is crucial for avoiding API call failures and controlling costs.
Trimming strategy prioritizes recent messages and system messages to ensure conversation coherence.

已知问题 / Known Issues:
- tiktoken 可能不支持所有模型，此时使用 cl100k_base 作为后备
- tiktoken may not support all models, cl100k_base is used as fallback
"""

import logging
from typing import List, Dict, Any
import tiktoken


class TokenManager:
    """
    Token管理器类 / Token Manager Class

    这个类提供 token 计数和历史管理功能。
    This class provides token counting and history management functionality.
    """

    def __init__(self, model_name: str = "gpt-4o", response_tokens: int = 2048):
        """
        初始化Token管理器 / Initialize Token Manager

        Args:
            model_name: 用于 token 计算的模型名称 / Model name for token calculation
            response_tokens: 预留给响应的 token 数量 / Tokens reserved for response
        """
        self.model_name = model_name
        self.response_tokens = response_tokens
        self.logger = logging.getLogger(__name__)

        # 初始化 tiktoken encoder / Initialize tiktoken encoder
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
            self.logger.info(
                "Token encoder 初始化成功，模型: %s / "
                "Token encoder initialized successfully, model: %s",
                model_name, model_name
            )
        except Exception as e:
            # 如果模型不支持，使用默认编码器
            # If model not supported, use default encoder
            self.encoder = tiktoken.get_encoding("cl100k_base")
            self.logger.warning(
                "模型 %s 不支持，使用默认编码器 cl100k_base / "
                "Model %s not supported, using default encoder cl100k_base. "
                "错误 / Error: %s",
                model_name, model_name, e
            )

    def count_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        计算消息列表的 token 数量 / Count Tokens in Message List

        Args:
            messages: 消息列表，每个消息包含 role 和 content
                     Message list, each message contains role and content

        Returns:
            int: 总 token 数量 / Total token count

        实现说明 / Implementation Notes:
        根据 OpenAI 的 token 计算规则：
        - 每条消息有 4 个固定 token 的开销
        - 消息内容按实际编码计算
        - 整个消息列表有 2 个固定 token 的开销
        According to OpenAI's token counting rules:
        - Each message has 4 tokens of fixed overhead
        - Message content is counted by actual encoding
        - The entire message list has 2 tokens of fixed overhead
        """
        total = 0
        for msg in messages:
            # 每条消息的固定开销 / Fixed overhead per message
            total += 4
            # 消息内容的 token 数 / Token count of message content
            content = msg.get("content", "")
            total += len(self.encoder.encode(content))

        # 整个列表的固定开销 / Fixed overhead for the entire list
        total += 2

        self.logger.debug(
            "计算 token 数量: %d 条消息, 总计 %d tokens / "
            "Counted tokens: %d messages, total %d tokens",
            len(messages), total, len(messages), total
        )

        return total

    def trim_history(self, messages: List[Dict[str, Any]], max_context: int) -> List[Dict[str, Any]]:
        """
        裁剪历史消息以适应上下文限制 / Trim History to Fit Context Limit

        Args:
            messages: 消息列表 / Message list
            max_context: 最大上下文 token 数 / Maximum context tokens

        Returns:
            List[Dict[str, Any]]: 裁剪后的消息列表 / Trimmed message list

        实现说明 / Implementation Notes:
        裁剪策略：
        1. 保留 system 消息（通常是第一条）
        2. 从最早的非 system 消息开始删除
        3. 确保剩余空间足够容纳响应
        4. 至少保留 2 条消息（system + 最新的用户消息）
        Trimming strategy:
        1. Preserve system messages (usually the first one)
        2. Delete from the earliest non-system message
        3. Ensure remaining space is sufficient for response
        4. Keep at least 2 messages (system + latest user message)
        """
        # 计算当前 token 数 / Calculate current token count
        current_tokens = self.count_tokens(messages)
        available_tokens = max_context - self.response_tokens

        self.logger.debug(
            "开始裁剪历史: 当前 %d tokens, 可用 %d tokens / "
            "Starting history trim: current %d tokens, available %d tokens",
            current_tokens, available_tokens, current_tokens, available_tokens
        )

        # 如果不需要裁剪，直接返回 / If no trimming needed, return directly
        if current_tokens <= available_tokens:
            self.logger.debug("无需裁剪 / No trimming needed")
            return messages

        # 开始裁剪 / Start trimming
        trimmed_count = 0
        while current_tokens > available_tokens and len(messages) > 2:
            # 找到第一条非 system 消息并删除
            # Find and remove the first non-system message
            for i, msg in enumerate(messages):
                if msg["role"] != "system":
                    removed = messages.pop(i)
                    trimmed_count += 1
                    self.logger.info(
                        "裁剪消息 [%s]: %s... / "
                        "Trimmed message [%s]: %s...",
                        removed["role"], removed["content"][:40],
                        removed["role"], removed["content"][:40]
                    )
                    # 重新计算 token 数 / Recalculate token count
                    current_tokens = self.count_tokens(messages)
                    break
            else:
                # 如果没有找到非 system 消息，退出循环
                # If no non-system message found, break loop
                self.logger.warning(
                    "无法继续裁剪，只剩 system 消息 / "
                    "Cannot continue trimming, only system messages left"
                )
                break

        self.logger.info(
            "裁剪完成: 删除 %d 条消息, 剩余 %d tokens / "
            "Trimming completed: removed %d messages, remaining %d tokens",
            trimmed_count, current_tokens, trimmed_count, current_tokens
        )

        return messages

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int,
                      prompt_price: float = 0.01, completion_price: float = 0.03) -> float:
        """
        估算 API 调用成本 / Estimate API Call Cost

        Args:
            prompt_tokens: 提示 token 数 / Prompt tokens
            completion_tokens: 完成 token 数 / Completion tokens
            prompt_price: 每 1K prompt tokens 的价格（美元）/ Price per 1K prompt tokens (USD)
            completion_price: 每 1K completion tokens 的价格（美元）/ Price per 1K completion tokens (USD)

        Returns:
            float: 估算成本（美元）/ Estimated cost (USD)

        注意 / Note:
        这只是一个估算函数，实际价格可能因模型和时间而异。
        This is only an estimation function, actual prices may vary by model and time.

        TODO: 支持从配置文件读取不同模型的价格
        TODO: Support reading prices for different models from config file
        """
        cost = (prompt_tokens / 1000 * prompt_price +
                completion_tokens / 1000 * completion_price)
        return cost
