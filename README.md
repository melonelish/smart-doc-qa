# SmartDocQA 🤖 | 智能文档问答系统

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square" alt="Python 3.11+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square" alt="FastAPI"></a>
  <a href="https://www.langchain.com/"><img src="https://img.shields.io/badge/LangChain-1.3+-green.svg?style=flat-square" alt="LangChain"></a>
  <a href="https://github.com/facebookresearch/faiss"><img src="https://img.shields.io/badge/FAISS-1.14+-orange.svg?style=flat-square" alt="FAISS"></a>
  <img src="https://img.shields.io/badge/Release-v2.2-brightgreen.svg?style=flat-square" alt="v2.2">
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
| ⚡ **Streaming Answers** | SSE streaming for real-time AI responses |
| 📎 **Source Attribution** | Citation markers `[¹][²][³]` with source details |
| 💬 **Conversation History** | Multi-turn dialogue with history panel, delete & restore |
| 🔌 **RESTful API** | FastAPI with auto-generated Swagger docs |
| 💾 **Local Embeddings** | Supports local TF-IDF vectorization, no external API required |
| 🧠 **Hybrid Search** | FAISS vector search + BM25 keyword search + RRF fusion |

---

## 🏗️ Architecture | 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS/CSS)            │
│  ┌──────────────┐  ┌─────────────────┐              │
│  │ Domain Nav   │  │ Chat Interface  │              │
│  │ • Enterprise │  │ • Streaming     │              │
│  │ • Research   │  │ • Citations     │              │
│  │ • Legal      │  │ • History Panel │              │
│  └──────┬───────┘  └────────┬────────┘              │
└─────────┼───────────────────┼───────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                     │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │ KB API   │  │ Doc API    │  │ Q&A API (SSE)   │ │
│  │ /kbs     │  │ /docs      │  │ /ask, /ask-stream│ │
│  └────┬─────┘  └─────┬──────┘  └───────┬──────────┘ │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼─────────┐  │
│  │            LangChain Service Layer              │  │
│  │  • Document Loading & Splitting               │  │
│  │  • Vector Embedding (Local TF-IDF / OpenAI)   │  │
│  │  • FAISS Vector Store + BM25 Keyword Search   │  │
│  │  • RRF Fusion + Cross-Encoder Rerank          │  │
│  │  • LLM Chain (RAG)                           │  │
│  └──────────────────┬────────────────────────────┘  │
└─────────────────────┼───────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  FAISS + MySQL 8.0    │
          └───────────────────────┘
```

**RAG Pipeline：**

```
Indexing:  Document → Text Splitter → Chunks → Embedding → FAISS Index + BM25 Index
                                                              ↓
Query:     Question → Embedding → FAISS Search ──┐
                        ↓                         ├─→ RRF Fusion → Rerank → LLM → Answer
                  BM25 Keyword Search ────────────┘
```

---

## 🛠️ Tech Stack | 技术栈

| Layer | Technology | Description |
|-------|------------|-------------|
| **Web Framework** | FastAPI | High-performance async web framework |
| **Frontend** | Vanilla HTML/CSS/JS | Lightweight single-page app |
| **AI Framework** | LangChain | LLM application development framework |
| **LLM** | OpenAI GPT-4o-mini / Compatible | Pluggable LLM backend |
| **Embeddings** | Local TF-IDF (default) / OpenAI | Text vectorization |
| **Vector DB** | FAISS | High-speed similarity search |
| **Keyword Search** | BM25 (via rank_bm25) | Lexical fallback search |
| **Reranker** | Cross-Encoder (BAAI/bge-reranker-v2-m3) | Re-rank fusion results |
| **Relational DB** | MySQL 8.0 | Metadata, conversations, KBs |
| **Container** | Docker + Compose | One-command deployment |

---

## 📂 Project Structure | 项目结构

```
smart-doc-qa/
├── app/
│   ├── api/                     # API Routes
│   │   ├── documents.py        # Document endpoints
│   │   ├── knowledge_bases.py  # KB CRUD endpoints
│   │   └── qa.py               # Q&A endpoints (ask, ask-stream, history)
│   ├── core/
│   │   └── config.py           # Pydantic Settings
│   ├── db/
│   │   └── database.py         # SQLAlchemy setup
│   ├── models/
│   │   └── document.py         # ORM: Document, KnowledgeBase, ConversationRecord
│   ├── services/
│   │   ├── document_service.py # Document processing logic
│   │   ├── knowledge_base_service.py  # KB business logic
│   │   └── qa_service.py       # RAG Q&A logic (retrieve, rerank, generate)
│   ├── utils/
│   ├── static/                 # Frontend assets
│   │   ├── index.html          # Main SPA
│   │   ├── css/style.css       # Styles
│   │   └── js/app.js           # App logic
│   └── main.py                 # FastAPI entry point
├── alembic/                    # Database migrations
│   └── versions/
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
   ┌── Embedding → FAISS Vector Search (top 10)
   └── BM25 Keyword Search (top 10)
        ↓
   RRF (Reciprocal Rank Fusion) → Merge & Score
        ↓
   Cross-Encoder Reranker → Re-rank top 5
        ↓
   LLM Generation → Answer + Source Citations
   ```

This architecture addresses two major LLM pain points:
- **Knowledge Cutoff**: Augments the model with uploaded documents
- **Hallucination**: Answers grounded in real document content with source attribution

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