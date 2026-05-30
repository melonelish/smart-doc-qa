// ─── State ────────────────────────────────────────────
let selectedDocId = null;
let selectedDocName = null;
let selectedDocReady = false;
let conversationId = null;

const API_BASE = '';
const STORAGE_PREFIX = 'smartdocqa_conv_';
const THEME_KEY = 'smartdocqa_theme';

// ─── Dark / Light Mode ────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  localStorage.setItem(THEME_KEY, next);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ─── Persistence (per-document) ─────────────────────────
function _storageKey(docId) {
  return STORAGE_PREFIX + docId;
}

function saveConversation() {
  if (!selectedDocId) return;
  const messages = buildMessageList();
  console.log('[SMARTDOC] saveConversation: saving', messages.length, 'msgs for', selectedDocName);
  if (messages.length === 0) { console.log('[SMARTDOC] saveConversation: empty, skipping'); return; }
  const data = {
    docId: selectedDocId,
    docName: selectedDocName,
    conversationId: conversationId,
    messages: messages,
    savedAt: new Date().toISOString(),
  };
  try {
    sessionStorage.setItem(_storageKey(selectedDocId), JSON.stringify(data));
  } catch (e) {
    console.warn('saveConversation failed:', e);
  }
}

function loadConversation(docId) {
  try {
    const raw = sessionStorage.getItem(_storageKey(docId));
    console.log('[SMARTDOC] loadConversation: key=', _storageKey(docId), 'found=', !!raw);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

function clearStoredConversation(docId) {
  const id = docId || selectedDocId;
  if (id) sessionStorage.removeItem(_storageKey(id));
}

function buildMessageList() {
  const msgs = chatMessages.querySelectorAll('.message');
  const list = [];
  msgs.forEach(m => {
    const role = m.classList.contains('user') ? 'user' : 'assistant';
    const text = m.querySelector('.message-bubble')?.innerText || '';
    if (text) list.push({ role, text });
  });
  return list;
}

// ─── Init ────────────────────────────────────────────────
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const docList = document.getElementById('doc-list');
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const uploadProgress = document.getElementById('upload-progress');
const progressFill = document.getElementById('progress-fill');
const uploadFilename = document.getElementById('upload-filename');
const uploadPercent = document.getElementById('upload-percent');
const chatDocName = document.getElementById('chat-doc-name');
const chatDocStatus = document.getElementById('chat-doc-status');

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 5000);
}

/* ============================================
   WebSocket Progress (replaces fake progress)
   ============================================ */
function connectProgressWS(docId, filename) {
  showProcessingModal(filename);
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${location.host}/ws/progress/${docId}`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'progress') {
        document.getElementById('processing-bar').style.width = data.percent + '%';
        document.getElementById('processing-title').textContent = data.stage;

        // Update stage indicators
        const pct = data.percent;
        if (pct >= 10) updateProcessingStage('read', true);
        if (pct >= 30) updateProcessingStage('split', true);
        if (pct >= 50) updateProcessingStage('embed', true);
        if (pct >= 80) updateProcessingStage('store', true);

        if (pct >= 100) {
          document.getElementById('processing-title').textContent = '✅ 处理完成';
          setTimeout(() => {
            hideProcessingModal();
            showToast(`✅ "${filename}" 处理完成`, 'success');
            refreshDocs();
            ws.close();
          }, 800);
        }
      }
    } catch (err) {}
  };

  ws.onerror = () => {
    // WebSocket failed — fall back to old polling-style
    console.log('[WS] connection failed, falling back to fetch');
  };

  ws.onclose = () => {};
}

/* ============================================
   Processing Progress Modal
   ============================================ */
function showProcessingModal(filename) {
  let modal = document.getElementById('processing-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'processing-modal';
    modal.className = 'processing-overlay';
    modal.innerHTML = `
      <div class="processing-card">
        <div class="processing-icon">⚙️</div>
        <h3 id="processing-title">正在处理文档...</h3>
        <p id="processing-filename"></p>
        <div class="processing-stages" id="processing-stages">
          <div class="stage" data-stage="read">
            <span class="stage-icon">○</span>
            <span class="stage-text">读取文件内容</span>
          </div>
          <div class="stage" data-stage="split">
            <span class="stage-icon">○</span>
            <span class="stage-text">智能文本分割</span>
          </div>
          <div class="stage" data-stage="embed">
            <span class="stage-icon">○</span>
            <span class="stage-text">AI 向量嵌入</span>
          </div>
          <div class="stage" data-stage="store">
            <span class="stage-icon">○</span>
            <span class="stage-text">构建检索索引</span>
          </div>
        </div>
        <div class="processing-progress">
          <div class="processing-bar" id="processing-bar"></div>
        </div>
        <p class="processing-hint">处理速度取决于文档大小和 AI 服务响应时间</p>
      </div>`;
    document.body.appendChild(modal);
    addProcessingStyles();
  }
  document.getElementById('processing-filename').textContent = filename;
  document.getElementById('processing-title').textContent = '正在处理文档...';
  document.getElementById('processing-bar').style.width = '0%';
  modal.querySelectorAll('.stage').forEach(s => {
    s.className = 'stage';
    s.querySelector('.stage-icon').textContent = '○';
  });
  modal.style.display = 'flex';
}

function updateProcessingStage(stage, done) {
  const el = document.querySelector(`.stage[data-stage="${stage}"]`);
  if (!el) return;
  if (done) {
    el.className = 'stage done';
    el.querySelector('.stage-icon').textContent = '✓';
  } else {
    el.className = 'stage active';
    el.querySelector('.stage-icon').textContent = '◉';
  }
}

function hideProcessingModal() {
  const modal = document.getElementById('processing-modal');
  if (modal) modal.style.display = 'none';
}

function addProcessingStyles() {
  if (document.getElementById('processing-styles')) return;
  const style = document.createElement('style');
  style.id = 'processing-styles';
  style.textContent = `
    .processing-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      display: flex; align-items: center; justify-content: center;
      z-index: 9999; backdrop-filter: blur(4px);
    }
    .processing-card {
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: var(--radius-lg); padding: 32px 36px;
      width: 420px; max-width: 90vw; text-align: center;
      box-shadow: var(--shadow-lg);
    }
    .processing-icon { font-size: 40px; margin-bottom: 12px; }
    .processing-card h3 { font-size: 16px; margin-bottom: 4px; }
    .processing-card #processing-filename {
      font-size: 13px; color: var(--accent-light); margin-bottom: 20px;
      word-break: break-all;
    }
    .processing-stages { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
    .stage { display: flex; align-items: center; gap: 10px; font-size: 13px;
      color: var(--text-muted); transition: var(--transition); padding: 6px 8px;
      border-radius: 6px;
    }
    .stage.active { color: var(--accent-light); background: rgba(99,102,241,0.06); }
    .stage.done { color: var(--success); }
    .stage .stage-icon { width: 20px; text-align: center; font-size: 14px; }
    .processing-progress {
      height: 4px; background: var(--bg-input);
      border-radius: 2px; overflow: hidden; margin-bottom: 12px;
    }
    .processing-bar {
      height: 100%; background: var(--gradient-2);
      border-radius: 2px; transition: width 0.5s ease;
    }
    .processing-hint { font-size: 11px; color: var(--text-muted); }
  `;
  document.head.appendChild(style);
}

/* ============================================
   Navigation
   ============================================ */
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');
    const view = item.dataset.view;
    document.getElementById('page-title').textContent =
      view === 'chat' ? '💬 AI 智能问答' :
      view === 'documents' ? '📁 文档管理' : '📤 上传文档';
    if (view === 'upload') {
      document.getElementById('column-left').scrollIntoView({ behavior: 'smooth' });
      uploadZone.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

/* ============================================
   Upload
   ============================================ */
uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (file) uploadFile(file);
});

async function uploadFile(file) {
  const maxSize = 10 * 1024 * 1024;
  const allowed = ['.pdf', '.txt', '.md', '.csv', '.docx'];

  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast(`不支持的文件类型: ${ext}`, 'error');
    return;
  }
  if (file.size > maxSize) {
    showToast('文件大小超过 10MB 限制', 'error');
    return;
  }

  uploadProgress.classList.add('active');
  uploadFilename.textContent = file.name;
  uploadPercent.textContent = '0%';
  progressFill.style.width = '0%';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/api/v1/documents/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        progressFill.style.width = pct + '%';
        uploadPercent.textContent = pct + '%';
      }
    };

    xhr.onload = () => {
      resetUploadProgress();
      if (xhr.status === 200) {
        const resp = JSON.parse(xhr.responseText);
        showToast(`📄 "${file.name}" 上传成功 (${formatSize(resp.file_size)})`, 'success');
        refreshDocs();
        processDocumentAfterUpload(resp.id, file.name);
      } else {
        const detail = JSON.parse(xhr.responseText).detail || '上传失败';
        showToast(`上传失败: ${detail}`, 'error');
      }
    };

    xhr.onerror = () => {
      resetUploadProgress();
      showToast('网络错误，请确认服务是否正常运行', 'error');
    };

    xhr.send(formData);
  } catch (e) {
    resetUploadProgress();
    showToast('上传异常: ' + e.message, 'error');
  }
}

function resetUploadProgress() {
  uploadProgress.classList.remove('active');
  progressFill.style.width = '0%';
  uploadPercent.textContent = '0%';
}

async function processDocumentAfterUpload(docId, filename) {
  showProcessingModal(filename);
  updateProcessingStage('read', false);
  document.getElementById('processing-bar').style.width = '5%';

  await sleep(400);
  updateProcessingStage('read', true);
  updateProcessingStage('split', false);
  document.getElementById('processing-bar').style.width = '25%';

  await sleep(400);
  updateProcessingStage('split', true);
  updateProcessingStage('embed', false);
  document.getElementById('processing-bar').style.width = '45%';

  try {
    const resp = await fetch(`${API_BASE}/api/v1/documents/${docId}/process`, { method: 'POST' });

    if (resp.ok) {
      updateProcessingStage('embed', true);
      updateProcessingStage('store', false);
      document.getElementById('processing-bar').style.width = '80%';
      await sleep(500);

      const data = await resp.json();
      updateProcessingStage('store', true);
      document.getElementById('processing-bar').style.width = '100%';
      document.getElementById('processing-title').textContent = '✅ 处理完成';
      await sleep(800);
      hideProcessingModal();
      showToast(`✅ "${filename}" 处理完成 (${data.chunk_count} 个分块)`, 'success');
      refreshDocs();
    } else {
      document.getElementById('processing-title').textContent = '❌ 处理失败';
      const err = await resp.json();
      hideProcessingModal();
      showToast(`处理失败: ${err.detail}`, 'error');
      refreshDocs();
    }
  } catch (e) {
    document.getElementById('processing-title').textContent = '❌ 处理异常';
    hideProcessingModal();
    showToast('处理异常: ' + e.message, 'error');
    refreshDocs();
  }
}

async function processDocument(docId, filename) {
  // Try WebSocket progress, with fetch fallback
  connectProgressWS(docId, filename);

  try {
    const resp = await fetch(`${API_BASE}/api/v1/documents/${docId}/process`, { method: 'POST' });
    if (resp.ok) {
      const data = await resp.json();
      // If WS is active, it'll handle completion
      if (!document.getElementById('processing-modal')?.style.display ||
          document.getElementById('processing-modal').style.display === 'none') {
        hideProcessingModal();
        showToast(`✅ 处理完成 (${data.chunk_count} 个分块)`, 'success');
        refreshDocs();
      }
    } else {
      hideProcessingModal();
      const err = await resp.json();
      showToast(`处理失败: ${err.detail || '未知错误'}`, 'error');
      refreshDocs();
    }
  } catch (e) {
    hideProcessingModal();
    showToast('处理异常: ' + e.message, 'error');
    refreshDocs();
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ============================================
   Delete
   ============================================ */
async function deleteDocument(docId) {
  if (!confirm('确定要删除此文档及其所有数据吗？')) return;
  try {
    const resp = await fetch(`${API_BASE}/api/v1/documents/${docId}`, { method: 'DELETE' });
    if (resp.ok) {
      if (selectedDocId === docId) {
        selectedDocId = null;
        selectedDocName = null;
        selectedDocReady = false;
        conversationId = null;
        clearStoredConversation(docId);
        updateChatHeader();
      }
      showToast('文档已删除', 'info');
      refreshDocs();
    } else {
      const err = await resp.json();
      showToast(`删除失败: ${err.detail}`, 'error');
    }
  } catch (e) {
    showToast('删除异常: ' + e.message, 'error');
  }
}

/* ============================================
   Document List
   ============================================ */
async function refreshDocs() {
  try {
    const resp = await fetch(`${API_BASE}/api/v1/documents/?skip=0&limit=50`);
    if (!resp.ok) return;
    const data = await resp.json();
    renderDocList(data.items);
    document.getElementById('doc-count-badge').textContent =
      `${data.items.length} 个文档`;
  } catch (e) {
    console.error('获取文档列表失败:', e);
  }
}

function renderDocList(items) {
  if (!items || items.length === 0) {
    docList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>暂无文档，请上传你的第一个文档</p>
      </div>`;
    return;
  }

  docList.innerHTML = items.map(doc => {
    const ext = (doc.file_type || '').replace('.', '');
    const iconClass = ['pdf', 'txt', 'csv', 'md'].includes(ext) ? ext : 'default';
    const date = new Date(doc.created_at).toLocaleDateString('zh-CN', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
    const size = formatSize(doc.file_size);
    const statusLabel = {
      ready: '就绪', processing: '处理中', uploaded: '待处理', failed: '失败'
    }[doc.status] || doc.status;
    const statusClass = `status-${doc.status}`;
    const isSelected = doc.id === selectedDocId;

    return `
      <div class="doc-item${isSelected ? ' selected' : ''}" data-doc-id="${doc.id}">
        <div class="doc-item-info" onclick="selectDocument('${doc.id}', '${escapeHtml(doc.filename)}', '${doc.status}')">
          <div class="doc-icon ${iconClass}">${ext.toUpperCase()}</div>
          <div class="doc-meta">
            <div class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
            <div class="doc-date">${date} · ${size}</div>
          </div>
          <span class="status-tag ${statusClass}">${statusLabel}</span>
        </div>
        <div class="doc-actions">
          ${doc.status === 'uploaded' || doc.status === 'failed' ? `
            <button class="btn-icon success" title="处理文档" onclick="event.stopPropagation();processDocument('${doc.id}','${escapeHtml(doc.filename)}')">⚡</button>
          ` : ''}
          <button class="btn-icon danger" title="删除" onclick="event.stopPropagation();deleteDocument('${doc.id}')">🗑️</button>
        </div>
      </div>`;
  }).join('');
}

function selectDocument(docId, filename, status) {
  // Save current document's conversation before switching
  if (selectedDocId && selectedDocId !== docId) {
    console.log('[SMARTDOC] selectDocument: switching from', selectedDocName, 'to', filename);
    saveConversation();
  }

  if (docId !== selectedDocId) {
    conversationId = null;
  }
  selectedDocId = docId;
  selectedDocName = filename;
  selectedDocReady = status === 'ready';
  updateChatHeader();
  renderDocListFromCache();

  if (selectedDocReady) {
    const stored = loadConversation(selectedDocId);
    if (stored && stored.messages && stored.messages.length > 0) {
      conversationId = stored.conversationId;
      chatMessages.innerHTML = '';
      stored.messages.forEach(msg => {
        appendMessageEl(msg.role, msg.text, null, false);
      });
    } else {
      clearChat();
    }
  }
}

function renderDocListFromCache() {
  const items = docList.querySelectorAll('.doc-item');
  items.forEach(item => {
    item.classList.toggle('selected', item.dataset.docId === selectedDocId);
  });
}

function updateChatHeader() {
  const convIndicator = conversationId
    ? `<span class="conv-badge" title="多轮对话中">🔄</span>`
    : '';
  if (!selectedDocId) {
    chatDocName.innerHTML = '选择文档开始对话';
    chatDocStatus.textContent = '请先在左侧选择一个已处理的文档';
    chatInput.disabled = true;
    btnSend.disabled = true;
  } else if (!selectedDocReady) {
    chatDocName.innerHTML = selectedDocName + convIndicator;
    chatDocStatus.textContent = '⚠️ 文档尚未处理，请先点击 ⚡ 处理';
    chatInput.disabled = true;
    btnSend.disabled = true;
  } else {
    chatDocName.innerHTML = selectedDocName + convIndicator;
    const msgCount = chatMessages.querySelectorAll('.message').length;
    chatDocStatus.textContent = msgCount > 0
      ? `📖 共 ${msgCount} 条对话，点击「清空对话」重置`
      : '✅ AI 已就绪，开始提问吧';
    chatInput.disabled = false;
    btnSend.disabled = false;
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
  return Math.round(bytes * 10) / 10 + ' ' + units[i];
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/* ============================================
   Chat — SSE Streaming
   ============================================ */
async function sendMessage() {
  const question = chatInput.value.trim();
  if (!question || !selectedDocId || !selectedDocReady) return;

  chatInput.value = '';
  chatInput.style.height = 'auto';
  chatInput.disabled = true;
  btnSend.disabled = true;

  // Persist user message immediately
  appendMessageEl('user', question, null, true);

  // Create streaming assistant bubble
  const streamMsg = createStreamingMessage();
  let fullAnswer = '';

  const payload = {
    document_id: selectedDocId,
    question: question,
    top_k: 4,
    conversation_id: conversationId || undefined,
    use_hybrid: true,
    use_rerank: true,
  };

  try {
    // SSE via streaming fetch
    const resp = await fetch(`${API_BASE}/api/v1/qa/ask-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      removeStreamingMessage(streamMsg);
      const err = await resp.json();
      appendMessageEl('assistant', `❌ 出错了：${err.detail || '请求失败'}`, null, true);
      chatInput.disabled = false; btnSend.disabled = false; chatInput.focus();
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let metaSources = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // incomplete line stays in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const jsonStr = line.slice(6);
        try {
          const evt = JSON.parse(jsonStr);
          if (evt.type === 'meta') {
            if (evt.conversation_id) conversationId = evt.conversation_id;
            metaSources = (evt.source_details || []).map(s => s.source);
          } else if (evt.type === 'token') {
            fullAnswer += evt.text;
            updateStreamingContent(streamMsg, fullAnswer);
          } else if (evt.type === 'done') {
            // finalize
          }
        } catch (e) {}
      }
    }

    // Replace streaming bubble with final rendered version
    finalizeStreamingMessage(streamMsg, fullAnswer, metaSources, true);
    updateChatHeader();
  } catch (e) {
    removeStreamingMessage(streamMsg);
    appendMessageEl('assistant', `❌ 网络错误：${e.message}`, null, true);
  }

  chatInput.disabled = false;
  btnSend.disabled = false;
  chatInput.focus();
}

/* Streaming message helpers */
function createStreamingMessage() {
  const empty = chatMessages.querySelector('.chat-empty');
  if (empty) empty.remove();

  const msg = document.createElement('div');
  msg.className = 'message assistant streaming';
  msg.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-bubble">
      <span id="stream-text-${Date.now()}" class="stream-content"></span>
      <span class="stream-cursor">▊</span>
    </div>`;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msg;
}

function updateStreamingContent(msg, text) {
  const span = msg.querySelector('.stream-content');
  if (span) {
    span.textContent = text;
    msg.querySelector('.message-bubble').classList.remove('streaming-pulse');
    msg.querySelector('.message-bubble').classList.add('streaming-pulse');
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeStreamingMessage(msg) {
  if (msg) msg.remove();
}

function finalizeStreamingMessage(msg, text, sources, persist) {
  if (!msg) return;
  msg.classList.remove('streaming');

  const bubble = msg.querySelector('.message-bubble');
  bubble.innerHTML = formatAssistantText(text);
  bubble.classList.remove('streaming-pulse');

  // Remove cursor
  const cursor = bubble.querySelector('.stream-cursor');
  if (cursor) cursor.remove();

  if (sources && sources.length > 0) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';
    sourcesDiv.innerHTML = '📎 来源：' + sources.map(s => {
      const name = s.split(/[\\/]/).pop();
      return `<span class="source-tag">${escapeHtml(name)}</span>`;
    }).join('');
    bubble.appendChild(sourcesDiv);
  }

  chatMessages.scrollTop = chatMessages.scrollHeight;
  if (persist) saveConversation();
}

/**
 * Append a message element to the chat area.
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - plain text content (LLM answers are plain text now)
 * @param {string[]|null} sources - source filenames
 * @param {boolean} persist - if true, save conversation to sessionStorage
 */
function appendMessageEl(role, content, sources, persist) {
  const empty = chatMessages.querySelector('.chat-empty');
  if (empty) empty.remove();

  const message = document.createElement('div');
  message.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'user' ? '👤' : '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  // User messages: plain text
  // Assistant messages: treat as preformatted plain text with line breaks preserved
  if (role === 'user') {
    bubble.textContent = content;
  } else {
    // Use innerText-style rendering: line breaks preserved, no Markdown interpretation
    bubble.innerHTML = formatAssistantText(content);
  }

  message.appendChild(avatar);
  message.appendChild(bubble);

  if (sources && sources.length > 0) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';
    sourcesDiv.innerHTML = '📎 来源：' + sources.map(s => {
      const name = s.split(/[\\/]/).pop();
      return `<span class="source-tag">${escapeHtml(name)}</span>`;
    }).join('');
    bubble.appendChild(sourcesDiv);
  }

  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  if (persist) saveConversation();
}

/**
 * Render assistant plain-text answer into semantic HTML.
 *
 * Structure produced:
 *   <div class="ans-section">
 *     <div class="ans-header">结论：</div>
 *     <div class="ans-body">...content / lists...</div>
 *   </div>
 *   <div class="ans-section">...
 *
 * Lists are rendered as <ol>/<ul> where possible.
 */
function formatAssistantText(text) {
  if (!text) return '';

  // 1 ▸ Strip Markdown artifacts the LLM may still emit
  text = text
    .replace(/\*\*/g, '')
    .replace(/__/g, '')
    .replace(/^#{1,6}\s/gm, '');

  // 2 ▸ Split into lines
  const lines = text.split('\n');

  // 3 ▸ Classify each line
  const SECTION_RE = /^(结论|依据|引用|分析|注意|补充|说明|总结|拓展|备注)[：:]\s*/;
  const OL_RE     = /^(\d{1,2})[\.\)、]\s*/;          // 1. 2) 3、
  const UL_RE     = /^[\-·•—]\s*/;                      // - · • —

  // 4 ▸ Group consecutive lines into blocks
  const blocks = [];   // { type: 'section'|'para'|'ol'|'ul', ... }
  let cur = null;      // current block being built

  function flush() {
    if (cur) blocks.push(cur);
    cur = null;
  }

  for (const raw of lines) {
    const line = raw.trim();

    // blank line → flush current block
    if (!line) { flush(); continue; }

    // section header?
    const sm = line.match(SECTION_RE);
    if (sm) {
      flush();
      cur = { type: 'section', label: sm[1], content: line.slice(sm[0].length).trim(), items: [] };
      continue;
    }

    // ordered list item?
    const om = line.match(OL_RE);
    if (om) {
      if (!cur || (cur.type !== 'ol' && cur.type !== 'section')) {
        flush();
        cur = { type: 'ol', items: [] };
      }
      cur.items.push({ idx: om[1], text: line.slice(om[0].length).trim() });
      continue;
    }

    // unordered list item?
    const um = line.match(UL_RE);
    if (um) {
      if (!cur || (cur.type !== 'ul' && cur.type !== 'section')) {
        flush();
        cur = { type: 'ul', items: [] };
      }
      cur.items.push(line.slice(um[0].length).trim());
      continue;
    }

    // plain text — attach to section body or start a paragraph
    if (cur && cur.type === 'section') {
      cur.items.push({ text: line });
    } else if (cur && cur.type === 'para') {
      cur.text += ' ' + line;
    } else {
      flush();
      cur = { type: 'para', text: line };
    }
  }
  flush();

  // 5 ▸ Render blocks → HTML
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function citeWrap(html) {
    // highlight [来源: ...] markers
    return html.replace(
      /(\[来源[：:][^\]]+\])/g,
      '<span class="answer-cite">$1</span>'
    );
  }

  function renderItems(items) {
    // Detect if items are a mix of numbered / plain text within a section
    // Split into sub-blocks: runs of numbered items → <ol>, plain text → <p>
    const parts = [];
    let olBuffer = [];

    for (const item of items) {
      if (item.idx !== undefined) {
        olBuffer.push(item);
      } else {
        if (olBuffer.length) {
          parts.push('<ol>' + olBuffer.map(o =>
            '<li>' + citeWrap(esc(o.text)) + '</li>'
          ).join('') + '</ol>');
          olBuffer = [];
        }
        parts.push('<p>' + citeWrap(esc(item.text)) + '</p>');
      }
    }
    if (olBuffer.length) {
      parts.push('<ol>' + olBuffer.map(o =>
        '<li>' + citeWrap(esc(o.text)) + '</li>'
      ).join('') + '</ol>');
    }
    return parts.join('');
  }

  let html = '';
  for (const b of blocks) {
    if (b.type === 'section') {
      html += '<div class="ans-section">';
      html += '<div class="ans-header">' + esc(b.label) + '：</div>';
      if (b.content) {
        html += '<p>' + citeWrap(esc(b.content)) + '</p>';
      }
      if (b.items.length) {
        html += '<div class="ans-body">' + renderItems(b.items) + '</div>';
      }
      html += '</div>';
    } else if (b.type === 'ol') {
      html += '<ol>' + b.items.map(o =>
        '<li>' + citeWrap(esc(o.text)) + '</li>'
      ).join('') + '</ol>';
    } else if (b.type === 'ul') {
      html += '<ul>' + b.items.map(t =>
        '<li>' + citeWrap(esc(t)) + '</li>'
      ).join('') + '</ul>';
    } else if (b.type === 'para') {
      html += '<p>' + citeWrap(esc(b.text)) + '</p>';
    }
  }

  return html;
}

function showTypingIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'message assistant';
  indicator.id = 'typing-indicator';
  indicator.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-bubble">
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  chatMessages.appendChild(indicator);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

function clearChat() {
  chatMessages.innerHTML = `
    <div class="chat-empty">
      <div class="empty-icon">🤖</div>
      <h3>开始智能文档问答</h3>
      <p>上传文档并点击「处理」后，AI 将深入理解你的文档内容。你可以像和人类专家对话一样，对文档提出任何问题。</p>
    </div>`;
  conversationId = null;
  clearStoredConversation(selectedDocId);
  updateChatHeader();
}

function handleChatKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!chatInput.disabled) sendMessage();
  }
}

chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

// ── CSS for answer rendering (fallback) ──────────────────
const answerStyle = document.createElement('style');
answerStyle.textContent = `
  .answer-cite {
    color: #94a3b8;
    font-size: 12px;
  }
  .conv-badge {
    margin-left: 6px;
    font-size: 14px;
  }
`;
document.head.appendChild(answerStyle);

// ── Send Message (replaces sendMessage) ─────────────────
async function sendMessage() {
  var question = chatInput.value.trim();
  if (!question || !selectedDocId || !selectedDocReady) return;

  chatInput.value = '';
  chatInput.style.height = 'auto';
  chatInput.disabled = true;
  btnSend.disabled = true;

  appendMessageEl('user', question, null, true);
  showTypingIndicator();

  var payload = {
    document_id: selectedDocId,
    question: question,
    top_k: 4,
    conversation_id: conversationId || undefined,
    use_hybrid: true,
    use_rerank: true,
  };

  try {
    var resp = await fetch('/api/v1/qa/ask-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    removeTypingIndicator();

    if (!resp.ok) {
      var err = await resp.json();
      appendMessageEl('assistant', '\u274c \u51fa\u4e86\u95ee\u9898\uff1a' + (err.detail || '\u8bf7\u6c42\u5931\u8d25'), null, true);
      chatInput.disabled = false; btnSend.disabled = false; chatInput.focus();
      return;
    }

    var reader = resp.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';
    var fullText = '';
    var metaData = { sources: [] };

    // Create a streaming bubble placeholder
    var streamBubble = createStreamingBubble();

    while (true) {
      var result = await reader.read();
      if (result.done) break;
      buffer += decoder.decode(result.value, { stream: true });
      var lines = buffer.split('\n');
      buffer = lines.pop();

      for (var i = 0; i < lines.length; i++) {
        var ln = lines[i];
        if (!ln.startsWith('data: ')) continue;
        try {
          var evt = JSON.parse(ln.slice(6));
          if (evt.type === 'meta') {
            if (evt.conversation_id) conversationId = evt.conversation_id;
            metaData.sources = (evt.source_details || []).map(function(s) { return s.source; });
          } else if (evt.type === 'token') {
            fullText += evt.text;
            if (streamBubble) streamBubble.textContent = fullText;
          } else if (evt.type === 'done') {
            // finalize
          }
        } catch(e) {}
      }
    }

    // Replace streaming bubble with formatted final answer
    finalizeStreamBubble(streamBubble, fullText, metaData.sources, true);
    updateChatHeader();
  } catch(e) {
    removeTypingIndicator();
    var sb = document.getElementById('stream-bubble');
    if (sb) sb.parentElement.remove();
    appendMessageEl('assistant', '\u274c \u7f51\u7edc\u9519\u8bef\uff1a' + e.message, null, true);
  }

  chatInput.disabled = false;
  btnSend.disabled = false;
  chatInput.focus();
}

function createStreamingBubble() {
  var empty = chatMessages.querySelector('.chat-empty');
  if (empty) empty.remove();

  var msg = document.createElement('div');
  msg.className = 'message assistant streaming';
  msg.innerHTML = '<div class="message-avatar">\ud83e\udd16</div>' +
    '<div id="stream-bubble" class="message-bubble" style="white-space:pre-wrap;word-break:break-word;"></div>';
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return document.getElementById('stream-bubble');
}

function finalizeStreamBubble(bubble, text, sources, persist) {
  if (!bubble) return;
  var parent = bubble.parentElement;
  if (!parent) return;
  parent.classList.remove('streaming');

  // Format the text
  bubble.innerHTML = formatAssistantText(text);
  bubble.removeAttribute('id');

  // Add sources
  if (sources && sources.length > 0) {
    var sd = document.createElement('div');
    sd.className = 'message-sources';
    sd.innerHTML = '\ud83d\udcce \u6765\u6e90\uff1a' + sources.map(function(s) {
      var name = s.split(/[\\\\\/]/).pop();
      return '<span class="source-tag">' + escapeHtml(name) + '</span>';
    }).join('');
    bubble.appendChild(sd);
  }

  chatMessages.scrollTop = chatMessages.scrollHeight;
  if (persist) saveConversation();
}

// ── History Panel ───────────────────────────────────
async function loadHistory(docId) {
  try {
    var resp = await fetch('/api/v1/qa/history/' + docId + '?limit=100');
    if (!resp.ok) return;
    var data = await resp.json();
    renderHistoryPanel(data.items || []);
  } catch(e) { console.error('loadHistory:', e); }
}

function renderHistoryPanel(items) {
  var panel = document.getElementById('history-panel-body');
  if (!panel) return;
  if (!items || items.length === 0) {
    panel.innerHTML = '<div class=\"empty-state\"><p>\u6682\u65e0\u95ee\u7b54\u8bb0\u5f55</p></div>';
    return;
  }
  var groups = {};
  for (var i = 0; i < items.length; i++) {
    var r = items[i];
    if (!groups[r.conversation_id]) groups[r.conversation_id] = [];
    groups[r.conversation_id].push(r);
  }
  panel.innerHTML = Object.keys(groups).map(function(cid) {
    var conv = groups[cid];
    var firstQ = null;
    for (var j = 0; j < conv.length; j++) {
      if (conv[j].role === 'user') { firstQ = conv[j]; break; }
    }
    var preview = firstQ ? firstQ.content.slice(0, 80) : '(\u7a7a\u5bf9\u8bdd)';
    var date = conv[0].created_at ? new Date(conv[0].created_at).toLocaleString('zh-CN') : '';
    return '<div class=\"history-item\" onclick=\"restoreConversation(\x27' + cid + '\x27)\">' +
      '<div class=\"history-preview\">' + escapeHtml(preview) + (preview.length >= 80 ? '...' : '') + '</div>' +
      '<div class=\"history-meta\">' + conv.length + ' \u6761 \u00b7 ' + date + '</div>' +
    '</div>';
  }).join('');
}

async function restoreConversation(convId) {
  if (!selectedDocId) return;
  conversationId = convId;
  chatMessages.innerHTML = '';
  try {
    var resp = await fetch('/api/v1/qa/history/' + selectedDocId + '?conversation_id=' + convId + '&limit=100');
    if (!resp.ok) return;
    var data = await resp.json();
    for (var i = 0; i < data.items.length; i++) {
      appendMessageEl(data.items[i].role, data.items[i].content, null, false);
    }
    updateChatHeader();
    showToast('\u5386\u53f2\u5bf9\u8bdd\u5df2\u6062\u590d', 'info');
  } catch(e) { console.error('restoreConversation:', e); }
}

// ── Document Preview ────────────────────────────────
async function previewDocument(docId) {
  var modal = document.getElementById('preview-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'preview-modal';
    modal.className = 'preview-overlay';
    modal.innerHTML = '<div class=\"preview-card\">' +
      '<div class=\"preview-header\">' +
        '<h3 style=\"font-size:14px;font-weight:600;\" id=\"preview-title\">\u6587\u6863\u9884\u89c8</h3>' +
        '<button class=\"btn-icon\" onclick=\"document.getElementById(\x27preview-modal\x27).style.display=\x27none\x27\">\u2715</button>' +
      '</div>' +
      '<div class=\"preview-body\" id=\"preview-content\"></div>' +
    '</div>';
    modal.addEventListener('click', function(e) { if (e.target === modal) modal.style.display = 'none'; });
    document.body.appendChild(modal);
  }
  modal.style.display = 'flex';
  document.getElementById('preview-title').textContent = '\u52a0\u8f7d\u4e2d...';
  document.getElementById('preview-content').innerHTML = '<div class=\"empty-state\"><p>\u23f3 \u52a0\u8f7d\u4e2d...</p></div>';

  try {
    var docResp = await fetch('/api/v1/documents/' + docId);
    if (!docResp.ok) throw new Error();
    var doc = await docResp.json();
    document.getElementById('preview-title').textContent = doc.filename;

    if (doc.file_type === '.txt' || doc.file_type === '.md') {
      var textResp = await fetch('/api/v1/documents/' + docId + '/content');
      if (textResp.ok) {
        var text = await textResp.text();
        document.getElementById('preview-content').innerHTML =
          '<pre style=\"white-space:pre-wrap;word-break:break-word;font-size:13px;line-height:1.7;\">' +
          escapeHtml(text.slice(0, 30000)) + '</pre>';
      }
    } else if (doc.file_type === '.csv') {
      var csvResp = await fetch('/api/v1/documents/' + docId + '/content');
      if (csvResp.ok) {
        var csvText = await csvResp.text();
        var rows = csvText.split('\n').slice(0, 200).map(function(r) {
          var cells = r.split(',').map(function(c) {
            return '<td style=\"border:1px solid var(--border);padding:4px 8px;font-size:12px;\">' +
              escapeHtml(c.trim()) + '</td>';
          }).join('');
          return '<tr>' + cells + '</tr>';
        }).join('');
        document.getElementById('preview-content').innerHTML =
          '<div style=\"overflow:auto;max-height:60vh;\"><table style=\"border-collapse:collapse;width:100%;font-size:12px;\">' +
          rows + '</table></div>';
      }
    } else {
      document.getElementById('preview-content').innerHTML =
        '<div class=\"empty-state\"><p>\ud83d\udcc4 ' + escapeHtml(doc.filename) + ' (' +
        formatSize(doc.file_size) + ')</p><p style=\"margin-top:8px;font-size:12px;\">' +
        '\u6b64\u683c\u5f0f\u6682\u4e0d\u652f\u6301\u5728\u7ebf\u9884\u89c8</p></div>';
    }
  } catch(e) {
    document.getElementById('preview-content').innerHTML =
      '<div class=\"empty-state\"><p>\u274c \u52a0\u8f7d\u5931\u8d25</p></div>';
  }
}

// ── Dark Mode ───────────────────────────────────────
function initTheme() {
  var saved = 'dark';
  try { saved = localStorage.getItem('smartdocqa_theme') || 'dark'; } catch(e) {}
  applyTheme(saved);
}

function toggleTheme() {
  var cur = document.documentElement.getAttribute('data-theme') || 'dark';
  var next = cur === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem('smartdocqa_theme', next); } catch(e) {}
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  var btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = theme === 'dark' ? '\u2600\ufe0f' : '\ud83c\udf19';
}

// ── Init ────────────────────────────────────────────
initTheme();
refreshDocs();
