<template>
  <nav class="sidebar-nav">
    <div class="nav-section-label">领域导航</div>
    <button
      v-for="d in domainStore.domains"
      :key="d.id"
      class="domain-item"
      :class="{ active: domainStore.current === d.id, disabled: d.id === 'legal' }"
      @click="domainStore.select(d.id)"
    >
      <span class="nav-icon">{{ d.icon }}</span>
      {{ d.name }}
      <span v-if="d.id === 'legal'" class="dev-badge">开发中</span>
    </button>
  </nav>
</template>

<script setup lang="ts">
import { useDomainStore } from '../../stores/domain'
const domainStore = useDomainStore()
</script>

<style scoped>
.sidebar-nav {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-section-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  padding: 6px 8px 4px;
  font-weight: 600;
}
.domain-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
  font-size: 12px;
  font-weight: 500;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
}
.domain-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}
.domain-item.active {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
}
.domain-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.domain-item .nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}
.dev-badge {
  font-size: 8px;
  padding: 1px 5px;
  border-radius: 8px;
  background: var(--bg-input);
  color: var(--text-muted);
  margin-left: auto;
}
</style>
