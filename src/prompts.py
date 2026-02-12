"""
提示词模板模块 / Prompt Template Module

功能说明 / Functionality:
这个模块管理所有AI讨论中使用的提示词模板，支持多语言和变量替换。
This module manages all prompt templates used in AI discussions,
supporting multiple languages and variable substitution.

实现细节 / Implementation Details:
- 提供默认的中文提示词模板
- 支持从环境变量自定义提示词
- 使用 Python 字符串格式化进行变量替换
- Provides default Chinese prompt templates
- Supports custom prompts from environment variables
- Uses Python string formatting for variable substitution

设计理由 / Design Rationale:
将提示词集中管理便于维护和国际化，用户可以通过环境变量自定义提示词而无需修改代码。
Centralized prompt management facilitates maintenance and internationalization,
users can customize prompts via environment variables without modifying code.
"""

import os
from typing import Dict, Any


class PromptTemplates:
    """
    提示词模板管理类 / Prompt Template Management Class

    这个类封装了所有提示词模板，并提供格式化方法。
    This class encapsulates all prompt templates and provides formatting methods.
    """

    def __init__(self):
        """
        初始化提示词模板 / Initialize Prompt Templates

        从环境变量加载自定义模板，如果未设置则使用默认模板。
        Load custom templates from environment variables, use defaults if not set.
        """
        # ===== 系统提示词 / System Prompt =====
        self.system_prompt_template: str = os.getenv("SYSTEM_PROMPT", (
            "你是 {model_name}，正在参与一场多AI圆桌讨论。\\n"
            "讨论主题：「{topic}」\\n"
            "参与者：{participants}\\n\\n"
            "规则：\\n"
            "1. 你必须以自己的身份发言，有独立的立场和思考角度\\n"
            "2. 认真阅读其他参与者的观点，可以赞同、反驳或补充\\n"
            "3. 用清晰的逻辑和论据支撑你的观点\\n"
            "4. 避免空泛的套话，给出有深度的分析\\n"
            "5. 每轮发言控制在300字以内，精炼表达"
        ))

        # ===== 首轮提示词 / First Round Prompt =====
        self.first_round_prompt: str = os.getenv("FIRST_ROUND_PROMPT", (
            "# Agent\\n"
            "【第 {current_round}/{total_rounds} 轮 | 剩余 {remaining} 轮】\\n\\n"
            "请作为 {model_name} 率先发表你对「{topic}」的观点。\\n"
            "要求：亮明立场，给出核心论点和支撑论据。"
        ))

        # ===== 讨论提示词 / Discussion Prompt =====
        self.discussion_prompt: str = os.getenv("DISCUSSION_PROMPT", (
            "# Agent\\n"
            "【第 {current_round}/{total_rounds} 轮 | 剩余 {remaining} 轮】\\n\\n"
            "以下是上一轮其他参与者的发言：\\n{others_text}\\n"
            "请参考以上观点，继续深入讨论。你可以：\\n"
            "- 反驳你不认同的观点并给出理由\\n"
            "- 补充其他人遗漏的角度\\n"
            "- 在他人观点基础上进一步推演\\n"
            "- 修正或完善自己之前的立场"
        ))

        # ===== 人类指导提示词 / Human Guide Prompt =====
        self.human_guide_prompt: str = os.getenv("HUMAN_GUIDE_PROMPT", (
            "# Human\\n"
            "用户介入指导：\\n{human_input}\\n\\n"
            "请根据用户的指导调整你的讨论方向和重点。"
        ))

        # ===== 总结提示词 / Summary Prompt =====
        self.summary_prompt: str = os.getenv("SUMMARY_PROMPT", (
            "# Agent\\n"
            "【最终总结轮】\\n\\n"
            "讨论即将结束，请总结：\\n"
            "1. 你的最终立场\\n"
            "2. 讨论中最有价值的观点（包括他人的）\\n"
            "3. 仍存在的分歧或待探讨的问题"
        ))

    def format_system_prompt(self, model_name: str, topic: str, participants: str) -> str:
        """
        格式化系统提示词 / Format System Prompt

        Args:
            model_name: 模型名称 / Model name
            topic: 讨论主题 / Discussion topic
            participants: 参与者列表 / Participant list

        Returns:
            str: 格式化后的系统提示词 / Formatted system prompt
        """
        return self.system_prompt_template.format(
            model_name=model_name,
            topic=topic,
            participants=participants
        )

    def format_first_round_prompt(self, current_round: int, total_rounds: int,
                                   remaining: int, model_name: str, topic: str) -> str:
        """
        格式化首轮提示词 / Format First Round Prompt

        Args:
            current_round: 当前轮次 / Current round
            total_rounds: 总轮次 / Total rounds
            remaining: 剩余轮次 / Remaining rounds
            model_name: 模型名称 / Model name
            topic: 讨论主题 / Discussion topic

        Returns:
            str: 格式化后的首轮提示词 / Formatted first round prompt
        """
        return self.first_round_prompt.format(
            current_round=current_round,
            total_rounds=total_rounds,
            remaining=remaining,
            model_name=model_name,
            topic=topic
        )

    def format_discussion_prompt(self, current_round: int, total_rounds: int,
                                  remaining: int, others_text: str) -> str:
        """
        格式化讨论提示词 / Format Discussion Prompt

        Args:
            current_round: 当前轮次 / Current round
            total_rounds: 总轮次 / Total rounds
            remaining: 剩余轮次 / Remaining rounds
            others_text: 其他参与者的发言 / Other participants' statements

        Returns:
            str: 格式化后的讨论提示词 / Formatted discussion prompt
        """
        return self.discussion_prompt.format(
            current_round=current_round,
            total_rounds=total_rounds,
            remaining=remaining,
            others_text=others_text
        )

    def format_human_guide_prompt(self, human_input: str) -> str:
        """
        格式化人类指导提示词 / Format Human Guide Prompt

        Args:
            human_input: 用户输入的指导内容 / User's guidance input

        Returns:
            str: 格式化后的人类指导提示词 / Formatted human guide prompt
        """
        return self.human_guide_prompt.format(human_input=human_input)

    def format_summary_prompt(self) -> str:
        """
        格式化总结提示词 / Format Summary Prompt

        Returns:
            str: 格式化后的总结提示词 / Formatted summary prompt
        """
        return self.summary_prompt
