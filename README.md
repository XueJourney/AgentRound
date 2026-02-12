<div align="center">

# 🗣️ AgentRound

**多模型 AI 圆桌讨论框架**

让多个 AI 模型围绕同一主题展开多轮辩论、碰撞观点、产出洞察

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-AGPLv3-blue?style=flat-square)](LICENSE)
[![GitHub](https://img.shields.io/github/stars/XueJourney/AgentRound?style=flat-square&logo=github)](https://github.com/XueJourney/AgentRound)

<img src="https://raw.githubusercontent.com/XueJourney/AgentRound/main/assets/demo.gif" alt="demo" width="680">

[快速开始](#-快速开始) · [功能特性](#-功能特性) · [配置说明](#%EF%B8%8F-配置说明) · [提示词工程](#-提示词工程) · [输出示例](#-输出示例)

</div>

---

## ✨ 功能特性

```
┌─────────────────────────────────────────────────────┐
│                    AgentRound                       │
├──────────────┬──────────────┬───────────────────────┤
│  🤖 多模型    │  🧑 人类介入  │  📊 Token 管理         │
│  并发讨论     │  实时指导     │  自动裁剪上下文         │
├──────────────┼──────────────┼───────────────────────┤
│  📝 Markdown │  🎨 Rich     │  🔧 全配置化            │
│  完整记录     │  终端渲染     │  .env 一站式管理        │
└──────────────┴──────────────┴───────────────────────┘
```

- **多模型并发** — 基于 `ThreadPoolExecutor`，多个模型同时生成回复，不串行等待
- **人类介入** — 每轮结束后可注入指导意见，引导讨论方向
- **智能裁剪** — 对话超出 Token 上限时自动移除最早的非 System 消息，保证 System Prompt 不丢失
- **Rich 渲染** — 每个模型独立配色，Panel + Markdown 渲染，终端阅读体验拉满
- **Markdown 导出** — 实时保存完整讨论记录，支持分享 / 复盘 / 归档
- **结构化日志** — 终端仅显示 WARNING+，详细日志写入文件，互不干扰
- **Token 容错** — API 不返回 usage 时自动回退 tiktoken 本地估算
- **全 .env 配置** — API、模型、参数、提示词模板全部可配置，零硬编码

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 任意 OpenAI 兼容 API（OpenAI / DeepSeek / Ollama / vLLM / OneAPI ...）

### 安装

```bash
git clone https://github.com/XueJourney/AgentRound.git
cd AgentRound
pip install -r requirements.txt
```

### 依赖

```txt
openai
python-dotenv
tiktoken
rich
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API 信息：

```ini
BASE_API=https://api.openai.com/v1
API_KEY=sk-your-key-here
MODELS=gpt-4o,claude-sonnet-4,gemini-2.5-pro
```

### 运行

```bash
python main.py
```

---

## 🔄 工作流程

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  选择模型  │────▶│  设定主题/轮数  │────▶│  第 1 轮讨论   │
└──────────┘     └──────────────┘     └──────┬───────┘
                                             │
                      ┌──────────────────────┘
                      ▼
               ┌─────────────┐    并发请求     ┌─────────────┐
               │   Model A   │◄──────────────▶│   Model B   │
               └──────┬──────┘               └──────┬──────┘
                      │         ┌─────────────┐      │
                      └────▶│   Model C   │◀─────┘
                                └──────┬──────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  汇总本轮回复     │
                              │  交叉注入上下文   │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │  轮次结束？       │
                              └────────┬────────┘
                                  ╱         ╲
                              是 ╱           ╲ 否
                               ╱             ╲
                    ┌─────────▼──┐    ┌──────▼────────┐
                    │ 🧑 人类介入  │    │  下一轮讨论     │
                    │ 追加轮数？   │    └───────────────┘
                    │ 指导方向？   │
                    └─────────┬──┘
                              │
                    ┌─────────▼──────────┐
                    │  继续 / 最终总结     │
                    └────────────────────┘
```

---

## ⚙️ 配置说明

### 完整 `.env` 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `BASE_API` | `https://api.openai.com/v1` | API 地址 |
| `API_KEY` | — | API 密钥（必填） |
| `MODELS` | — | 模型列表，逗号分隔。留空则从 API 自动获取 |
| `RESPONSE_TOKENS` | `2048` | 单次回复最大 Token |
| `MAX_TOKENS` | `32000` | 对话上下文 Token 上限，超出自动裁剪 |
| `TIKTOKEN_MODEL` | `gpt-4o` | tiktoken 本地估算用的模型名 |
| `TEMPERATURE_MIN` | `0.4` | 温度下限（每次随机取值） |
| `TEMPERATURE_MAX` | `1.2` | 温度上限 |
| `MAX_WORKERS` | `5` | 最大并发线程数 |
| `INITIAL_ROUNDS` | `3` | 初始讨论轮数 |
| `TOPIC` | — | 讨论主题，留空则运行时输入 |
| `OUTPUT_DIR` | `discussions` | Markdown 记录保存目录 |
| `LOG_DIR` | `log` | 日志文件保存目录 |

---

## 🎯 提示词工程

所有提示词均可通过 `.env` 覆盖，支持变量插值：

### System Prompt

> 变量：`{model_name}` `{topic}` `{participants}`

定义每个模型的身份、讨论规则和行为约束。

### First Round Prompt

> 变量：`{current_round}` `{total_rounds}` `{remaining}` `{model_name}` `{topic}`

首轮发言指令，要求模型亮明立场。

### Discussion Prompt

> 变量：`{current_round}` `{total_rounds}` `{remaining}` `{others_text}`

后续轮次指令，注入其他模型的上轮发言，引导交叉讨论。

### Human Guide Prompt

> 变量：`{human_input}`

人类介入时的指导注入，以 `# Human` 标识。

### Summary Prompt

最终总结指令，要求模型归纳立场、亮点和分歧。

```ini
# .env 自定义示例
SYSTEM_PROMPT=你是 {model_name}，一位资深技术架构师。主题：{topic}。参与者：{participants}。请用技术视角深入分析。
```

---

## 📄 输出示例

### 终端渲染

```
──────────────────── 📌 第 1/3 轮 ────────────────────

╭─────────────── 🤖 gpt-4o ───────────────╮
│                                          │
│  我认为这个问题的核心在于...               │
│                                          │
│  1. 首先，从技术角度来看...               │
│  2. 其次，考虑到实际应用场景...            │
│                                          │
╰──────────────── 第 1/3 轮 ───────────────╯

╭──────────── 🤖 claude-sonnet-4 ──────────╮
│                                          │
│  有趣的视角。不过我想补充的是...           │
│                                          │
╰──────────────── 第 1/3 轮 ───────────────╯

  📊 prompt: 1,234 | completion: 567 | total: 1,801
```

### Markdown 记录

生成路径：`discussions/20250212_143000_讨论主题.md`

包含完整的轮次记录、人类指导标注、Token 统计表格，可直接用于分享或复盘。

### 日志文件

生成路径：`log/讨论主题_20250212_143000.log`

包含 DEBUG 级别的完整运行日志：API 调用详情、Token 计数、上下文裁剪记录。

---

## 📁 项目结构

```
AgentRound/
├── main.py                    # 主程序入口
├── app.py                     # 原单文件版本（已废弃，保留作参考）
├── .env.example               # 配置模板
├── .env                       # 你的配置（git ignored）
├── requirements.txt           # 依赖
├── TODO_list.md               # 待实现功能索引
├── src/                       # 核心模块目录
│   ├── __init__.py            # 包初始化
│   ├── config.py              # 配置管理模块
│   ├── logger.py              # 日志系统模块
│   ├── prompts.py             # 提示词模板模块
│   ├── token_manager.py       # Token计数和历史管理
│   ├── api_client.py          # API客户端模块
│   ├── ui.py                  # 用户界面模块
│   ├── markdown_writer.py     # Markdown文件生成模块
│   └── discussion.py          # 讨论编排模块
├── discussions/               # Markdown 讨论记录
│   └── 20250212_*.md
├── log/                       # 运行日志
│   └── *_20250212.log
├── assets/                    # README 资源
└── LICENSE
```

### 🏗️ 模块化架构

项目采用清晰的模块化设计，每个模块职责单一：

| 模块 | 职责 | 主要功能 |
|------|------|---------|
| `config.py` | 配置管理 | 加载环境变量、验证配置、提供统一配置接口 |
| `logger.py` | 日志系统 | 控制台+文件双输出、分级日志、按主题命名 |
| `prompts.py` | 提示词管理 | 模板加载、变量替换、支持自定义 |
| `token_manager.py` | Token管理 | Token计数、历史裁剪、成本估算 |
| `api_client.py` | API客户端 | 模型列表获取、聊天请求、并发调用 |
| `ui.py` | 用户界面 | Rich渲染、交互输入、统计展示 |
| `markdown_writer.py` | 文档生成 | Markdown格式化、实时保存、双语支持 |
| `discussion.py` | 讨论编排 | 流程控制、轮次管理、历史维护 |

**架构优势**：
- ✅ 代码结构清晰，易于理解和维护
- ✅ 模块间低耦合，便于单元测试
- ✅ 详细的中英双语注释和文档
- ✅ 预留扩展接口，支持功能增强
- ✅ 符合 SOLID 设计原则

---

## 🛠️ 开发指南

### 代码规范

- **注释要求**：所有模块、类、函数都需要详细的中英双语文档字符串
- **日志记录**：使用 logger 记录关键操作和错误信息
- **类型提示**：使用 Python 类型提示提高代码可读性
- **错误处理**：合理使用异常处理，记录错误日志

### 添加新功能

1. 在对应模块中实现功能
2. 更新 `TODO_list.md` 标记完成状态
3. 添加必要的日志输出
4. 更新文档和注释

### 测试

```bash
# 运行主程序测试
python main.py

# 查看日志
tail -f log/*.log
```

### 待实现功能

查看 [TODO_list.md](TODO_list.md) 了解计划中的功能和改进项。

---

## 🤝 Contributing

欢迎 PR 和 Issue。

---

## 📜 License

本项目采用 **双许可证** 模式：

| 使用场景 | 许可证 | 要求 |
|---------|--------|------|
| 个人 / 学术 | AGPLv3 | 保持开源，链接回原仓库 |
| 修改 / Fork | AGPLv3 | 开源 + 链接原仓库 |
| 网络服务 (SaaS) | AGPLv3 | 公开源代码 |
| 商业 / 闭源 | 商业许可 | 联系作者获取授权 |

详见 [LICENSE](LICENSE) 文件。

商业授权联系：[admin@xuejourney.xin](mailto:admin@xuejourney.xin)

<div align="center">

Made with ❤️ by [XueJourney](https://github.com/XueJourney)

</div>