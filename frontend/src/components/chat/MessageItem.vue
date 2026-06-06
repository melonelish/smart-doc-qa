<template>
  <div class="message" :class="message.role">
    <div class="message-avatar">{{ message.role === 'user' ? '👤' : '🤖' }}</div>
    <div class="message-bubble">
      <div v-if="message.content === ''" class="typing-indicator-inline">
        <span></span><span></span><span></span>
      </div>
      <div v-else class="message-content" v-html="renderedContent"></div>
      <!-- Sources -->
      <div v-if="message.sourceDetails?.length" class="message-sources">
        <div v-for="(sd, i) in message.sourceDetails" :key="i" class="source-line">
          <span class="source-num">[{{ i + 1 }}]</span>
          <span>{{ sd.source }}</span>
        </div>
      </div>
      <!-- Tool calls -->
      <div v-if="message.toolLog?.length" class="tool-log">
        <div class="tl-header" @click="toolLogOpen = !toolLogOpen" role="button" tabindex="0">
          <div class="tl-header-left">
            <span class="tl-icon">🔧</span>
            <span class="tl-title">工具调用过程</span>
            <span class="tl-badge">{{ message.toolLog.length }}步</span>
          </div>
          <div class="tl-header-right">
            <span class="tl-status" v-if="!toolLogOpen">点击展开详情</span>
            <svg
              class="tl-arrow"
              :class="{ open: toolLogOpen }"
              width="14" height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>
        </div>
        <transition name="tl-expand">
          <div v-show="toolLogOpen" class="tl-body">
            <div
              v-for="(t, i) in message.toolLog"
              :key="i"
              class="tl-step"
            >
              <div class="tl-step-connector">
                <div class="tl-step-dot">{{ i + 1 }}</div>
                <div v-if="i < message.toolLog.length - 1" class="tl-step-line"></div>
              </div>
              <div class="tl-step-card">
                <div class="tl-step-header">
                  <span class="tl-step-icon">{{ toolIcons[t.tool] || '⚙️' }}</span>
                  <span class="tl-step-name">{{ toolNames[t.tool] || t.tool }}</span>
                  <span class="tl-step-status">✅ 完成</span>
                </div>
                <div class="tl-step-detail">
                  <div class="tl-section-label">参数</div>
                  <div class="tl-args-grid">
                    <div
                      v-for="(val, key) in t.args"
                      :key="key"
                      class="tl-arg-item"
                    >
                      <span class="tl-arg-key">{{ key }}</span>
                      <code class="tl-arg-val">{{ String(val) }}</code>
                    </div>
                  </div>
                  <div class="tl-section-label">结果</div>
                  <div class="tl-result-box">
                    <svg class="tl-result-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span class="tl-result-text">{{ t.result.slice(0, 200) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
      <!-- Method tag -->
      <n-tag v-if="message.retrievalMethod" size="tiny" :bordered="false" style="margin-top: 6px">
        {{ message.retrievalMethod }}
      </n-tag>
      <!-- Copy button -->
      <div class="message-actions">
        <button
          class="msg-copy-btn"
          :class="{ copied: copied }"
          @click="handleCopy"
          :title="copied ? '已复制' : '复制消息'"
        >
          <span v-if="copied">✓ 已复制</span>
          <span v-else class="msg-copy-label">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 3px;">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            消息复制
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NTag } from 'naive-ui'
import type { Message } from '../../stores/conversation'

const props = defineProps<{ message: Message; highlight?: string }>()

const copied = ref(false)
const toolLogOpen = ref(false)

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback for non-HTTPS contexts
    const ta = document.createElement('textarea')
    ta.value = props.message.content
    ta.style.position = 'fixed'
    ta.style.left = '-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

const toolIcons: Record<string, string> = { calculator: '🧮', web_search: '🌐' }
const toolNames: Record<string, string> = { calculator: '计算器', web_search: '联网搜索' }

function formatAssistantText(text: string): string {
  if (!text) return ''

  const lines = text.split('\n')

  function esc(s: string) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
  function citeWrap(html: string) {
    return html.replace(/(\[来源[：:][^\]]+\])/g, '<span class="answer-cite">$1</span>')
  }

  function renderInline(s: string): string {
    let h = esc(s)
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    h = h.replace(/__(.+?)__/g, '<strong>$1</strong>')
    h = h.replace(/`([^`]+)`/g, '<code>$1</code>')
    return citeWrap(h)
  }

  const isTableLine = (l: string) => l.trim().startsWith('|') && l.trim().endsWith('|')
  const isSeparator = (l: string) => /^\|[\s\-:|]+\|$/.test(l.trim())

  const result: string[] = []
  let i = 0

  while (i < lines.length) {
    const raw = lines[i]
    const line = raw.trim()

    if (!line) { i++; continue }

    if (/^-{2,}$/.test(line) || /^_{2,}$/.test(line)) {
      result.push('<hr class="ans-hr">')
      i++; continue
    }

    if (line.startsWith('> ')) {
      const quoteLines: string[] = []
      while (i < lines.length && lines[i].trim().startsWith('> ')) {
        quoteLines.push(lines[i].trim().slice(2))
        i++
      }
      result.push('<blockquote class="ans-quote">' + renderInline(quoteLines.join(' ')) + '</blockquote>')
      continue
    }

    if (isTableLine(line) && !isSeparator(line)) {
      const tableLines: string[] = []
      while (i < lines.length && isTableLine(lines[i].trim())) {
        if (!isSeparator(lines[i].trim())) {
          tableLines.push(lines[i].trim())
        }
        i++
      }
      if (tableLines.length > 0) {
        const parseRow = (row: string) => row.split('|').slice(1, -1).map(c => c.trim())
        const header = parseRow(tableLines[0])
        let html = '<div class="ans-table-wrap"><table class="ans-table"><thead><tr>'
        header.forEach(h => { html += '<th>' + renderInline(h) + '</th>' })
        html += '</tr></thead><tbody>'
        for (let r = 1; r < tableLines.length; r++) {
          const cells = parseRow(tableLines[r])
          html += '<tr>' + cells.map(c => '<td>' + renderInline(c) + '</td>').join('') + '</tr>'
        }
        html += '</tbody></table></div>'
        result.push(html)
      }
      continue
    }

    const sectionMatch = line.match(/^(结论|依据|引用|分析|注意|补充|说明|总结|拓展|备注|背景|数据)[：:]\s*(.*)/)
    if (sectionMatch) {
      result.push('<div class="ans-section"><div class="ans-header">' + renderInline(sectionMatch[1]) + '</div>')
      if (sectionMatch[2]) result.push('<p>' + renderInline(sectionMatch[2]) + '</p>')
      i++
      while (i < lines.length) {
        const sl = lines[i].trim()
        if (!sl) { i++; break }
        if (/^-{2,}$/.test(sl) || /^_{2,}$/.test(sl)) { i++; break }
        const subSec = sl.match(/^(结论|依据|引用|分析|注意|补充|说明|总结|拓展|备注|背景|数据)[：:]\s*/) 
        if (subSec) break
        if (/^\d{1,2}[\.\)、]/.test(sl) || /^[\-·•—]\s/.test(sl) || sl.startsWith('>') || isTableLine(sl)) break
        result.push('<p>' + renderInline(sl) + '</p>')
        i++
      }
      result.push('</div>')
      continue
    }

    if (/^\d{1,2}[\.\)、]\s/.test(line)) {
      while (i < lines.length && /^\d{1,2}[\.\)、]\s/.test(lines[i].trim())) {
        const m = lines[i].trim().match(/^(\d{1,2})[\.\)、]\s*(.*)/)
        if (m) result.push('<div class="ans-ol-item"><span class="ans-ol-num">' + m[1] + '</span><span>' + renderInline(m[2]) + '</span></div>')
        i++
      }
      continue
    }

    if (/^[\-·•—]\s/.test(line)) {
      while (i < lines.length && /^[\-·•—]\s/.test(lines[i].trim())) {
        const content = lines[i].trim().replace(/^[\-·•—]\s*/, '')
        result.push('<div class="ans-ul-item"><span class="ans-ul-dot">•</span><span>' + renderInline(content) + '</span></div>')
        i++
      }
      continue
    }

    const headingMatch = line.match(/^([一二三四五六七八九十]+)[、．.]\s*(.*)/)
    if (headingMatch) {
      result.push('<div class="ans-heading2"><span class="ans-heading2-num">' + headingMatch[1] + '、</span>' + renderInline(headingMatch[2]) + '</div>')
      i++; continue
    }

    result.push('<p>' + renderInline(line) + '</p>')
    i++
  }

  return result.join('')
}

const renderedContent = computed(() => {
  let html = ''
  if (props.message.role === 'assistant') {
    try {
      html = formatAssistantText(props.message.content)
    } catch (e) {
      html = ''
    }
    if (!html && props.message.content) {
      html = '<p>' + props.message.content.replace(/\n/g, '<br/>') + '</p>'
    }
    if (props.message.sourceDetails?.length) {
      html = html.replace(/\[(\d+)\]/g, (_, num) => {
        return '<sup class="cite-ref">[' + num + ']</sup>'
      })
    }
  } else {
    html = '<p>' + props.message.content.replace(/\n/g, '<br/>') + '</p>'
  }
  // Apply search highlight
  if (props.highlight) {
    html = highlightText(html, props.highlight)
  }
  return html
})

function highlightText(html: string, query: string): string {
  const q = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${q})`, 'gi')
  // Only highlight text outside HTML tags
  return html.replace(/(>|^)([^<]+)/g, (match, boundary, text) => {
    const highlighted = text.replace(regex, '<mark class="search-highlight">$1</mark>')
    return boundary + highlighted
  })
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 8px;
  animation: fadeInUp 0.25s ease;
  padding: 0;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.message.user {
  margin-left: auto;
  margin-right: 0;
  width: fit-content;
  max-width: 88%;
  justify-content: flex-end;
}
.message.user .message-avatar {
  display: none;
}
.message.assistant {
  align-self: flex-start;
  max-width: 92%;
}
.message-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 2px;
}
.message.user .message-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
}
.message.assistant .message-avatar {
  background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
  color: #fff;
}
.message-bubble {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 13.5px;
  line-height: 1.7;
  word-break: break-word;
  min-width: 60px;
}
.message.user .message-bubble {
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}
.message.assistant .message-bubble {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.message-content {
  font-size: 13.5px;
  line-height: 1.75;
}
.message-content :deep(p) {
  margin: 6px 0;
}
.message-content :deep(strong) {
  color: var(--accent-light);
  font-weight: 600;
}
.message-content :deep(code) {
  background: rgba(99, 102, 241, 0.12);
  color: var(--accent-light);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
  font-family: 'Fira Code', 'Consolas', monospace;
}
.message-content :deep(.ans-hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 10px 0;
}
.message-content :deep(.ans-quote) {
  margin: 8px 0;
  padding: 8px 14px;
  border-left: 3px solid var(--accent);
  background: rgba(99, 102, 241, 0.06);
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary);
  font-size: 12.5px;
  font-style: italic;
}
.message-content :deep(.ans-section) {
  margin: 10px 0;
  padding: 10px 14px;
  background: rgba(99, 102, 241, 0.05);
  border-left: 3px solid var(--accent);
  border-radius: 0 6px 6px 0;
}
.message-content :deep(.ans-header) {
  font-weight: 700;
  color: var(--accent-light);
  font-size: 14px;
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}
.message-content :deep(.ans-heading2) {
  margin: 12px 0 6px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
}
.message-content :deep(.ans-heading2-num) {
  color: var(--accent-light);
  font-weight: 700;
}
.message-content :deep(.ans-ol-item) {
  display: flex;
  gap: 8px;
  margin: 4px 0;
  padding: 3px 0;
  font-size: 13px;
  line-height: 1.7;
}
.message-content :deep(.ans-ol-num) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: var(--accent);
  border-radius: 50%;
  margin-top: 2px;
}
.message-content :deep(.ans-ul-item) {
  display: flex;
  gap: 8px;
  margin: 3px 0;
  padding: 3px 0;
  font-size: 13px;
  line-height: 1.7;
}
.message-content :deep(.ans-ul-dot) {
  flex-shrink: 0;
  color: var(--accent-light);
  font-weight: 700;
  margin-top: 1px;
}
.message-content :deep(.ans-table-wrap) {
  overflow-x: auto;
  margin: 10px 0;
  border-radius: 6px;
  border: 1px solid var(--border);
}
.message-content :deep(.ans-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  line-height: 1.5;
  white-space: nowrap;
}
.message-content :deep(.ans-table th) {
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent-light);
  font-weight: 600;
  text-align: left;
  border-bottom: 2px solid var(--border);
  position: sticky;
  top: 0;
}
.message-content :deep(.ans-table td) {
  padding: 6px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}
.message-content :deep(.ans-table tr:last-child td) {
  border-bottom: none;
}
.message-content :deep(.ans-table tr:hover td) {
  background: rgba(99, 102, 241, 0.04);
}
.message-sources {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-muted);
}
.source-line {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 2px 0;
}
.source-num {
  color: var(--accent-light);
  font-weight: 600;
  min-width: 20px;
  font-size: 10px;
}
.tool-log {
  margin-top: 10px;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}

/* ── Header ── */
.tl-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(15,165,233,0.06) 100%);
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}
.tl-header:hover {
  background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(15,165,233,0.12) 100%);
}
.tl-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tl-icon {
  font-size: 13px;
}
.tl-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}
.tl-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%);
  color: #fff;
  line-height: 1.5;
}
.tl-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tl-status {
  font-size: 10px;
  color: var(--text-muted);
}
.tl-arrow {
  color: var(--text-muted);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tl-arrow.open {
  transform: rotate(180deg);
}

/* ── Expand/Collapse Animation ── */
.tl-expand-enter-active {
  animation: tlExpandIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.tl-expand-leave-active {
  animation: tlExpandIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) reverse;
}
@keyframes tlExpandIn {
  from {
    opacity: 0;
    transform: translateY(-6px) scaleY(0.95);
    max-height: 0;
  }
  to {
    opacity: 1;
    transform: translateY(0) scaleY(1);
    max-height: 800px;
  }
}

/* ── Body ── */
.tl-body {
  padding: 8px 0 2px 0;
}

/* ── Timeline Steps ── */
.tl-step {
  display: flex;
  gap: 10px;
  position: relative;
}
.tl-step-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 22px;
  flex-shrink: 0;
}
.tl-step-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
  flex-shrink: 0;
  z-index: 1;
}
.tl-step-line {
  width: 2px;
  flex: 1;
  min-height: 12px;
  background: linear-gradient(180deg, rgba(99,102,241,0.3) 0%, rgba(15,165,233,0.3) 100%);
  border-radius: 1px;
  margin-top: 2px;
}

/* ── Step Card ── */
.tl-step-card {
  flex: 1;
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 6px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.tl-step-card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
}
.tl-step:last-child .tl-step-card {
  margin-bottom: 0;
}
.tl-step-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
}
.tl-step-icon {
  font-size: 13px;
}
.tl-step-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}
.tl-step-status {
  font-size: 10px;
  color: #52c41a;
  font-weight: 500;
  white-space: nowrap;
}

/* ── Detail Sections ── */
.tl-step-detail {
  padding-left: 0;
}
.tl-section-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 3px;
  margin-top: 4px;
}
.tl-section-label:first-child {
  margin-top: 0;
}

/* Args grid */
.tl-args-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}
.tl-arg-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.1);
  border-radius: 4px;
  padding: 2px 7px;
}
.tl-arg-key {
  font-size: 10px;
  font-weight: 600;
  color: var(--accent-light);
}
.tl-arg-val {
  font-size: 10px;
  color: var(--text-secondary);
  background: none;
  padding: 0;
  font-family: 'Fira Code', 'Consolas', monospace;
  word-break: break-all;
}

/* Result box */
.tl-result-box {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  padding: 4px 8px;
  background: rgba(82, 196, 26, 0.06);
  border: 1px solid rgba(82, 196, 26, 0.15);
  border-radius: 5px;
}
.tl-result-icon {
  flex-shrink: 0;
  margin-top: 3px;
  color: #52c41a;
}
.tl-result-text {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.5;
  word-break: break-word;
}
:deep(.answer-cite) {
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-light);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-style: italic;
}
:deep(.cite-ref) {
  color: var(--accent-light);
  font-size: 10px;
  font-weight: 600;
  vertical-align: super;
}
.typing-indicator-inline {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.typing-indicator-inline span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite;
}
.typing-indicator-inline span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator-inline span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}
.message-actions {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
}
.msg-copy-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.msg-copy-btn:hover {
  background: rgba(99, 102, 241, 0.08);
  color: var(--accent-light);
}
.msg-copy-btn.copied {
  color: #52c41a;
  font-weight: 600;
}
:deep(.search-highlight) {
  background: rgba(99, 102, 241, 0.35);
  color: var(--accent-light);
  padding: 0 3px;
  border-radius: 3px;
  font-weight: 600;
}
</style>