# SmartDocQA 🤖 | 智能文档问答系统

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square" alt="Python 3.11+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square" alt="FastAPI"></a>
  <a href="https://www.langchain.com/"><img src="https://img.shields.io/badge/LangChain-1.3+-green.svg?style=flat-square" alt="LangChain"></a>
  <a href="https://github.com/facebookresearch/faiss"><img src="https://img.shields.io/badge/FAISS-1.14+-orange.svg?style=flat-square" alt="FAISS"></a>
  <img src="https://img.shields.io/badge/Release-v2.6-brightgreen.svg?style=flat-square" alt="v2.6">
  <a href="https://github.com/melonskin/smart-doc-qa/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/melonskin/smart-doc-qa"><img src="https://img.shields.io/github/stars/melonskin/smart-doc-qa?style=flat-square&label=Stars" alt="Stars"></a>
</p>

<p align="center">
  <b>Domain-driven document Q&A with RAG. Upload documents to knowledge bases, ask questions, get AI answers with source citations.</b><br/>
  基于领域的文档问答系统。将文档上传到知识库，AI 跨文档检索，精准回答并标注来源。
</p>

---

## 🌟 Overview | 项目简介

**English:**  
SmartDocQA is an intelligent document Q&A system with a **domain-driven architecture**. The system supports multiple domains (Enterprise Assistant, Research Assistant, Legal Assistant), each with **isolated knowledge bases**. Upload documents (PDF, TXT, Markdown, CSV) to a knowledge base, and the system will automatically parse, embed, and index them. Ask questions in natural language — the system retrieves the most relevant passages across the entire knowledge base, using **RAG (Retrieval-Augmented Generation)** powered by LLM, with source attribution and citation markers.

**中文：**  
SmartDocQA 是基于 **领域驱动架构** 的智能文档问答系统。支持多个领域（企业助手、科研助手、法律助手），每个领域拥有**独立的知识库**。将文档（PDF、TXT、Markdown、CSV）上传到知识库后，系统自动解析、向量化并建立索引。你可以用自然语言提问——系统会跨整个知识库检索最相关的段落，基于大语言模型生成精准回答，并标注引用来源。

---

## ✨ Features | 核心特性

| Feature | 说明 |
|---------|------|
| 🏢 **Domain Navigation** | Multi-domain architecture: Enterprise, Research, Legal (pluggable) |
| 📚 **Knowledge Base Management** | Create, list, delete KBs; each domain has independent KBs |
| 🔍 **RAG Architecture** | LangChain + FAISS hybrid search with Cross-Encoder rerank |
| 📄 **Multi-format Support** | PDF, TXT, Markdown, CSV, Word + OCR image support |
| ⚡ **Streaming Answers** | SSE streaming for real-time AI responses (Vue 3 frontend) |
| 📎 **Source Attribution** | Citation markers `[¹][²][³]` with source details |
| 💬 **Conversation History** | Multi-turn dialogue with history panel, delete & restore, grouped by date |
| 🔌 **RESTful API** | FastAPI with auto-generated Swagger docs |
| 💾 **Local Embeddings** | Supports local TF-IDF vectorization, no external API required |
| 🧠 **Hybrid Search** | FAISS vector search + BM25 keyword search + RRF fusion |
| 🔄 **Cross-Document Comparison** | Auto-detect comparison queries, group by document, structured tables |
| 🤖 **Agent Tools** | LLM-driven function calling: calculator for precise math, web search for real-time info |
| 🎨 **Modern Frontend** | Vue 3.5 + TypeScript 5 + Vite 8 + Naive UI 2, Pinia state management |

---

## 🏗️ Architecture | 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│              Frontend (Vue 3.5 + TypeScript 5)            │
│  ┌──────────┐  ┌─────────────────────────────────────┐   │
│  │ SideNav   │  │ ChatPanel (Naive UI 2)             │   │
│  │ • KBs    │  │  • MessageList (SSE streaming)    │   │
│  │ • History │  │  • MessageInput (Ctrl+Enter换行) │   │
│  └────┬─────┘  │  • HistoryPanel (日期分组)        │   │
│         │        └──────────────────┬──────────────────┘   │
└─────────┼──────────────────────────┼──────────────────────┘
          │                          │
          ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Uvicorn)                 │
│  ┌──────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │ KB API   │  │ Doc API    │  │ Q&A API (SSE)      │  │
│  │ /kbs     │  │ /docs      │  │ /ask, /ask-stream  │  │
│  └────┬─────┘  └─────┬──────┘  └─────────┬─────────┘  │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼─────────┐      │
│  │            LangChain Service Layer              │      │
│  │  • Document Loading & Splitting               │      │
│  │  • Vector Embedding (Local TF-IDF / OpenAI)  │      │
│  │  • FAISS Vector Store + BM25 Keyword Search  │      │
│  │  • RRF Fusion + Cross-Encoder Rerank         │      │
│  │  • Agent Loop (Tool Calling → Execute → LLM) │      │
│  │  • LLM Chain (RAG) + Streaming              │      │
│  └──────────────────┬────────────────────────────┘      │
└─────────────────────┼─────────────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  FAISS + MySQL 8.0    │
          └─────────────────────────┘
```

**Frontend Architecture (Vue 3 + Pinia):**
```
frontend/src/
├── stores/          # Pinia (conversation, document, ui, ...)
├── components/      # Reusable Vue components
├── views/           # Page-level components
├── api/             # Axios + TypeScript types
├── composables/     # Composition API hooks
└── router/          # Vue Router
```

**RAG Pipeline：**

```
Indexing:  Document → Text Splitter → Chunks → Embedding → FAISS Index + BM25 Index
                                                              ↓
Query:     Question → Query Type Detection ──────────────────┐
                        ↓                                     │
              ┌─────────┴─────────┐                          │
              │ numeric/semantic/ │                          │
              │   comparison      │                          │
              └─────────┬─────────┘                          │
                        ↓                                     │
              FAISS Search ───────────────────────────────────┤
                        ↓                                     │
              BM25 Keyword Search ────────────────────────────┤
                        ↓                                     │
                  RRF Fusion → Rerank ────────────────────────┤
                                                              │
              Agent Loop (optional): ─────────────────────────┤
              LLM → tool_call? → calculator/web_search → LLM  │
                                                              │
                        ↓                                     │
                    Final Answer + Sources + Tool Log ────────┘
```

---

## 🛠️ Tech Stack | 技术栈

| Layer | Technology | Description |
|-------|------------|-------------|
| **Web Framework** | FastAPI | High-performance async web framework |
| **Frontend** | Vue 3.5 + TypeScript 5 + Vite 8 + Naive UI 2 | Modern reactive SPA |
| **State Management** | Pinia | Lightweight, TypeScript-first stores |
| **AI Framework** | LangChain | LLM application development framework |
| **LLM** | DeepSeek V4 (Flash) / OpenAI Compatible | Pluggable LLM backend |
| **Embeddings** | Local TF-IDF (default) / OpenAI | Text vectorization |
| **Vector DB** | FAISS | High-speed similarity search |
| **Keyword Search** | BM25 (via rank_bm25) | Lexical fallback search |
| **Reranker** | Cross-Encoder (BAAI/bge-reranker-v2-m3) | Re-rank fusion results |
| **Relational DB** | MySQL 8.0 | Metadata, conversations, KBs |
| **Container** | Docker + Compose (multi-stage build) | One-command deployment |

---

## 📂 Project Structure | 项目结构

```
smart-doc-qa/
├── frontend/                  # Vue 3.5 + TypeScript 5 + Vite 8 frontend
│   ├── src/
│   │   ├── api/             # API layer (Axios + TypeScript types)
│   │   ├── assets/          # Static assets (CSS variables, images)
│   │   ├── components/      # Vue components (chat, history, documents, KB)
│   │   ├── composables/     # Composition API hooks (useWebSocket)
│   │   ├── router/          # Vue Router
│   │   ├── stores/          # Pinia stores (conversation, document, ui, ...)
│   │   ├── types/           # TypeScript type definitions
│   │   ├── utils/           # Utility functions
│   │   ├── views/           # Page components (KnowledgeBaseView, etc.)
│   │   ├── App.vue
│   │   ├── main.ts
│   │   └── style.css
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── env.d.ts
├── app/                       # FastAPI backend
│   ├── api/                  # API Routes (documents, knowledge_bases, qa)
│   ├── core/                 # Config, exceptions
│   ├── db/                   # Database setup
│   ├── models/               # SQLAlchemy ORM models
│   ├── services/             # Business logic (qa_service, document_service, ...)
│   ├── utils/                # Utilities
│   ├── static/               # Legacy static files (DEPRECATED)
│   └── main.py               # FastAPI entry point
├── alembic/                    # Database migrations
├── tests/
├── data/                       # Runtime data (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start | 快速开始

### Prerequisites | 环境要求

- Python 3.11+
- MySQL 8.0+
- OpenAI API Key (or use local embeddings)
- Docker & Docker Compose (optional)

---

### Option 1: Docker Deployment | 方式一：Docker 部署

```bash
git clone https://github.com/melonskin/smart-doc-qa.git
cd smart-doc-qa

# Configure environment
cp .env.example .env
# Edit .env: fill in OPENAI_API_KEY, DB credentials

# Start services
docker-compose up -d

# Run database migrations
docker exec -it smart-doc-qa alembic upgrade head

# Visit
# http://localhost:8000
```

---

### Option 2: Local Development | 方式二：本地开发

```bash
# Clone the repo
git clone https://github.com/melonskin/smart-doc-qa.git
cd smart-doc-qa

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux / macOS
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, MYSQL_HOST, MYSQL_PASSWORD, etc.

# Start MySQL (ensure running)

# Run database migrations
alembic upgrade head

# Start the app
python -m app.main
# or: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Visit
# http://127.0.0.1:8000
```

---

## 📖 API Reference | 接口文档

Once the server is running, visit: **http://127.0.0.1:8000/docs**

### Knowledge Base Management | 知识库管理

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/knowledge-bases/` | Create KB (with domain) | 创建知识库 |
| GET | `/api/v1/knowledge-bases/` | List KBs (filter by domain) | 知识库列表 |
| GET | `/api/v1/knowledge-bases/{id}` | KB detail | 知识库详情 |
| DELETE | `/api/v1/knowledge-bases/{id}` | Delete KB | 删除知识库 |
| GET | `/api/v1/knowledge-bases/{id}/documents` | List documents in KB | 知识库内文档列表 |

### Document Management | 文档管理

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/documents/upload` | Upload document to KB | 上传文档到知识库 |
| POST | `/api/v1/documents/{id}/process` | Process & vectorize | 处理文档（向量化） |
| GET | `/api/v1/documents/` | List documents | 文档列表 |
| GET | `/api/v1/documents/{id}` | Document detail | 文档详情 |
| DELETE | `/api/v1/documents/{id}` | Delete document | 删除文档 |

### Q&A | 智能问答

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/qa/ask` | Ask a question (sync) | 提问（同步） |
| POST | `/api/v1/qa/ask-stream` | Ask a question (SSE stream) | 提问（流式） |
| GET | `/api/v1/qa/history/{kb_id}` | Get conversation history | 获取对话历史 |
| DELETE | `/api/v1/qa/history/{conversation_id}` | Delete a conversation | 删除对话 |

---

## 💡 Usage Example | 使用示例

### Using the Web UI (Recommended)

1. Open `http://localhost:8000` in your browser
2. **Enterprise Assistant** is selected by default — view the domain introduction page
3. Click **Create Knowledge Base** to create your first KB
4. Upload documents (PDF, TXT, MD, CSV) to the KB and click **Process**
5. Ask questions in the chat area — AI will search all documents in the KB

### Using the API

```bash
# 1. Create a Knowledge Base | 创建知识库
curl -X POST http://127.0.0.1:8000/api/v1/knowledge-bases/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Company Policies", "domain": "enterprise"}'

# Returns: { "id": "kb_uuid", "name": "Company Policies", ... }

# 2. Upload a document to the KB | 上传文档到知识库
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload \
  -F "file=@policies.pdf" \
  -F "kb_id=kb_uuid"

# Returns: { "id": "doc_uuid", "filename": "policies.pdf", ... }

# 3. Process the document | 处理文档
curl -X POST http://127.0.0.1:8000/api/v1/documents/doc_uuid/process

# 4. Ask a question to the KB | 向知识库提问
curl -X POST http://127.0.0.1:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "kb_uuid",
    "question": "What is our annual leave policy?",
    "conversation_id": null
  }'

# Sample response | 返回示例：
# {
#   "answer": "According to the company policies, employees are entitled to...",
#   "sources": [{"source": "policies.pdf", "chunks": [...]}],
#   "conversation_id": "conv_uuid"
# }
```

---

## 🧭 Domain Navigation | 领域导航

The v2.2 release introduces a **domain-driven architecture**:

| Domain | Status | Purpose |
|--------|--------|---------|
| 🏢 **Enterprise Assistant** | ✅ Active | Company knowledge: policies, tech docs, workflows |
| 🔬 **Research Assistant** | ✅ Active | Academic papers, research data, literature review |
| ⚖️ **Legal Assistant** | 🚧 Coming Soon | Legal documents, contracts, case analysis |

Each domain has **completely isolated knowledge bases** — documents, conversations, and data never cross domain boundaries. Switching domains shows a dedicated introduction page for that domain.

---

## 🔬 How It Works | 核心原理

### Hybrid RAG Pipeline

1. **Indexing Phase | 文档索引阶段：**
   ```
   Document → Text Splitter → Chunks
                       ↓
            ┌── Embedding → FAISS Index
            └── Tokenize → BM25 Index
   ```

2. **Query Phase | 问答检索阶段：**
   ```
   User Question
        ↓
   Query Type Detection (numeric / semantic / comparison)
        ↓
   ┌── Embedding → FAISS Vector Search (top 10)
   └── BM25 Keyword Search (top 10)
        ↓
   RRF (Reciprocal Rank Fusion) → Merge & Score
        ↓
   Cross-Encoder Reranker → Re-rank top 5
        ↓
   Agent Loop: LLM → tool_call? → calculator / web_search → LLM
        ↓
   LLM Generation → Answer + Source Citations + Tool Log
   ```

This architecture addresses two major LLM pain points:
- **Knowledge Cutoff**: Augments the model with uploaded documents
- **Hallucination**: Answers grounded in real document content with source attribution

---

## 📋 v2.6 Changelog | 更新日志

> 完整变更记录请查看 [CHANGELOG.md](CHANGELOG.md)

### ✨ Added（新功能）
- 历史记录功能（按日期分组：今天/昨天/日期）
- 流式输出支持（SSE 逐 token 显示）
- 多轮对话上下文记忆（`conversation_id` 跨轮次保持）
- 对话历史 API（`GET /api/v1/qa/history`，返回 `last_question` + `last_activity_at`）

### 🐛 Fixed（Bug 修复）
- 修复删除文档后向量库未清理（仍能检索已删文档内容）
- 修复历史面板时间显示错误（UTC 时区未正确转换）
- 修复流式输出双机器人头像、Ctrl+Enter 无法换行、空文件上传崩溃
- 修复后端 500 错误（Windows 路径非法字符，缺少 `@staticmethod` 装饰器）
- 修复历史面板点击无反应、挤压主内容区、缺少滚动条

### ♻️ Changed（变更）
- **前端架构完全升级**：Vue 3.5 + TypeScript 5 + Vite 8 + Naive UI 2
- 状态管理迁移到 Pinia（5 个 store）
- 流式输出改用 fetch API（非 Axios，支持 SSE）
- Markdown 渲染支持（marked + highlight.js）
- 主题切换支持（dark/light 模式）
- Docker 多阶段构建（前端独立构建）
- 后端时区修复（全项目 `datetime.utcnow` → `datetime.now(timezone.utc)`）

---

## 📋 v2.5 Changelog | 更新日志

### 🚀 New Features
- **Agent Tools (Function Calling)** — LLM 自主决策调用工具
  - `calculator(expression)` — 精确计算数值表达式（安全 AST 求值，避免 LLM 推算错误）
  - `web_search(query)` — 联网搜索补充文档外信息（基于 DuckDuckGo，免费无需 API Key）
  - Agent Loop: LLM → tool_call → execute → feed back → LLM（最多 3 轮）
- **Cross-Document Comparison** — 跨文档对比分析
  - 自动检测对比类问题（对比/比较/差异/趋势/各份/版本）
  - 检索结果按 `document_name` 分组展示
  - 注入对比格式指令，输出结构化对比表格
- **Query Type 三分类** — 新增 `comparison` 类型，优先于 `numeric` 检测
- **Agent 调用可视化** — 前端展示工具调用过程（工具名、参数、结果）

### 🔧 Improvements
- 企业助手系统提示词新增「多文档对比」规则（第8条）
- retrieval_method 标签支持 `+ agent`、`+ comparison`、`+ tables`
- 前端企业助手能力卡片新增 Agent 自主决策、多文档对比、趋势检测
- 清理所有调试日志代码（`_debug_*.txt`）

### 📦 Dependencies
- 新增 `ddgs>=9.0.0`（DuckDuckGo 搜索）

---

## 📋 v2.2 Changelog | 更新日志

### 🚀 New Features
- **Domain navigation sidebar** — Replaced 3 generic tabs with domain entries
- **Domain-specific KBs** — Isolated knowledge bases per domain (Alembic migration)
- **Domain introduction page** — Rich welcome page per domain
- **Per-domain KB filtering** — KB dropdown, creation, docs filtered by active domain

### 🔧 Improvements
- **Conversation history rewrite** — Correct ordering, delete works, restore all messages
- **Citation markers** — `[¹][²][³]` superscripts with source details
- **Enterprise SYSTEM_PROMPT** — Structured LLM output
- **Removed "All Documents" mode** — Strictly KB-based operation
- **Toast repositioned** — Non-blocking, no longer covers UI

### 🐛 Bug Fixes
- Upload button calls correct function name
- Document preview via click (eye icon removed)
- History panel auto-refresh after delete
- Conversation restore shows all messages (not just 1/N)
- KB data isolation per domain

---

## ⚙️ Configuration | 配置说明

See `.env.example` for all available configuration options. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *required* | Your OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom API endpoint (for proxies) |
| `EMBEDDING_MODE` | `local` | `local` (TF-IDF) or `openai` |
| `MYSQL_HOST` | `localhost` | MySQL server host |
| `MYSQL_DATABASE` | `smart_doc_qa` | Database name |
| `VECTOR_STORE_PATH` | _(auto)* | Path to FAISS index (auto-managed) |

> When `VECTOR_STORE_PATH` is commented out, the app auto-resolves to `{PROJECT_ROOT}/data/vector_store`.

---

## 🧪 Run Tests | 运行测试

```bash
pytest tests/ -v
```

---

## 🤝 Contributing | 贡献指南

Contributions are welcome! Feel free to open an issue or submit a PR.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License | 许可证

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
本项目采用 MIT 许可证 — 详见 [LICENSE](LICENSE)。

---

## 👤 Author | 作者

**melonskin**
- GitHub: [@melonskin](https://github.com/melonskin)
- Gitee: [@melonskin](https://gitee.com/melonskin)

> Built with ❤️ using FastAPI + LangChain + FAISS