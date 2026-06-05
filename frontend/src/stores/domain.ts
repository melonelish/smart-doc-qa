import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DomainDefinition } from '../api/types'

export const useDomainStore = defineStore('domain', () => {
  const current = ref<string>('enterprise')

  const domains = ref<DomainDefinition[]>([
    {
      id: 'enterprise',
      name: '企业助手',
      icon: '🏢',
      description: '你公司的内部知识库。上传制度、技术文档、流程文件，AI 帮你在秒级找到答案。',
      features: [
        { q: '「年假怎么休？」', a: '查询公司制度、考勤规定' },
        { q: '「报销流程是什么？」', a: '按步骤列出财务流程 + 引用相关制度文档' },
        { q: '「对比Q1和Q2的利润率趋势」', a: '自动提取多份报表数据，生成对比分析' },
      ],
      docTypes: [
        { icon: '📄', name: '公司制度', desc: '员工手册、考勤报销、绩效制度' },
        { icon: '📘', name: '技术文档', desc: 'API 文档、架构设计、运维手册' },
        { icon: '📋', name: '流程文件', desc: 'SOP、审批流程、项目管理规范' },
      ],
      capabilities: [
        { icon: '🎯', label: '精准匹配', desc: '从海量文档中秒级定位答案' },
        { icon: '📑', label: '条款溯源', desc: '每个回答附带原始出处引用' },
        { icon: '📊', label: '表格解析', desc: 'PDF 表格数据自动提取与精确回答' },
        { icon: '🔄', label: '多文档对比', desc: '自动关联多份文档，生成对比分析表格' },
        { icon: '🤖', label: 'Agent 自主决策', desc: '自动判断是否需要联网搜索或精确计算' },
      ],
    },
    {
      id: 'research',
      name: '科研助手',
      icon: '🔬',
      description: '你的智能文献分析伙伴。上传学术论文、实验报告，AI 深度分析、交叉对比。',
      features: [
        { q: '「这篇论文的核心创新点？」', a: '提炼方法、结果与贡献，标注置信度' },
        { q: '「这几篇论文方法有何异同？」', a: '交叉对比技术路线与实验设置' },
      ],
      docTypes: [
        { icon: '📄', name: '学术论文', desc: '期刊论文、会议论文、预印本' },
        { icon: '📊', name: '实验数据', desc: '实验报告、统计结果、方法说明' },
      ],
      capabilities: [
        { icon: '📊', label: '置信度标注', desc: '高/中/低三档区分结论可信程度' },
        { icon: '⚠️', label: '批判性分析', desc: '主动指出方法局限与潜在风险' },
        { icon: '🔍', label: '溯源追问', desc: '回答后自动生成深入追问建议' },
      ],
    },
    {
      id: 'legal',
      name: '法律助手',
      icon: '⚖️',
      description: '分析法律文件、合同条款和法规条文。',
      features: [
        { q: '「这份合同有什么风险？」', a: '逐条分析条款风险' },
      ],
      docTypes: [
        { icon: '📄', name: '合同协议', desc: '合作协议、保密协议、服务合同' },
        { icon: '📚', name: '法规条文', desc: '法律法规、行业规范' },
      ],
      capabilities: [
        { icon: '⚠️', label: '风险提示', desc: '主动识别法律风险点' },
      ],
    },
  ])

  const currentDomain = computed(() =>
    domains.value.find((d) => d.id === current.value) || domains.value[0],
  )

  function select(id: string) {
    current.value = id
  }

  return { current, domains, currentDomain, select }
})
