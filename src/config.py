"""
配置管理模块 / Configuration Management Module

功能说明 / Functionality:
这个模块负责加载和管理所有应用程序配置，包括API设置、模型参数、Token限制等。
This module is responsible for loading and managing all application configurations,
including API settings, model parameters, token limits, etc.

实现细节 / Implementation Details:
- 使用 python-dotenv 从 .env 文件加载环境变量
- 提供类型安全的配置访问接口
- 支持默认值和配置验证
- Uses python-dotenv to load environment variables from .env file
- Provides type-safe configuration access interface
- Supports default values and configuration validation

设计理由 / Design Rationale:
将配置集中管理可以提高代码的可维护性和可测试性，避免配置散落在各处。
Centralized configuration management improves code maintainability and testability,
avoiding scattered configuration throughout the codebase.
"""

import os
import sys
from typing import Optional, List
from dotenv import load_dotenv


class Config:
    """
    配置管理类 / Configuration Management Class

    这个类封装了所有应用程序配置，提供统一的访问接口。
    This class encapsulates all application configurations and provides
    a unified access interface.
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置 / Initialize Configuration

        Args:
            env_file: .env 文件路径，默认为当前目录的 .env
                     Path to .env file, defaults to .env in current directory
        """
        # 加载环境变量 / Load environment variables
        load_dotenv(env_file)

        # ===== API 配置 / API Configuration =====
        self.base_api: str = os.getenv("BASE_API", "https://api.openai.com/v1")
        self.api_key: Optional[str] = os.getenv("API_KEY")

        # 验证必需配置 / Validate required configuration
        if not self.api_key:
            print("错误: API_KEY 未设置，请检查 .env 文件")
            print("Error: API_KEY not set, please check .env file")
            sys.exit(1)

        # ===== Token 配置 / Token Configuration =====
        self.response_tokens: int = int(os.getenv("RESPONSE_TOKENS", "2048"))
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "32000"))
        self.tiktoken_model: str = os.getenv("TIKTOKEN_MODEL", "gpt-4o")

        # ===== 生成参数 / Generation Parameters =====
        self.temperature_min: float = float(os.getenv("TEMPERATURE_MIN", "0.4"))
        self.temperature_max: float = float(os.getenv("TEMPERATURE_MAX", "1.2"))
        self.max_workers: int = int(os.getenv("MAX_WORKERS", "5"))

        # ===== 讨论配置 / Discussion Configuration =====
        self.initial_rounds: int = int(os.getenv("INITIAL_ROUNDS", "3"))
        self.topic: str = os.getenv("TOPIC", "")

        # ===== 输出配置 / Output Configuration =====
        self.output_dir: str = os.getenv("OUTPUT_DIR", "discussions")
        self.log_dir: str = os.getenv("LOG_DIR", "log")

        # ===== 模型配置 / Model Configuration =====
        # 从环境变量读取模型列表，逗号分隔
        # Read model list from environment variable, comma-separated
        model_env = os.getenv("MODELS", "")
        self.models: List[str] = [m.strip() for m in model_env.split(",") if m.strip()]

        # 创建必要的目录 / Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    def validate(self) -> bool:
        """
        验证配置的有效性 / Validate configuration validity

        Returns:
            bool: 配置是否有效 / Whether configuration is valid
        """
        # TODO: 添加更详细的配置验证逻辑
        # TODO: Add more detailed configuration validation logic
        if not self.api_key:
            return False
        if self.max_tokens < self.response_tokens:
            print("警告: MAX_TOKENS 小于 RESPONSE_TOKENS，可能导致问题")
            print("Warning: MAX_TOKENS is less than RESPONSE_TOKENS, may cause issues")
            return False
        return True

    def __repr__(self) -> str:
        """
        返回配置的字符串表示（隐藏敏感信息）
        Return string representation of configuration (hiding sensitive info)
        """
        return (
            f"Config(base_api={self.base_api}, "
            f"api_key={'***' + self.api_key[-8:] if self.api_key else None}, "
            f"max_tokens={self.max_tokens}, "
            f"response_tokens={self.response_tokens})"
        )
