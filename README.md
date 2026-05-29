# SmartDocQA 🤖 | 智能文档问答系统

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square" alt="Python 3.11+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square" alt="FastAPI"></a>
  <a href="https://www.langchain.com/"><img src="https://img.shields.io/badge/LangChain-1.3+-green.svg?style=flat-square" alt="LangChain"></a>
  <a href="https://github.com/facebookresearch/faiss"><img src="https://img.shields.io/badge/FAISS-1.14+-orange.svg?style=flat-square" alt="FAISS"></a>
  <a href="https://github.com/melonskin/smart-doc-qa/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/melonskin/smart-doc-qa"><img src="https://img.shields.io/github/stars/melonskin/smart-doc-qa?style=flat-square&label=Stars" alt="Stars"></a>
</p>

<p align="center">
  <b>Upload documents, ask questions, get answers with sources.</b><br/>
  上传文档，像聊天一样提问，AI 基于文档内容精准回答，并附带来源。
</p>

---

## 🌟 Overview | 项目简介

**English:**  
SmartDocQA is an intelligent document Q&A system built on **LangChain + FastAPI + FAISS**. Upload your documents (PDF, TXT, Markdown, CSV), and the system will automatically parse, embed, and index them. Then ask questions in natural language — the system retrieves the most relevant passages and generates accurate answers powered by LLM, with source attribution for every answer.

**中文：**  
SmartDocQA 是基于 **LangChain + FastAPI + FAISS** 构建的智能文档问答系统。上传文档（PDF、TXT、Markdown、CSV）后，系统自动解析、向量化并建立索引。你可以用自然语言向文档提问——系统会检索最相关的段落，由大语言模型生成精准回答，并为每个答案标注信息来源。

---

## ✨ Features | 核心特性

| Feature | 说明 |
|---------|------|
| 📄 **Multi-format Support** | PDF, TXT, Markdown, CSV 等常见格式 |
| 🔍 **RAG Architecture** | 基于 LangChain + OpenAI 的检索增强生成，回答准确有据 |
| ⚡ **Fast Vector Search** | FAISS 向量数据库，毫秒级语义检索 |
| 📎 **Source Attribution** | 每个回答均标注来源文档，可追溯、可信赖 |
| 🔌 **RESTful API** | FastAPI 构建，自动生成 Swagger 文档 |
| 🐳 **Docker Ready** | 支持 Docker Compose 一键部署 |
| 💾 **Local Embeddings** | 支持本地 TF-IDF 向量化，无需外部嵌入 API |

---

## 🏗️ Architecture | 系统架构

```
┌─────────────┐     Upload       ┌──────────────┐
│   User      │  ─────────────►  │  FastAPI     │
│  (Browser)  │                  │  /docs UI    │
└─────────────┘                  └──────┬───────┘
     │                                   │
     │ Ask Question                      │ Process Document
     ▼                                   ▼
┌──────────────────────────────────────────────────────┐
│                    FastAPI Backend                    │
│  ┌──────────┐   ┌───────────┐   ┌──────────────┐  │
│  │ /upload  │   │ /process  │   │    /ask      │  │
│  └────┬─────┘   └─────┬─────┘   └──────┬───────┘  │
│       │                │                  │          │
│  ┌────▼──────────────▼──────────────────▼──────┐    │
│  │           LangChain Service Layer            │    │
│  │  • Document Loading & Splitting            │    │
│  │  • Vector Embedding (Local TF-IDF / OpenAI)│    │
│  │  • FAISS Vector Store                      │    │
│  │  • LLM Chain (RAG)                        │    │
│  └──────────────────┬─────────────────────────┘    │
└─────────────────────┼───────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  FAISS + MySQL + Redis │
          └───────────────────────┘
```

**RAG Pipeline | 检索增强生成流程：**

```
Indexing:  Document → Text Splitter → Embedding → FAISS Store
                              ↓
Query:    Question → Embedding → Similarity Search → Context → LLM → Answer + Sources
```

---

## 🛠️ Tech Stack | 技术栈

| Layer | Technology | Description |
|-------|------------|-------------|
| **Web Framework** | FastAPI | High-performance async web framework |
| **AI Framework** | LangChain | LLM application development framework |
| **LLM** | OpenAI GPT-4o-mini / Local | Pluggable LLM backend |
| **Embeddings** | Local TF-IDF (default) / OpenAI | Text vectorization |
| **Vector DB** | FAISS | High-speed similarity search |
| **Relational DB** | MySQL 8.0 | Document metadata storage |
| **Cache** | Redis (optional) | Caching & task queue |
| **Container** | Docker + Compose | One-command deployment |

---

## 📂 Project Structure | 项目结构

```
smart-doc-qa/
├── app/
│   ├── api/                # API Routes | API 路由层
│   │   ├── documents.py    # Document management endpoints
│   │   └── qa.py          # Q&A endpoints
│   ├── core/               # Core config | 核心配置
│   │   └── config.py      # Pydantic Settings
│   ├── db/                 # Database layer | 数据库层
│   │   └── database.py    # SQLAlchemy setup
│   ├── models/             # ORM Models | 数据模型
│   │   └── document.py
│   ├── services/           # Business logic | 业务逻辑层
│   │   ├── document_service.py
│   │   └── qa_service.py
│   ├── utils/              # Utilities | 工具函数
│   └── main.py            # FastAPI entry point | 应用入口
├── tests/                  # Test cases | 测试用例
├── data/                   # Runtime data (gitignored) | 运行时数据
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
- Redis 7+ (optional | 可选)
- OpenAI API Key (or use local embeddings | 或使用本地向量化)
- Docker & Docker Compose (for containerized deployment | 用于容器化部署)

---

### Option 1: Docker Deployment (Recommended) | 方式一：Docker 部署（推荐）

```bash
# Clone the repo | 克隆项目
git clone https://github.com/melonskin/smart-doc-qa.git
cd smart-doc-qa

# Configure environment | 配置环境变量
cp .env.example .env
# Edit .env and fill in your OpenAI API Key
# 编辑 .env，填入你的 OpenAI API Key

# Start services | 启动服务
docker-compose up -d

# Visit API docs | 访问 API 文档
# http://localhost:8000/docs
```

---

### Option 2: Local Development | 方式二：本地开发

```bash
# Clone the repo | 克隆项目
git clone https://github.com/melonskin/smart-doc-qa.git
cd smart-doc-qa

# Create virtual environment | 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Linux / macOS
# venv\Scripts\activate    # Windows

# Install dependencies | 安装依赖
pip install -r requirements.txt

# Configure environment | 配置环境变量
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, DB credentials, etc.
# 编辑 .env：设置 OPENAI_API_KEY、数据库密码等

# Start MySQL (make sure it's running) | 确保 MySQL 已启动
# Database tables are created automatically | 数据库表会自动创建

# Run the app | 启动应用
python -m app.main
# or | 或使用：
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Visit | 访问：
# http://127.0.0.1:8000/docs
```

---

## 📖 API Reference | 接口文档

Once the server is running, visit the interactive Swagger docs at:  
**http://127.0.0.1:8000/docs**

服务启动后，访问交互式 API 文档： **http://127.0.0.1:8000/docs**

### Document Management | 文档管理

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/documents/upload` | Upload document | 上传文档 |
| POST | `/api/v1/documents/{id}/process` | Process & vectorize | 处理文档（向量化） |
| GET | `/api/v1/documents/` | List documents | 文档列表 |
| GET | `/api/v1/documents/{id}` | Document detail | 文档详情 |
| DELETE | `/api/v1/documents/{id}` | Delete document | 删除文档 |

### Q&A | 智能问答

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/qa/ask` | Ask a question | 向文档提问 |

---

## 💡 Usage Example | 使用示例

```bash
# 1. Upload a document | 上传文档
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload \
  -F "file=@report.pdf"

# Returns: { "id": "doc_abc123", "filename": "report.pdf", ... }

# 2. Process the document (vectorize) | 处理文档（向量化）
curl -X POST http://127.0.0.1:8000/api/v1/documents/doc_abc123/process

# 3. Ask a question | 提问
curl -X POST http://127.0.0.1:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_abc123",
    "question": "这份报告的核心结论是什么？"
  }'

# Sample response | 返回示例：
# {
#   "question": "这份报告的核心结论是什么？",
#   "answer": "根据报告内容，核心结论是...",
#   "sources": ["report.pdf"],
#   "source_count": 3
# }
```

---

## 🔬 How It Works | 核心原理

### RAG (Retrieval-Augmented Generation)

1. **Indexing Phase | 文档索引阶段：**
   ```
   Document → Text Splitter → Embedding Vector → FAISS Index
                                           ↓
                                    stored on disk
   ```

2. **Query Phase | 问答检索阶段：**
   ```
   User Question → Embedding → FAISS Similarity Search
           ↓
   Top-K Relevant Chunks → LLM Context Window
           ↓
   Generated Answer + Source Attribution
   ```

This architecture solves two major LLM pain points:
- **Knowledge Cutoff | 知识时效性**：Augments the model with external documents  
  结合外部文档，不受训练数据时间限制
- **Hallucination | 幻觉问题**：Answers grounded in real document content  
  回答基于真实文档内容，减少编造

---

## ⚙️ Configuration | 配置说明

See `.env.example` for all available configuration options. Key variables:  
关键配置项请参考 `.env.example`：

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *required* | Your OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom API endpoint (for proxies) |
| `EMBEDDING_MODE` | `local` | `local` (TF-IDF) or `openai` |
| `MYSQL_HOST` | `localhost` | MySQL server host |
| `MYSQL_DATABASE` | `smart_doc_qa` | Database name |
| `VECTOR_STORE_PATH` | _(auto)* | Path to FAISS index (auto-managed) |

> \* When `VECTOR_STORE_PATH` is commented out, the app auto-resolves to `{PROJECT_ROOT}/data/vector_store`.
> 若注释掉 `VECTOR_STORE_PATH`，应用会自动解析为 `{项目根目录}/data/vector_store`。

---

## 🧪 Run Tests | 运行测试

```bash
pytest tests/ -v
```

---

## 🤝 Contributing | 贡献指南

Contributions are welcome! Feel free to open an issue or submit a PR.  
欢迎贡献！如有建议欢迎提 Issue 或提交 PR。

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

## ⭐ Star History | Star 历史

If you find this project helpful, please consider giving it a star! ⭐  
如果你觉得这个项目有帮助，欢迎点个 Star！⭐

[![Star History Chart](https://api.star-history.com/svg?repos=melonskin/smart-doc-qa&type=Date)](https://star-history.com/#melonskin/smart-doc-qa&Date)

---

## 👤 Author | 作者

**melonskin**  
- GitHub: [@melonskin](https://github.com/melonskin)  
- Gitee: [@melonskin](https://gitee.com/melonskin)

> Built with ❤️ using FastAPI + LangChain + FAISS
