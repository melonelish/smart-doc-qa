# Changelog

## [v2.4] - 2026-06-03

### 🚀 Structured Data Extraction

Automatic PDF table extraction, precise numerical Q&A, and intelligent query type detection.

#### New Features

- **PDF Table Parsing**: Extract structured tables from PDF files using pdfplumber — supports complex headers and multi-row tables
- **Query Type Detection**: Classify questions as `numeric` (how many / ratio / growth / ranking) vs `semantic` — different retrieval paths
- **Structured Q&A**: Numerical questions answered from extracted table data first; LLM performs trend comparison (↑/↓/→)
- **PDF Inline Preview**: Click a document to preview PDF directly in the browser — no more forced downloads
- **Download Button**: ⬇ button in the preview header gives users the choice to download or not

#### Architecture Improvements

- **Dual-path retrieval**: numeric → structured table lookup + semantic → FAISS+BM25+Rerank vector search, running in parallel
- **Query classifier**: lightweight keyword + comparison-word based detector
- **Prompt enhancement**: Enterprise System Prompt updated with "prefer table data" and "trend analysis" rules
- **Frontend capabilities**: Enterprise domain now shows "Table Parsing", "Numerical Query", "Trend Detection" badges

### 🐛 Bug Fixes

- **Pydantic v2 type coercion**: `SourceChunk.page` defined as `str` but FAISS metadata `page` is `int` — ValueError was caught silently → fixed to `str(doc.metadata.get("page") or "")`
- **PDF auto-download**: `FileResponse` with `filename` caused Starlette to overwrite `Content-Disposition` to `attachment` → removed `filename` param, use `headers` only for `inline`
- **Download button no-op**: Preview download button had UI but no logic → bound click event to trigger download

### 🔧 Improvements

- Enterprise capability tags updated: removed "Flow Decomposition", added "Table Parsing", "Numerical Query", "Trend Detection"
- Preview modal layout: width 680px → 800px, max-height 80vh → 90vh
- Skip table extraction for non-PDF files (zero overhead)
- Debug log cleanup: removed `_debug_askkb.txt`, `_debug_load.txt` temporary files

---

## [v2.3] - 2026-06-03

### 🚀 Research Assistant — Fully Active

The scientific research domain is now live with **5 enhanced AI capabilities**:

- **Confidence annotation**: Automatic `〖High confidence〗` `〖Medium confidence〗` `〖Low confidence〗` markers on conclusions, helping users assess reliability
- **Critical analysis**: `⚠️ Note:` section proactively highlights methodology limitations, data biases, and generalization risks
- **Traceable follow-ups**: Each answer ends with `🔍 Further questions:` suggestions to guide deeper exploration
- **Multi-format citations**: `[¹][²][³]` superscript references with APA / MLA / GB/T 7714 support
- **Cross-lingual analysis**: Mixed Chinese/English input and output; domain-specific terms preserved in original language

### ✨ AI Capabilities Showcase

- New **"🤖 AI Capabilities"** card area on the domain intro page, visually displaying each domain's unique AI strengths
- Cards feature hover highlight interaction, helping new users quickly understand AI specialties

### 🐛 Bug Fixes

#### Backend
- **HF_ENDPOINT timing issue**: `qa_service.py` set the env var after `huggingface_hub` was already imported, causing `WinError 10060` connection timeouts → fixed by parsing `.env` at module level before any HF imports, ensuring offline cache is used
- **Dependency installation**: Added `rank-bm25` and `jieba` to dependencies; BM25 hybrid search is now fully functional instead of throwing ImportError

### 🔧 Improvements

- Research domain SYSTEM_PROMPT now embeds all 5 enhancement rules
- Frontend `DOMAINS` config supports `capabilities` structure for easy domain extension

---

## [v2.1] - 2026-06-01

### 🐛 Bug Fixes

#### Backend
- **SSE conversation persistence**: `ask_question_stream` missing `db` parameter — conversations never saved to database
- **History ordering**: user/assistant order unstable with same timestamp — added `case(role=="user", 0)` secondary sort
- **Conversation delete**: `DELETE /conversation/{id}` only cleared in-memory cache, not DB records — added DB deletion + `deleted_records` count
- **Database encoding**: `database_url` missing `?charset=utf8mb4` — Chinese characters stored as mojibake
- **Document preview encoding**: `/content` endpoint returned JSON instead of plain text — switched to `PlainTextResponse`

#### Frontend
- **Document mode chat**: `sendMessage` hardcoded `if (!selectedKbId) return` — document mode completely broken
- **History restore**: `restoreConversation` hardcoded `selectedDocId` — null in KB mode caused silent exit
- **History panel open**: `toggleHistoryPanel` only used `selectedKbId` — empty panel in document mode
- **KB dropdown case**: HTML `toggleKBDropdown` vs JS `toggleKbDropdown` — unified to camelCase
- **History button event**: button used `classList.toggle('open')` instead of calling `toggleHistoryPanel()`
- **Duplicate functions**: `sendMessage` defined twice (second overwrites first), `initTheme/toggleTheme/applyTheme` each duplicated

### ✨ Improvements

- **Cache disabled**: new `NoCacheStaticMiddleware` ASGI middleware, `/static/*` paths force `no-cache, no-store, must-revalidate`
- **HTML meta tags**: added `<meta http-equiv="Cache-Control">` to prevent browser caching
- **History sources parsing**: `_parse_sources` correctly extracts source field, returns string list instead of raw JSON
- **Delete record endpoint**: new `DELETE /history/{record_id}` for single record deletion

### 🔧 Technical Debt

- Removed duplicate function declarations, JS reduced from 1612 to ~1400 lines
- Unified `_save_turn` naming (was `_save_conversation_turn`)
- Removed redundant `from app.models.document import ConversationRecord` imports

---

## [v2.0] - 2026-06-01

### 🚀 Knowledge Base
- Knowledge Base CRUD (create/list/update/delete)
- Document association (batch bind/unbind/direct upload)
- Cross-document QA (FAISS hybrid search + BM25 + reranking)
- Frontend KB management UI (cards/create modal/upload/delete)
- KB mode SSE streaming QA + source attribution

---

## [v1.3] - 2026-05-30

### ✨ UI Improvements
- Dark/Light theme toggle
- Conversation history panel (slide-in)
- Document preview modal (Markdown/CSV/Text rendering)

### 🔧 Backend
- `/content` endpoint returns raw file content
- `/ask-stream` SSE streaming QA
- `/history` conversation history list

---

## [v1.1] - 2026-05-29

### 🔍 Retrieval QA — 6 Core Improvements
1. Semantic embeddings (BAAI/bge-small-zh-v1.5)
2. Hybrid retrieval (FAISS + BM25 RRF fusion)
3. Reranking (BAAI/bge-reranker-base Cross-Encoder)
4. Multi-turn dialogue (ConversationMemory + TTL)
5. Prompt engineering (structured System Prompt)
6. Source attribution (source_details + chunk_index)
