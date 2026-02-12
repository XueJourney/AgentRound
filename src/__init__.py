"""
AgentRound - 多AI圆桌讨论系统 / Multi-AI Roundtable Discussion System

这个包提供了一个完整的多模型AI讨论框架，支持多个AI模型之间的结构化对话和讨论。
This package provides a complete multi-model AI discussion framework that supports
structured conversations and discussions between multiple AI models.

主要模块 / Main Modules:
- config: 配置管理 / Configuration management
- logger: 日志系统 / Logging system
- prompts: 提示词模板 / Prompt templates
- token_manager: Token计数和历史管理 / Token counting and history management
- api_client: API客户端 / API client
- ui: 用户界面组件 / User interface components
- markdown_writer: Markdown文件生成 / Markdown file generation
- discussion: 讨论编排逻辑 / Discussion orchestration logic

版本 / Version: 2.0.0
作者 / Author: AgentRound Team
许可 / License: MIT
"""

__version__ = "2.0.0"
__author__ = "AgentRound Team"

# 导出主要组件 / Export main components
from .config import Config
from .logger import setup_logger
from .api_client import APIClient
from .discussion import DiscussionManager

__all__ = [
    "Config",
    "setup_logger",
    "APIClient",
    "DiscussionManager",
]
