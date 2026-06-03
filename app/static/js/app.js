// ─── State ────────────────────────────────────────────
let selectedDocId = null;
let selectedDocName = null;
let selectedDocReady = false;
let selectedKbId = null;
let selectedKbName = null;
let conversationId = null;
let selectedDomain = 'enterprise';

const DOMAINS = {
  enterprise: {
    id: 'enterprise',
    name: '企业助手',
    icon: '🏢',
    description: '你公司的内部知识库。上传制度、技术文档、流程文件，AI 帮你在秒级找到答案。',
    features: [
      { q: '「年假怎么休？」', a: '查询公司制度、考勤规定' },
      { q: '「报销流程是什么？」', a: '按步骤列出财务流程 + 引用相关制度文档' },
      { q: '「这个项目的架构是怎样的？」', a: '分析技术文档，给出全局视角' },
    ],
    docTypes: [
      { icon: '📄', name: '公司制度', desc: '员工手册、考勤制度、报销规定、绩效制度' },
      { icon: '📘', name: '技术文档', desc: 'API 文档、架构设计、运维手册、配置说明' },
      { icon: '📋', name: '流程文件', desc: '审批流程、SOP、项目管理规范' },
    ],
    capabilities: [
      { icon: '🎯', label: '精准匹配', desc: '从海量文档中秒级定位答案' },
      { icon: '📑', label: '条款溯源', desc: '每个回答附带原始出处引用' },
      { icon: '🔄', label: '多文档串联', desc: '跨文档关联分析，全局视角' },
      { icon: '📊', label: '流程拆解', desc: '制度流程逐步可视化呈现' },
    ],
  },
  research: {
    id: 'research',
    name: '科研助手',
    icon: '🔬',
    description: '你的智能文献分析伙伴。上传学术论文、实验报告，AI 深度分析、交叉对比、溯源追问。',
    features: [
      { q: '「这篇论文的核心创新点是什么？」', a: '提炼研究方法、实验结果与贡献，标注置信度' },
      { q: '「这几篇论文的方法有何异同？」', a: '交叉对比技术路线与实验设置，指出优劣' },
      { q: '「实验设计有什么潜在缺陷？」', a: '批判性分析样本量、方法局限、结论泛化风险' },
    ],
    docTypes: [
      { icon: '📄', name: '学术论文', desc: '期刊论文、会议论文、预印本、学位论文' },
      { icon: '📊', name: '实验报告', desc: '实验数据、统计分析、结果表格、方法说明' },
      { icon: '📚', name: '文献综述', desc: '研究进展、技术调研、白皮书、技术报告' },
    ],
    capabilities: [
      { icon: '📊', label: '置信度标注', desc: '高/中/低三档区分结论可信程度' },
      { icon: '⚠️', label: '批判性分析', desc: '主动指出方法局限与潜在风险' },
      { icon: '🔍', label: '溯源追问', desc: '回答后自动生成深入追问建议' },
      { icon: '📚', label: '多格式引用', desc: '支持 APA / MLA / GB/T 7714' },
      { icon: '🌐', label: '跨语言分析', desc: '中英文混合文献无障碍分析' },
    ],
  },
};

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
  // Support both document mode and KB mode
  var targetId = selectedDocId || selectedKbId;
  var targetName = selectedDocName || selectedKbName;
  var targetType = selectedDocId ? 'doc' : (selectedKbId ? 'kb' : null);
  if (!targetId || !targetType) {
    console.log('[SMARTDOC] saveConversation: no target, skipping');
    return;
  }
  const messages = buildMessageList();
  console.log('[SMARTDOC] saveConversation: saving', messages.length, 'msgs for', targetName, '(' + targetType + ')');
  if (messages.length === 0) { console.log('[SMARTDOC] saveConversation: empty, skipping'); return; }
  const data = {
    id: targetId,
    name: targetName,
    type: targetType,
    conversationId: conversationId,
    messages: messages,
    savedAt: new Date().toISOString(),
  };
  try {
    sessionStorage.setItem(_storageKey(targetId), JSON.stringify(data));
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
  if (docId) sessionStorage.removeItem(_storageKey(docId));
}

function relativeTime(dateStr) {
  if (!dateStr) return '';
  var diff = Date.now() - new Date(dateStr).getTime();
  var mins = Math.floor(diff / 60000);
  if (mins < 1) return '刚刚';
  if (mins < 60) return mins + '分钟前';
  var hours = Math.floor(mins / 60);
  if (hours < 24) return hours + '小时前';
  var days = Math.floor(hours / 24);
  if (days < 30) return days + '天前';
  return new Date(dateStr).toLocaleDateString('zh-CN');
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
const kbList = document.getElementById('kb-list');

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
   Domain Navigation
   ============================================ */
function selectDomain(domainId) {
  var domain = DOMAINS[domainId];
  if (!domain) return;

  if (selectedDomain === domainId) return;

  if (selectedKbId) {
    saveConversation();
    selectedKbId = null;
    selectedKbName = null;
    conversationId = null;
    updateChatHeader();
    updateUploadBtn();
    updateSelectorLabel();
    renderKBDropdown();
    refreshDocs();
  }

  selectedDomain = domainId;

  document.querySelectorAll('.domain-item').forEach(function(el) {
    el.classList.toggle('active', el.dataset.domain === domainId);
  });

  document.getElementById('page-title').textContent = domain.icon + ' ' + domain.name;

  refreshKBs();
  renderDomainIntro(domainId);
}

function renderDomainIntro(domainId) {
  var domain = DOMAINS[domainId];
  if (!domain) return;

  conversationId = null;
  clearStoredConversation(selectedKbId);

  var capabilitiesHtml = '';
  if (domain.capabilities && domain.capabilities.length > 0) {
    capabilitiesHtml = '<div class="domain-section-label">🤖 AI 能力特点</div>' +
      '<div class="domain-capabilities">' +
      domain.capabilities.map(function(c) {
        return '<div class="domain-capability">' +
          '<span class="domain-capability-icon">' + c.icon + '</span>' +
          '<div class="domain-capability-body">' +
            '<span class="domain-capability-label">' + c.label + '</span>' +
            '<span class="domain-capability-desc">' + c.desc + '</span>' +
          '</div>' +
        '</div>';
      }).join('') +
      '</div>';
  }

  var featuresHtml = '';
  if (domain.features && domain.features.length > 0) {
    featuresHtml = '<div class="domain-section-label">它能做什么</div>' +
      '<div class="domain-features">' +
      domain.features.map(function(f) {
        return '<div class="domain-feature">' +
          '<span class="domain-feature-q">' + f.q + '</span>' +
          '<span class="domain-feature-a">→ ' + f.a + '</span>' +
        '</div>';
      }).join('') +
      '</div>';
  }

  var docTypesHtml = '';
  if (domain.docTypes && domain.docTypes.length > 0) {
    docTypesHtml = '<div class="domain-section-label">建议上传的文件类型</div>' +
      '<div class="domain-doc-types">' +
      domain.docTypes.map(function(dt) {
        return '<div class="domain-doc-type">' +
          '<div class="domain-doc-type-icon">' + dt.icon + '</div>' +
          '<div class="domain-doc-type-name">' + dt.name + '</div>' +
          '<div class="domain-doc-type-desc">' + dt.desc + '</div>' +
        '</div>';
      }).join('') +
      '</div>';
  }

  var kbBanner = '';
  var footerHtml = '';
  if (selectedKbId) {
    kbBanner = '<div style="background:var(--success-bg);border:1px solid var(--success);border-radius:var(--radius-sm);padding:10px 14px;margin-bottom:20px;display:flex;align-items:center;gap:8px;">' +
      '<span style="font-size:16px;">✅</span>' +
      '<span style="font-size:13px;color:var(--text-primary);">已选择知识库：<strong>' + escapeHtml(selectedKbName) + '</strong></span>' +
    '</div>';
    footerHtml = '<p class="welcome-hint" style="text-align:center;margin-top:12px;">💡 在下方输入问题，AI 将检索知识库内所有文档来回答</p>';
  } else {
    footerHtml = '<div class="domain-intro-footer">' +
      '<button class="btn btn-primary welcome-btn" onclick="showCreateKBModal()">📁 创建知识库开始使用</button>' +
      '<p class="welcome-hint">或从左侧下拉选择一个已有知识库</p>' +
    '</div>';
  }

  chatMessages.innerHTML = '' +
    '<div class="chat-empty" style="padding:20px;">' +
      '<div class="domain-intro">' +
        kbBanner +
        '<div class="domain-intro-header">' +
          '<div class="domain-intro-icon">' + domain.icon + '</div>' +
          '<h2 class="domain-intro-title">' + domain.name + '</h2>' +
          '<p class="domain-intro-desc">' + domain.description + '</p>' +
        '</div>' +
        capabilitiesHtml +
        featuresHtml +
        docTypesHtml +
        footerHtml +
      '</div>' +
    '</div>';
}

/* ============================================
   Upload - Drag & Drop on Document Card
   ============================================ */
const docCard = document.getElementById('doc-card');
if (docCard) {
  docCard.addEventListener('dragover', (e) => {
    e.preventDefault();
    docCard.style.borderColor = 'var(--accent)';
  });
  docCard.addEventListener('dragleave', () => {
    docCard.style.borderColor = '';
  });
  docCard.addEventListener('drop', (e) => {
    e.preventDefault();
    docCard.style.borderColor = '';
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
}

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (file) uploadFile(file);
});

async function uploadFile(file) {
  if (!selectedKbId) { showToast('请先选择知识库', 'warning'); return; }
  uploadToKB(file);
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

/* ============================================
   Knowledge Base Dropdown
   ============================================ */
let _kbItemsCache = [];

async function refreshKBs() {
  try {
    const url = `${API_BASE}/api/v1/knowledge-bases/?limit=50&domain=${encodeURIComponent(selectedDomain)}`;
    const resp = await fetch(url);
    if (!resp.ok) return;
    const data = await resp.json();
    _kbItemsCache = data.items || [];
    renderKBDropdown();
  } catch (e) {
    console.error('Failed to load KBs:', e);
  }
}

function renderKBDropdown() {
  const container = document.getElementById('kb-dropdown-kbs');
  if (!container) return;

  if (!_kbItemsCache || _kbItemsCache.length === 0) {
    container.innerHTML = '<div class="kb-dropdown-item" style="color:var(--text-muted);cursor:default;font-size:12px;justify-content:center;">暂无知识库</div>';
    return;
  }

  container.innerHTML = _kbItemsCache.map(kb => {
    const isActive = kb.id === selectedKbId;
    const time = relativeTime(kb.updated_at);
    return `
      <div class="kb-dropdown-item${isActive ? ' active' : ''}" onclick="selectKB('${kb.id}', '${escapeHtml(kb.name)}')">
        <span class="kb-dd-icon">📚</span>
        <span class="kb-dd-info">
          <span class="kb-dd-name">${escapeHtml(kb.name)}</span>
          <span class="kb-dd-meta">${kb.document_count || 0} 个文档 · ${time}</span>
        </span>
        <span class="kb-dd-actions">
          <button class="dd-btn danger" title="删除" onclick="event.stopPropagation();deleteKB('${kb.id}')">×</button>
        </span>
      </div>`;
  }).join('');

  document.querySelectorAll('#kb-dropdown .kb-dropdown-item').forEach(el => {
    el.classList.toggle('active', el.querySelector('.kb-dd-name') &&
      _kbItemsCache.some(kb => kb.id === selectedKbId && kb.name === el.querySelector('.kb-dd-name').textContent));
  });
}

function toggleKbDropdown() {
  const dropdown = document.getElementById('kb-dropdown');
  const selector = document.getElementById('kb-selector');
  const isOpen = dropdown.style.display !== 'none';
  if (isOpen) {
    dropdown.style.display = 'none';
    selector.classList.remove('open');
  } else {
    renderKBDropdown();
    dropdown.style.display = 'block';
    selector.classList.add('open');
  }
}

function selectKB(kbId, kbName) {
  if (selectedKbId === kbId) {
    // Clicking the same KB → deselect
    if (selectedKbId) saveConversation();
    selectedKbId = null; selectedKbName = null;
  } else {
    // Switching to a different KB
    if (selectedKbId) saveConversation();
    selectedKbId = kbId;
    selectedKbName = kbName;
  }

  conversationId = null;
  updateChatHeader();
  updateUploadBtn();
  updateSelectorLabel();
  renderKBDropdown();
  closeKbDropdown();

  if (selectedKbId) {
    var stored = loadConversation(selectedKbId);
    if (stored && stored.messages && stored.messages.length > 0) {
      conversationId = stored.conversationId;
      chatMessages.innerHTML = '';
      stored.messages.forEach(function(msg) {
        appendMessageEl(msg.role, msg.text, null, false);
      });
    } else {
      clearChat();
    }
  } else {
    clearChat();
  }

  refreshDocs();
  document.querySelectorAll('.doc-item').forEach(el => el.classList.remove('selected'));
}

function updateSelectorLabel() {
  const label = document.getElementById('kb-selector-label');
  if (!label) return;
  label.textContent = selectedKbId ? selectedKbName : '请选择知识库';
}

function updateUploadBtn() {
  const btn = document.getElementById('btn-upload');
  if (!btn) return;
  if (selectedKbId) {
    btn.classList.add('kb-active');
    btn.querySelector('.btn-upload-text').textContent = '上传到知识库';
  } else {
    btn.classList.remove('kb-active');
    btn.querySelector('.btn-upload-text').textContent = '请先选择知识库';
  }
}

function closeKbDropdown() {
  const dropdown = document.getElementById('kb-dropdown');
  const selector = document.getElementById('kb-selector');
  if (dropdown) dropdown.style.display = 'none';
  if (selector) selector.classList.remove('open');
}

function triggerUpload() {
  fileInput.click();
}

async function deleteKB(kbId) {
  if (!confirm('删除此知识库？此操作不可撤销。')) return;
  try {
    const resp = await fetch(`${API_BASE}/api/v1/knowledge-bases/${kbId}`, { method: 'DELETE' });
    if (resp.ok) {
      if (selectedKbId === kbId) {
        selectedKbId = null; selectedKbName = null; conversationId = null;
        updateChatHeader();
        updateUploadBtn();
        updateSelectorLabel();
        clearChat();
      }
      showToast('知识库已删除', 'info');
    } else {
      const err = await resp.json();
      showToast('删除失败: ' + (err.detail || '错误'), 'error');
    }
  } catch (e) {
    showToast('删除异常: ' + e.message, 'error');
  }
  refreshKBs();
  refreshDocs();
}

/* Click outside to close dropdown */
document.addEventListener('click', function(e) {
  const selector = document.getElementById('kb-selector');
  if (selector && !selector.contains(e.target)) {
    closeKbDropdown();
  }
});

/* ============================================
   KB Create/Edit Modal
   ============================================ */
function showCreateKBModal() {
  let modal = document.getElementById('kb-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'kb-modal';
    modal.className = 'kb-modal-overlay';
    modal.innerHTML = `
      <div class="kb-modal-card">
        <h3>新建知识库</h3>
        <input id="kb-name-input" type="text" placeholder="知识库名称" maxlength="200" />
        <textarea id="kb-desc-input" placeholder="描述（可选）" maxlength="1000" rows="3"></textarea>
        <div class="kb-modal-actions">
          <button onclick="closeKBModal()">取消</button>
          <button class="primary" onclick="createKB()">创建</button>
        </div>
      </div>`;
    document.body.appendChild(modal);
  }
  modal.style.display = 'flex';
  document.getElementById('kb-name-input').value = '';
  document.getElementById('kb-desc-input').value = '';
  setTimeout(() => document.getElementById('kb-name-input').focus(), 100);
}

function closeKBModal() {
  const modal = document.getElementById('kb-modal');
  if (modal) modal.style.display = 'none';
}

async function createKB() {
  const name = document.getElementById('kb-name-input').value.trim();
  const desc = document.getElementById('kb-desc-input').value.trim();
  if (!name) { showToast('名称不能为空', 'error'); return; }
  try {
    const resp = await fetch(`${API_BASE}/api/v1/knowledge-bases/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: desc, domain: selectedDomain }),
    });
    if (resp.ok) {
      const kb = await resp.json();
      showToast(`知识库 "${kb.name}" 已创建`, 'success');
      closeKBModal();
      refreshKBs();
    } else {
      const err = await resp.json();
      showToast('创建失败: ' + (err.detail || '错误'), 'error');
    }
  } catch (e) {
    showToast('创建异常: ' + e.message, 'error');
  }
}

async function uploadToKB(file) {
  if (!selectedKbId) { showToast('请先选择知识库', 'warning'); return; }
  const maxSize = 10 * 1024 * 1024;
  const allowed = ['.pdf', '.txt', '.md', '.csv', '.docx'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) { showToast('不支持的文件类型: ' + ext, 'error'); return; }
  if (file.size > maxSize) { showToast('文件超过 10MB 限制', 'error'); return; }

  uploadProgress.classList.add('active');
  uploadFilename.textContent = file.name;
  uploadPercent.textContent = '0%';
  progressFill.style.width = '0%';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/api/v1/knowledge-bases/${selectedKbId}/upload`);

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
        showToast('已上传到知识库: ' + file.name, 'success');
        refreshKBs();
        refreshDocs();
      } else {
        let detail = '上传失败';
        try { detail = JSON.parse(xhr.responseText).detail || '上传失败'; } catch(e) {}
        showToast('上传失败: ' + detail, 'error');
      }
    };

    xhr.onerror = () => {
      resetUploadProgress();
      showToast('网络错误', 'error');
    };
    xhr.send(formData);
  } catch (e) {
    resetUploadProgress();
    showToast('上传异常: ' + e.message, 'error');
  }
}

async function refreshDocs() {
  if (!selectedKbId) {
    docList.innerHTML = '' +
      '<div class="empty-state">' +
        '<div class="empty-icon">📚</div>' +
        '<p>知识库（Knowledge Base）是存放和管理文档的地方</p>' +
        '<p style="font-size:12px;color:var(--text-muted);margin-top:6px;">将公司制度、技术文档、流程文件上传到知识库，AI 即可跨文档检索，秒级给出答案</p>' +
      '</div>';
    var badge = document.getElementById('doc-count-badge');
    if (badge) badge.textContent = '请选择知识库';
    var inlineCount = document.getElementById('doc-count-inline');
    if (inlineCount) inlineCount.textContent = '';
    return;
  }
  try {
    var url = `${API_BASE}/api/v1/knowledge-bases/${selectedKbId}/documents`;
    const resp = await fetch(url);
    if (!resp.ok) return;
    const data = await resp.json();
    renderDocList(data.items);
    const count = data.items ? data.items.length : 0;
    const badge = document.getElementById('doc-count-badge');
    if (badge) badge.textContent = `${count} 个文档`;
    const inlineCount = document.getElementById('doc-count-inline');
    if (inlineCount) inlineCount.textContent = `${count} 个文档`;
  } catch (e) {
    console.error('获取文档列表失败:', e);
  }
}

function renderDocList(items) {
  if (!items || items.length === 0) {
    docList.innerHTML = '' +
      '<div class="empty-state">' +
        '<div class="empty-icon">📭</div>' +
        '<p>' + (selectedKbId ? '该知识库暂无文档，点击「上传到知识库」添加文件' : '知识库（Knowledge Base）是存放和管理文档的地方。将文档上传到知识库后，AI 即可跨文档检索，智能回答你的问题。') + '</p>' +
      '</div>';
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

    return `
      <div class="doc-item" data-doc-id="${doc.id}">
        <div class="doc-item-info" onclick="previewDocument('${doc.id}')" title="点击预览文档内容">
          <div class="doc-icon ${iconClass}">${ext.toUpperCase()}</div>
          <div class="doc-meta">
            <div class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
            <div class="doc-date">${date} · ${size}</div>
          </div>
          <span class="status-tag ${statusClass}">${statusLabel}</span>
        </div>
        ${doc.status === 'failed' && doc.error_message ? `
          <div class="doc-error-message" title="${escapeHtml(doc.error_message)}">⚠️ ${escapeHtml(doc.error_message.substring(0, 50))}${doc.error_message.length > 50 ? '...' : ''}</div>
        ` : ''}
        <div class="doc-actions">
          ${doc.status === 'uploaded' || doc.status === 'failed' ? `
            <button class="btn-icon success" title="处理文档" onclick="event.stopPropagation();processDocument('${doc.id}','${escapeHtml(doc.filename)}')">⚡</button>
          ` : ''}
          <button class="btn-icon danger" title="删除" onclick="event.stopPropagation();deleteDocument('${doc.id}')">🗑️</button>
        </div>
      </div>`;
  }).join('');
}

function updateChatHeader() {
  const convIndicator = conversationId
    ? `<span class="conv-badge" title="多轮对话中">🔄</span>`
    : '';
  if (selectedKbId) {
    chatDocName.innerHTML = DOMAINS[selectedDomain]?.icon + ' ' + selectedKbName + convIndicator;
    chatDocStatus.textContent = DOMAINS[selectedDomain]?.name + ' · 检索知识库内全部文档回答';
    chatInput.disabled = false;
    btnSend.disabled = false;
    return;
  }
  chatDocName.innerHTML = '选择知识库开始对话';
  chatDocStatus.textContent = '请先选择或创建一个知识库';
  chatInput.disabled = true;
  btnSend.disabled = true;
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
    var superscripts = '¹²³⁴⁵⁶⁷⁸⁹';
    var markers = sources.map(function(_, i) {
      var num = superscripts[i] || (i + 1);
      return '<sup class="cite-sup">[' + num + ']</sup>';
    }).join('');
    bubble.innerHTML += '<span class="cite-markers">' + markers + '</span>';

    var sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';
    var sourcesHtml = '<div style="font-weight:500;margin-bottom:6px;">📎 来源：</div>';
    sources.forEach(function(s, i) {
      var num = superscripts[i] || (i + 1);
      var name = s.split(/[\\/]/).pop();
      sourcesHtml += '<div class="source-line"><span class="source-num">[' + num + ']</span><span class="source-tag">' + escapeHtml(name) + '</span></div>';
    });
    sourcesDiv.innerHTML = sourcesHtml;
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
  conversationId = null;
  clearStoredConversation(selectedKbId);
  updateChatHeader();
  renderDomainIntro(selectedDomain);
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

// ── Send Message ─────────────────────────────────────
async function sendMessage() {
  var question = chatInput.value.trim();
  if (!question) return;

  if (!selectedKbId) {
    showToast('请先选择知识库', 'warning');
    return;
  }

  chatInput.value = '';
  chatInput.style.height = 'auto';
  chatInput.disabled = true;
  btnSend.disabled = true;

  appendMessageEl('user', question, null, true);
  showTypingIndicator();

  var payload = {
    kb_id: selectedKbId,
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
      appendMessageEl('assistant', '❌ 出了问题：' + (err.detail || '请求失败'), null, true);
      chatInput.disabled = false; btnSend.disabled = false; chatInput.focus();
      return;
    }

    var reader = resp.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';
    var fullText = '';
    var metaData = { sources: [] };

    var streamMsg = document.createElement('div');
    streamMsg.className = 'message assistant streaming';
    streamMsg.innerHTML = '<div class="message-avatar">🤖</div>' +
      '<div class="message-bubble" style="white-space:pre-wrap;word-break:break-word;"></div>';
    var empty = chatMessages.querySelector('.chat-empty');
    if (empty) empty.remove();
    chatMessages.appendChild(streamMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    var streamBubble = streamMsg.querySelector('.message-bubble');

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
          }
        } catch(e) {}
      }
    }

    streamMsg.classList.remove('streaming');
    if (streamBubble) {
      streamBubble.innerHTML = formatAssistantText(fullText);
      if (metaData.sources && metaData.sources.length > 0) {
        var superscripts = '¹²³⁴⁵⁶⁷⁸⁹';
        var markers = metaData.sources.map(function(_, i) {
          var num = superscripts[i] || (i + 1);
          return '<sup class="cite-sup">[' + num + ']</sup>';
        }).join('');
        streamBubble.innerHTML += '<span class="cite-markers">' + markers + '</span>';

        var sd = document.createElement('div');
        sd.className = 'message-sources';
        var sHtml = '<div style="font-weight:500;margin-bottom:6px;">📎 来源：</div>';
        metaData.sources.forEach(function(s, i) {
          var num = superscripts[i] || (i + 1);
          var name = s.split(/[\\/]/).pop();
          sHtml += '<div class="source-line"><span class="source-num">[' + num + ']</span><span class="source-tag">' + escapeHtml(name) + '</span></div>';
        });
        sd.innerHTML = sHtml;
        streamBubble.appendChild(sd);
      }
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveConversation();
    updateChatHeader();
  } catch(e) {
    removeTypingIndicator();
    appendMessageEl('assistant', '❌ 网络错误：' + e.message, null, true);
  }

  chatInput.disabled = false;
  btnSend.disabled = false;
  chatInput.focus();
}

// ── History Panel ───────────────────────────────────
var _historyPanelDocId = null;

async function toggleHistoryPanel() {
  var panel = document.getElementById('history-panel');
  var isOpen = panel.classList.toggle('open');
  if (isOpen) {
    _historyPanelDocId = selectedKbId;
    if (_historyPanelDocId) {
      await loadHistory(_historyPanelDocId);
    } else {
      document.getElementById('history-panel-body').innerHTML =
        '<div class="empty-state"><p>📋 请先选择知识库</p></div>';
    }
  }
}

async function loadHistory(kbId) {
  try {
    var resp = await fetch('/api/v1/qa/history/' + kbId + '?limit=100');
    if (!resp.ok) return;
    var data = await resp.json();
    renderHistoryPanel(data.items || []);
  } catch(e) { console.error('loadHistory:', e); }
}

function renderHistoryPanel(items) {
  var panel = document.getElementById('history-panel-body');
  if (!panel) return;
  if (!items || items.length === 0) {
    panel.innerHTML = '<div class="empty-state" style="padding:24px 16px;"><p>📭 暂无对话记录</p><p style="font-size:11px;color:var(--text-muted);margin-top:4px;">开始提问后，对话将自动保存</p></div>';
    return;
  }

  var groups = {};
  for (var i = 0; i < items.length; i++) {
    var r = items[i];
    if (!groups[r.conversation_id]) groups[r.conversation_id] = [];
    groups[r.conversation_id].push(r);
  }
  var convIds = Object.keys(groups);

  var headerHtml = '<div style="padding:8px 12px;font-size:11px;color:var(--text-muted);border-bottom:1px solid var(--border);">共 ' + convIds.length + ' 个对话 · ' + items.length + ' 条消息</div>';

  var listHtml = convIds.map(function(cid) {
    var conv = groups[cid];
    var firstQ = null;
    for (var j = 0; j < conv.length; j++) {
      if (conv[j].role === 'user') { firstQ = conv[j]; break; }
    }
    var preview = firstQ ? firstQ.content.slice(0, 60) : '(空对话)';
    var date = conv[0].created_at ? new Date(conv[0].created_at).toLocaleString('zh-CN') : '';
    return '<div class="history-item">' +
      '<div class="history-item-main" onclick="restoreConversation(\'' + cid + '\')">' +
        '<div style="font-weight:500;font-size:13px;line-height:1.4;margin-bottom:4px;">💬 ' + escapeHtml(preview) + (preview.length >= 60 ? '...' : '') + '</div>' +
        '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);">' +
          '<span>📝 ' + conv.length + ' 条消息</span>' +
          '<span>🕐 ' + date + '</span>' +
        '</div>' +
      '</div>' +
      '<button class="history-del-btn" onclick="event.stopPropagation();deleteHistoryConversation(\'' + cid + '\')" title="删除该对话历史">✕</button>' +
    '</div>';
  }).join('');

  panel.innerHTML = headerHtml + listHtml;
}

async function restoreConversation(convId) {
  if (!_historyPanelDocId) return;
  conversationId = convId;
  chatMessages.innerHTML = '';
  try {
    var resp = await fetch('/api/v1/qa/history/' + _historyPanelDocId + '?conversation_id=' + convId + '&limit=100');
    if (!resp.ok) { console.error('restoreConversation: HTTP', resp.status); return; }
    var data = await resp.json();
    var items = data.items || [];
    for (var i = 0; i < items.length; i++) {
      var sources = items[i].sources;
      if (typeof sources === 'string') {
        try { sources = JSON.parse(sources); } catch(e) { sources = []; }
      }
      appendMessageEl(items[i].role, items[i].content, sources, false);
    }
    updateChatHeader();
    saveConversation();
    toggleHistoryPanel();
    if (items.length > 0) showToast('已恢复 ' + items.length + ' 条消息', 'info');
  } catch(e) { console.error('restoreConversation:', e); }
}

async function deleteHistoryConversation(convId) {
  if (!confirm('确定要删除该对话历史吗？此操作不可恢复。')) return;
  try {
    var resp = await fetch('/api/v1/qa/conversation/' + encodeURIComponent(convId), { method: 'DELETE' });
    if (!resp.ok) { showToast('删除失败', 'error'); return; }
    var data = await resp.json();
    showToast('已删除 ' + (data.deleted_records || 0) + ' 条记录', 'info');
    if (conversationId === convId) clearChat();
    if (_historyPanelDocId) await loadHistory(_historyPanelDocId);
  } catch(e) { console.error('deleteHistoryConversation:', e); showToast('删除失败', 'error'); }
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

    if (doc.file_type === '.md') {
      var textResp = await fetch('/api/v1/documents/' + docId + '/content');
      if (textResp.ok) {
        var text = await textResp.text();
        if (typeof marked !== 'undefined') {
          marked.setOptions({ breaks: true, gfm: true });
          document.getElementById('preview-content').innerHTML =
            '<div class="markdown-preview">' + marked.parse(text.slice(0, 50000)) + '</div>';
        } else {
          document.getElementById('preview-content').innerHTML =
            '<pre style="white-space:pre-wrap;word-break:break-word;font-size:13px;line-height:1.7;padding:16px;">' +
            escapeHtml(text.slice(0, 30000)) + '</pre>';
        }
      }
    } else if (doc.file_type === '.txt') {
      var textResp = await fetch('/api/v1/documents/' + docId + '/content');
      if (textResp.ok) {
        var text = await textResp.text();
        document.getElementById('preview-content').innerHTML =
          '<pre style="white-space:pre-wrap;word-break:break-word;font-size:13px;line-height:1.7;padding:16px;">' +
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
initTheme();
refreshDocs();
refreshKBs();
renderDomainIntro('enterprise');
