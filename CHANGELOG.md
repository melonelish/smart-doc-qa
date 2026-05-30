# 更新日志

## [v1.1] - 2026-05-29

### 🚀 六项核心改进

#### 1. 语义嵌入模型（替代 TF-IDF）
- 引入 `BAAI/bge-small-zh-v1.5` 中文语义嵌入模型（768 维向量）
- 首次运行自动从 HuggingFace 下载（~100MB），后续本地缓存
- 支持国内镜像加速（`HF_ENDPOINT=https://hf-mirror.com`）
- 替换原有 `scikit-learn TF-IDF` 稀疏向量为稠密语义向量

#### 2. 混合检索（向量 + BM25）
- FAISS 向量检索 + BM25 关键词检索双路召回
- Reciprocal Rank Fusion (RRF) 融合两路排序结果
- BM25 使用 `jieba` 中文分词，适配中文场景
- 可通过 `use_hybrid` 参数开关（默认开启）

#### 3. Cross-Encoder 重排序
- 引入 `BAAI/bge-reranker-base` 交叉编码器
- 对混合检索结果二次排序，提升 Top-K 精度
- 可通过 `use_rerank` 参数开关（默认开启）
- 模型首次运行自动下载（~1GB）

#### 4. 多轮对话支持
- `ConversationMemory` 类管理对话历史（内存存储 + TTL 自动过期）
- `conversation_id` 标识对话上下文，支持追问
- 自动将历史对话注入 LLM Prompt，实现上下文连贯
- 对话有效期可配置（默认 3600 秒）
- 新增 `DELETE /api/v1/qa/conversation/{id}` 清除对话接口

#### 5. Prompt 工程优化
- 结构化 System Prompt：角色定义 → 回答规则 → 引用格式 → 思考链 → 示例
- 要求 LLM 先给出结论，再附依据和引用
- 答案格式：`**结论**` + `**依据**` + `[来源: xxx]`
- 限制最大输出 2048 token，避免冗长

#### 6. 引用溯源
- 答案自动标注来源文档和段落
- 新增 `source_details` 字段，包含：
  - `source`：来源文档名
  - `chunks[].chunk_index`：文档块序号
  - `chunks[].snippet`：原文片段
- 新增 `retrieval_method` 字段（`"hybrid"` / `"vector_only"`）

---

### 📁 变更文件清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `app/services/qa_service.py` | 重写 | 641 行新增/重构：语义嵌入、混合检索、重排序、多轮对话、Prompt、溯源 |
| `app/api/qa.py` | 增强 | 新增请求字段（conversation_id, use_hybrid, use_rerank, top_k）；新增 source_details 响应模型 |
| `app/core/config.py` | 新增 | `hf_endpoint` 配置项（国内 HuggingFace 镜像） |
| `requirements.txt` | 新增 | `langchain-huggingface`, `rank-bm25`, `jieba`, `sentence-transformers`, `numpy<2.0` |
| `.env` | 新增 | `HF_ENDPOINT`, `LOCAL_EMBEDDING_MODEL`, `RERANKER_MODEL`, `CONVERSATION_TTL_SECONDS` |
| `.env.example` | 更新 | 同步新增配置项及中文注释 |

---

### 🐛 Bug 修复

- **numpy ABI 崩溃**：`sentence-transformers` 安装时拉高 `numpy` 至 2.x，与 `pandas`/`sklearn` C 扩展不兼容导致 `SystemError`。锁定 `numpy>=1.26.0,<2.0.0`，同步降级 `scipy<1.14`、`sklearn<1.6`、`pandas<2.3`
- **HuggingFace 下载超时**：国内直连 `huggingface.co` 超时，新增 `HF_ENDPOINT` 环境变量支持国内镜像
- **LangChain 弃用警告**：`HuggingFaceEmbeddings` 从 `langchain_community` 迁移至 `langchain_huggingface`

---

### 🏗️ 环境依赖版本

| 包 | 版本 |
|---|------|
| Python | 3.10.20 |
| numpy | 1.26.4 |
| scipy | 1.13.1 |
| scikit-learn | 1.5.2 |
| pandas | 2.2.3 |
| sentence-transformers | 5.5.1 |
| faiss-cpu | 1.14.2 |
| langchain | 0.3.x |
| langchain-huggingface | 0.1.x |
| rank-bm25 | 0.2.x |
| jieba | 0.42.1 |

---

### 📡 API 变更

**POST `/api/v1/qa/ask` 请求新增字段：**
```json
{
  "conversation_id": "",       // 对话ID，空=新对话
  "top_k": 4,                  // 检索数量 (1-20)
  "use_hybrid": true,          // 启用混合检索
  "use_rerank": true           // 启用重排序
}
```

**POST `/api/v1/qa/ask` 响应新增字段：**
```json
{
  "conversation_id": "uuid",   // 对话ID（多轮追问用）
  "source_details": [          // 引用溯源详情
    {
      "source": "doc.txt",
      "chunks": [
        { "chunk_index": 1, "page": "", "snippet": "原文片段..." }
      ]
    }
  ],
  "retrieval_method": "hybrid" // 检索方式
}
```

**新增接口：**
- `DELETE /api/v1/qa/conversation/{conversation_id}` — 清除对话历史

---

## [v1.0] - 2026-05-28

### 🎉 初始版本

- FastAPI + LangChain + FAISS + MySQL 架构搭建
- 文档上传、处理、问答基础功能
- TF-IDF 向量化 + FAISS 索引
- OpenAI / DeepSeek LLM 集成
- MySQL 文档元数据管理
- Swagger API 文档
