<template>
  <n-modal
    :show="true"
    preset="card"
    title="📚 创建知识库"
    style="width: 420px; max-width: 90vw"
    :mask-closable="false"
    @update:show="close"
  >
    <n-space vertical size="medium">
      <n-input
        v-model:value="name"
        placeholder="知识库名称"
        :maxlength="200"
        @keyup.enter="submit"
      />
      <n-input
        v-model:value="description"
        type="textarea"
        placeholder="知识库描述（可选）"
        :rows="3"
        :maxlength="1000"
      />
      <n-space justify="end">
        <n-button @click="close">取消</n-button>
        <n-button type="primary" :disabled="!name.trim()" @click="submit">创建</n-button>
      </n-space>
    </n-space>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NModal, NInput, NButton, NSpace, useMessage } from 'naive-ui'
import { useUiStore } from '../../stores/ui'
import { useKnowledgeBaseStore } from '../../stores/knowledgeBase'
import { useDomainStore } from '../../stores/domain'

const ui = useUiStore()
const kbStore = useKnowledgeBaseStore()
const domainStore = useDomainStore()
const message = useMessage()

const name = ref('')
const description = ref('')

async function submit() {
  if (!name.value.trim()) return
  try {
    await kbStore.create({
      name: name.value.trim(),
      description: description.value.trim(),
      domain: domainStore.current,
    })
    message.success('知识库创建成功')
    ui.createKBModalOpen = false
    name.value = ''
    description.value = ''
  } catch (e: any) {
    message.error('创建失败: ' + (e.response?.data?.detail || e.message))
  }
}

function close() {
  ui.createKBModalOpen = false
}
</script>