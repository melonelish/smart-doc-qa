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
        <n-collapse>
          <n-collapse-item title="🛠️ 工具调用" :name="'tools'">
            <div v-for="(t, i) in message.toolLog" :key="i" class="tool-log-item">
              <span class="tool-name">{{ toolIcons[t.tool] || '🔢' }} {{ toolNames[t.tool] || t.tool }}</span>
              <code class="tool-args">{{ JSON.stringify(t.args) }}</code>
              <div class="tool-result">{{ t.result.slice(0, 200) }}</div>
            </div>
          </n-collapse-item>
        </n-collapse>
      </div>
      <!-- Method tag -->
      <n-tag v-if="message.retrievalMethod" size="tiny" :bordered="false" style="margin-top: 6px">
        {{ message.retrievalMethod }}
      </n-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTag, NCollapse, NCollapseItem } from 'naive-ui'
import type { Message } from '../../stores/conversation'

const props = defineProps<{ message: Message }>()

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
  return html
})
</script>

<style scoped>
.message {
  display: flex;
  gap: 10px;
  max-width: 85%;
  animation: fadeInUp 0.3s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message.assistant {
  align-self: flex-start;
}
.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
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
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.65;
  word-break: break-word;
}
.message.user .message-bubble {
  background: var(--accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message.assistant .message-bubble {
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
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
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}
.tool-log-item {
  padding: 4px 8px;
  margin: 4px 0;
  background: var(--bg-card);
  border-radius: 4px;
  font-size: 11px;
}
.tool-name {
  color: var(--warning);
  font-weight: 600;
}
.tool-args {
  font-size: 10px;
  color: var(--text-muted);
  margin-left: 4px;
}
.tool-result {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 2px;
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
</style>