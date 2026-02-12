"""
主程序入口 / Main Program Entry Point

功能说明 / Functionality:
这是应用程序的主入口，负责初始化各个组件并启动讨论流程。
This is the main entry point of the application, responsible for initializing
components and starting the discussion process.

实现细节 / Implementation Details:
- 加载配置
- 初始化日志系统
- 获取和选择模型
- 启动讨论管理器
- Loads configuration
- Initializes logging system
- Gets and selects models
- Starts discussion manager

设计理由 / Design Rationale:
将主程序逻辑与业务逻辑分离，使代码结构更清晰，便于测试和维护。
Separating main program logic from business logic makes code structure clearer,
easier to test and maintain.

使用方法 / Usage:
    python main.py

环境变量配置 / Environment Variable Configuration:
    请参考 .env.example 文件配置必要的环境变量。
    Please refer to .env.example file to configure necessary environment variables.
"""

import sys
import logging
from src.config import Config
from src.logger import setup_logger
from src.api_client import APIClient
from src.ui import UIManager
from src.discussion import DiscussionManager


def main():
    """
    主函数 / Main Function

    执行流程 / Execution Flow:
    1. 加载配置 / Load configuration
    2. 获取可用模型 / Get available models
    3. 用户选择模型 / User selects models
    4. 用户输入讨论主题和轮数 / User inputs topic and rounds
    5. 初始化日志系统 / Initialize logging system
    6. 启动讨论 / Start discussion
    7. 保存结果 / Save results
    """
    # ===== 1. 加载配置 / Load Configuration =====
    try:
        config = Config()
        if not config.validate():
            print("配置验证失败，请检查 .env 文件 / Configuration validation failed, please check .env file")
            sys.exit(1)
    except Exception as e:
        print(f"配置加载失败 / Configuration loading failed: {e}")
        sys.exit(1)

    # ===== 2. 初始化 UI / Initialize UI =====
    ui = UIManager()

    # ===== 3. 获取可用模型 / Get Available Models =====
    try:
        api_client = APIClient(
            base_url=config.base_api,
            api_key=config.api_key,
            temperature_min=config.temperature_min,
            temperature_max=config.temperature_max,
            max_workers=config.max_workers
        )
        models = api_client.get_available_models(config.models)

        if not models:
            print("错误: 模型列表为空 / Error: Model list is empty")
            sys.exit(1)

    except Exception as e:
        print(f"获取模型列表失败 / Failed to get model list: {e}")
        sys.exit(1)

    # ===== 4. 用户选择模型 / User Selects Models =====
    ui.display_model_table(models)
    chosen_models = ui.select_models(models)

    if not chosen_models:
        print("错误: 未选择任何模型 / Error: No models selected")
        sys.exit(1)

    # ===== 5. 用户输入讨论主题和轮数 / User Inputs Topic and Rounds =====
    topic = config.topic if config.topic else ui.prompt_topic()
    rounds = config.initial_rounds if config.initial_rounds else ui.prompt_rounds()

    # ===== 6. 初始化日志系统 / Initialize Logging System =====
    logger = setup_logger(
        log_dir=config.log_dir,
        name="AgentRound",
        topic=topic
    )

    logger.info("=" * 60)
    logger.info("AgentRound 启动 / AgentRound Started")
    logger.info("=" * 60)
    logger.info("配置信息 / Configuration: %s", config)
    logger.info("选中模型 / Selected models: %s", [m["id"] for m in chosen_models])
    logger.info("讨论主题 / Discussion topic: %s", topic)
    logger.info("初始轮数 / Initial rounds: %d", rounds)

    # ===== 7. 启动讨论 / Start Discussion =====
    try:
        discussion_manager = DiscussionManager(
            config=config,
            chosen_models=chosen_models,
            topic=topic
        )

        md_filename = discussion_manager.run_discussion(rounds)

        logger.info("讨论成功完成 / Discussion completed successfully")
        logger.info("Markdown 文件 / Markdown file: %s", md_filename)
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("用户中断程序 / User interrupted program")
        print("\n\n程序已中断 / Program interrupted")
        sys.exit(0)

    except Exception as e:
        logger.error("讨论过程中发生错误 / Error occurred during discussion: %s", e, exc_info=True)
        print(f"\n错误 / Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
