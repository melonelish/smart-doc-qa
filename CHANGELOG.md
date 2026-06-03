# 更新日志

## [v2.3] - 2026-06-03

### 🚀 科研助手正式上线

科研领域知识库全面激活，新增 **5 项 AI 增强问答能力**：

- **置信度标注**：回答中自动标注 `〖高置信度〗` `〖中等置信度〗` `〖低置信度〗`，让用户评估结论可信度
- **批判性分析**：`⚠️ 注意：` 区块主动指出方法局限、数据偏差、结论泛化风险
- **溯源追问**：每条回答末尾自动生成 `🔍 进一步追问：` 建议，引导深度挖掘
- **多格式引用**：引用标注 `[¹][²][³]` 支持 APA / MLA / GB/T 7714 格式
- **跨语言分析**：中英文混合输入输出，专业术语自动保留原文

### ✨ AI 能力特点展示

- 领域介绍页新增 **「🤖 AI 能力特点」** 卡片区域，直观展示各领域 AI 助手独特能力标签
- 卡片支持 hover 高亮交互，帮助新用户快速了解 AI 特长

### 🐛 Bug 修复

#### 后端
- **HF_ENDPOINT 加载时序**：`qa_service.py` 中环境变量在 `huggingface_hub` 导入后才设置导致 `WinError 10060` 连接超时 → 改为在模块级别解析 `.env` 文件，同步设置 `TRANSFORMERS_OFFLINE` 等变量，确保离线缓存命中
- **依赖补充**：安装 `rank-bm25` 和 `jieba` 库，BM25 混合检索从异常提示变为可用状态

### 🔧 改进

- 科研领域系统提示词（SYSTEM_PROMPT）内置 5 项增强规则
- 前端 `DOMAINS` 配置支持 `capabilities` 结构，便于后续扩展领域

---

## [v2.1] - 2026-06-01

### 🐛 Bug 修复

#### 后端
- **流式对话数据库保存**：`ask_question_stream` 缺少 `db` 参数，SSE 对话从未写入数据库 → 添加 `db: Session = Depends(get_db)` + 调用 `_save_turn`
- **对话历史排序**：相同时间戳下 user/assistant 顺序不稳定 → 添加 `case(role=="user", 0)` 二级排序
- **对话删除端点**：`DELETE /conversation/{id}` 仅清内存不清数据库 → 添加 DB 记录删除 + 返回 `deleted_records` 数量
- **数据库编码**：`database_url` 缺少 `?charset=utf8mb4`，中文存储乱码
- **文档预览编码**：`/content` 端点返回 JSON 而非纯文本 → 改用 `PlainTextResponse`

#### 前端
- **文档模式发消息**：`sendMessage` 硬编码 `if (!selectedKbId) return`，文档模式无法问答 → 支持 doc/KB 双模式
- **对话历史恢复**：`restoreConversation` 硬编码 `selectedDocId`，KB 模式下为 null 导致退出 → 使用 `_historyPanelDocId`
- **历史面板打开**：`toggleHistoryPanel` 只取 `selectedKbId`，文档模式下历史面板为空 → `selectedDocId || selectedKbId`
- **KB 下拉框大小写**：HTML `toggleKBDropdown` vs JS `toggleKbDropdown` → 统一小写
- **历史按钮事件**：按钮用 `classList.toggle('open')` 而非调用 `toggleHistoryPanel()` → 修正为函数调用
- **重复函数**：`sendMessage` 定义 2 次（第二个覆盖第一个）、`initTheme/toggleTheme/applyTheme` 各重复 1 次 → 删除旧版

### ✨ 改进

- **缓存禁用**：新增 `NoCacheStaticMiddleware` ASGI 中间件，`/static/*` 路径强制 `no-cache, no-store, must-revalidate`
- **HTML meta 标签**：添加 `<meta http-equiv="Cache-Control">` 禁止浏览器缓存
- **对话历史 sources 解析**：`_parse_sources` 正确提取 source 字段，返回字符串列表而非原始 JSON
- **删除记录端点**：新增 `DELETE /history/{record_id}` 支持单条记录删除

### 🔧 技术债务

- 清理重复函数声明，JS 代码行数从 1612 优化至 ~1400 行
- 统一 `_save_turn` 命名（原 `_save_conversation_turn`）
- 移除冗余 `from app.models.document import ConversationRecord` 导入

---

## [v2.0] - 2026-06-01

### 🚀 知识库功能
- 知识库 CRUD（创建/列表/详情/更新/删除）
- 文档关联（批量绑定/解绑/直接上传）
- 跨文档问答（FAISS 混合检索 + BM25 + 重排序）
- 前端 KB 管理界面（卡片/创建弹窗/上传/删除）
- KB 模式 SSE 流式问答 + 引用溯源

---

## [v1.3] - 2026-05-30

### ✨ UI 改进
- Dark/Light 主题切换
- 对话历史面板（滑入式）
- 文档预览弹窗（Markdown/CSV/Text 渲染）

### 🔧 后端
- `/content` 端点返回原始文件内容
- `/ask-stream` SSE 流式问答
- `/history` 对话历史列表

---

## [v1.1] - 2026-05-29

### 🔍 检索问答 6 项核心改进
1. 语义嵌入（BAAI/bge-small-zh-v1.5）
2. 混合检索（FAISS + BM25 RRF 融合）
3. 重排序（BAAI/bge-reranker-base Cross-Encoder）
4. 多轮对话（ConversationMemory + TTL）
5. Prompt 工程（结构化 System Prompt）
6. 引用溯源（source_details + chunk_index）
