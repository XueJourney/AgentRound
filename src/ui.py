"""
用户界面模块 / User Interface Module

功能说明 / Functionality:
这个模块使用 Rich 库提供美观的终端用户界面，包括模型选择、对话渲染等。
This module uses the Rich library to provide a beautiful terminal user interface,
including model selection, conversation rendering, etc.

实现细节 / Implementation Details:
- 使用 Rich 库的各种组件（Panel, Table, Markdown等）
- 为不同模型分配不同颜色以便区分
- 提供交互式输入功能
- Uses various Rich library components (Panel, Table, Markdown, etc.)
- Assigns different colors to different models for distinction
- Provides interactive input functionality

设计理由 / Design Rationale:
良好的用户界面可以显著提升用户体验，Rich 库提供了强大的终端渲染能力。
A good user interface significantly enhances user experience,
Rich library provides powerful terminal rendering capabilities.
"""

import logging
from typing import List, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.rule import Rule
from rich.text import Text


# 模型配色方案 / Model Color Scheme
MODEL_COLORS = [
    "cyan", "green", "yellow", "magenta", "blue",
    "red", "bright_cyan", "bright_green", "bright_yellow", "bright_magenta"
]


class UIManager:
    """
    用户界面管理器类 / User Interface Manager Class

    这个类负责所有终端用户界面的渲染和交互。
    This class is responsible for all terminal user interface rendering and interaction.
    """

    def __init__(self):
        """
        初始化UI管理器 / Initialize UI Manager
        """
        self.console = Console()
        self.model_color_map: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)

        self.logger.info("UI管理器初始化完成 / UI manager initialized")

    def get_model_color(self, model_id: str) -> str:
        """
        获取模型的颜色 / Get Model Color

        Args:
            model_id: 模型 ID / Model ID

        Returns:
            str: 颜色名称 / Color name

        实现说明 / Implementation Notes:
        为每个模型分配一个唯一的颜色，循环使用预定义的颜色列表。
        Assigns a unique color to each model, cycling through predefined color list.
        """
        if model_id not in self.model_color_map:
            idx = len(self.model_color_map) % len(MODEL_COLORS)
            self.model_color_map[model_id] = MODEL_COLORS[idx]
            self.logger.debug(
                "为模型 %s 分配颜色: %s / Assigned color to model %s: %s",
                model_id, MODEL_COLORS[idx], model_id, MODEL_COLORS[idx]
            )
        return self.model_color_map[model_id]

    def display_model_table(self, models: List[Dict[str, str]]) -> None:
        """
        显示模型列表表格 / Display Model List Table

        Args:
            models: 模型列表 / Model list
        """
        table = Table(title="可用模型 / Available Models", show_header=True, header_style="bold cyan")
        table.add_column("序号 / Index", style="dim", width=12)
        table.add_column("模型名称 / Model Name", style="bold")

        for i, model in enumerate(models):
            table.add_row(str(i), model["id"])

        self.console.print()
        self.console.print(table)
        self.logger.debug("显示了 %d 个模型 / Displayed %d models", len(models), len(models))

    def select_models(self, models: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        交互式选择模型 / Interactive Model Selection

        Args:
            models: 可用模型列表 / Available model list

        Returns:
            List[Dict[str, str]]: 选中的模型列表 / Selected model list

        实现说明 / Implementation Notes:
        允许用户多次选择模型，直到用户确认完成。
        Allows users to select models multiple times until confirmation.
        """
        chosen_models = []

        while True:
            try:
                idx = IntPrompt.ask("\n请输入模型序号 / Please enter model index")
                if 0 <= idx < len(models):
                    chosen_models.append(models[idx])
                    chosen_names = [m["id"] for m in chosen_models]
                    self.console.print(
                        f"  已选择 / Selected: [bold green]{', '.join(chosen_names)}[/]"
                    )
                    if not Confirm.ask("继续选择? / Continue selecting?", default=False):
                        break
                else:
                    self.console.print("[red]序号超出范围 / Index out of range[/]")
            except (ValueError, IndexError):
                self.console.print("[red]输入错误，请重新输入 / Invalid input, please try again[/]")

        self.logger.info(
            "用户选择了 %d 个模型 / User selected %d models: %s",
            len(chosen_models), len(chosen_models),
            [m["id"] for m in chosen_models]
        )

        return chosen_models

    def render_response(self, model_id: str, content: str, round_label: str) -> None:
        """
        渲染模型响应 / Render Model Response

        Args:
            model_id: 模型 ID / Model ID
            content: 响应内容 / Response content
            round_label: 轮次标签 / Round label
        """
        color = self.get_model_color(model_id)
        panel = Panel(
            Markdown(content),
            title=f"[bold {color}]🤖 {model_id}[/]",
            subtitle=f"[dim]{round_label}[/]",
            border_style=color,
            padding=(1, 2)
        )
        self.console.print(panel)

    def render_human_input(self, text: str) -> None:
        """
        渲染人类输入 / Render Human Input

        Args:
            text: 输入文本 / Input text
        """
        panel = Panel(
            Text(text, style="bold white"),
            title="[bold bright_white]🧑 Human 指导 / Human Guidance[/]",
            border_style="bright_white",
            padding=(1, 2)
        )
        self.console.print(panel)

    def render_stats(self, prompt_tokens: int, completion_tokens: int) -> None:
        """
        渲染统计信息 / Render Statistics

        Args:
            prompt_tokens: 提示 token 数 / Prompt tokens
            completion_tokens: 完成 token 数 / Completion tokens
        """
        total = prompt_tokens + completion_tokens
        self.console.print(
            f"  [dim]📊 prompt: {prompt_tokens:,} | "
            f"completion: {completion_tokens:,} | "
            f"total: {total:,}[/]"
        )

    def render_round_header(self, round_label: str) -> None:
        """
        渲染轮次标题 / Render Round Header

        Args:
            round_label: 轮次标签 / Round label
        """
        self.console.print()
        self.console.print(Rule(f"[bold]📌 {round_label}[/]", style="bright_blue"))
        self.console.print()

    def render_discussion_start(self, topic: str, participants: str, rounds: int) -> None:
        """
        渲染讨论开始信息 / Render Discussion Start Info

        Args:
            topic: 讨论主题 / Discussion topic
            participants: 参与者列表 / Participant list
            rounds: 轮数 / Number of rounds
        """
        self.console.print()
        self.console.print(Rule("[bold bright_blue]🗣️ 多模型讨论开始 / Multi-Model Discussion Start[/]", style="bright_blue"))
        self.console.print(f"  主题 / Topic: [bold]{topic}[/]")
        self.console.print(f"  模型 / Models: [bold green]{participants}[/]")
        self.console.print(f"  轮数 / Rounds: [bold]{rounds}[/]")
        self.console.print()

    def render_summary_table(self, total_rounds: int, num_models: int,
                            prompt_tokens: int, completion_tokens: int) -> None:
        """
        渲染统计表格 / Render Statistics Table

        Args:
            total_rounds: 总轮数 / Total rounds
            num_models: 模型数量 / Number of models
            prompt_tokens: 提示 token 数 / Prompt tokens
            completion_tokens: 完成 token 数 / Completion tokens
        """
        stats_table = Table(title="📊 讨论统计 / Discussion Statistics",
                           show_header=True, header_style="bold cyan")
        stats_table.add_column("指标 / Metric", style="bold")
        stats_table.add_column("数值 / Value", justify="right")

        stats_table.add_row("总轮数 / Total Rounds", str(total_rounds))
        stats_table.add_row("参与模型 / Participating Models", str(num_models))
        stats_table.add_row("Prompt Tokens", f"{prompt_tokens:,}")
        stats_table.add_row("Completion Tokens", f"{completion_tokens:,}")
        stats_table.add_row("总 Tokens / Total Tokens", f"{prompt_tokens + completion_tokens:,}")

        self.console.print()
        self.console.print(stats_table)

    def prompt_topic(self) -> str:
        """
        提示用户输入讨论主题 / Prompt User for Discussion Topic

        Returns:
            str: 讨论主题 / Discussion topic
        """
        return Prompt.ask("\n请输入讨论主题 / Please enter discussion topic")

    def prompt_rounds(self) -> int:
        """
        提示用户输入轮数 / Prompt User for Number of Rounds

        Returns:
            int: 轮数 / Number of rounds
        """
        return IntPrompt.ask("请输入对话轮数 / Please enter number of rounds")

    def prompt_continue(self) -> bool:
        """
        询问是否继续新轮次 / Ask if Continue New Round

        Returns:
            bool: 是否继续 / Whether to continue
        """
        return Confirm.ask("是否开启新的轮次? / Start new round?", default=False)

    def prompt_extra_rounds(self) -> int:
        """
        询问追加轮数 / Ask for Extra Rounds

        Returns:
            int: 追加轮数 / Extra rounds
        """
        return IntPrompt.ask("追加几轮 / How many extra rounds")

    def prompt_human_guidance(self) -> str:
        """
        询问人类指导 / Ask for Human Guidance

        Returns:
            str: 指导内容 / Guidance content
        """
        return Prompt.ask(
            "有需要指导的方向吗? (直接回车跳过) / "
            "Any guidance needed? (Press Enter to skip)",
            default=""
        ).strip()

    def render_discussion_end(self, md_filename: str, log_path: str) -> None:
        """
        渲染讨论结束信息 / Render Discussion End Info

        Args:
            md_filename: Markdown 文件路径 / Markdown file path
            log_path: 日志文件路径 / Log file path
        """
        self.console.print()
        self.console.print(f"  📄 对话记录 / Discussion Record: [link={md_filename}]{md_filename}[/]")
        self.console.print(f"  📋 运行日志 / Run Log: [link={log_path}]{log_path}[/]")
        self.console.print()
        self.console.print(Rule("[bold bright_blue]讨论结束 / Discussion End[/]", style="bright_blue"))
