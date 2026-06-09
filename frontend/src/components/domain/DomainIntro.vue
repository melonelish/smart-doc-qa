<template>
  <div class="domain-intro">
    <div class="domain-intro-header">
      <div class="welcome-icon">{{ domain.icon }}</div>
      <h1 class="welcome-title">{{ domain.name }}</h1>
      <p class="welcome-subtitle">{{ domain.description }}</p>
    </div>

    <!-- Features -->
    <div class="mb-6">
      <div class="domain-section-label">常见问题示例</div>
      <div class="domain-features">
        <div v-for="(f, i) in domain.features" :key="i" class="domain-feature">
          <span class="domain-feature-q">{{ f.q }}</span>
          <span class="domain-feature-a">{{ f.a }}</span>
        </div>
      </div>
    </div>

    <!-- Doc Types -->
    <div class="mb-6">
      <div class="domain-section-label">支持文档类型</div>
      <div class="domain-doc-types">
        <div v-for="(dt, i) in domain.docTypes" :key="i" class="domain-doc-type">
          <div class="domain-doc-type-icon">{{ dt.icon }}</div>
          <div class="domain-doc-type-name">{{ dt.name }}</div>
          <div class="domain-doc-type-desc">{{ dt.desc }}</div>
        </div>
      </div>
    </div>

    <!-- Capabilities -->
    <div class="mb-6">
      <div class="domain-section-label">核心能力</div>
      <div class="domain-capabilities">
        <div v-for="(c, i) in domain.capabilities" :key="i" class="domain-capability">
          <div class="domain-capability-icon">{{ c.icon }}</div>
          <div class="domain-capability-body">
            <div class="domain-capability-label">{{ c.label }}</div>
            <div class="domain-capability-desc">{{ c.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="domain-intro-footer">
      <n-button class="create-kb-btn" type="primary" size="large" @click="ui.createKBModalOpen = true">
        ＋ 创建知识库开始使用
      </n-button>
      <p class="welcome-hint mt-2">支持 PDF / TXT / Markdown / CSV / Word</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'
import { useUiStore } from '../../stores/ui'
import { useDomainStore } from '../../stores/domain'

const ui = useUiStore()
const domainStore = useDomainStore()
const domain = domainStore.currentDomain
</script>

<style scoped>
.domain-intro {
  max-width: 540px;
  margin: 0 auto;
  padding: 20px 10px;
}
.domain-intro-header {
  margin-bottom: 28px;
  text-align: center;
}
.welcome-icon {
  font-size: 48px;
  margin-bottom: 10px;
}
.welcome-title {
  font-size: 26px;
  font-weight: 800;
  background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 6px;
}
.welcome-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.kb-selector-area {
  margin-top: 16px;
  max-width: 320px;
  margin-left: auto;
  margin-right: auto;
}
.domain-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.domain-features {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.domain-feature {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.domain-feature-q {
  font-weight: 600;
  color: var(--accent-light);
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}
.domain-feature-a {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}
.domain-doc-types {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.domain-doc-type {
  padding: 10px 12px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  text-align: center;
}
.domain-doc-type-icon { font-size: 20px; margin-bottom: 4px; }
.domain-doc-type-name { font-size: 12px; font-weight: 600; color: var(--text-primary); margin-bottom: 2px; }
.domain-doc-type-desc { font-size: 10px; color: var(--text-muted); line-height: 1.3; }
.domain-capabilities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.domain-capability {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  transition: border-color 0.2s;
}
.domain-capability:hover {
  border-color: var(--accent);
}
.domain-capability-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-input);
  border-radius: 6px;
}
.domain-capability-label { font-size: 11px; font-weight: 600; color: var(--text-primary); }
.domain-capability-desc { font-size: 10px; color: var(--text-muted); line-height: 1.3; }
.domain-intro-footer {
  text-align: center;
  padding: 16px 0 8px;
  border-top: 1px solid var(--border);
  margin-top: 8px;
}
.welcome-hint {
  font-size: 11px;
  color: var(--text-muted);
}
.mt-2 { margin-top: 8px; }
.create-kb-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
  color: #fff !important;
  border: none !important;
  font-weight: 500;
}
.create-kb-btn:hover {
  background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%) !important;
}
.kb-active-banner {
  margin-top: 12px;
  padding: 8px 14px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  font-size: 12px;
  color: #10b981;
  text-align: center;
}
</style>