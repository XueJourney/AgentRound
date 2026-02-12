"""
Markdown文件生成模块 / Markdown File Generation Module

功能说明 / Functionality:
这个模块负责将讨论内容保存为 Markdown 格式的文件，便于后续查看和分享。
This module is responsible for saving discussion content as Markdown files
for easy viewing and sharing.

实现细节 / Implementation Details:
- 使用增量写入方式，实时保存讨论内容
- 支持中英双语标题和格式
- 包含元数据、讨论内容和统计信息
- Uses incremental writing to save discussion content in real-time
- Supports bilingual titles and formatting
- Includes metadata, discussion content, and statistics

设计理由 / Design Rationale:
Markdown 格式易于阅读和编辑，支持代码高亮和格式化，是记录技术讨论的理想格式。
Markdown format is easy to read and edit, supports code highlighting and formatting,
making it ideal for recording technical discussions.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional


class MarkdownWriter:
    """
    Markdown文件写入器类 / Markdown File Writer Class

    这个类负责生成和维护讨论的 Markdown 记录。
    This class is responsible for generating and maintaining Markdown records of discussions.
    """

    def __init__(self, output_dir: str, topic: str, participants: str, max_tokens: int):
        """
        初始化Markdown写入器 / Initialize Markdown Writer

        Args:
            output_dir: 输出目录 / Output directory
            topic: 讨论主题 / Discussion topic
            participants: 参与者列表 / Participant list
            max_tokens: Token 上限 / Token limit
        """
        self.output_dir = output_dir
        self.topic = topic
        self.participants = participants
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)

        # 创建输出目录 / Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # 生成文件名 / Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(
            c if c.isalnum() or c in "_- " else "_"
            for c in topic
        )[:50]
        self.filename = os.path.join(self.output_dir, f"{timestamp}_{safe_topic}.md")

        # 内容缓冲区 / Content buffer
        self.lines: List[str] = []

        # 初始化文件头 / Initialize file header
        self._write_header()

        self.logger.info(
            "Markdown写入器初始化完成 / Markdown writer initialized: %s",
            self.filename
        )

    def _write_header(self) -> None:
        """
        写入文件头 / Write File Header

        包含讨论的元数据信息。
        Contains metadata information about the discussion.
        """
        self.lines.extend([
            "# 🗣️ 多模型讨论记录 / Multi-Model Discussion Record",
            "",
            f"> **主题 / Topic**: {self.topic}  ",
            f"> **时间 / Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"> **参与模型 / Participating Models**: {self.participants}  ",
            f"> **Token 上限 / Token Limit**: {self.max_tokens}",
            "",
            "---",
            ""
        ])

    def add_round_header(self, round_label: str, human_input: Optional[str] = None) -> None:
        """
        添加轮次标题 / Add Round Header

        Args:
            round_label: 轮次标签 / Round label
            human_input: 人类指导内容（可选）/ Human guidance content (optional)
        """
        self.lines.extend([
            f"## 📌 {round_label}",
            ""
        ])

        if human_input:
            self.lines.extend([
                "### 🧑 Human 指导 / Human Guidance",
                "",
                f"> {human_input}",
                ""
            ])

        self.logger.debug("添加轮次标题: %s / Added round header: %s", round_label, round_label)

    def add_model_response(self, model_id: str, content: str) -> None:
        """
        添加模型响应 / Add Model Response

        Args:
            model_id: 模型 ID / Model ID
            content: 响应内容 / Response content
        """
        self.lines.extend([
            f"### 🤖 {model_id}",
            "",
            content,
            ""
        ])

        self.logger.debug("添加模型响应: %s / Added model response: %s", model_id, model_id)

    def add_token_stats(self, prompt_tokens: int, completion_tokens: int) -> None:
        """
        添加 Token 统计 / Add Token Statistics

        Args:
            prompt_tokens: 提示 token 数 / Prompt tokens
            completion_tokens: 完成 token 数 / Completion tokens
        """
        self.lines.extend([
            f"> 📊 累计 tokens / Cumulative tokens — "
            f"prompt: {prompt_tokens:,}, completion: {completion_tokens:,}",
            "",
            "---",
            ""
        ])

    def add_summary_header(self) -> None:
        """
        添加总结标题 / Add Summary Header
        """
        self.lines.extend([
            "## 📝 最终总结 / Final Summary",
            ""
        ])

    def add_statistics_table(self, total_rounds: int, num_models: int,
                            prompt_tokens: int, completion_tokens: int) -> None:
        """
        添加统计表格 / Add Statistics Table

        Args:
            total_rounds: 总轮数 / Total rounds
            num_models: 模型数量 / Number of models
            prompt_tokens: 提示 token 数 / Prompt tokens
            completion_tokens: 完成 token 数 / Completion tokens
        """
        total_tokens = prompt_tokens + completion_tokens

        self.lines.extend([
            "---",
            "",
            "## 📊 统计 / Statistics",
            "",
            "| 指标 / Metric | 数值 / Value |",
            "|--------------|--------------|",
            f"| 总轮数 / Total Rounds | {total_rounds} |",
            f"| 参与模型 / Participating Models | {num_models} |",
            f"| Prompt Tokens | {prompt_tokens:,} |",
            f"| Completion Tokens | {completion_tokens:,} |",
            f"| 总 Tokens / Total Tokens | {total_tokens:,} |",
            ""
        ])

        self.logger.debug("添加统计表格 / Added statistics table")

    def save(self) -> str:
        """
        保存文件 / Save File

        Returns:
            str: 文件路径 / File path

        实现说明 / Implementation Notes:
        将缓冲区的内容写入文件，使用 UTF-8 编码。
        Writes buffer content to file using UTF-8 encoding.
        """
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))

            self.logger.info(
                "Markdown文件已保存 / Markdown file saved: %s",
                self.filename
            )
            return self.filename

        except Exception as e:
            self.logger.error(
                "保存Markdown文件失败 / Failed to save Markdown file: %s",
                e
            )
            raise

    def get_filename(self) -> str:
        """
        获取文件名 / Get Filename

        Returns:
            str: 文件路径 / File path
        """
        return self.filename
