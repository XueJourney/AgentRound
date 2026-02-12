# TODO List - AgentRound 项目 / AgentRound Project

本文档记录了项目中所有待实现的功能和改进项。
This document records all pending features and improvements in the project.

## 优先级说明 / Priority Levels
- 🔴 高优先级 / High Priority - 核心功能或重要bug / Core features or important bugs
- 🟡 中优先级 / Medium Priority - 功能增强 / Feature enhancements
- 🟢 低优先级 / Low Priority - 优化和改进 / Optimizations and improvements

---

## 配置模块 / Config Module (`src/config.py`)

### 🟡 添加更详细的配置验证逻辑
- **位置 / Location**: `config.py:67`
- **描述 / Description**: 当前的 validate() 方法只做了基本验证，需要添加更多验证规则
- **建议实现 / Suggested Implementation**:
  - 验证 API URL 格式
  - 验证 temperature 范围
  - 验证 token 数值的合理性
  - Validate API URL format
  - Validate temperature range
  - Validate token value reasonableness

---

## Token管理模块 / Token Manager Module (`src/token_manager.py`)

### 🟢 支持从配置文件读取不同模型的价格
- **位置 / Location**: `token_manager.py:145`
- **描述 / Description**: estimate_cost() 方法当前使用硬编码的价格，应该支持从配置读取
- **建议实现 / Suggested Implementation**:
  - 在配置文件中添加模型价格映射
  - 修改 estimate_cost() 方法支持动态价格
  - Add model price mapping in config file
  - Modify estimate_cost() method to support dynamic pricing

---

## API客户端模块 / API Client Module (`src/api_client.py`)

### 🔴 添加请求重试机制
- **位置 / Location**: `api_client.py:30`
- **描述 / Description**: 当前网络错误会直接抛出，应该实现自动重试
- **建议实现 / Suggested Implementation**:
  - 使用 tenacity 或 backoff 库实现指数退避重试
  - 配置最大重试次数和超时时间
  - 记录重试日志
  - Use tenacity or backoff library for exponential backoff retry
  - Configure max retry attempts and timeout
  - Log retry attempts

### 🟡 添加请求速率限制
- **位置 / Location**: `api_client.py:31`
- **描述 / Description**: 避免触发 API 速率限制
- **建议实现 / Suggested Implementation**:
  - 实现 token bucket 或 leaky bucket 算法
  - 支持配置每分钟/每秒请求数限制
  - Implement token bucket or leaky bucket algorithm
  - Support configurable requests per minute/second limit

### 🟡 支持流式响应
- **位置 / Location**: `api_client.py:32`
- **描述 / Description**: 支持 streaming 模式，实时显示生成内容
- **建议实现 / Suggested Implementation**:
  - 添加 stream 参数到 get_chat_completion()
  - 实现流式响应处理逻辑
  - 更新 UI 以支持实时渲染
  - Add stream parameter to get_chat_completion()
  - Implement streaming response handling logic
  - Update UI to support real-time rendering

---

## 讨论模块 / Discussion Module (`src/discussion.py`)

### 🟡 支持讨论暂停和恢复
- **位置 / Location**: `discussion.py:33`
- **描述 / Description**: 允许用户暂停讨论并在稍后恢复
- **建议实现 / Suggested Implementation**:
  - 实现状态序列化和反序列化
  - 保存讨论快照到文件
  - 添加恢复命令
  - Implement state serialization and deserialization
  - Save discussion snapshot to file
  - Add resume command

### 🟢 支持讨论分支
- **位置 / Location**: `discussion.py:34`
- **描述 / Description**: 允许从某个轮次创建分支，探索不同的讨论方向
- **建议实现 / Suggested Implementation**:
  - 实现历史记录的分支管理
  - 支持切换和合并分支
  - Implement branch management for history
  - Support switching and merging branches

### 🟢 添加讨论质量评估
- **位置 / Location**: `discussion.py:35`
- **描述 / Description**: 自动评估讨论质量和深度
- **建议实现 / Suggested Implementation**:
  - 分析观点多样性
  - 检测重复内容
  - 评估论证质量
  - Analyze viewpoint diversity
  - Detect duplicate content
  - Evaluate argument quality

---

## 新功能建议 / New Feature Suggestions

### 🟡 国际化支持增强
- **描述 / Description**: 完善 i18n 支持，添加更多语言
- **建议实现 / Suggested Implementation**:
  - 使用 gettext 或类似库
  - 添加语言配置选项
  - 支持日语、韩语、法语等
  - Use gettext or similar library
  - Add language configuration option
  - Support Japanese, Korean, French, etc.

### 🟢 Web界面
- **描述 / Description**: 提供基于 Web 的用户界面
- **建议实现 / Suggested Implementation**:
  - 使用 FastAPI + React 或 Streamlit
  - 支持实时查看讨论进度
  - 提供历史讨论浏览功能
  - Use FastAPI + React or Streamlit
  - Support real-time discussion progress viewing
  - Provide historical discussion browsing

### 🟢 讨论模板
- **描述 / Description**: 预定义常见讨论场景的模板
- **建议实现 / Suggested Implementation**:
  - 头脑风暴模板
  - 辩论模板
  - 技术评审模板
  - Brainstorming template
  - Debate template
  - Technical review template

### 🟢 导出格式扩展
- **描述 / Description**: 支持更多导出格式
- **建议实现 / Suggested Implementation**:
  - PDF 导出
  - HTML 导出
  - JSON 导出（用于数据分析）
  - PDF export
  - HTML export
  - JSON export (for data analysis)

---

## 性能优化 / Performance Optimization

### 🟢 缓存机制
- **描述 / Description**: 缓存相似的请求以减少 API 调用
- **建议实现 / Suggested Implementation**:
  - 实现请求哈希和缓存
  - 配置缓存过期时间
  - Implement request hashing and caching
  - Configure cache expiration time

### 🟢 异步IO优化
- **描述 / Description**: 使用 asyncio 替代 ThreadPoolExecutor
- **建议实现 / Suggested Implementation**:
  - 迁移到 async/await 模式
  - 使用 aiohttp 进行异步 HTTP 请求
  - Migrate to async/await pattern
  - Use aiohttp for async HTTP requests

---

## 测试 / Testing

### 🔴 单元测试
- **描述 / Description**: 为所有模块添加单元测试
- **建议实现 / Suggested Implementation**:
  - 使用 pytest 框架
  - 目标覆盖率 > 80%
  - 添加 CI/CD 集成
  - Use pytest framework
  - Target coverage > 80%
  - Add CI/CD integration

### 🟡 集成测试
- **描述 / Description**: 测试模块间的集成
- **建议实现 / Suggested Implementation**:
  - 模拟 API 响应
  - 测试完整讨论流程
  - Mock API responses
  - Test complete discussion flow

---

## 文档 / Documentation

### 🟡 API文档
- **描述 / Description**: 生成详细的 API 文档
- **建议实现 / Suggested Implementation**:
  - 使用 Sphinx 或 MkDocs
  - 添加使用示例
  - Use Sphinx or MkDocs
  - Add usage examples

### 🟡 用户指南
- **描述 / Description**: 编写详细的用户使用指南
- **建议实现 / Suggested Implementation**:
  - 快速入门教程
  - 高级功能说明
  - 常见问题解答
  - Quick start tutorial
  - Advanced features guide
  - FAQ

---

## 更新日志 / Update Log

- **2024-XX-XX**: 创建 TODO 列表 / Created TODO list
- **2024-XX-XX**: 完成模块化重构 / Completed modularization refactoring

---

## 贡献指南 / Contribution Guidelines

如果你想贡献代码来实现这些 TODO 项，请：
If you want to contribute code to implement these TODO items, please:

1. 在 GitHub 上创建 issue 讨论实现方案 / Create an issue on GitHub to discuss implementation
2. Fork 项目并创建特性分支 / Fork the project and create a feature branch
3. 编写代码和测试 / Write code and tests
4. 提交 Pull Request / Submit a Pull Request

感谢你的贡献！/ Thank you for your contribution!
