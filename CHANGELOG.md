# Changelog

本文档记录 Smart Doc QA 的所有版本变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

---

## [Unreleased]

### Added
### Fixed
### Changed

---

## [2.7.0] - 2026-06-06

### ✨ Added（新功能）
- Agent tool call log display with timeline-style collapsible UI（Agent 工具调用日志展示，时间轴风格可折叠 UI）
- Document selector moved to chat toolbar dropdown（文档选择器从左侧面板移至聊天工具栏下拉框）
- ProcessingModal: 4-step upload progress window（ProcessingModal：4步上传进度弹窗）
- Message copy button with visual feedback（消息复制按钮，带视觉反馈）
- Chat message search and filter（聊天消息搜索过滤）
- Automatic scroll to latest message（自动滚动到最新消息）
- Duplicate document upload prevention（重复文档上传检测）
- web_search tool switched from DuckDuckGo to Bing (cn.bing.com)（联网搜索从 DuckDuckGo 切换到 Bing 国内可用版本）

### 🐛 Fixed（Bug 修复）
- Backend 502 errors caused by blocking sync calls in async event loop（后端 async 事件循环中同步阻塞调用导致的 502 错误）
  - Wrapped QAService calls in `asyncio.to_thread()` for all endpoints（所有端点使用 `asyncio.to_thread()` 隔离同步调用）
- web_search timeout due to DuckDuckGo being inaccessible in China（联网搜索因 DuckDuckGo 被墙导致超时）
- Chat history mixing across different knowledge bases（不同知识库的对话历史混在一起的问题）
- User message bubble right-alignment issue（用户消息气泡靠右对齐问题）
- Missing ProcessingModal after document selector refactor（文档选择器重构后缺失的 ProcessingModal）

### ♻️ Changed（变更）
- Tool call log UI: gradient header, step timeline, animated collapse（工具调用日志 UI 全面美化：渐变头部、步骤时间轴、弹性动画）
- Message copy button always visible instead of hover-only（消息复制按钮改为始终可见）
- User message bubble alignment with margin-left: auto（用户消息气泡对齐改为 margin-left: auto）
- web_search timeout reduced from 10s to 5s（联网搜索超时从 10 秒缩短到 5 秒）
- DocumentSelector.vue added as new component（新增 DocumentSelector.vue 组件）

---

## [2.6.0] - 2026-06-05

### ✨ Added（新功能）
- 历史记录功能（按日期分组：今天/昨天/日期）
- 流式输出支持（SSE 逐 token 显示）
- 多轮对话上下文记忆（`conversation_id` 跨轮次保持）
- 对话历史 API（`GET /api/v1/qa/history`）
- 历史面板按日期分组显示（今天/昨天/6月5日）
- 历史项显示最新问题（`last_question`）

### 🐛 Fixed（Bug 修复）
- 修复删除文档后向量库未清理（仍能检索已删文档内容）
- 修复历史面板时间显示错误（UTC 时区未正确转换，显示"8小时前"）
- 修复流式输出双机器人头像问题
- 修复 Ctrl+Enter 无法换行（直接发送）问题
- 修复空文件上传 `list index out of range` 崩溃
- 修复后端 500 错误（Windows 路径非法字符 `<>`，缺少 `@staticmethod` 装饰器）
- 修复历史按钮点击无反应（`HistoryPanel` 组件未引入渲染）
- 修复历史面板挤压主内容区（`Teleport` 在 HMR 下失效，改为脱离 flex 容器）
- 修复历史面板缺少滚动条导致内容拥挤
- 修复新对话不自动出现在历史面板中（`loadHistory()` 未调用）
- 修复历史面板显示旧问题（`first_question` 而非 `last_question`）
- 修复历史记录按创建时间分组而非最后活动时间

### ♻️ Changed（变更）
- 前端架构完全升级（Vue 3.5 + TypeScript 5 + Vite 8 + Naive UI 2）
- 状态管理迁移到 Pinia（5 个 store：conversation、document、domain、knowledgeBase、ui）
- API 层统一封装（Axios + TypeScript 类型安全）
- 流式输出改用 fetch API（非 Axios，支持 SSE）
- Markdown 渲染支持（marked + highlight.js）
- 主题切换支持（dark/light 模式，localStorage 持久化）
- WebSocket 进度推送（文档处理实时进度）
- 构建优化（Vite 8 多阶段构建、manualChunks 分包）
- 优化向量检索性能
- 更新 DeepSeek API 到 v4-flash
- 历史 API 新增 `last_activity_at` 和 `last_question` 字段
- 后端时区修复（全项目 `datetime.utcnow` → `datetime.now(timezone.utc)`）
- Docker 多阶段构建（前端独立构建）

### 🗑️ Removed（移除）
- 移除旧版 jQuery 前端

---

## [2.5.0] - 2026-05-XX

### ✨ Added
- 文档上传功能
- WebSocket 进度推送
- 知识库 CRUD
- 基础问答功能（非流式）

### 🐛 Fixed
- 修复空文件上传崩溃

---

## [2.4.0] - 2026-05-01

### ✨ Added
- 项目初始化
- FastAPI 后端框架搭建
- MySQL 数据库设计
- FAISS + BM25 混合检索

---

[Unreleased]: https://github.com/melonelish/smart-doc-qa/compare/v2.7.0...HEAD
[2.7.0]: https://github.com/melonelish/smart-doc-qa/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/melonelish/smart-doc-qa/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/melonelish/smart-doc-qa/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/melonelish/smart-doc-qa/releases/tag/v2.4.0
