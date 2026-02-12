"""
讨论编排模块 / Discussion Orchestration Module

功能说明 / Functionality:
这个模块是整个应用的核心，负责编排多模型讨论的流程，包括轮次管理、消息历史维护等。
This module is the core of the application, responsible for orchestrating
the multi-model discussion process, including round management, message history maintenance, etc.

实现细节 / Implementation Details:
- 管理每个模型的独立对话历史
- 协调多轮讨论流程
- 处理人类介入指导
- 生成最终总结
- Manages independent conversation history for each model
- Coordinates multi-round discussion process
- Handles human intervention guidance
- Generates final summary

设计理由 / Design Rationale:
将讨论逻辑集中在一个模块中，便于理解和维护整个讨论流程。
Centralizing discussion logic in one module makes it easier to understand
and maintain the entire discussion process.

已知问题 / Known Issues:
- 无 / None

TODO:
- 支持讨论暂停和恢复
- 支持讨论分支
- 添加讨论质量评估
- Support discussion pause and resume
- Support discussion branching
- Add discussion quality assessment
"""

import logging
from typing import List, Dict, Any, Optional
from .config import Config
from .prompts import PromptTemplates
from .token_manager import TokenManager
from .api_client import APIClient
from .ui import UIManager
from .markdown_writer import MarkdownWriter


class DiscussionManager:
    """
    讨论管理器类 / Discussion Manager Class

    这个类负责整个讨论流程的编排和管理。
    This class is responsible for orchestrating and managing the entire discussion process.
    """

    def __init__(self, config: Config, chosen_models: List[Dict[str, str]], topic: str):
        """
        初始化讨论管理器 / Initialize Discussion Manager

        Args:
            config: 配置对象 / Configuration object
            chosen_models: 选中的模型列表 / Selected model list
            topic: 讨论主题 / Discussion topic
        """
        self.config = config
        self.chosen_models = chosen_models
        self.topic = topic
        self.logger = logging.getLogger(__name__)

        # 初始化各个组件 / Initialize components
        self.prompts = PromptTemplates()
        self.token_manager = TokenManager(
            model_name=config.tiktoken_model,
            response_tokens=config.response_tokens
        )
        self.api_client = APIClient(
            base_url=config.base_api,
            api_key=config.api_key,
            temperature_min=config.temperature_min,
            temperature_max=config.temperature_max,
            max_workers=config.max_workers
        )
        self.ui = UIManager()

        # 参与者字符串 / Participants string
        self.participants_str = "、".join(m["id"] for m in chosen_models)

        # 初始化 Markdown 写入器 / Initialize Markdown writer
        self.md_writer = MarkdownWriter(
            output_dir=config.output_dir,
            topic=topic,
            participants=self.participants_str,
            max_tokens=config.max_tokens
        )

        # Token 统计 / Token statistics
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

        # 对话历史 / Conversation history
        # 每个模型维护独立的历史记录
        # Each model maintains independent history
        self.history: Dict[str, List[Dict[str, Any]]] = {}
        self._initialize_history()

        self.logger.info(
            "讨论管理器初始化完成 / Discussion manager initialized: "
            "topic=%s, models=%d",
            topic, len(chosen_models)
        )

    def _initialize_history(self) -> None:
        """
        初始化对话历史 / Initialize Conversation History

        为每个模型创建独立的历史记录，包含 system 消息。
        Creates independent history for each model, including system message.
        """
        for model in self.chosen_models:
            model_id = model["id"]
            system_prompt = self.prompts.format_system_prompt(
                model_name=model_id,
                topic=self.topic,
                participants=self.participants_str
            )
            self.history[model_id] = [
                {"role": "system", "content": system_prompt}
            ]

        self.logger.debug(
            "初始化了 %d 个模型的对话历史 / Initialized conversation history for %d models",
            len(self.chosen_models), len(self.chosen_models)
        )

    def _build_others_text(self, last_responses: Dict[str, str], exclude_model_id: str) -> str:
        """
        构建其他参与者的发言文本 / Build Other Participants' Text

        Args:
            last_responses: 上一轮的响应 / Last round responses
            exclude_model_id: 要排除的模型 ID / Model ID to exclude

        Returns:
            str: 格式化的其他参与者发言 / Formatted other participants' text
        """
        parts = []
        for model in self.chosen_models:
            model_id = model["id"]
            if model_id != exclude_model_id and model_id in last_responses:
                parts.append(f"---\n【{model_id}】:\n{last_responses[model_id]}")

        return "\n\n".join(parts)

    def run_round(self, round_idx: int, total_rounds: int,
                  last_responses: Dict[str, str],
                  human_input: Optional[str] = None) -> Dict[str, str]:
        """
        运行一轮讨论 / Run One Round of Discussion

        Args:
            round_idx: 当前轮次索引 / Current round index
            total_rounds: 总轮次数 / Total number of rounds
            last_responses: 上一轮的响应 / Last round responses
            human_input: 人类指导内容（可选）/ Human guidance content (optional)

        Returns:
            Dict[str, str]: 本轮各模型的响应 / This round's responses from each model

        实现说明 / Implementation Notes:
        1. 为每个模型构建提示词
        2. 裁剪历史以适应上下文限制
        3. 并发调用 API 获取响应
        4. 更新历史记录
        5. 渲染和保存结果
        1. Build prompts for each model
        2. Trim history to fit context limits
        3. Concurrently call API to get responses
        4. Update history
        5. Render and save results
        """
        responses = {}
        remaining = total_rounds - round_idx

        self.logger.info(
            "开始第 %d/%d 轮讨论 / Starting round %d/%d",
            round_idx, total_rounds, round_idx, total_rounds
        )

        # ===== 构建提示词 / Build Prompts =====
        requests = []
        for model in self.chosen_models:
            model_id = model["id"]

            # 如果有人类指导，添加到历史 / If human guidance, add to history
            if human_input:
                self.history[model_id].append({
                    "role": "user",
                    "content": self.prompts.format_human_guide_prompt(human_input)
                })

            # 构建本轮提示词 / Build this round's prompt
            if round_idx == 1 and not last_responses:
                # 首轮 / First round
                prompt = self.prompts.format_first_round_prompt(
                    current_round=round_idx,
                    total_rounds=total_rounds,
                    remaining=remaining,
                    model_name=model_id,
                    topic=self.topic
                )
            else:
                # 后续轮次 / Subsequent rounds
                others_text = self._build_others_text(last_responses, model_id)
                prompt = self.prompts.format_discussion_prompt(
                    current_round=round_idx,
                    total_rounds=total_rounds,
                    remaining=remaining,
                    others_text=others_text
                )

            self.history[model_id].append({"role": "user", "content": prompt})

            # 裁剪历史 / Trim history
            self.history[model_id] = self.token_manager.trim_history(
                self.history[model_id],
                self.config.max_tokens
            )

            # 准备请求 / Prepare request
            requests.append((
                self.history[model_id],
                model_id,
                self.config.response_tokens
            ))

        # ===== 并发调用 API / Concurrent API Calls =====
        results = self.api_client.get_batch_completions(requests)

        # ===== 更新历史和统计 / Update History and Statistics =====
        for model in self.chosen_models:
            model_id = model["id"]
            if model_id in results:
                content, pt, ct = results[model_id]
                responses[model_id] = content
                self.total_prompt_tokens += pt
                self.total_completion_tokens += ct

                # 添加到历史 / Add to history
                self.history[model_id].append({
                    "role": "assistant",
                    "content": content
                })

        # ===== 渲染和保存 / Render and Save =====
        round_label = f"第 {round_idx}/{total_rounds} 轮"
        if human_input:
            round_label += " (含人类指导)"

        self.ui.render_round_header(round_label)

        if human_input:
            self.ui.render_human_input(human_input)

        self.md_writer.add_round_header(round_label, human_input)

        for model in self.chosen_models:
            model_id = model["id"]
            content = responses.get(model_id, "[无回复]")
            self.ui.render_response(model_id, content, round_label)
            self.md_writer.add_model_response(model_id, content)

        self.ui.render_stats(self.total_prompt_tokens, self.total_completion_tokens)
        self.md_writer.add_token_stats(self.total_prompt_tokens, self.total_completion_tokens)
        self.md_writer.save()

        self.logger.info(
            "第 %d 轮讨论完成 / Round %d completed",
            round_idx, round_idx
        )

        return responses

    def run_summary(self) -> None:
        """
        运行最终总结 / Run Final Summary

        让每个模型生成最终总结。
        Have each model generate a final summary.
        """
        self.logger.info("开始最终总结 / Starting final summary")

        self.ui.console.print()
        self.ui.console.print(
            self.ui.console.rule("[bold bright_magenta]📝 最终总结 / Final Summary[/]",
                                style="bright_magenta")
        )
        self.ui.console.print()

        self.md_writer.add_summary_header()

        # 准备请求 / Prepare requests
        requests = []
        for model in self.chosen_models:
            model_id = model["id"]
            summary_prompt = self.prompts.format_summary_prompt()
            self.history[model_id].append({"role": "user", "content": summary_prompt})
            self.history[model_id] = self.token_manager.trim_history(
                self.history[model_id],
                self.config.max_tokens
            )
            requests.append((
                self.history[model_id],
                model_id,
                self.config.response_tokens
            ))

        # 并发调用 API / Concurrent API calls
        results = self.api_client.get_batch_completions(requests)

        # 渲染和保存 / Render and save
        for model in self.chosen_models:
            model_id = model["id"]
            if model_id in results:
                content, pt, ct = results[model_id]
                self.total_prompt_tokens += pt
                self.total_completion_tokens += ct
                self.ui.render_response(model_id, content, "最终总结")
                self.md_writer.add_model_response(model_id, content)

        self.logger.info("最终总结完成 / Final summary completed")

    def run_discussion(self, initial_rounds: int) -> str:
        """
        运行完整的讨论流程 / Run Complete Discussion Process

        Args:
            initial_rounds: 初始轮数 / Initial number of rounds

        Returns:
            str: Markdown 文件路径 / Markdown file path

        实现说明 / Implementation Notes:
        这是主要的讨论循环，支持：
        - 多轮讨论
        - 动态追加轮次
        - 人类介入指导
        - 最终总结
        This is the main discussion loop, supporting:
        - Multiple rounds of discussion
        - Dynamic addition of rounds
        - Human intervention guidance
        - Final summary
        """
        # 显示讨论开始信息 / Display discussion start info
        self.ui.render_discussion_start(
            self.topic,
            self.participants_str,
            initial_rounds
        )

        cumulative_round = 0
        total_rounds = initial_rounds
        last_responses = {}

        # 主循环 / Main loop
        while True:
            # 运行剩余的轮次 / Run remaining rounds
            batch_rounds = total_rounds - cumulative_round
            for _ in range(batch_rounds):
                cumulative_round += 1
                last_responses = self.run_round(
                    cumulative_round,
                    total_rounds,
                    last_responses
                )

            # 轮次结束 / Round end
            self.ui.console.print()
            self.ui.console.print(
                self.ui.console.rule("[bold yellow]轮次结束 / Round End[/]", style="yellow")
            )
            self.ui.render_stats(self.total_prompt_tokens, self.total_completion_tokens)
            self.ui.console.print()

            # 询问是否继续 / Ask if continue
            if not self.ui.prompt_continue():
                break

            # 追加轮次 / Add extra rounds
            extra = self.ui.prompt_extra_rounds()
            total_rounds = cumulative_round + extra

            # 人类指导 / Human guidance
            human_input = self.ui.prompt_human_guidance()
            if human_input:
                cumulative_round += 1
                total_rounds = cumulative_round + extra - 1
                last_responses = self.run_round(
                    cumulative_round,
                    total_rounds,
                    last_responses,
                    human_input=human_input
                )

        # 最终总结 / Final summary
        self.run_summary()

        # 显示统计 / Display statistics
        self.ui.render_summary_table(
            cumulative_round,
            len(self.chosen_models),
            self.total_prompt_tokens,
            self.total_completion_tokens
        )

        # 保存统计到 Markdown / Save statistics to Markdown
        self.md_writer.add_statistics_table(
            cumulative_round,
            len(self.chosen_models),
            self.total_prompt_tokens,
            self.total_completion_tokens
        )
        md_filename = self.md_writer.save()

        # 显示结束信息 / Display end info
        # 获取日志文件路径 / Get log file path
        log_path = f"{self.config.log_dir}/{self.topic[:50]}_{self.md_writer.filename.split('/')[-1].split('_')[0]}.log"
        self.ui.render_discussion_end(md_filename, log_path)

        self.logger.info(
            "讨论流程完成 / Discussion process completed: "
            "rounds=%d, models=%d, total_tokens=%d",
            cumulative_round, len(self.chosen_models),
            self.total_prompt_tokens + self.total_completion_tokens
        )

        return md_filename
