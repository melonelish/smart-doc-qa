# Changelog

本文档记录 Smart Doc QA 的所有版本变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

---

## [Unreleased]

### Added
### Fixed
### Changed

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

[Unreleased]: https://github.com/melonelish/smart-doc-qa/compare/v2.6.0...HEAD
[2.6.0]: https://github.com/melonelish/smart-doc-qa/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/melonelish/smart-doc-qa/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/melonelish/smart-doc-qa/releases/tag/v2.4.0
