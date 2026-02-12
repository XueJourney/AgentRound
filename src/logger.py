"""
日志系统模块 / Logging System Module

功能说明 / Functionality:
这个模块提供统一的日志配置和管理，支持控制台和文件双输出。
This module provides unified logging configuration and management,
supporting both console and file output.

实现细节 / Implementation Details:
- 使用 Python 标准库 logging 模块
- 控制台输出 WARNING 及以上级别
- 文件输出 DEBUG 及以上级别
- 支持按主题命名日志文件
- Uses Python standard library logging module
- Console output for WARNING and above
- File output for DEBUG and above
- Supports naming log files by topic

设计理由 / Design Rationale:
分离控制台和文件日志级别可以在不干扰用户的情况下记录详细的调试信息。
Separating console and file log levels allows detailed debug information
to be recorded without disturbing the user.

已知问题 / Known Issues:
- 无 / None
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional


class LoggerManager:
    """
    日志管理器类 / Logger Manager Class

    这个类负责配置和管理应用程序的日志系统。
    This class is responsible for configuring and managing the application's logging system.
    """

    def __init__(self, log_dir: str = "log"):
        """
        初始化日志管理器 / Initialize Logger Manager

        Args:
            log_dir: 日志文件目录 / Log file directory
        """
        self.log_dir = log_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger: Optional[logging.Logger] = None
        self.file_handler: Optional[logging.FileHandler] = None

        # 创建日志目录 / Create log directory
        os.makedirs(self.log_dir, exist_ok=True)

    def setup_logger(self, name: str = __name__, topic: Optional[str] = None) -> logging.Logger:
        """
        设置日志记录器 / Setup Logger

        Args:
            name: 日志记录器名称 / Logger name
            topic: 讨论主题，用于命名日志文件 / Discussion topic for naming log file

        Returns:
            logging.Logger: 配置好的日志记录器 / Configured logger

        实现说明 / Implementation Notes:
        - 创建一个新的 logger 实例
        - 添加控制台 handler (WARNING+)
        - 如果提供了 topic，添加文件 handler (DEBUG+)
        - Creates a new logger instance
        - Adds console handler (WARNING+)
        - If topic provided, adds file handler (DEBUG+)
        """
        # 创建 logger / Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的 handlers，避免重复 / Clear existing handlers to avoid duplication
        self.logger.handlers.clear()

        # ===== 控制台 handler / Console Handler =====
        # 只显示 WARNING 及以上级别，避免干扰用户界面
        # Only show WARNING and above to avoid interfering with user interface
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # ===== 文件 handler / File Handler =====
        # 如果提供了主题，创建文件日志
        # If topic provided, create file log
        if topic:
            log_path = self._create_file_handler(topic)
            self.logger.info("日志系统初始化完成 / Logging system initialized")
            self.logger.info("日志文件路径 / Log file path: %s", log_path)

        return self.logger

    def _create_file_handler(self, topic: str) -> str:
        """
        创建文件日志处理器 / Create File Log Handler

        Args:
            topic: 讨论主题 / Discussion topic

        Returns:
            str: 日志文件路径 / Log file path

        实现说明 / Implementation Notes:
        - 清理主题名称，移除非法字符
        - 创建带时间戳的日志文件
        - 设置 DEBUG 级别，记录所有详细信息
        - Sanitize topic name, remove illegal characters
        - Create timestamped log file
        - Set DEBUG level to record all detailed information
        """
        # 清理主题名称，只保留字母数字和部分符号
        # Sanitize topic name, keep only alphanumeric and some symbols
        safe_topic = "".join(
            c if c.isalnum() or c in "_- " else "_"
            for c in topic
        )[:50]  # 限制长度 / Limit length

        # 构建日志文件路径 / Build log file path
        log_filename = f"{safe_topic}_{self.timestamp}.log"
        log_path = os.path.join(self.log_dir, log_filename)

        # 创建文件 handler / Create file handler
        self.file_handler = logging.FileHandler(log_path, encoding="utf-8")
        self.file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(file_formatter)
        self.logger.addHandler(self.file_handler)

        return log_path

    def get_logger(self) -> Optional[logging.Logger]:
        """
        获取日志记录器实例 / Get Logger Instance

        Returns:
            Optional[logging.Logger]: 日志记录器，如果未初始化则返回 None
                                     Logger instance, None if not initialized
        """
        return self.logger


def setup_logger(log_dir: str = "log", name: str = __name__,
                 topic: Optional[str] = None) -> logging.Logger:
    """
    便捷函数：设置日志记录器 / Convenience Function: Setup Logger

    这是一个便捷函数，用于快速设置日志系统。
    This is a convenience function for quickly setting up the logging system.

    Args:
        log_dir: 日志目录 / Log directory
        name: 日志记录器名称 / Logger name
        topic: 讨论主题 / Discussion topic

    Returns:
        logging.Logger: 配置好的日志记录器 / Configured logger
    """
    manager = LoggerManager(log_dir)
    return manager.setup_logger(name, topic)
