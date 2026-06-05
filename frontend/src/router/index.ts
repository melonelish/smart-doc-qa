import { createRouter, createWebHistory } from 'vue-router'
import DomainHome from '../views/DomainHome.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: DomainHome,
    },
    {
      path: '/kb/:kbId',
      name: 'knowledgeBase',
      component: () => import('../views/KnowledgeBaseView.vue'),
    },
    {
      path: '/doc/:docId',
      name: 'document',
      component: () => import('../views/DocumentView.vue'),
    },
  ],
})

export default router
